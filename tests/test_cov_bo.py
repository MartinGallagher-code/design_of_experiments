# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Targeted line-coverage tests for bo.py, report.py, suggest.py, archive.py.

These tests exercise the edge/error branches that the broader suites leave
uncovered: degenerate GP inputs, minimise-vs-maximise acquisition, batch
fallbacks and constant-liar refit failures, empty/missing report sections,
the design-suggestion decision tree, and archive skip/error paths.

All tests are deterministic (seeded numpy) and hermetic (tmp_path only).
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from doe.models import (
    DOEConfig,
    Factor,
    ResponseVar,
    RunnerConfig,
    DesignMatrix,
    ExperimentRun,
    AnalysisReport,
    StationaryPoint,
    AliasStructure,
    AliasEntry,
)
from doe.design import generate_design
from doe.analysis import analyze

import doe.bo as bo
from doe.bo import (
    fit_gp,
    predict,
    expected_improvement,
    propose_batch,
    is_pareto_front,
    propose_batch_multi_objective,
)
import doe.report as report_mod
from doe.report import (
    _run_optimization,
    _build_optimization,
    _build_results,
    _model_adequacy_html,
    _cross_validation_html,
    _achieved_power_html,
    _stationary_point_html,
    _build_alias_structure,
    _anchor_id,
)
from doe.suggest import suggest
from doe.archive import archive_session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(responses, operation="full_factorial", lhs_samples=0):
    return DOEConfig(
        factors=[
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
        ],
        fixed_factors={},
        responses=responses,
        block_count=1,
        test_script="",
        operation=operation,
        processed_directory="",
        out_directory="",
        lhs_samples=lhs_samples,
    )


def _write_results(results_dir, matrix, value_fn):
    os.makedirs(results_dir, exist_ok=True)
    for i, run in enumerate(matrix.runs):
        with open(os.path.join(results_dir, f"run_{run.run_id}.json"), "w") as f:
            json.dump(value_fn(i, run), f)


class _FakeRSM:
    """Minimal stand-in for an RSM fit result with a controllable R²."""

    def __init__(self, r2):
        self.r_squared = r2
        self.adj_r_squared = r2 - 0.05
        self.coefficients = {"intercept": 1.0, "A": 0.5, "B": -0.25}
        self.predicted_optimum = {"A": "5.0", "B": "5.0"}
        self.predicted_value = 42.0


def _simple_gp(seed=0, n=6):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1.0, 1.0, size=(n, 2))
    y = X[:, 0] * 2.0 - X[:, 1] + rng.normal(0, 0.05, size=n)
    return fit_gp(X, y, seed=seed)


# ===========================================================================
# bo.py
# ===========================================================================

