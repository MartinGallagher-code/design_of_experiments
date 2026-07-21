# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-coverage tests for adaptive.py, sensitivity.py, knee.py, codegen.py.

These target the error/edge branches that the functional test-suite does not
exercise: degenerate factor encoders, strategy fallbacks (GP-fit failures,
propose failures), empty/insufficient inputs, categorical snapping paths,
and small helper edge cases. All inputs are crafted and deterministic
(fixed seeds, ``tmp_path`` only) so the tests are hermetic.
"""

import json
import os
import sys

import numpy as np
import pytest

from doe.models import DOEConfig, DesignMatrix, ExperimentRun, Factor, ResponseVar
from doe.adaptive import (
    AdaptiveConfig,
    AdaptiveState,
    plan_next_batch,
    _multi_objective_strategy,
    _bayesian_strategy,
    _model_guided_strategy,
    _refine_strategy,
    _explore_strategy,
    _decoded_run,
    _build_factor_encoder,
    _FactorEncoder,
    _save_state,
)
from doe.bo import fit_gp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(factors, responses, out_directory=""):
    return DOEConfig(
        factors=factors,
        fixed_factors={},
        responses=responses,
        block_count=1,
        test_script="",
        operation="full_factorial",
        processed_directory="",
        out_directory=out_directory,
    )


def _runs(specs):
    """specs: list of (run_id, factor_values dict)."""
    return [ExperimentRun(run_id=rid, block_id=1, factor_values=fv) for rid, fv in specs]


def _write_results(results_dir, mapping):
    """mapping: dict run_id -> dict of response values."""
    os.makedirs(results_dir, exist_ok=True)
    for run_id, data in mapping.items():
        with open(os.path.join(results_dir, f"run_{run_id}.json"), "w") as f:
            json.dump(data, f)


def _raise(*args, **kwargs):
    raise RuntimeError("forced failure")


# ---------------------------------------------------------------------------
# plan_next_batch top-level branches (87, 95, 109)
# ---------------------------------------------------------------------------

class TestPlanNextBatchBranches:

    def test_empty_matrix_runs_raises(self, tmp_path):
        """No runs at all -> _load_all_results returns {} -> FileNotFoundError (87)."""
        cfg = _make_cfg(
            [Factor(name="A", levels=["0", "10"], type="continuous")],
            [ResponseVar(name="y", optimize="maximize")],
            out_directory=str(tmp_path),
        )
        matrix = DesignMatrix(runs=[], factor_names=["A"], operation="x")
        adaptive_cfg = AdaptiveConfig(strategy="refine", batch_size=2)
        with pytest.raises(FileNotFoundError, match="No result files found"):
            plan_next_batch(matrix, cfg, adaptive_cfg,
                            results_dir=str(tmp_path), seed=0)

    def test_response_name_selection(self, tmp_path):
        """adaptive_cfg.response_name matching a declared response (95)."""
        results_dir = str(tmp_path / "results")
        cfg = _make_cfg(
            [Factor(name="A", levels=["0", "10"], type="continuous"),
             Factor(name="B", levels=["0", "10"], type="continuous")],
            [ResponseVar(name="y", optimize="maximize")],
            out_directory=results_dir,
        )
        matrix = DesignMatrix(
            runs=_runs([
                (1, {"A": "0", "B": "0"}),
                (2, {"A": "10", "B": "0"}),
                (3, {"A": "0", "B": "10"}),
                (4, {"A": "10", "B": "10"}),
            ]),
            factor_names=["A", "B"],
            operation="full_factorial",
        )
        _write_results(results_dir, {r.run_id: {"y": float(r.run_id)} for r in matrix.runs})
        adaptive_cfg = AdaptiveConfig(strategy="refine", batch_size=2, response_name="y")
        new_matrix, state = plan_next_batch(
            matrix, cfg, adaptive_cfg, results_dir=results_dir, seed=0)
        assert len(new_matrix.runs) == 2

    def test_no_data_for_response_raises(self, tmp_path):
        """Files exist but none carry the response value -> FileNotFoundError (109)."""
        results_dir = str(tmp_path / "results")
        cfg = _make_cfg(
            [Factor(name="A", levels=["0", "10"], type="continuous")],
            [ResponseVar(name="y", optimize="maximize")],
            out_directory=results_dir,
        )
        matrix = DesignMatrix(
            runs=_runs([(1, {"A": "0"}), (2, {"A": "10"})]),
            factor_names=["A"],
            operation="full_factorial",
        )
        # Present files, but with the wrong key -> no data for "y".
        _write_results(results_dir, {1: {"other": 1.0}, 2: {"other": 2.0}})
        adaptive_cfg = AdaptiveConfig(strategy="refine", batch_size=2)
        with pytest.raises(FileNotFoundError, match="No data for response"):
            plan_next_batch(matrix, cfg, adaptive_cfg, results_dir=results_dir, seed=0)


# ---------------------------------------------------------------------------
# _FactorEncoder build / encode / decode / propose (478-548, 584, 599-611)
# ---------------------------------------------------------------------------

class TestFactorEncoder:

    def test_build_skips_non_numeric_and_degenerate(self):
        """Non-numeric continuous levels (478-479) and low==high (481) are skipped."""
        factors = [
            Factor(name="bad", levels=["lo", "hi"], type="continuous"),
            Factor(name="same", levels=["5", "5"], type="continuous"),
            Factor(name="good", levels=["0", "10"], type="continuous"),
            Factor(name="cat", levels=["a", "b"], type="categorical"),
        ]
        enc = _build_factor_encoder(["bad", "same", "good", "cat"], factors)
        assert enc is not None
        # Only "good" is numeric; "cat" is the sole categorical.
        assert enc.numeric_names == ["good"]
        assert enc.categorical_names == ["cat"]

    def test_build_returns_none_when_nothing_usable(self):
        """No numeric and no categorical factors -> None (491)."""
        enc = _build_factor_encoder(
            ["same"], [Factor(name="same", levels=["5", "5"], type="continuous")])
        assert enc is None

    def test_encode_bad_numeric_falls_back_to_midpoint(self):
        """Unparseable numeric value -> midpoint (517-518)."""
        enc = _build_factor_encoder(
            ["good"], [Factor(name="good", levels=["0", "10"], type="continuous")])
        row = enc.encode({"good": "not-a-number"})
        # midpoint of [0,10] is 5 -> coded 0.0
        assert row[0] == pytest.approx(0.0)

    def test_encode_unknown_category_uses_index_zero(self):
        """Categorical value not in levels -> idx 0 (525-526)."""
        enc = _build_factor_encoder(
            ["cat"], [Factor(name="cat", levels=["a", "b"], type="categorical")])
        row = enc.encode({"cat": "zzz"})
        assert row[0] == 1.0  # first level slot set

    def test_decode_fills_unencoded_factors(self):
        """A factor present in factor_names but not encodable gets its first level (547-548)."""
        factors = [
            Factor(name="good", levels=["0", "10"], type="continuous"),
            Factor(name="fixed", levels=["only"], type="categorical"),  # 1 level -> unencoded
        ]
        enc = _build_factor_encoder(["good", "fixed"], factors)
        assert enc is not None
        out = enc.decode(np.array([0.0]))
        assert out["fixed"] == "only"
        assert "good" in out

    def test_propose_with_gp_minimize(self):
        """Minimize direction path in propose_with_gp (584)."""
        enc = _build_factor_encoder(
            ["good"], [Factor(name="good", levels=["0", "10"], type="continuous")])
        X = np.array([[-1.0], [-0.4], [0.4], [1.0]])
        y = np.array([4.0, 3.0, 2.0, 1.0])
        gp = fit_gp(X, y, seed=0)
        proposed = enc.propose_with_gp(
            gp, batch_size=2, direction="minimize", n_candidates=40, seed=0)
        assert proposed.shape == (2, 1)

    def test_propose_with_gp_zero_ei_and_refit_failure(self, monkeypatch):
        """EI all-zero -> variance fallback (599-600); refit exception -> pass (610-611)."""
        enc = _build_factor_encoder(
            ["good"], [Factor(name="good", levels=["0", "10"], type="continuous")])
        X = np.array([[-1.0], [-0.4], [0.4], [1.0]])
        y = np.array([1.0, 2.0, 3.0, 4.0])
        gp = fit_gp(X, y, seed=0)  # real fit before patching
        monkeypatch.setattr(
            "doe.bo.expected_improvement",
            lambda g, xs, best, direction="maximize": np.zeros(xs.shape[0]))
        monkeypatch.setattr("doe.bo.fit_gp", _raise)
        proposed = enc.propose_with_gp(
            gp, batch_size=2, direction="maximize", n_candidates=30, seed=0)
        assert proposed.shape == (2, 1)


# ---------------------------------------------------------------------------
# _multi_objective_strategy fallbacks (283, 292, 310, 322-323, 345-346)
# ---------------------------------------------------------------------------

class TestMultiObjectiveStrategy:

    def _matrix(self):
        return DesignMatrix(
            runs=_runs([
                (1, {"A": "0", "B": "0"}),
                (2, {"A": "10", "B": "0"}),
                (3, {"A": "0", "B": "10"}),
                (4, {"A": "10", "B": "10"}),
            ]),
            factor_names=["A", "B"],
            operation="full_factorial",
        )

    def _factors(self):
        return [Factor(name="A", levels=["0", "10"], type="continuous"),
                Factor(name="B", levels=["0", "10"], type="continuous")]

    def test_single_response_delegates_to_bayesian(self, tmp_path):
        """<2 responses -> mono-objective bayesian path (283)."""
        results_dir = str(tmp_path / "results")
        matrix = self._matrix()
        _write_results(results_dir,
                       {r.run_id: {"y1": float(r.run_id)} for r in matrix.runs})
        cfg = _make_cfg(self._factors(), [ResponseVar(name="y1", optimize="maximize")])
        out = _multi_objective_strategy(
            matrix.runs, results_dir, cfg, matrix, batch_size=2, start_run_id=4, seed=0)
        assert len(out) == 2

    def test_encoder_none_delegates_to_model_guided(self, tmp_path):
        """Degenerate factors -> encoder None -> model_guided (292)."""
        results_dir = str(tmp_path / "results")
        matrix = DesignMatrix(
            runs=_runs([(1, {"A": "5"}), (2, {"A": "5"}), (3, {"A": "5"})]),
            factor_names=["A"],
            operation="full_factorial",
        )
        _write_results(results_dir, {
            1: {"y1": 1.0, "y2": 9.0},
            2: {"y1": 2.0, "y2": 8.0},
            3: {"y1": 3.0, "y2": 7.0},
        })
        cfg = _make_cfg(
            [Factor(name="A", levels=["5", "5"], type="continuous")],
            [ResponseVar(name="y1", optimize="maximize"),
             ResponseVar(name="y2", optimize="minimize")],
        )
        out = _multi_objective_strategy(
            matrix.runs, results_dir, cfg, matrix, batch_size=2, start_run_id=3, seed=0)
        assert len(out) >= 1

    def test_response_with_insufficient_data(self, tmp_path):
        """A response with <2 usable points -> bayesian fallback (310)."""
        results_dir = str(tmp_path / "results")
        matrix = self._matrix()
        # y1 on all runs, y2 on only one run.
        _write_results(results_dir, {
            1: {"y1": 1.0, "y2": 5.0},
            2: {"y1": 2.0},
            3: {"y1": 3.0},
            4: {"y1": 4.0},
        })
        cfg = _make_cfg(self._factors(),
                        [ResponseVar(name="y1", optimize="maximize"),
                         ResponseVar(name="y2", optimize="minimize")])
        out = _multi_objective_strategy(
            matrix.runs, results_dir, cfg, matrix, batch_size=2, start_run_id=4, seed=0)
        assert len(out) == 2

    def test_gp_fit_failure_falls_back(self, tmp_path, monkeypatch):
        """fit_gp raising -> bayesian fallback (322-323)."""
        results_dir = str(tmp_path / "results")
        matrix = self._matrix()
        _write_results(results_dir, {
            r.run_id: {"y1": float(r.run_id), "y2": float(10 - r.run_id)}
            for r in matrix.runs
        })
        cfg = _make_cfg(self._factors(),
                        [ResponseVar(name="y1", optimize="maximize"),
                         ResponseVar(name="y2", optimize="minimize")])
        monkeypatch.setattr("doe.bo.fit_gp", _raise)
        out = _multi_objective_strategy(
            matrix.runs, results_dir, cfg, matrix, batch_size=2, start_run_id=4, seed=0)
        assert len(out) == 2

    def test_propose_failure_falls_back(self, tmp_path, monkeypatch):
        """propose_batch_multi_objective raising -> bayesian fallback (345-346)."""
        results_dir = str(tmp_path / "results")
        matrix = self._matrix()
        _write_results(results_dir, {
            r.run_id: {"y1": float(r.run_id), "y2": float(10 - r.run_id)}
            for r in matrix.runs
        })
        cfg = _make_cfg(self._factors(),
                        [ResponseVar(name="y1", optimize="maximize"),
                         ResponseVar(name="y2", optimize="minimize")])
        monkeypatch.setattr("doe.bo.propose_batch_multi_objective", _raise)
        out = _multi_objective_strategy(
            matrix.runs, results_dir, cfg, matrix, batch_size=2, start_run_id=4, seed=0)
        assert len(out) == 2


# ---------------------------------------------------------------------------
# _bayesian_strategy fallbacks (398, 414-415, 424-425)
# ---------------------------------------------------------------------------

class TestBayesianStrategy:

    def _matrix(self):
        return DesignMatrix(
            runs=_runs([
                (1, {"A": "0", "B": "0"}),
                (2, {"A": "10", "B": "0"}),
                (3, {"A": "0", "B": "10"}),
                (4, {"A": "10", "B": "10"}),
            ]),
            factor_names=["A", "B"],
            operation="full_factorial",
        )

    def _cfg(self):
        return _make_cfg(
            [Factor(name="A", levels=["0", "10"], type="continuous"),
             Factor(name="B", levels=["0", "10"], type="continuous")],
            [ResponseVar(name="y", optimize="maximize")],
        )

    def test_insufficient_runs_delegates_to_model_guided(self):
        """len(valid_runs) < 2 -> model_guided (398)."""
        matrix = self._matrix()
        resp = ResponseVar(name="y", optimize="maximize")
        out = _bayesian_strategy(
            [matrix.runs[0]], {1: 5.0}, resp, self._cfg(), matrix,
            batch_size=2, start_run_id=10, seed=0)
        assert len(out) == 2

    def test_gp_fit_failure_delegates_to_model_guided(self, monkeypatch):
        """fit_gp raising -> model_guided (414-415)."""
        matrix = self._matrix()
        resp = ResponseVar(name="y", optimize="maximize")
        responses = {r.run_id: float(r.run_id) for r in matrix.runs}
        monkeypatch.setattr("doe.bo.fit_gp", _raise)
        out = _bayesian_strategy(
            matrix.runs, responses, resp, self._cfg(), matrix,
            batch_size=2, start_run_id=10, seed=0)
        assert len(out) == 2

    def test_propose_failure_delegates_to_model_guided(self, monkeypatch):
        """propose_with_gp raising (via expected_improvement) -> model_guided (424-425)."""
        matrix = self._matrix()
        resp = ResponseVar(name="y", optimize="maximize")
        responses = {r.run_id: float(r.run_id) for r in matrix.runs}
        monkeypatch.setattr("doe.bo.expected_improvement", _raise)
        out = _bayesian_strategy(
            matrix.runs, responses, resp, self._cfg(), matrix,
            batch_size=2, start_run_id=10, seed=0)
        assert len(out) == 2


# ---------------------------------------------------------------------------
# _model_guided_strategy branches (649, 660-662, 678-679, 690-691, 713-732)
# ---------------------------------------------------------------------------

class TestModelGuidedStrategy:

    def test_empty_valid_runs_returns_empty(self):
        """No valid runs -> returns [] (649)."""
        cfg = _make_cfg(
            [Factor(name="A", levels=["0", "10"], type="continuous")],
            [ResponseVar(name="y", optimize="maximize")])
        matrix = DesignMatrix(runs=[], factor_names=["A"], operation="x")
        resp = ResponseVar(name="y", optimize="maximize")
        out = _model_guided_strategy(
            [], {}, resp, cfg, matrix, batch_size=2,
            rng=np.random.default_rng(0), start_run_id=0)
        assert out == []

    def _two_factor(self):
        factors = [Factor(name="A", levels=["0", "10"], type="continuous"),
                   Factor(name="B", levels=["0", "10"], type="continuous")]
        matrix = DesignMatrix(
            runs=_runs([
                (1, {"A": "0", "B": "0"}),
                (2, {"A": "10", "B": "0"}),
                (3, {"A": "0", "B": "10"}),
                (4, {"A": "10", "B": "10"}),
            ]),
            factor_names=["A", "B"],
            operation="full_factorial",
        )
        responses = {1: 75.0, 2: 90.0, 3: 88.0, 4: 100.0}
        return factors, matrix, responses

    def test_fit_rsm_failure_falls_back_to_refine(self, monkeypatch):
        """fit_rsm raising -> refine (660, 662)."""
        factors, matrix, responses = self._two_factor()
        cfg = _make_cfg(factors, [ResponseVar(name="y", optimize="maximize")])
        resp = ResponseVar(name="y", optimize="maximize")
        monkeypatch.setattr("doe.rsm.fit_rsm", _raise)
        out = _model_guided_strategy(
            matrix.runs, responses, resp, cfg, matrix, batch_size=3,
            rng=np.random.default_rng(0), start_run_id=10)
        assert len(out) == 3

    def test_optimize_surface_failure_swallowed(self, monkeypatch):
        """optimize_surface raising -> pass, continue with uncertainty (678-679)."""
        factors, matrix, responses = self._two_factor()
        cfg = _make_cfg(factors, [ResponseVar(name="y", optimize="maximize")])
        resp = ResponseVar(name="y", optimize="maximize")
        monkeypatch.setattr("doe.rsm.optimize_surface", _raise)
        out = _model_guided_strategy(
            matrix.runs, responses, resp, cfg, matrix, batch_size=3,
            rng=np.random.default_rng(0), start_run_id=10)
        assert len(out) == 3

    def test_pinv_failure_then_explore_padding(self, monkeypatch):
        """XtX_inv failure -> None (690-691); short batch padded via explore (731-732)."""
        factors, matrix, responses = self._two_factor()
        cfg = _make_cfg(factors, [ResponseVar(name="y", optimize="maximize")])
        resp = ResponseVar(name="y", optimize="maximize")
        monkeypatch.setattr("doe.adaptive._safe_pinv", _raise)
        out = _model_guided_strategy(
            matrix.runs, responses, resp, cfg, matrix, batch_size=4,
            rng=np.random.default_rng(0), start_run_id=10)
        assert len(out) == 4

    def test_topup_loop_when_spacing_too_aggressive(self):
        """Large batch in 1-D forces the min-spacing top-up loop (713-718)."""
        factors = [Factor(name="A", levels=["0", "10"], type="continuous")]
        matrix = DesignMatrix(
            runs=_runs([
                (1, {"A": "0"}), (2, {"A": "2"}), (3, {"A": "5"}),
                (4, {"A": "7"}), (5, {"A": "10"}),
            ]),
            factor_names=["A"],
            operation="full_factorial",
        )
        # y = -(A-5)^2 + 100, clear interior optimum.
        responses = {}
        for r in matrix.runs:
            a = float(r.factor_values["A"])
            responses[r.run_id] = -(a - 5.0) ** 2 + 100.0
        cfg = _make_cfg(factors, [ResponseVar(name="y", optimize="maximize")])
        resp = ResponseVar(name="y", optimize="maximize")
        out = _model_guided_strategy(
            matrix.runs, responses, resp, cfg, matrix, batch_size=10,
            rng=np.random.default_rng(0), start_run_id=100)
        assert len(out) == 10


# ---------------------------------------------------------------------------
# _decoded_run categorical / parse branches (796-807)
# ---------------------------------------------------------------------------

class TestDecodedRun:

    def test_continuous_parse_failure_and_two_level_snap(self):
        """Non-numeric continuous -> pass (796-797); 2-level categorical snap (799-801)."""
        factors = [
            Factor(name="bad", levels=["lo", "hi"], type="continuous"),
            Factor(name="cat2", levels=["x", "y"], type="categorical"),
        ]
        run = _decoded_run(1, np.array([0.8, 0.5]), ["bad", "cat2"], factors)
        # sorted(["lo","hi"]) == ["hi","lo"]; cv=0.8>0 -> "lo"
        assert run.factor_values["bad"] == "lo"
        assert run.factor_values["cat2"] == "y"

    def test_two_level_snap_negative(self):
        run = _decoded_run(
            2, np.array([-0.5]), ["cat2"],
            [Factor(name="cat2", levels=["x", "y"], type="categorical")])
        assert run.factor_values["cat2"] == "x"

    def test_multi_level_categorical_snap(self):
        """>2 level categorical index computation (803-807)."""
        run = _decoded_run(
            3, np.array([0.5]), ["c"],
            [Factor(name="c", levels=["a", "b", "c", "d"], type="categorical")])
        assert run.factor_values["c"] in {"a", "b", "c", "d"}


# ---------------------------------------------------------------------------
# _refine_strategy parse branches (849-850, 853)
# ---------------------------------------------------------------------------

class TestRefineStrategy:

    def test_non_numeric_continuous_and_categorical_kept(self):
        """Continuous value that won't parse -> pass (849-850) -> keep best (853)."""
        factors = [
            Factor(name="num", levels=["0", "10"], type="continuous"),
            Factor(name="cat", levels=["a", "b"], type="categorical"),
        ]
        matrix = DesignMatrix(runs=[], factor_names=["num", "cat"], operation="x")
        valid_runs = _runs([(1, {"num": "not-a-number", "cat": "a"})])
        responses = {1: 5.0}
        cfg = _make_cfg(factors, [ResponseVar(name="y", optimize="maximize")])
        out = _refine_strategy(
            valid_runs, responses, cfg, matrix, batch_size=2,
            rng=np.random.default_rng(0), start_run_id=0)
        assert len(out) == 2
        for run in out:
            assert run.factor_values["num"] == "not-a-number"
            assert run.factor_values["cat"] == "a"


