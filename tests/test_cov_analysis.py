# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-coverage tests for doe/analysis.py, doe/aliasing.py and doe/power.py.

These tests deliberately exercise the edge and error branches of the DOE
statistics engine: missing / blank / non-numeric responses, degenerate
designs, single-level factors, absent scipy, optional-submodule failures,
and the plotting/export fallbacks. Everything is hermetic (tmp_path, seeded
numpy, no network) and deterministic.
"""

import json
import os
import sys

import numpy as np
import pytest

from doe.models import (
    AliasEntry, AliasStructure, AnalysisReport, AnovaRow, AnovaTable,
    AchievedPower, AchievedPowerEntry, CrossValidation, CrossValidationFold,
    DOEConfig, DesignMatrix, EffectResult, ExperimentRun, Factor,
    ModelAdequacy, ResponseAnalysis, ResponseVar, RunnerConfig, StationaryPoint,
)
from doe import analysis
from doe.analysis import (
    analyze,
    export_csv,
    plot_normal_effects,
    plot_half_normal_effects,
    plot_rsm_surface,
    _coerce_response_value,
    _compute_anova,
    _compute_cross_validation_safe,
    _compute_main_effects,
    _compute_model_adequacy_and_stationary,
    _compute_ordinal_trends,
    _compute_split_plot_anova,
    _detect_knee_points,
    _load_all_results,
)
from doe.analysis import plot_diagnostics
from doe.analysis import _compute_interaction_effects
from doe.aliasing import compute_alias_structure
from doe.power import power_for_factor, mde_for_factor, achieved_power
from doe.rsm import ModelDiagnostics, RSMModel


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _run(run_id, block_id=1, whole_plot_id=0, **factor_values):
    return ExperimentRun(
        run_id=run_id,
        block_id=block_id,
        factor_values={k: str(v) for k, v in factor_values.items()},
        whole_plot_id=whole_plot_id,
    )


def _cfg(factors, responses=None, operation="full_factorial"):
    return DOEConfig(
        factors=factors,
        fixed_factors={},
        responses=responses or [ResponseVar(name="y")],
        block_count=1,
        test_script="",
        operation=operation,
        processed_directory="",
        out_directory="",
        runner=RunnerConfig(),
    )


def _write_results(results_dir, mapping):
    """mapping: run_id -> dict of response values (raw, may be None/str)."""
    os.makedirs(results_dir, exist_ok=True)
    for run_id, data in mapping.items():
        with open(os.path.join(results_dir, f"run_{run_id}.json"), "w") as f:
            json.dump(data, f)


def _full_factorial_3(response_offsets=None):
    """Eight-run 3x2-level design; distinct responses give df_error > 0."""
    factors = [
        Factor(name="A", levels=["0", "1"]),
        Factor(name="B", levels=["0", "1"]),
        Factor(name="C", levels=["0", "1"]),
    ]
    runs = []
    rid = 1
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                runs.append(_run(rid, A=a, B=b, C=c))
                rid += 1
    matrix = DesignMatrix(runs=runs, factor_names=["A", "B", "C"], operation="full_factorial")
    return factors, matrix


# ===========================================================================
# power.py
# ===========================================================================

class TestPower:
    def test_power_for_factor_zero_sigma_returns_one(self):
        # sigma <= 0 short-circuits to guaranteed detection.
        assert power_for_factor(8, 2, 4, delta=1.0, sigma=0.0) == 1.0

    def test_power_for_factor_guard_returns_zero(self):
        # df_error < 1  -> line 39
        assert power_for_factor(8, 2, 0, delta=1.0, sigma=1.0) == 0.0
        # n_levels < 2  -> line 39
        assert power_for_factor(8, 1, 4, delta=1.0, sigma=1.0) == 0.0

    def test_mde_guard_returns_inf(self):
        # df_error < 1 -> line 64
        assert mde_for_factor(8, 2, 0, sigma=1.0) == float("inf")
        # n_levels < 2 -> line 64
        assert mde_for_factor(8, 1, 4, sigma=1.0) == float("inf")

    def test_mde_unreachable_target_returns_inf(self):
        # A target power that the non-central F can never reach forces the
        # `hi`-doubling loop to exhaust and hit the for/else -> line 76.
        assert mde_for_factor(8, 2, 5, sigma=1.0, target_power=2.0) == float("inf")

    def test_mde_reachable_is_finite(self):
        val = mde_for_factor(16, 2, 8, sigma=1.0, target_power=0.8)
        assert np.isfinite(val) and val > 0

    def test_achieved_power_skips_single_level_factor(self):
        # A one-level factor is skipped (continue) -> line 116.
        matrix = DesignMatrix(
            runs=[_run(1, A=0, S=0), _run(2, A=1, S=0)],
            factor_names=["A", "S"],
            operation="full_factorial",
        )
        factors = [
            Factor(name="A", levels=["0", "1"]),
            Factor(name="S", levels=["0"]),  # single level -> skipped
        ]
        ap = achieved_power(matrix, factors, residual_ms=1.0, df_error=3)
        assert ap is not None
        names = [e.factor_name for e in ap.per_factor]
        assert "A" in names and "S" not in names

    def test_achieved_power_saturated_returns_none(self):
        matrix = DesignMatrix(runs=[_run(1, A=0)], factor_names=["A"], operation="full_factorial")
        assert achieved_power(matrix, [Factor(name="A", levels=["0", "1"])],
                              residual_ms=1.0, df_error=0) is None


# ===========================================================================
# aliasing.py
# ===========================================================================

class TestAliasing:
    def test_returns_none_for_non_screening_operation(self):
        matrix = DesignMatrix(runs=[_run(1, A=0, B=0)], factor_names=["A", "B"],
                              operation="full_factorial")
        assert compute_alias_structure(matrix) is None

    def test_returns_none_with_fewer_than_two_factors(self):
        # Screening op but only one factor -> line 52.
        matrix = DesignMatrix(runs=[_run(1, A=0), _run(2, A=1)],
                              factor_names=["A"], operation="fractional_factorial")
        assert compute_alias_structure(matrix) is None

    def test_returns_none_with_empty_runs(self):
        # Screening op, >=2 factors, but no runs -> line 52.
        matrix = DesignMatrix(runs=[], factor_names=["A", "B"],
                              operation="fractional_factorial")
        assert compute_alias_structure(matrix) is None

    def test_returns_none_when_factor_not_two_level(self):
        # Factor B has three distinct levels -> not a 2-level design -> line 66.
        runs = [
            _run(1, A=0, B=0), _run(2, A=1, B=1),
            _run(3, A=0, B=2), _run(4, A=1, B=0),
        ]
        matrix = DesignMatrix(runs=runs, factor_names=["A", "B"],
                              operation="fractional_factorial")
        assert compute_alias_structure(matrix) is None

    def test_zero_norm_column_is_dropped(self, monkeypatch):
        # Force a zero-norm column so the safety-drop branch runs (lines 95-98).
        # The coded matrix is always +/-1 so no column can be zero naturally;
        # patch np.linalg.norm within the aliasing module to zero the first
        # column's norm, exercising the keep/drop bookkeeping.
        import doe.aliasing as al
        real_norm = np.linalg.norm

        def fake_norm(cols, axis=0):
            n = real_norm(cols, axis=axis)
            n = np.array(n, dtype=float)
            n[0] = 0.0  # pretend the first column is degenerate
            return n

        monkeypatch.setattr(al.np.linalg, "norm", fake_norm)

        runs = [
            _run(1, A=0, B=0), _run(2, A=1, B=1),
            _run(3, A=0, B=1), _run(4, A=1, B=0),
        ]
        matrix = DesignMatrix(runs=runs, factor_names=["A", "B"],
                              operation="fractional_factorial")
        result = compute_alias_structure(matrix)
        assert result is not None
        # The dropped label (first main effect "A") must not appear.
        assert all(e.effect != "A" for e in result.main_effects)


# ===========================================================================
# analysis.py — _coerce_response_value
# ===========================================================================

class TestCoerceResponseValue:
    def test_none_value_returns_none(self):
        assert _coerce_response_value({"y": None}, "y", 1, "results") is None

    def test_blank_string_returns_none(self):
        assert _coerce_response_value({"y": "   "}, "y", 1, "results") is None

    def test_missing_key_returns_none(self):
        assert _coerce_response_value({}, "y", 1, "results") is None

    def test_non_numeric_raises_valueerror(self):
        with pytest.raises(ValueError, match="Invalid value for response"):
            _coerce_response_value({"y": "not-a-number"}, "y", 7, "results")


# ===========================================================================
# analysis.py — analyze() pipeline branches
# ===========================================================================

class TestAnalyzePipeline:
    def test_missing_and_blank_and_valid(self, tmp_path, capsys):
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        # run 1 blank, run 2 explicit null, rest valid numbers
        mapping = {}
        for i, run in enumerate(matrix.runs):
            if run.run_id == 1:
                mapping[run.run_id] = {"y": ""}
            elif run.run_id == 2:
                mapping[run.run_id] = {"y": None}
            else:
                mapping[run.run_id] = {"y": float(10 + i)}
        _write_results(rdir, mapping)
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True)
        assert "y" in report.results_by_response
        assert "missing in result files" in capsys.readouterr().out

    def test_all_missing_response_skipped(self, tmp_path, capsys):
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {} for run in matrix.runs})
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True)
        assert "y" not in report.results_by_response
        assert "no data found" in capsys.readouterr().out

    def test_non_numeric_response_raises(self, tmp_path):
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        mapping = {run.run_id: {"y": float(run.run_id)} for run in matrix.runs}
        mapping[1] = {"y": "oops"}
        _write_results(rdir, mapping)
        with pytest.raises(ValueError, match="Invalid value for response"):
            analyze(matrix, cfg, results_dir=rdir, no_plots=True)

    def test_filter_factors_subset(self, tmp_path):
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(run.run_id)} for run in matrix.runs})
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True,
                         filter_factors=["A", "B"])
        names = {e.factor_name for e in report.results_by_response["y"].effects}
        assert names == {"A", "B"}

    def test_filter_factors_unknown_raises(self, tmp_path):
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(run.run_id)} for run in matrix.runs})
        with pytest.raises(ValueError, match="Unknown factor"):
            analyze(matrix, cfg, results_dir=rdir, no_plots=True,
                    filter_factors=["Z"])

    def test_achieved_power_computed(self, tmp_path):
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(run.run_id * 3)} for run in matrix.runs})
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True)
        assert report.results_by_response["y"].achieved_power is not None

    def test_anova_failure_swallowed(self, tmp_path, monkeypatch):
        # Force _compute_anova to raise so the except/pass fallback runs (158-159).
        def boom(*a, **k):
            raise RuntimeError("anova failure")

        monkeypatch.setattr(analysis, "_compute_anova", boom)
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(run.run_id)} for run in matrix.runs})
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True)
        assert report.results_by_response["y"].anova_table is None

    def test_achieved_power_failure_swallowed(self, tmp_path, monkeypatch):
        import doe.power as power_mod

        def boom(*a, **k):
            raise RuntimeError("power failure")

        monkeypatch.setattr(power_mod, "achieved_power", boom)
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(run.run_id * 3)} for run in matrix.runs})
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True)
        assert report.results_by_response["y"].achieved_power is None

    def test_alias_structure_failure_swallowed(self, tmp_path, monkeypatch):
        import doe.aliasing as al

        def boom(*a, **k):
            raise RuntimeError("alias failure")

        monkeypatch.setattr(al, "compute_alias_structure", boom)
        factors, matrix = _full_factorial_3()
        cfg = _cfg(factors, responses=[ResponseVar(name="y")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(run.run_id)} for run in matrix.runs})
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True)
        assert report.alias_structure is None

    def test_mixture_scheffe_failure_swallowed(self, tmp_path, monkeypatch):
        # A mixture operation triggers the Scheffe fit block (203-206); patch
        # fit_scheffe to raise so the except path (210-211) runs too.
        import doe.mixture as mix

        def boom(*a, **k):
            raise RuntimeError("scheffe failure")

        monkeypatch.setattr(mix, "fit_scheffe", boom)
        factors = [
            Factor(name="A", levels=["0", "1"], type="continuous"),
            Factor(name="B", levels=["0", "1"], type="continuous"),
            Factor(name="C", levels=["0", "1"], type="continuous"),
        ]
        runs = [
            _run(1, A=1, B=0, C=0), _run(2, A=0, B=1, C=0),
            _run(3, A=0, B=0, C=1), _run(4, A=0.5, B=0.5, C=0),
        ]
        matrix = DesignMatrix(runs=runs, factor_names=["A", "B", "C"],
                              operation="mixture_simplex_lattice")
        cfg = _cfg(factors, responses=[ResponseVar(name="y")],
                   operation="mixture_simplex_lattice")
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(run.run_id)} for run in matrix.runs})
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=True)
        assert report.results_by_response["y"].scheffe_model is None

    def test_corrupt_result_file_raises(self, tmp_path):
        factors, matrix = _full_factorial_3()
        rdir = tmp_path / "r"
        rdir.mkdir()
        for run in matrix.runs:
            (rdir / f"run_{run.run_id}.json").write_text('{"y": 1.0}')
        (rdir / "run_1.json").write_text("{not valid json")
        with pytest.raises(ValueError, match="Corrupt result file"):
            _load_all_results(matrix.runs, str(rdir))


# ===========================================================================
# analysis.py — plotting fallbacks inside analyze()
# ===========================================================================

class TestAnalyzePlottingFallbacks:
    def _setup(self, tmp_path):
        factors = [
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
        ]
        runs = [
            _run(1, A=0, B=0), _run(2, A=0, B=10),
            _run(3, A=10, B=0), _run(4, A=10, B=10),
            _run(5, A=5, B=5), _run(6, A=5, B=5),
        ]
        matrix = DesignMatrix(runs=runs, factor_names=["A", "B"], operation="full_factorial")
        cfg = _cfg(factors, responses=[ResponseVar(name="y", unit="s")])
        rdir = str(tmp_path / "r")
        _write_results(rdir, {run.run_id: {"y": float(10 + run.run_id)} for run in matrix.runs})
        cfg.processed_directory = str(tmp_path / "proc")
        return matrix, cfg, rdir

    def test_normal_plot_importerror_swallowed(self, tmp_path, monkeypatch):
        pytest.importorskip("matplotlib")
        matrix, cfg, rdir = self._setup(tmp_path)

        def raise_import(*a, **k):
            raise ImportError("no scipy")

        monkeypatch.setattr(analysis, "plot_normal_effects", raise_import)
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=False)
        assert "y" not in report.normal_plot_paths

    def test_diagnostics_failure_swallowed(self, tmp_path, monkeypatch):
        pytest.importorskip("matplotlib")
        matrix, cfg, rdir = self._setup(tmp_path)

        def boom(*a, **k):
            raise RuntimeError("diag failure")

        monkeypatch.setattr(analysis, "plot_diagnostics", boom)
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=False)
        assert "y" not in report.diagnostics_plot_paths

    def test_matplotlib_unavailable_swallowed(self, tmp_path, monkeypatch, capsys):
        matrix, cfg, rdir = self._setup(tmp_path)
        # Make `import matplotlib` raise ImportError for the plotting block.
        monkeypatch.setitem(sys.modules, "matplotlib", None)
        report = analyze(matrix, cfg, results_dir=rdir, no_plots=False)
        assert "matplotlib not available" in capsys.readouterr().out
        assert report.pareto_chart_paths == {}


# ===========================================================================
# analysis.py — model-adequacy / cross-validation helper fallbacks
# ===========================================================================

def _quad_design():
    """Two continuous factors on a 3x3 grid -> 9 runs, quadratic-fittable."""
    factors = [
        Factor(name="A", levels=["0", "10"], type="continuous"),
        Factor(name="B", levels=["0", "10"], type="continuous"),
    ]
    runs = []
    responses = {}
    rid = 1
    for a in (0, 5, 10):
        for b in (0, 5, 10):
            runs.append(_run(rid, A=a, B=b))
            responses[rid] = 100.0 - (a - 5) ** 2 - (b - 5) ** 2 + 0.1 * rid
            rid += 1
    return factors, runs, responses, ["A", "B"]


class TestModelAdequacyHelper:
    def test_rsm_import_failure_returns_none(self, monkeypatch):
        # `from .rsm import ...` fails -> (None, None), lines 383-384.
        monkeypatch.setitem(sys.modules, "doe.rsm", None)
        factors, runs, responses, names = _quad_design()
        assert _compute_model_adequacy_and_stationary(runs, responses, names, factors) == (None, None)

    def test_fit_rsm_failure_returns_none(self, monkeypatch):
        import doe.rsm as rsm

        def boom(*a, **k):
            raise RuntimeError("fit failure")

        monkeypatch.setattr(rsm, "fit_rsm", boom)
        factors, runs, responses, names = _quad_design()
        assert _compute_model_adequacy_and_stationary(runs, responses, names, factors) == (None, None)

    def test_adequacy_failure_yields_none_adequacy(self, monkeypatch):
        import doe.rsm as rsm

        def boom(*a, **k):
            raise RuntimeError("adequacy failure")

        monkeypatch.setattr(rsm, "compute_model_adequacy", boom)
        # Linear model (few runs) so stationary path is skipped.
        factors = [Factor(name="A", levels=["0", "10"], type="continuous")]
        runs = [_run(1, A=0), _run(2, A=10), _run(3, A=5)]
        responses = {1: 1.0, 2: 2.0, 3: 1.5}
        adequacy, stationary = _compute_model_adequacy_and_stationary(runs, responses, ["A"], factors)
        assert adequacy is None and stationary is None

    def test_stationary_failure_yields_none_stationary(self, monkeypatch):
        import doe.rsm as rsm

        def boom(*a, **k):
            raise RuntimeError("stationary failure")

        monkeypatch.setattr(rsm, "characterize_stationary_point", boom)
        factors, runs, responses, names = _quad_design()
        adequacy, stationary = _compute_model_adequacy_and_stationary(runs, responses, names, factors)
        assert stationary is None

    def test_cross_validation_failure_returns_none(self, monkeypatch):
        import doe.rsm as rsm

        def boom(*a, **k):
            raise RuntimeError("cv failure")

        monkeypatch.setattr(rsm, "compute_cross_validation", boom)
        factors, runs, responses, names = _quad_design()
        assert _compute_cross_validation_safe(runs, responses, names, factors, "linear", None) is None


# ===========================================================================
# analysis.py — scipy-absent import fallbacks in the stats helpers
# ===========================================================================

class TestScipyAbsentFallbacks:
    def _two_level_runs(self):
        runs = [
            _run(1, A=0, B=0), _run(2, A=0, B=1),
            _run(3, A=1, B=0), _run(4, A=1, B=1),
        ]
        responses = {1: 10.0, 2: 12.0, 3: 15.0, 4: 20.0}
        return runs, responses, ["A", "B"]

    def test_main_effects_without_scipy(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "scipy.stats", None)
        runs, responses, names = self._two_level_runs()
        effects = _compute_main_effects(runs, responses, names)
        assert {e.factor_name for e in effects} == {"A", "B"}
        assert all(e.ci_low == 0.0 and e.ci_high == 0.0 for e in effects)

    def test_anova_without_scipy(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "scipy.stats", None)
        runs, responses, names = self._two_level_runs()
        factors = [Factor(name="A", levels=["0", "1"]), Factor(name="B", levels=["0", "1"])]
        table = _compute_anova(runs, responses, names, factors)
        assert table is not None
        assert all(r.p_value is None for r in table.rows)

    def test_ordinal_trends_without_scipy(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "scipy.stats", None)
        factors = [Factor(name="A", levels=["0", "1", "2"], type="ordinal")]
        runs = [_run(1, A=0), _run(2, A=1), _run(3, A=2),
                _run(4, A=0), _run(5, A=1), _run(6, A=2)]
        responses = {1: 1.0, 2: 4.0, 3: 9.0, 4: 1.5, 5: 4.5, 6: 9.5}
        trends = _compute_ordinal_trends(runs, responses, factors, ["A"], "y",
                                         ms_error=1.0, df_error=3)
        assert trends and trends[0].linear_f_value is not None
        assert trends[0].linear_p_value is None  # scipy absent

    def test_split_plot_without_scipy(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "scipy.stats", None)
        factors = [
            Factor(name="W", levels=["a", "b"], role="whole_plot"),
            Factor(name="S", levels=["0", "1"], role="subplot"),
        ]
        runs = [
            _run(1, whole_plot_id=1, W="a", S=0), _run(2, whole_plot_id=1, W="a", S=1),
            _run(3, whole_plot_id=2, W="b", S=0), _run(4, whole_plot_id=2, W="b", S=1),
            _run(5, whole_plot_id=3, W="a", S=0), _run(6, whole_plot_id=3, W="a", S=1),
            _run(7, whole_plot_id=4, W="b", S=0), _run(8, whole_plot_id=4, W="b", S=1),
        ]
        responses = {i: float(10 + i) for i in range(1, 9)}
        table = _compute_split_plot_anova(runs, responses, ["W", "S"], factors)
        assert table is not None and table.error_method == "split_plot"


# ===========================================================================
# analysis.py — ordinal trends F-test with error term present
# ===========================================================================

class TestOrdinalTrendsFTest:
    def test_ftest_with_error_and_scipy(self):
        factors = [Factor(name="A", levels=["0", "1", "2"], type="ordinal")]
        runs = [_run(1, A=0), _run(2, A=1), _run(3, A=2),
                _run(4, A=0), _run(5, A=1), _run(6, A=2)]
        responses = {1: 1.0, 2: 4.0, 3: 9.0, 4: 1.5, 5: 4.5, 6: 9.5}
        trends = _compute_ordinal_trends(runs, responses, factors, ["A"], "y",
                                         ms_error=2.0, df_error=3)
        assert trends
        t = trends[0]
        assert t.linear_f_value is not None and t.quadratic_f_value is not None
        assert t.linear_p_value is not None and t.quadratic_p_value is not None


# ===========================================================================
# analysis.py — split-plot degenerate branches
# ===========================================================================

class TestSplitPlotDegenerate:
    def test_no_whole_plot_factor_falls_back_to_pooled(self):
        # No factor with role "whole_plot" -> returns _compute_anova (line 620).
        factors = [Factor(name="A", levels=["0", "1"]), Factor(name="B", levels=["0", "1"])]
        runs = [_run(1, A=0, B=0), _run(2, A=0, B=1), _run(3, A=1, B=0), _run(4, A=1, B=1)]
        responses = {1: 10.0, 2: 12.0, 3: 15.0, 4: 20.0}
        table = _compute_split_plot_anova(runs, responses, ["A", "B"], factors)
        assert table is not None
        assert table.error_method != "split_plot"

    def test_single_level_whole_plot_skips_interactions(self):
        # Whole-plot factor with one level -> df_htc == 0 -> interaction loop
        # hits `continue` (line 699).
        factors = [
            Factor(name="W", levels=["a"], role="whole_plot"),
            Factor(name="S", levels=["0", "1"], role="subplot"),
        ]
        runs = [
            _run(1, whole_plot_id=1, W="a", S=0), _run(2, whole_plot_id=1, W="a", S=1),
            _run(3, whole_plot_id=2, W="a", S=0), _run(4, whole_plot_id=2, W="a", S=1),
        ]
        responses = {1: 10.0, 2: 12.0, 3: 11.0, 4: 13.0}
        table = _compute_split_plot_anova(runs, responses, ["W", "S"], factors)
        assert table is not None
        assert not any("*" in r.source for r in table.rows)


# ===========================================================================
# analysis.py — knee-point detection branches
# ===========================================================================

class TestKneePoints:
    def test_categorical_factor_skipped(self):
        factors = [Factor(name="A", levels=["x", "y", "z"], type="categorical")]
        runs = [_run(1, A="x"), _run(2, A="y"), _run(3, A="z")]
        responses = {1: 1.0, 2: 2.0, 3: 3.0}
        assert _detect_knee_points(runs, responses, factors, ["A"], "y") == []

    def test_fewer_than_three_levels_skipped(self):
        factors = [Factor(name="A", levels=["0", "1"], type="continuous")]
        runs = [_run(1, A=0), _run(2, A=1)]
        responses = {1: 1.0, 2: 2.0}
        assert _detect_knee_points(runs, responses, factors, ["A"], "y") == []

    def test_non_numeric_levels_skipped(self):
        # Ordinal factor with 3+ non-numeric levels -> float() ValueError -> continue.
        factors = [Factor(name="A", levels=["low", "mid", "high"], type="ordinal")]
        runs = [_run(1, A="low"), _run(2, A="mid"), _run(3, A="high"),
                _run(4, A="low"), _run(5, A="mid"), _run(6, A="high")]
        responses = {1: 1.0, 2: 2.0, 3: 3.0, 4: 1.1, 5: 2.1, 6: 3.1}
        assert _detect_knee_points(runs, responses, factors, ["A"], "y") == []


# ===========================================================================
# analysis.py — plot_rsm_surface branches
# ===========================================================================

class TestPlotRsmSurface:
    def test_full_surface_with_categorical_and_bad_point(self, tmp_path):
        pytest.importorskip("matplotlib")
        factors = [
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
            Factor(name="C", levels=["x", "y"], type="categorical"),
            Factor(name="D", levels=["p", "q"], type="continuous"),  # non-numeric -> 1271-1272
        ]
        runs = [
            _run(1, A=0, B=0, C="x", D="p"), _run(2, A=0, B=10, C="y", D="q"),
            _run(3, A=10, B=0, C="x", D="p"), _run(4, A=10, B=10, C="y", D="q"),
            _run(5, A=5, B=5, C="x", D="p"),
            _run(6, A="bad", B=5, C="y", D="q"),  # non-numeric A -> scatter 1393-1394
        ]
        responses = {i: float(10 + i) for i in range(1, 7)}
        created = plot_rsm_surface(runs, responses, factors, ["A", "B", "C", "D"],
                                   "y", str(tmp_path / "out"), response_unit="s")
        assert len(created) == 1 and os.path.exists(created[0])

    def test_fit_failure_returns_empty(self, tmp_path, monkeypatch):
        pytest.importorskip("matplotlib")
        import doe.rsm as rsm

        def boom(*a, **k):
            raise RuntimeError("fit failure")

        monkeypatch.setattr(rsm, "fit_rsm", boom)
        factors = [
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
        ]
        runs = [_run(1, A=0, B=0), _run(2, A=10, B=10), _run(3, A=5, B=5)]
        responses = {1: 1.0, 2: 2.0, 3: 1.5}
        assert plot_rsm_surface(runs, responses, factors, ["A", "B"], "y",
                                str(tmp_path / "out")) == []

    def test_duplicate_name_non_numeric_levels_continue(self, tmp_path):
        # factor_map[fa] resolves to a duplicate factor with non-numeric levels
        # so the per-pair float() conversion raises -> continue (1307-1308).
        pytest.importorskip("matplotlib")
        factors = [
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
            Factor(name="A", levels=["x", "y"], type="continuous"),  # shadows A in factor_map
        ]
        runs = [_run(1, A=0, B=0), _run(2, A=10, B=10), _run(3, A=5, B=5)]
        responses = {1: 1.0, 2: 2.0, 3: 1.5}
        created = plot_rsm_surface(runs, responses, factors, ["A", "B"], "y",
                                   str(tmp_path / "out"))
        assert created == []

    def test_duplicate_name_zero_halfrange_encode(self, tmp_path):
        # factor_map[fa] resolves to a duplicate with a zero half-range so the
        # encode() zero-guard runs (line 1345).
        pytest.importorskip("matplotlib")
        factors = [
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
            Factor(name="A", levels=["5", "5"], type="continuous"),  # half-range 0
        ]
        runs = [_run(1, A=5, B=0), _run(2, A=5, B=10), _run(3, A=5, B=5)]
        responses = {1: 1.0, 2: 2.0, 3: 1.5}
        created = plot_rsm_surface(runs, responses, factors, ["A", "B"], "y",
                                   str(tmp_path / "out"))
        assert len(created) == 1

    def test_reversed_interaction_key(self, tmp_path, monkeypatch):
        # A model whose interaction coefficient is keyed "B*A" (reversed vs the
        # plotted (A, B) pair) exercises the symmetric elif (line 1370).
        pytest.importorskip("matplotlib")
        import doe.rsm as rsm

        fake = RSMModel(
            response_name="y",
            coefficients={"intercept": 50.0, "A": 1.0, "B": 1.0, "B*A": 2.0},
            r_squared=0.9,
            adj_r_squared=0.9,
            predicted_optimum={"A": "10", "B": "10"},
            predicted_value=60.0,
        )
        monkeypatch.setattr(rsm, "fit_rsm", lambda *a, **k: fake)
        factors = [
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
        ]
        runs = [_run(1, A=0, B=0), _run(2, A=10, B=10), _run(3, A=5, B=5)]
        responses = {1: 1.0, 2: 2.0, 3: 1.5}
        created = plot_rsm_surface(runs, responses, factors, ["A", "B"], "y",
                                   str(tmp_path / "out"))
        assert len(created) == 1


# ===========================================================================
# analysis.py — normal / half-normal plots with too few effects
# ===========================================================================

class TestEffectPlotsTooFew:
    def test_normal_effects_single_effect_returns_early(self, tmp_path):
        pytest.importorskip("matplotlib")
        out = str(tmp_path / "n.png")
        plot_normal_effects([EffectResult("A", 1.0, 0.1, 100.0)], out)
        assert not os.path.exists(out)

    def test_half_normal_single_effect_returns_early(self, tmp_path):
        pytest.importorskip("matplotlib")
        out = str(tmp_path / "hn.png")
        plot_half_normal_effects([EffectResult("A", 1.0, 0.1, 100.0)], out)
        assert not os.path.exists(out)

    def test_diagnostics_too_few_residuals_returns_early(self, tmp_path):
        pytest.importorskip("matplotlib")
        pytest.importorskip("scipy")
        out = str(tmp_path / "diag.png")
        diag = ModelDiagnostics(
            residuals=[0.1, -0.2],
            fitted_values=[1.0, 2.0],
            hat_matrix_diag=[0.5, 0.5],
            press=1.0,
            predicted_r_squared=0.5,
            run_ids=[1, 2],
        )
        plot_diagnostics(diag, out)  # n < 3 -> early return (line 1431)
        assert not os.path.exists(out)


# ===========================================================================
# analysis.py — export_csv branches
# ===========================================================================

class TestExportCsv:
    def test_export_full_report(self, tmp_path):
        alias = AliasStructure(
            design_type="fractional_factorial",
            resolution=3,
            notes=["res III"],
            main_effects=[AliasEntry(effect="A", aliased_with=[("B*C", 1.0)])],
            two_factor_interactions=[
                AliasEntry(effect="B*C", aliased_with=[]),          # empty -> continue (1589)
                AliasEntry(effect="A*B", aliased_with=[("C", 0.5)]),
            ],
        )
        adequacy = ModelAdequacy(
            model_type="quadratic", n_observations=9, n_parameters=6,
            r_squared=0.95, adj_r_squared=0.9, predicted_r_squared=0.8, press=1.2,
            shapiro_w=0.98, shapiro_p=0.5, durbin_watson=2.0,
            runorder_drift_slope=0.01, runorder_drift_p=0.4,
            max_leverage=0.8, leverage_threshold=1.3, high_leverage_run_ids=[3],
            max_cooks_distance=0.5, cooks_threshold=0.44, high_influence_run_ids=[3],
        )
        power = AchievedPower(
            n_runs=9, df_error=3, residual_ms=1.0, sigma=1.0, alpha=0.05,
            delta=2.0, target_power=0.8,
            per_factor=[
                AchievedPowerEntry("A", 2, 0.6, 1.5),
                AchievedPowerEntry("B", 2, 0.5, float("inf")),  # inf -> blank cell
            ],
        )
        cv = CrossValidation(
            model_type="quadratic", k=3, n_observations=9,
            rmse=1.0, mae=0.8, r_squared_cv=0.7,
            folds=[CrossValidationFold(0, [1, 2], [10.0, 11.0], [10.5, 10.8])],
        )
        stationary = StationaryPoint(
            nature="rising_ridge",
            coded_location={"A": 0.2, "B": 0.3},
            natural_location={"A": "6", "B": "6.5"},
            predicted_value=99.0,
            eigenvalues=[0.0, -2.0],
            eigenvectors=[[1.0, 0.0], [0.0, 1.0]],
            factor_order=["A", "B"],
            inside_design_region=True,
            ridge_direction={"A": 1.0, "B": 0.0},  # -> ridge loop (1704-1705)
        )
        analysis_obj = ResponseAnalysis(
            response_name="y",
            effects=[EffectResult("A", 2.0, 0.1, 60.0), EffectResult("B", 1.0, 0.1, 40.0)],
            summary_stats={"A": {"0": {"n": 4, "mean": 10.0, "std": 1.0, "min": 8.0, "max": 12.0},
                                 "1": {"n": 4, "mean": 15.0, "std": 1.0, "min": 13.0, "max": 17.0}}},
            model_adequacy=adequacy,
            achieved_power=power,
            cross_validation=cv,
            stationary_point=stationary,
        )
        report = AnalysisReport(
            results_by_response={"y": analysis_obj},
            alias_structure=alias,
        )
        created = export_csv(report, str(tmp_path / "csv"))
        assert any("alias_structure.csv" in p for p in created)
        assert any("summary_stats_y.csv" in p for p in created)
        assert any("model_adequacy_y.csv" in p for p in created)
        assert any("stationary_point_y.csv" in p for p in created)
        # ridge axis rows must be present in the stationary CSV
        sp_path = next(p for p in created if "stationary_point_y.csv" in p)
        assert "ridge_axis[A]" in open(sp_path).read()


def test_interaction_effect_all_concordant_zero():
    """Two perfectly-correlated 2-level factors produce only concordant
    pairs (no discordant), so the interaction effect falls back to 0.0
    (analysis.py line 542)."""
    # A and B move together: (lo,lo) and (hi,hi) only -> every run is
    # concordant, discordant stays empty -> `concordant and discordant`
    # is False -> effect = 0.0.
    runs = [
        ExperimentRun(run_id=1, block_id=0, factor_values={"A": "0", "B": "0"}),
        ExperimentRun(run_id=2, block_id=0, factor_values={"A": "1", "B": "1"}),
    ]
    responses = {1: 10.0, 2: 20.0}
    interactions = _compute_interaction_effects(runs, responses, ["A", "B"])
    assert len(interactions) == 1
    assert interactions[0].interaction_effect == 0.0
    assert interactions[0].factor_a == "A"
    assert interactions[0].factor_b == "B"