class TestBO:

    def test_fit_gp_requires_two_points(self):
        X = np.array([[0.0, 0.0]])
        y = np.array([1.0])
        with pytest.raises(ValueError, match="at least 2 observations"):
            fit_gp(X, y)

    def test_fit_gp_constant_response(self):
        # y_std == 0 branch: constant data is standardised with y_std = 1.0.
        X = np.array([[-1.0, -1.0], [0.0, 0.0], [1.0, 1.0]])
        y = np.array([5.0, 5.0, 5.0])
        gp = fit_gp(X, y, seed=1)
        assert gp.y_std == 1.0
        mean, var = predict(gp, X)
        assert np.all(var > 0)

    def test_fit_gp_cholesky_failure_branch(self, monkeypatch):
        # Force the first cholesky call inside neg_log_marginal to fail so the
        # LinAlgError -> 1e12 fallback (lines 101-102) is exercised, then let
        # every subsequent call succeed so the final fit still works.
        real_chol = np.linalg.cholesky
        state = {"n": 0}

        def flaky(a):
            state["n"] += 1
            if state["n"] == 1:
                raise np.linalg.LinAlgError("forced failure")
            return real_chol(a)

        monkeypatch.setattr(np.linalg, "cholesky", flaky)
        X = np.array([[-1.0, -1.0], [1.0, 1.0], [0.0, 0.5], [0.5, -0.5]])
        y = np.array([1.0, 4.0, 2.0, 3.0])
        gp = fit_gp(X, y, seed=2)
        assert state["n"] >= 2
        assert gp.L.shape == (4, 4)

    def test_fit_gp_all_starts_fail_fallback_theta(self, monkeypatch):
        # When every optimiser start raises, best stays None and the default
        # theta fallback (line 129) is used.
        def boom(*a, **k):
            raise RuntimeError("optimiser unavailable")

        monkeypatch.setattr("scipy.optimize.minimize", boom)
        X = np.array([[-1.0, -1.0], [1.0, 1.0], [0.0, 0.5], [0.5, -0.5]])
        y = np.array([1.0, 4.0, 2.0, 3.0])
        gp = fit_gp(X, y, seed=3)
        # Default theta = [0, 0, log(0.1)]
        assert abs(gp.log_length_scale) < 1e-9
        assert abs(gp.log_signal_var) < 1e-9

    def test_predict_1d_input_is_reshaped(self):
        gp = _simple_gp()
        mean, var = predict(gp, np.array([0.1, -0.2]))
        assert mean.shape == (1,)
        assert var.shape == (1,)

    def test_expected_improvement_minimize(self):
        gp = _simple_gp()
        cands = np.array([[0.0, 0.0], [0.5, 0.5], [-0.5, 0.5]])
        ei = expected_improvement(gp, cands, best_y=0.0, direction="minimize")
        assert ei.shape == (3,)
        assert np.all(ei >= 0)

    def test_propose_batch_minimize(self):
        gp = _simple_gp()
        bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])
        batch = propose_batch(gp, bounds, batch_size=2, direction="minimize",
                              n_candidates=200, seed=5)
        assert batch.shape == (2, 2)

    def test_propose_batch_variance_fallback(self):
        # With a single candidate, the repulsion term drives EI to zero on the
        # second pick, forcing the max-variance fallback (lines 233-234).
        gp = _simple_gp()
        bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])
        batch = propose_batch(gp, bounds, batch_size=2, direction="maximize",
                              n_candidates=1, seed=7)
        assert batch.shape == (2, 2)

    def test_propose_batch_refit_failure_is_swallowed(self, monkeypatch):
        # The constant-liar refit failure branch (lines 245-248).
        gp = _simple_gp()
        bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])

        def boom(*a, **k):
            raise RuntimeError("refit failed")

        monkeypatch.setattr(bo, "fit_gp", boom)
        batch = propose_batch(gp, bounds, batch_size=1, direction="maximize",
                              n_candidates=100, seed=9)
        assert batch.shape == (1, 2)

    def test_is_pareto_front_direction_length_mismatch(self):
        Y = np.array([[1.0, 2.0], [3.0, 1.0]])
        with pytest.raises(ValueError, match="directions has length"):
            is_pareto_front(Y, ["maximize"])

    def test_is_pareto_front_with_dominated_rows(self):
        Y = np.array([[1.0, 1.0], [2.0, 2.0], [0.5, 0.5]])
        mask = is_pareto_front(Y, ["maximize", "maximize"])
        assert mask[1]  # (2,2) dominates the rest
        assert not mask[0]
        assert not mask[2]
        # Minimise flip branch
        mask_min = is_pareto_front(Y, ["minimize", "minimize"])
        assert mask_min[2]  # (0.5, 0.5) is best when minimising

    def test_multi_objective_requires_gps(self):
        bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])
        with pytest.raises(ValueError, match="at least one GP"):
            propose_batch_multi_objective([], bounds, batch_size=1,
                                          directions=[])

    def test_multi_objective_gps_directions_mismatch(self):
        gp = _simple_gp()
        bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])
        with pytest.raises(ValueError, match="len\\(gps\\) must equal"):
            propose_batch_multi_objective([gp], bounds, batch_size=1,
                                          directions=["maximize", "minimize"])

    def test_multi_objective_score_fallback(self):
        # Single candidate -> repulsion zeroes the score on the second pick,
        # forcing the distance-based fallback (line 380).
        rng = np.random.default_rng(11)
        X = rng.uniform(-1.0, 1.0, size=(6, 2))
        gp1 = fit_gp(X, X[:, 0] * 2.0, seed=11)
        gp2 = fit_gp(X, -X[:, 1] * 1.5, seed=12)
        bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])
        batch = propose_batch_multi_objective(
            [gp1, gp2], bounds, batch_size=2,
            directions=["maximize", "minimize"], n_candidates=1, seed=13,
        )
        assert batch.shape == (2, 2)

    def test_multi_objective_refit_failure_is_swallowed(self, monkeypatch):
        # The multi-objective constant-liar refit failure branch (396-397).
        rng = np.random.default_rng(14)
        X = rng.uniform(-1.0, 1.0, size=(6, 2))
        gp1 = fit_gp(X, X[:, 0] * 2.0, seed=14)
        gp2 = fit_gp(X, -X[:, 1] * 1.5, seed=15)
        bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])

        def boom(*a, **k):
            raise RuntimeError("refit failed")

        monkeypatch.setattr(bo, "fit_gp", boom)
        batch = propose_batch_multi_objective(
            [gp1, gp2], bounds, batch_size=1,
            directions=["maximize", "minimize"], n_candidates=100, seed=16,
        )
        assert batch.shape == (1, 2)