# ---------------------------------------------------------------------------
# _explore_strategy categorical branches (882-888, 920-923)
# ---------------------------------------------------------------------------

class TestExploreStrategy:

    def test_categorical_encoding_and_decoding(self):
        """Categorical encode (882-888) and decode (920-923)."""
        factors = [Factor(name="cat", levels=["a", "b", "c"], type="categorical")]
        matrix = DesignMatrix(runs=[], factor_names=["cat"], operation="x")
        # One value in levels, one value not in levels (fallback 0.5).
        valid_runs = _runs([(1, {"cat": "a"}), (2, {"cat": "zzz"})])
        cfg = _make_cfg(factors, [ResponseVar(name="y", optimize="maximize")])
        out = _explore_strategy(
            valid_runs, cfg, matrix, batch_size=2,
            rng=np.random.default_rng(0), start_run_id=5)
        assert len(out) == 2
        for run in out:
            assert run.factor_values["cat"] in {"a", "b", "c"}


# ---------------------------------------------------------------------------
# sensitivity.py (68, 70, 82-83, 228-231, 266-270)
# ---------------------------------------------------------------------------

from doe.sensitivity import (
    sobol_indices,
    SensitivityResult,
    SobolIndex,
    _render_sobol_stacked_bar,
    _anchor_id,
)


