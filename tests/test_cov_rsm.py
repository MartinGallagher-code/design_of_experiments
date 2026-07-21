# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-coverage tests for doe/rsm.py and doe/optimize.py.

These tests target edge and error branches that the main suite does not
exercise: singular / degenerate matrices, too-few-point quadratic fits,
saddle / ridge / flat stationary points, minimize-vs-maximize gradients,
missing bounds, empty intersections and degenerate desirability functions.

The tests are deterministic (seeded numpy / generate_design) and hermetic
(all IO under tmp_path, no network).
"""

import json
import math

import numpy as np
import pytest

import doe.optimize
import doe.rsm as rsm_mod
from doe.models import DOEConfig, ExperimentRun, Factor, ResponseVar
from doe.design import generate_design
from doe.optimize import multi_objective, recommend
from doe.rsm import (
    RSMModel,
    _decode_settings,
    _encode_factor_value,
    _format_factor_value,
    characterize_stationary_point,
    compute_cross_validation,
    compute_model_adequacy,
    fit_rsm,
    optimize_surface,
    steepest_ascent,
)
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_model(coefficients, diagnostics=None):
    return RSMModel(
        response_name="y",
        coefficients=dict(coefficients),
        r_squared=0.5,
        adj_r_squared=0.4,
        predicted_optimum={},
        predicted_value=0.0,
        diagnostics=diagnostics,
    )


def _grid_dataset():
    """A 3x3 coded grid (9 points) with a quadratic signal + tiny noise.

    Factors A, B are continuous with levels [-1, 1] so encoded values equal
    the raw grid coordinates. Returns (runs, responses, factor_names, factors).
    """
    factors = [
        Factor(name="A", levels=["-1", "1"], type="continuous"),
        Factor(name="B", levels=["-1", "1"], type="continuous"),
    ]
    factor_names = ["A", "B"]
    coords = [-1.0, 0.0, 1.0]
    runs = []
    responses = {}
    noise = [0.3, -0.2, 0.15, -0.1, 0.25, -0.3, 0.2, -0.15, 0.1]
    rid = 1
    k = 0
    for a in coords:
        for b in coords:
            runs.append(
                ExperimentRun(
                    run_id=rid,
                    block_id=1,
                    factor_values={"A": str(a), "B": str(b)},
                )
            )
            y = 10 + 2 * a + 3 * b + 1.5 * a * b + a * a - 0.5 * b * b + noise[k]
            responses[rid] = y
            rid += 1
            k += 1
    return runs, responses, factor_names, factors


def _write_results(matrix, results_dir, value_fn):
    results_dir.mkdir(parents=True, exist_ok=True)
    for run in matrix.runs:
        with open(results_dir / f"run_{run.run_id}.json", "w") as f:
            json.dump(value_fn(run), f)


# ---------------------------------------------------------------------------
# rsm.py: _format_factor_value
# ---------------------------------------------------------------------------

def test_format_factor_value_int_bad_levels():
    """int dtype with non-numeric levels falls back (lines 50-51)."""
    factor = Factor(name="n", levels=["a", "b"], type="ordinal", dtype="int")
    assert _format_factor_value(factor, 3.6) == "4"


# ---------------------------------------------------------------------------
# rsm.py: _encode_factor_value
# ---------------------------------------------------------------------------

def test_encode_continuous_zero_half_range():
    """Continuous factor with identical levels -> 0.0 (line 75)."""
    factor = Factor(name="c", levels=["5", "5"], type="continuous")
    assert _encode_factor_value("5", factor) == 0.0


def test_encode_continuous_non_numeric_falls_back():
    """Continuous factor with non-numeric levels -> categorical (lines 77-78)."""
    factor = Factor(name="c", levels=["a", "b"], type="continuous")
    assert _encode_factor_value("a", factor) == -1.0
    assert _encode_factor_value("b", factor) == 1.0


def test_encode_single_level_categorical():
    """Single-level categorical -> 0.0 (line 90)."""
    factor = Factor(name="c", levels=["only"], type="categorical")
    assert _encode_factor_value("only", factor) == 0.0


# ---------------------------------------------------------------------------
# rsm.py: fit_rsm diagnostics fallback
# ---------------------------------------------------------------------------

def test_fit_rsm_diagnostics_exception():
    """Diagnostics failure is swallowed gracefully (lines 217-218)."""
    runs, responses, factor_names, factors = _grid_dataset()
    with patch("numpy.linalg.pinv", side_effect=RuntimeError("boom")):
        model = fit_rsm(runs, responses, factor_names, factors, model_type="linear")
    assert model.diagnostics is None


# ---------------------------------------------------------------------------
# rsm.py: optimize_surface
# ---------------------------------------------------------------------------

def test_optimize_surface_all_restarts_fail():
    """Every restart raising -> no result (lines 280, 281, 283, 284)."""
    model = _make_model({"intercept": 1.0, "A": 2.0, "A^2": -1.0})
    factors = [Factor(name="A", levels=["0", "10"], type="continuous")]
    with patch("scipy.optimize.minimize", side_effect=RuntimeError("no")):
        result = optimize_surface(model, ["A"], factors, direction="maximize")
    assert result["converged"] is False
    assert result["optimal_settings"] == {}


def test_optimize_surface_non_numeric_continuous_decode():
    """Continuous factor with non-numeric levels hits decode fallback (lines 301-302)."""
    model = _make_model({"intercept": 1.0, "A": 2.0, "A^2": -1.0})
    factors = [Factor(name="A", levels=["a", "b"], type="continuous")]
    result = optimize_surface(model, ["A"], factors, direction="maximize")
    assert "A" in result["optimal_settings"]


# ---------------------------------------------------------------------------
# rsm.py: compute_model_adequacy
# ---------------------------------------------------------------------------

def test_model_adequacy_no_diagnostics():
    """No diagnostics -> None (line 335)."""
    model = _make_model({"intercept": 1.0}, diagnostics=None)
    assert compute_model_adequacy(model) is None


def test_model_adequacy_success_and_run_order_variants():
    """Success path with and without run-order (lines 353, 355)."""
    runs, responses, factor_names, factors = _grid_dataset()
    model = fit_rsm(runs, responses, factor_names, factors, model_type="linear")
    assert model.diagnostics is not None

    # No run_ids_in_order -> line 355 branch.
    adq_default = compute_model_adequacy(model)
    assert adq_default is not None

    # Partial run_ids_in_order (length mismatch) -> line 353 branch.
    adq_partial = compute_model_adequacy(model, run_ids_in_order=[1, 2])
    assert adq_partial is not None

    # Full, valid run order -> reorder branch (lines 350-351).
    full_order = list(reversed([r.run_id for r in runs]))
    adq_full = compute_model_adequacy(model, run_ids_in_order=full_order)
    assert adq_full is not None


def test_model_adequacy_scipy_failures():
    """drift / shapiro / f-threshold failures are swallowed (378-379, 390-391, 423-424)."""
    runs, responses, factor_names, factors = _grid_dataset()
    model = fit_rsm(runs, responses, factor_names, factors, model_type="linear")

    with patch("scipy.stats.linregress", side_effect=RuntimeError("x")):
        adq = compute_model_adequacy(model)
    assert adq is not None
    assert adq.runorder_drift_slope is None

    with patch("scipy.stats.shapiro", side_effect=RuntimeError("x")):
        adq = compute_model_adequacy(model)
    assert adq is not None
    assert adq.shapiro_w is None

    with patch("scipy.stats.f") as mock_f:
        mock_f.ppf.side_effect = RuntimeError("x")
        adq = compute_model_adequacy(model)
    assert adq is not None


# ---------------------------------------------------------------------------
# rsm.py: compute_cross_validation
# ---------------------------------------------------------------------------

def test_cross_validation_empty_folds():
    """Empty train/test folds are skipped -> None (lines 536, 579)."""
    runs, responses, factor_names, factors = _grid_dataset()

    def fake_split(arr, k):
        n = len(arr)
        return [np.array([], dtype=int), np.arange(n)]

    with patch.object(rsm_mod._np, "array_split", side_effect=fake_split):
        cv = compute_cross_validation(
            runs, responses, factor_names, factors, model_type="linear", seed=0
        )
    assert cv is None


def test_cross_validation_train_fit_raises():
    """Training-fold fit failures are skipped -> None (lines 540, 541, 579)."""
    runs, responses, factor_names, factors = _grid_dataset()

    orig_fit = rsm_mod.fit_rsm
    state = {"n": 0}

    def fake_fit(*args, **kwargs):
        state["n"] += 1
        if state["n"] == 1:
            # First call is the trial full-model fit used to count params.
            return orig_fit(*args, **kwargs)
        raise RuntimeError("singular training subset")

    with patch.object(rsm_mod, "fit_rsm", side_effect=fake_fit):
        cv = compute_cross_validation(
            runs, responses, factor_names, factors, model_type="linear", seed=0
        )
    assert cv is None


# ---------------------------------------------------------------------------
# rsm.py: characterize_stationary_point
# ---------------------------------------------------------------------------

def test_characterize_no_factors():
    """Empty factor list -> None (line 621)."""
    model = _make_model({"A^2": 1.0})
    assert characterize_stationary_point(model, [], []) is None


def test_characterize_pinv_linalg_error():
    """LinAlgError from pinv -> None (lines 649-650)."""
    model = _make_model({"A^2": 1.0, "A": 1.0})
    factors = [Factor(name="A", levels=["0", "10"], type="continuous")]
    with patch("numpy.linalg.pinv", side_effect=np.linalg.LinAlgError("bad")):
        assert characterize_stationary_point(model, ["A"], factors) is None


def test_characterize_flat():
    """Zero Hessian -> flat (line 661)."""
    model = _make_model({"A^2": 0.0, "B^2": 0.0})
    factors = [
        Factor(name="A", levels=["0", "10"], type="continuous"),
        Factor(name="B", levels=["0", "10"], type="continuous"),
    ]
    sp = characterize_stationary_point(model, ["A", "B"], factors)
    assert sp is not None
    assert sp.nature == "flat"


def test_characterize_ridge():
    """Near-zero eigenvalue with positive others -> ridge (line 685)."""
    model = _make_model({"A^2": 1.0, "B^2": 0.001, "A": 0.5, "B": 0.2})
    factors = [
        Factor(name="A", levels=["0", "10"], type="continuous"),
        Factor(name="B", levels=["0", "10"], type="continuous"),
    ]
    sp = characterize_stationary_point(model, ["A", "B"], factors)
    assert sp is not None
    assert sp.nature == "ridge"
    assert sp.ridge_direction is not None


def test_characterize_saddle_with_ridge():
    """Near-zero eigenvalue with both signs present -> saddle (line 689)."""
    model = _make_model({"A^2": 1.0, "B^2": -1.0, "C^2": 0.001})
    factors = [
        Factor(name="A", levels=["0", "10"], type="continuous"),
        Factor(name="B", levels=["0", "10"], type="continuous"),
        Factor(name="C", levels=["0", "10"], type="continuous"),
    ]
    sp = characterize_stationary_point(model, ["A", "B", "C"], factors)
    assert sp is not None
    assert sp.nature == "saddle"


# ---------------------------------------------------------------------------
# rsm.py: _decode_settings
# ---------------------------------------------------------------------------

def test_decode_settings_all_branches():
    """Cover every decode branch (726-727, 737-738, 740-742, 745-752)."""
    factors = [
        # "X" intentionally absent -> factor is None (726-727)
        Factor(name="cont_bad", levels=["a", "b"], type="continuous"),  # 737-738
        Factor(name="cat2", levels=["p", "q"], type="categorical"),      # 740-742
        Factor(name="cat1", levels=["solo"], type="categorical"),        # 745-748
        Factor(name="cat3", levels=["a", "b", "c"], type="categorical"), # 745-746, 750-752
    ]
    factor_names = ["X", "cont_bad", "cat2", "cat1", "cat3"]
    coded = {"X": 0.3, "cont_bad": 0.5, "cat2": 0.5, "cat1": 0.0, "cat3": 0.9}
    out = _decode_settings(coded, factor_names, factors)
    assert out["X"] == "0.3000"
    assert out["cont_bad"] == "0.5000"
    assert out["cat2"] == "q"       # coded > 0 -> second level
    assert out["cat1"] == "solo"    # single level
    assert out["cat3"] == "c"       # coded 0.9 -> highest index


# ---------------------------------------------------------------------------
# rsm.py: steepest_ascent
# ---------------------------------------------------------------------------

def test_steepest_ascent_minimize():
    """Minimize negates the gradient (line 774)."""
    model = _make_model({"intercept": 0.0, "A": 2.0, "B": 1.0})
    factors = [
        Factor(name="A", levels=["0", "10"], type="continuous"),
        Factor(name="B", levels=["0", "10"], type="continuous"),
    ]
    path = steepest_ascent(model, ["A", "B"], factors, direction="minimize", n_steps=2)
    assert len(path) == 3
    # Moving in the descent direction lowers A below its centre.
    assert float(path[-1]["settings"]["A"]) < 5.0


def test_steepest_ascent_zero_gradient():
    """Zero gradient -> empty path (line 779)."""
    model = _make_model({"intercept": 5.0})
    factors = [Factor(name="A", levels=["0", "10"], type="continuous")]
    assert steepest_ascent(model, ["A"], factors) == []


def test_steepest_ascent_decode_branches():
    """Non-numeric continuous + categorical decode (lines 802-803, 805)."""
    model = _make_model({"intercept": 0.0, "A": 2.0, "B": 1.0})
    factors = [
        Factor(name="A", levels=["a", "b"], type="continuous"),   # 802-803
        Factor(name="B", levels=["lo", "hi"], type="categorical"),  # 805
    ]
    path = steepest_ascent(model, ["A", "B"], factors, direction="maximize", n_steps=1)
    assert len(path) == 2
    # A decodes via the string fallback; B decodes to a level label.
    assert path[1]["settings"]["B"] in ("lo", "hi")


# ---------------------------------------------------------------------------
# optimize.py: recommend
# ---------------------------------------------------------------------------

def _rsq_config():
    return DOEConfig(
        factors=[
            Factor(name="A", levels=["0", "2"], type="continuous"),
            Factor(name="B", levels=["0", "2"], type="continuous"),
        ],
        fixed_factors={},
        responses=[ResponseVar(name="y", optimize="maximize")],
        block_count=1,
        test_script="t.sh",
        operation="full_factorial",
        processed_directory="",
        out_directory="results",
    )


def _corner_response(run, c):
    a = (float(run.factor_values["A"]) - 1.0)  # half_range == 1
    b = (float(run.factor_values["B"]) - 1.0)
    return {"y": 14.0 + 2.0 * a + 2.0 * b + c * a * b}


def test_recommend_good_fit_quality(tmp_path):
    """R^2 in (0.7, 0.9] -> 'Good fit' branch (line 162)."""
    cfg = _rsq_config()
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "good"
    c = math.sqrt(2.0)  # -> R^2 == 0.8
    _write_results(matrix, results_dir, lambda r: _corner_response(r, c))
    recommend(matrix, cfg, results_dir=str(results_dir))


def test_recommend_moderate_fit_quality(tmp_path):
    """R^2 in (0.5, 0.7] -> 'Moderate fit' branch (line 164)."""
    cfg = _rsq_config()
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "moderate"
    c = math.sqrt(16.0 / 3.0)  # -> R^2 == 0.6
    _write_results(matrix, results_dir, lambda r: _corner_response(r, c))
    recommend(matrix, cfg, results_dir=str(results_dir))


def test_recommend_quadratic_negligible_curvature(tmp_path):
    """Constant response -> negligible curvature branch (line 107)."""
    cfg = DOEConfig(
        factors=[
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
        ],
        fixed_factors={},
        responses=[ResponseVar(name="y", optimize="maximize")],
        block_count=1,
        test_script="t.sh",
        operation="central_composite",
        processed_directory="",
        out_directory="results",
    )
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "const"
    _write_results(matrix, results_dir, lambda r: {"y": 50.0})
    recommend(matrix, cfg, results_dir=str(results_dir))


def test_recommend_quadratic_fit_raises(tmp_path):
    """Quadratic fit failure is swallowed (lines 126-127)."""
    cfg = DOEConfig(
        factors=[
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
        ],
        fixed_factors={},
        responses=[ResponseVar(name="y", optimize="maximize")],
        block_count=1,
        test_script="t.sh",
        operation="central_composite",
        processed_directory="",
        out_directory="results",
    )
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "quadfail"
    _write_results(matrix, results_dir, lambda r: {"y": 40.0 + float(r.factor_values["A"])})

    orig_fit = doe.optimize.fit_rsm

    def fake_fit(*args, **kwargs):
        if kwargs.get("model_type") == "quadratic":
            raise RuntimeError("singular matrix")
        return orig_fit(*args, **kwargs)

    with patch.object(doe.optimize, "fit_rsm", side_effect=fake_fit):
        recommend(matrix, cfg, results_dir=str(results_dir))


def test_recommend_optimize_surface_import_error(tmp_path, monkeypatch):
    """Missing optimize_surface -> ImportError swallowed (lines 154-155)."""
    cfg = _rsq_config()
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "noscipy"
    _write_results(matrix, results_dir, lambda r: {"y": 80.0 + float(r.factor_values["A"])})
    monkeypatch.delattr(rsm_mod, "optimize_surface")
    recommend(matrix, cfg, results_dir=str(results_dir))


# ---------------------------------------------------------------------------
# optimize.py: multi_objective
# ---------------------------------------------------------------------------

def _mo_config(operation="full_factorial", factor_b_categorical=False, weights=(1.0, 1.0)):
    b_kwargs = (
        dict(levels=["x", "y"], type="categorical")
        if factor_b_categorical
        else dict(levels=["0", "10"], type="continuous")
    )
    return DOEConfig(
        factors=[
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", **b_kwargs),
        ],
        fixed_factors={},
        responses=[
            ResponseVar(name="r1", optimize="maximize", weight=weights[0]),
            ResponseVar(name="r2", optimize="minimize", weight=weights[1]),
        ],
        block_count=1,
        test_script="t.sh",
        operation=operation,
        processed_directory="",
        out_directory="results",
    )


def test_multi_objective_quadratic_fit_raises(tmp_path):
    """Quadratic fit failure swallowed in multi_objective (lines 242-243)."""
    cfg = _mo_config(operation="central_composite")
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "moquad"
    _write_results(
        matrix, results_dir,
        lambda r: {"r1": 80.0 + float(r.factor_values["A"]),
                   "r2": 100.0 - float(r.factor_values["A"])},
    )

    orig_fit = doe.optimize.fit_rsm

    def fake_fit(*args, **kwargs):
        if kwargs.get("model_type") == "quadratic":
            raise RuntimeError("singular matrix")
        return orig_fit(*args, **kwargs)

    with patch.object(doe.optimize, "fit_rsm", side_effect=fake_fit):
        multi_objective(matrix, cfg, results_dir=str(results_dir))


def test_multi_objective_insufficient_response_data(tmp_path):
    """Only one response has data -> early return (lines 249-250)."""
    cfg = _mo_config()
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "onedata"
    _write_results(matrix, results_dir, lambda r: {"r1": 80.0 + float(r.factor_values["A"])})
    multi_objective(matrix, cfg, results_dir=str(results_dir))


def test_multi_objective_individual_zero_desirability(tmp_path):
    """A run with a zero individual desirability (lines 318-319)."""
    cfg = _mo_config()
    # Explicit bounds so an observed value can land exactly on the low edge.
    cfg.responses[0].bounds = [80.0, 90.0]
    cfg.responses[1].bounds = [90.0, 110.0]
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "zerod"

    vals = {}
    for i, run in enumerate(matrix.runs):
        # First run sits at the low bound of a maximize response -> d == 0.
        r1 = 80.0 if i == 0 else 85.0 + i
        vals[run.run_id] = {"r1": r1, "r2": 100.0}
    _write_results(matrix, results_dir, lambda r: vals[r.run_id])
    multi_objective(matrix, cfg, results_dir=str(results_dir))


def test_multi_objective_zero_total_weight(tmp_path):
    """Zero total weight with all-positive desirabilities (line 321)."""
    cfg = _mo_config(weights=(0.0, 0.0))
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "zerow"
    _write_results(
        matrix, results_dir,
        lambda r: {"r1": 80.0 + float(r.factor_values["A"]),
                   "r2": 100.0 - float(r.factor_values["A"])},
    )
    multi_objective(matrix, cfg, results_dir=str(results_dir))


def test_multi_objective_no_common_runs(tmp_path):
    """Disjoint response coverage -> empty intersection (lines 326-327)."""
    cfg = _mo_config()
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "disjoint"
    results_dir.mkdir(parents=True, exist_ok=True)
    runs = matrix.runs
    half = len(runs) // 2
    for i, run in enumerate(runs):
        payload = {"r1": 80.0 + i} if i < half else {"r2": 100.0 - i}
        with open(results_dir / f"run_{run.run_id}.json", "w") as f:
            json.dump(payload, f)
    multi_objective(matrix, cfg, results_dir=str(results_dir))


def test_multi_objective_non_numeric_continuous_grid(tmp_path):
    """Continuous factor with non-numeric levels raises in grid build (345-346)."""
    cfg = _mo_config(factor_b_categorical=False)
    # Make factor B continuous but with non-numeric levels.
    cfg.factors[1] = Factor(name="B", levels=["a", "b"], type="continuous")
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "badgrid"
    _write_results(
        matrix, results_dir,
        lambda r: {"r1": 80.0 + float(r.factor_values["A"]),
                   "r2": 100.0 - float(r.factor_values["A"])},
    )
    with pytest.raises(ValueError):
        multi_objective(matrix, cfg, results_dir=str(results_dir))


def test_multi_objective_desirability_edge_bounds(tmp_path):
    """Exercise every _desirability branch (lines 278, 283, 288, 290)."""
    cfg = DOEConfig(
        factors=[
            Factor(name="A", levels=["0", "10"], type="continuous"),
            Factor(name="B", levels=["0", "10"], type="continuous"),
        ],
        fixed_factors={},
        responses=[
            ResponseVar(name="rA", optimize="maximize"),  # degenerate bounds
            ResponseVar(name="rB", optimize="maximize"),
            ResponseVar(name="rC", optimize="minimize"),
        ],
        block_count=1,
        test_script="t.sh",
        operation="full_factorial",
        processed_directory="",
        out_directory="results",
    )
    cfg.responses[0].bounds = [90.0, 90.0]    # high == low -> line 278
    cfg.responses[1].bounds = [80.0, 90.0]    # maximize
    cfg.responses[2].bounds = [95.0, 105.0]   # minimize
    matrix = generate_design(cfg, seed=42)    # 4 runs
    vals = [
        {"rA": 90.0, "rB": 95.0, "rC": 90.0},   # rB >= high (283), rC <= low (290)
        {"rA": 90.0, "rB": 70.0, "rC": 110.0},  # rB <= low (281), rC >= high (288)
        {"rA": 90.0, "rB": 85.0, "rC": 100.0},  # interior
        {"rA": 90.0, "rB": 88.0, "rC": 98.0},   # interior
    ]
    mapping = {run.run_id: vals[i] for i, run in enumerate(matrix.runs)}
    _write_results(matrix, tmp_path / "edge", lambda r: mapping[r.run_id])
    multi_objective(matrix, cfg, results_dir=str(tmp_path / "edge"))


def test_multi_objective_grid_beats_observed(tmp_path):
    """Grid optimum (conflicting objectives) beats observed (423-426, 437-440, 470-478)."""
    cfg = _mo_config(factor_b_categorical=True)
    matrix = generate_design(cfg, seed=42)
    results_dir = tmp_path / "gridwin"
    # r1 wants high A, r2 wants low A -> interior compromise wins.
    _write_results(
        matrix, results_dir,
        lambda r: {"r1": float(r.factor_values["A"]),
                   "r2": float(r.factor_values["A"])},
    )
    multi_objective(matrix, cfg, results_dir=str(results_dir))