# ===========================================================================
# report.py
# ===========================================================================

class TestReport:

    def test_run_optimization_minimize_branch(self, tmp_path):
        cfg = _make_cfg([ResponseVar(name="y", optimize="minimize")])
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "res")
        _write_results(results_dir, matrix,
                       lambda i, run: {"y": float(10 + i * 5)})
        recs = _run_optimization(matrix, cfg, results_dir)
        assert recs[0]["direction"] == "minimize"

    def test_run_optimization_quad_fit_failure_swallowed(self, tmp_path, monkeypatch):
        # Enough runs to attempt a quadratic fit; force that fit to raise so
        # the except/pass branch (273-274) runs. Linear must still succeed.
        cfg = _make_cfg([ResponseVar(name="y")], operation="latin_hypercube",
                        lhs_samples=10)
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "res")
        _write_results(results_dir, matrix,
                       lambda i, run: {"y": float(20 + i)})

        real_fit = report_mod.fit_rsm

        def wrap(*args, **kwargs):
            if kwargs.get("model_type") == "quadratic":
                raise RuntimeError("quadratic fit failed")
            return real_fit(*args, **kwargs)

        monkeypatch.setattr(report_mod, "fit_rsm", wrap)
        recs = _run_optimization(matrix, cfg, results_dir)
        assert recs[0]["quad_r2"] is None

    @pytest.mark.parametrize("r2,fragment", [
        (0.8, "Good fit"),        # 0.7 < r2 <= 0.9  (line 289)
        (0.6, "Moderate fit"),    # 0.5 < r2 <= 0.7  (line 291)
    ])
    def test_run_optimization_quality_bands(self, tmp_path, monkeypatch, r2, fragment):
        cfg = _make_cfg([ResponseVar(name="y")])
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "res")
        _write_results(results_dir, matrix,
                       lambda i, run: {"y": float(20 + i)})
        monkeypatch.setattr(report_mod, "fit_rsm", lambda *a, **k: _FakeRSM(r2))
        recs = _run_optimization(matrix, cfg, results_dir)
        assert fragment in recs[0]["quality"]

    def test_build_optimization_empty(self):
        cfg = _make_cfg([ResponseVar(name="y")])
        assert _build_optimization([], cfg) == ""

    def test_build_results_no_analysis(self):
        empty = AnalysisReport(results_by_response={})
        html = _build_results(empty, {}, {})
        assert "No analysis results available" in html

    def test_build_results_significant_anova_is_bold(self, tmp_path):
        # A replicated design with a dominant main effect yields an ANOVA row
        # with p < 0.05, exercising the significance-highlight branch (459).
        cfg = DOEConfig(
            factors=[
                Factor(name="A", levels=["0", "10"], type="continuous"),
                Factor(name="B", levels=["0", "10"], type="continuous"),
            ],
            fixed_factors={},
            responses=[ResponseVar(name="y")],
            block_count=1,
            test_script="",
            operation="full_factorial",
            processed_directory="",
            out_directory="",
            replicate_center=3,
        )
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "res")
        jitter = {1: 0.0, 5: 0.2, 7: -0.2}

        def value_fn(i, run):
            x = float(run.factor_values["A"])
            if x == 5:
                return {"y": 15.0 + jitter.get(run.run_id, 0.0)}
            return {"y": 3.0 * x}

        _write_results(results_dir, matrix, value_fn)
        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        html = _build_results(report, {}, {})
        assert 'style="font-weight:bold;"' in html

    def test_model_adequacy_html_none(self):
        assert _model_adequacy_html(None) == ""

    def test_cross_validation_html_none(self):
        assert _cross_validation_html(None) == ""

    def test_achieved_power_html_none(self):
        assert _achieved_power_html(None) == ""

    def test_stationary_point_html_with_ridge(self):
        sp = StationaryPoint(
            nature="ridge",
            coded_location={"A": 0.2, "B": -0.3},
            natural_location={"A": "6.0", "B": "4.0"},
            predicted_value=99.0,
            eigenvalues=[1.5, -0.0001],
            eigenvectors=[[1.0, 0.0], [0.0, 1.0]],
            factor_order=["A", "B"],
            inside_design_region=True,
            ridge_direction={"A": 0.7071, "B": -0.7071},
        )
        html = _stationary_point_html(sp)
        assert "Ridge axis" in html

    def test_build_alias_structure_mixed_entries(self):
        alias = AliasStructure(
            design_type="fractional_factorial",
            resolution=4,
            notes=["A resolution-IV note."],
            main_effects=[
                # Mixes a perfectly-aliased partner (no correlation span) with
                # a partially-aliased one (span rendered), plus an entry with
                # no aliases to hit the skip/continue branch (824-825).
                AliasEntry(effect="A", aliased_with=[("BCD", 1.0), ("EF", 0.5)]),
                AliasEntry(effect="B", aliased_with=[]),
            ],
            two_factor_interactions=[],
        )
        html = _build_alias_structure(alias)
        assert "Main Effects" in html
        assert "BCD" in html
        # The partial-correlation span is rendered for the 0.5 partner only.
        assert "(0.50)" in html

    def test_anchor_id_collapses_repeated_separators(self):
        # Two spaces produce "--" which the while-loop collapses (897-898).
        assert _anchor_id("My  Response") == "my-response"