class TestSensitivity:

    def test_mismatched_bounds_raises(self):
        """factor_names and bounds length mismatch (68)."""
        with pytest.raises(ValueError, match="equal length"):
            sobol_indices(lambda X: X[:, 0], ["a", "b"], [(0.0, 1.0)])

    def test_zero_factors_returns_note(self):
        """k == 0 short-circuit (70)."""
        result = sobol_indices(lambda X: X[:, 0], [], [])
        assert result.n_evaluations == 0
        assert result.indices == []
        assert "No factors" in result.notes[0]

    def test_sobol_unavailable_returns_note(self, monkeypatch):
        """scipy Sobol import failure -> note (82-83)."""
        import scipy.stats.qmc as qmc
        monkeypatch.delattr(qmc, "Sobol", raising=True)
        result = sobol_indices(
            lambda X: X[:, 0], ["a"], [(0.0, 1.0)], n_base_samples=8, seed=1)
        assert result.n_evaluations == 0
        assert "Sobol not available" in result.notes[0]

    def test_render_bar_no_matplotlib(self, monkeypatch):
        """matplotlib import failure -> empty string (228-229)."""
        monkeypatch.setitem(sys.modules, "matplotlib", None)
        result = SensitivityResult(
            response_name="r", n_base_samples=8, n_evaluations=32,
            indices=[SobolIndex("a", 0.5, 0.6, 0.1)])
        assert _render_sobol_stacked_bar(result) == ""

    def test_render_bar_no_indices(self):
        """No indices -> empty string (231)."""
        result = SensitivityResult(
            response_name="r", n_base_samples=8, n_evaluations=0, indices=[])
        assert _render_sobol_stacked_bar(result) == ""

    def test_anchor_id_special_chars_and_double_dash(self):
        """Separators mapped to '-' (266-267) and '--' collapsed (270)."""
        assert _anchor_id("My  Weird__Name..") == "my-weird-name"
        assert _anchor_id("!!!") == "section"