# ===========================================================================
# suggest.py
# ===========================================================================

class TestSuggest:

    def test_budget_must_be_positive(self):
        with pytest.raises(ValueError, match="budget must be >= 1"):
            suggest(n_factors=2, n_responses=1, budget=0)

    def test_response_surface_categorical_note(self):
        s = suggest(
            n_factors=3, n_responses=1, budget=100, goal="response_surface",
            factor_kinds=["continuous", "continuous", "categorical"],
        )
        assert any("categorical" in r for r in s.rationale)

    def test_response_surface_all_categorical_full_factorial(self):
        s = suggest(
            n_factors=2, n_responses=1, budget=100, goal="response_surface",
            factor_kinds=["categorical", "categorical"],
        )
        assert s.operation == "full_factorial"
        assert s.estimated_runs == 2 ** 2

    def test_response_surface_few_factors_full_factorial_fallback(self):
        # n_cont == 2: skips Box-Behnken (needs 3-5) and CCD (budget too
        # small), and n_cont < 3 skips definitive screening -> full factorial.
        s = suggest(n_factors=2, n_responses=1, budget=5, goal="response_surface")
        assert s.operation == "full_factorial"
        assert s.estimated_runs == 3 ** 2

    def test_optimization_budget_too_small_latin_hypercube(self):
        # seed_runs (8) >= budget -> one-shot Latin hypercube (line 230).
        s = suggest(n_factors=2, n_responses=1, budget=8, goal="optimization")
        assert s.operation == "latin_hypercube"
        assert s.adaptive_strategy is None


# ===========================================================================
# archive.py
# ===========================================================================

class TestArchive:

    def test_missing_config_raises(self, tmp_path):
        session = tmp_path / "sess"
        session.mkdir()
        (session / "run_1.json").write_text("{}")
        with pytest.raises(FileNotFoundError, match="Config not found"):
            archive_session(
                str(session), str(tmp_path / "out.tar.gz"),
                config_path=str(tmp_path / "does_not_exist.json"),
            )

    def test_missing_extra_is_skipped(self, tmp_path, capsys):
        session = tmp_path / "sess"
        session.mkdir()
        (session / "run_1.json").write_text("{}")
        manifest = archive_session(
            str(session), str(tmp_path / "out.tar.gz"),
            extras=[str(tmp_path / "missing_extra.txt")],
        )
        out = capsys.readouterr().out
        assert "skipping missing extra" in out
        assert os.path.isfile(str(tmp_path / "out.tar.gz"))
        assert manifest["tool"] == "doe"