# ---------------------------------------------------------------------------
# knee.py (47, 72-73, 97, 114, 147)
# ---------------------------------------------------------------------------

from doe.knee import detect_knee_point, _fit_piecewise, _fit_line


class TestKnee:

    def test_nan_response_returns_none(self):
        """NaN responses -> every RSS is NaN -> no valid breakpoint -> None (47)."""
        result = detect_knee_point(
            [1.0, 2.0, 3.0, 4.0], [1.0, float("nan"), 3.0, 4.0])
        assert result is None

    def test_no_bootstrap_uses_point_estimate(self):
        """n_bootstrap=0 -> empty samples -> CI collapses to the knee (72-73)."""
        result = detect_knee_point(
            [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, 3.0, 3.1, 3.15],
            n_bootstrap=0)
        assert result is not None
        assert result.ci_low == result.knee_value
        assert result.ci_high == result.knee_value

    def test_fit_piecewise_too_few_points(self):
        """_fit_piecewise with n < 3 (97)."""
        bp, rss, s1, s2, y_bp = _fit_piecewise(
            np.array([1.0, 2.0]), np.array([1.0, 2.0]))
        assert bp is None
        assert rss == np.inf

    def test_fit_piecewise_skips_short_segment(self):
        """A NaN in x makes a candidate breakpoint's right segment too short (114)."""
        x = np.array([1.0, 2.0, 3.0, np.nan])
        y = np.array([1.0, 2.0, 3.0, 4.0])
        bp, rss, s1, s2, y_bp = _fit_piecewise(x, y)
        # A valid breakpoint (bp=2.0) still exists from the finite points.
        assert bp == 2.0

    def test_fit_line_single_point(self):
        """_fit_line with a single point -> zero slope, mean intercept (147)."""
        slope, intercept = _fit_line(np.array([1.0]), np.array([5.0]))
        assert slope == 0.0
        assert intercept == 5.0


# ---------------------------------------------------------------------------
# codegen.py (130, 150, 274, 282)
# ---------------------------------------------------------------------------

from doe.codegen import (
    _write_executable,
    generate_config_template,
    _py_ident,
    _sh_var,
)


class TestCodegen:

    def test_write_executable_creates_missing_dirs(self, tmp_path):
        """Output directory does not exist -> created (130)."""
        target = tmp_path / "a" / "b" / "runner.sh"
        _write_executable(str(target), "#!/bin/sh\necho hi\n")
        assert target.exists()
        assert target.read_text().startswith("#!/bin/sh")

    def test_generate_config_template_creates_missing_dirs(self, tmp_path):
        """Output directory does not exist -> created (150)."""
        target = tmp_path / "cfg" / "nested" / "config.json"
        template = generate_config_template(str(target))
        assert target.exists()
        assert "factors" in template

    def test_py_ident_leading_digit(self):
        """Leading digit / empty -> underscore prefix (274)."""
        assert _py_ident("1abc") == "_1abc"
        assert _py_ident("") == "_"

    def test_sh_var_leading_digit(self):
        """Leading digit / empty -> underscore prefix (282)."""
        assert _sh_var("1abc") == "_1ABC"
        assert _sh_var("") == "_"
