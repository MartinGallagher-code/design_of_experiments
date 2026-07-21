# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-coverage tests for :mod:`doe.design`.

These tests drive the error branches, alternate design-size branches, and
fallback paths of ``doe/design.py`` that the functional test-suite does not
otherwise reach: the pyDOE3 import-guard clauses, alias-structure handling,
Taguchi orthogonal-array fallbacks, D-optimal / augmentation degenerate
cases, mixture and sweep expansions, and the design-evaluation metric
error handling.  Everything is deterministic (seeded / monkeypatched) and
hermetic (no filesystem writes, no network).
"""

import sys
from itertools import combinations

import numpy as np
import pytest

from doe.models import (
    DOEConfig,
    DesignMatrix,
    ExperimentRun,
    Factor,
    ResponseVar,
)
from doe import design as d
from doe.design import (
    generate_design,
    augment_design,
    evaluate_design,
    _latin_hypercube,
    _plackett_burman,
    _central_composite,
    _box_behnken,
    _fractional_factorial,
    _taguchi,
    _decode_lhs_value,
    _decode_coded_value,
    _best_generator_choice,
    _resolution_diagnostics,
    _alias_score,
    _d_optimal_augment,
)


def _cfg(factors, operation, **kw):
    """Build a minimal DOEConfig for the given factors / operation."""
    return DOEConfig(
        factors=factors,
        fixed_factors={},
        responses=[ResponseVar(name="y")],
        block_count=1,
        test_script="test.sh",
        operation=operation,
        processed_directory="",
        out_directory="",
        **kw,
    )


# ---------------------------------------------------------------------------
# generate_design dispatch
# ---------------------------------------------------------------------------

def test_generate_design_unknown_operation():
    """Line 61: unknown operation raises ValueError."""
    cfg = _cfg([Factor("A", ["1", "2"])], "does_not_exist")
    with pytest.raises(ValueError, match="Unknown operation"):
        generate_design(cfg)


# ---------------------------------------------------------------------------
# pyDOE3 import-guard clauses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "func, operation",
    [
        (_plackett_burman, "plackett_burman"),
        (_latin_hypercube, "latin_hypercube"),
        (_central_composite, "central_composite"),
        (_fractional_factorial, "fractional_factorial"),
        (_box_behnken, "box_behnken"),
        (_taguchi, "taguchi"),
    ],
)
def test_pydoe3_import_guard(monkeypatch, func, operation):
    """Lines 137-138, 161-162, 206-207, 380-381, 461-462, 658-659.

    When pyDOE3 cannot be imported, each design helper re-raises ImportError
    with an install hint.
    """
    # Ensure pyDOE3 is a real module first so monkeypatch can restore it.
    import pyDOE3  # noqa: F401
    monkeypatch.setitem(sys.modules, "pyDOE3", None)
    cfg = _cfg([Factor("A", ["1", "2"]), Factor("B", ["1", "2"])], operation)
    with pytest.raises(ImportError, match="pyDOE3 is required"):
        func(cfg)


# ---------------------------------------------------------------------------
# Latin hypercube: criterion TypeError fallback
# ---------------------------------------------------------------------------

def test_latin_hypercube_criterion_typeerror_fallback(monkeypatch):
    """Lines 176-177: pyDOE3.lhs without maximin criterion support."""
    import pyDOE3

    def fake_lhs(n, samples=None, **kwargs):
        if "criterion" in kwargs:
            raise TypeError("criterion unsupported in this pyDOE3 build")
        return np.linspace(0.0, 1.0, samples * n).reshape(samples, n)

    monkeypatch.setattr(pyDOE3, "lhs", fake_lhs)
    cfg = _cfg([Factor("A", ["0", "1"], type="continuous")],
               "latin_hypercube", lhs_samples=6)
    runs = _latin_hypercube(cfg, seed=7)
    assert len(runs) == 6


# ---------------------------------------------------------------------------
# _decode_lhs_value
# ---------------------------------------------------------------------------

def test_decode_lhs_value_non_numeric_continuous():
    """Lines 197-198, 200: continuous factor with non-numeric levels falls
    back to binning."""
    factor = Factor("A", ["low", "high"], type="continuous")
    # float("low") raises -> ValueError branch -> binned to a level.
    assert _decode_lhs_value(0.1, factor) == "low"
    assert _decode_lhs_value(0.9, factor) == "high"


def test_decode_lhs_value_categorical_binning():
    """Line 200: categorical multi-level factor bins into a level."""
    factor = Factor("A", ["p", "q", "r"], type="categorical")
    assert _decode_lhs_value(0.99, factor) == "r"
    assert _decode_lhs_value(0.0, factor) == "p"


# ---------------------------------------------------------------------------
# _decode_coded_value
# ---------------------------------------------------------------------------

def test_decode_coded_value_float_dtype():
    """Line 258: non-integer factor returns %.6g formatting."""
    factor = Factor("A", ["0.5", "1.5"], type="continuous")
    assert _decode_coded_value(0.5, factor) == "1.25"


# ---------------------------------------------------------------------------
# _best_generator_choice
# ---------------------------------------------------------------------------

def _interaction_pool(base_letters):
    pool = []
    for r in range(len(base_letters), 1, -1):
        for combo in combinations(base_letters, r):
            pool.append("".join(combo))
    return pool


def test_best_generator_choice_candidate_cap():
    """Line 297: candidate enumeration stops at MAX_CANDIDATES."""
    base = ["a", "b", "c", "d", "e"]
    pool = _interaction_pool(base)  # 26 interactions
    # C(26, 2) == 325 > 200 -> the break at MAX_CANDIDATES fires.
    result = _best_generator_choice(base, pool, 2, ["A", "B", "C", "D", "E"])
    assert len(result) == 2
    assert all(gen in pool for gen in result)


def test_best_generator_choice_all_fracfact_fail(monkeypatch):
    """Lines 304-305, 310: every fracfact call fails -> greedy fallback."""
    import pyDOE3

    def boom(_gen):
        raise RuntimeError("fracfact refused this generator string")

    monkeypatch.setattr(pyDOE3, "fracfact", boom)
    base = ["a", "b", "c"]
    pool = _interaction_pool(base)
    result = _best_generator_choice(base, pool, 2, ["A", "B", "C"])
    # No candidate survived -> returns the longest-first greedy prefix.
    assert result == pool[:2]


# ---------------------------------------------------------------------------
# _resolution_diagnostics / _alias_score
# ---------------------------------------------------------------------------

def test_resolution_diagnostics_single_column():
    """Line 349: fewer than two columns yields zero diagnostics."""
    assert _resolution_diagnostics(np.ones((4, 1))) == (0.0, 0.0)


def test_resolution_diagnostics_zero_norm_column():
    """Line 356: a degenerate (zero-norm) column returns full aliasing."""
    design = np.array([[0, 1], [0, -1], [0, 1], [0, -1]], dtype=float)
    assert _resolution_diagnostics(design) == (1.0, 1.0)


def test_alias_score_delegates():
    """Lines 373-374: _alias_score returns max of the two diagnostics."""
    design = np.array([[1, 1], [1, -1], [-1, 1], [-1, -1]], dtype=float)
    assert _alias_score(design) == 0.0


# ---------------------------------------------------------------------------
# _fractional_factorial alias-structure handling
# ---------------------------------------------------------------------------

def test_fractional_factorial_alias_info_list(monkeypatch):
    """Lines 442-443: fracfact_aliasing returning a list is stored directly."""
    import pyDOE3

    monkeypatch.setattr(pyDOE3, "fracfact_aliasing", lambda mat: ["a=bcd", "b=acd"])
    cfg = _cfg([Factor(n, ["1", "2"]) for n in "ABCD"], "fractional_factorial")
    _fractional_factorial(cfg)
    assert cfg._alias_structure == ["a=bcd", "b=acd"]


def test_fractional_factorial_alias_info_raises(monkeypatch):
    """Lines 444-445: an exception in alias analysis is swallowed."""
    import pyDOE3

    def boom(_mat):
        raise RuntimeError("alias analysis failed")

    monkeypatch.setattr(pyDOE3, "fracfact_aliasing", boom)
    cfg = _cfg([Factor(n, ["1", "2"]) for n in "ABCD"], "fractional_factorial")
    runs = _fractional_factorial(cfg)
    assert cfg._alias_structure is None
    assert len(runs) > 0


# ---------------------------------------------------------------------------
# Taguchi fallbacks
# ---------------------------------------------------------------------------

def _fake_taguchi_design(levels_per_factor):
    return np.zeros((4, len(levels_per_factor)), dtype=int)


def test_taguchi_no_orthogonal_array_found(monkeypatch):
    """Lines 681-682, 688-689: OA lookup fails -> taguchi_design fallback."""
    import pyDOE3

    def raising_get_oa(_name):
        raise RuntimeError("could not load orthogonal array")

    monkeypatch.setattr(pyDOE3, "get_orthogonal_array", raising_get_oa)
    monkeypatch.setattr(pyDOE3, "taguchi_design", _fake_taguchi_design)
    cfg = _cfg([Factor("A", ["1", "2"]), Factor("B", ["1", "2"])], "taguchi")
    runs = _taguchi(cfg)
    assert len(runs) == 4


def test_taguchi_list_oa_attribute_error(monkeypatch):
    """Lines 689, 691: list_orthogonal_arrays missing -> outer fallback."""
    import pyDOE3

    def raising_list_oa():
        raise AttributeError("list_orthogonal_arrays absent in this build")

    monkeypatch.setattr(pyDOE3, "list_orthogonal_arrays", raising_list_oa)
    monkeypatch.setattr(pyDOE3, "taguchi_design", _fake_taguchi_design)
    cfg = _cfg([Factor("A", ["1", "2"])], "taguchi")
    runs = _taguchi(cfg)
    assert len(runs) == 4


# ---------------------------------------------------------------------------
# _d_optimal
# ---------------------------------------------------------------------------

def test_d_optimal_non_numeric_continuous_factor():
    """Lines 733-735: a continuous factor with non-numeric levels is kept
    as-is during candidate enrichment."""
    cfg = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("B", ["a", "b"], type="continuous"),
        ],
        "d_optimal",
        lhs_samples=2,
    )
    matrix = generate_design(cfg, seed=3)
    assert len(matrix.runs) > 0
    assert matrix.operation == "d_optimal"


def test_d_optimal_det_failure(monkeypatch):
    """Lines 768-769: compute_d_criterion swallows determinant errors."""
    def boom_det(_x):
        raise RuntimeError("det blew up")

    monkeypatch.setattr(np.linalg, "det", boom_det)
    cfg = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("B", ["0", "10"], type="continuous"),
        ],
        "d_optimal",
        lhs_samples=4,
    )
    matrix = generate_design(cfg, seed=3)
    assert len(matrix.runs) == 4


# ---------------------------------------------------------------------------
# _d_optimal_augment
# ---------------------------------------------------------------------------

def test_d_optimal_augment_non_numeric_continuous():
    """Lines 831-833: augmentation keeps non-numeric continuous levels."""
    base = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("B", ["a", "b"], type="continuous"),
        ],
        "full_factorial",
    )
    matrix = generate_design(base, seed=1)
    augmented = augment_design(matrix, base, augment_type="d_optimal")
    assert len(augmented.runs) > len(matrix.runs)


def test_d_optimal_augment_score_failure(monkeypatch):
    """Lines 855-856: score() swallows determinant errors during augment."""
    base = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("B", ["0", "10"], type="continuous"),
        ],
        "full_factorial",
    )
    matrix = generate_design(base, seed=1)

    def boom_det(_x):
        raise RuntimeError("det blew up")

    monkeypatch.setattr(np.linalg, "det", boom_det)
    augmented = augment_design(matrix, base, augment_type="d_optimal")
    assert len(augmented.runs) > len(matrix.runs)


def test_d_optimal_augment_no_candidates():
    """Line 859: an empty candidate set returns the existing runs unchanged."""
    existing = [ExperimentRun(1, 1, {"X": "a"})]
    cfg = _cfg([Factor("X", [])], "d_optimal")
    out = _d_optimal_augment(existing, cfg, n_new=4, max_run_id=1, max_block_id=1)
    assert out == existing


def test_d_optimal_augment_fewer_candidates_than_requested():
    """Line 861: when candidates <= n_new, use them all."""
    existing = [ExperimentRun(1, 1, {"X": "a"})]
    cfg = _cfg([Factor("X", ["a", "b"])], "d_optimal")
    out = _d_optimal_augment(existing, cfg, n_new=5, max_run_id=1, max_block_id=1)
    # existing (1) + the two candidate combos.
    assert len(out) == 3


# ---------------------------------------------------------------------------
# augment_design branches
# ---------------------------------------------------------------------------

def test_augment_fold_over_multilevel_passthrough():
    """Line 933: fold-over leaves a >2-level factor's value unchanged."""
    cfg = _cfg(
        [Factor("A", ["1", "2"]), Factor("B", ["x", "y", "z"])],
        "full_factorial",
    )
    matrix = generate_design(cfg, seed=1)
    augmented = augment_design(matrix, cfg, augment_type="fold_over")
    assert len(augmented.runs) == 2 * len(matrix.runs)
    # The 3-level factor keeps one of its own levels on every mirrored run.
    for run in augmented.runs:
        assert run.factor_values["B"] in {"x", "y", "z"}


def test_augment_star_points_mixed_factors():
    """Lines 942-969: star-point augmentation across continuous, bad-continuous,
    and categorical factors."""
    cfg = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),   # numeric main + numeric "other"
            Factor("B", ["0", "20"], type="continuous"),
            Factor("C", ["a", "b"], type="categorical"),   # skipped as loop factor; ValueError as "other"
            Factor("D", ["x", "y"], type="continuous"),    # non-numeric continuous -> ValueError continue
        ],
        "full_factorial",
    )
    matrix = generate_design(cfg, seed=1)
    augmented = augment_design(matrix, cfg, augment_type="star_points")
    # Two continuous, numeric factors (A, B) each contribute 2 star points.
    assert len(augmented.runs) == len(matrix.runs) + 4


def test_augment_center_points_mixed_factors():
    """Lines 977-986: center-point augmentation with numeric + categorical."""
    cfg = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("C", ["a", "b"], type="categorical"),
        ],
        "full_factorial",
    )
    matrix = generate_design(cfg, seed=1)
    augmented = augment_design(matrix, cfg, augment_type="center_points")
    assert len(augmented.runs) == len(matrix.runs) + 3
    center_runs = augmented.runs[-3:]
    for run in center_runs:
        assert run.factor_values["A"] == "5"       # numeric midpoint
        assert run.factor_values["C"] == "a"       # categorical falls back to first level


# ---------------------------------------------------------------------------
# Sweep int-dtype expansion
# ---------------------------------------------------------------------------

def test_linear_sweep_int_dtype():
    """Lines 1048-1050: integer factor expands to every integer in range."""
    cfg = _cfg(
        [Factor("A", ["1", "5"], type="continuous", dtype="int")],
        "linear_sweep",
    )
    matrix = generate_design(cfg, seed=1)
    values = sorted(int(r.factor_values["A"]) for r in matrix.runs)
    assert values == [1, 2, 3, 4, 5]


def test_log_sweep_int_dtype():
    """Lines 1085-1086: integer factor with log spacing dedupes to ints."""
    cfg = _cfg(
        [Factor("A", ["1", "100"], type="continuous", dtype="int")],
        "log_sweep",
    )
    matrix = generate_design(cfg, seed=1)
    values = [int(r.factor_values["A"]) for r in matrix.runs]
    assert all(1 <= v <= 100 for v in values)
    # int-dtype log spacing dedupes to unique integers (run order is randomized).
    assert len(values) == len(set(values))
    assert 1 in values and 100 in values


# ---------------------------------------------------------------------------
# Mixture designs
# ---------------------------------------------------------------------------

def test_mixture_simplex_lattice_non_numeric_and_single_level():
    """Lines 1133-1134, 1136: non-numeric 2-level and single-level factors."""
    cfg = _cfg(
        [
            Factor("A", ["0", "1"], type="continuous"),   # numeric mapping
            Factor("B", ["a", "b"], type="continuous"),   # non-numeric -> ValueError branch
            Factor("C", ["x"], type="continuous"),        # <2 levels -> proportion branch
        ],
        "mixture_simplex_lattice",
    )
    matrix = generate_design(cfg, seed=1)
    assert len(matrix.runs) > 0
    assert matrix.operation == "mixture_simplex_lattice"


def test_mixture_simplex_centroid_higher_order_and_decodes():
    """Lines 1175-1179, 1193-1194, 1196: >=4 components exercise the
    higher-order centroid loop plus the non-numeric / single-level decode
    branches."""
    cfg = _cfg(
        [
            Factor("A", ["0", "1"], type="continuous"),
            Factor("B", ["a", "b"], type="continuous"),   # non-numeric decode
            Factor("C", ["x"], type="continuous"),        # single level decode
            Factor("D", ["0", "1"], type="continuous"),
        ],
        "mixture_simplex_centroid",
    )
    matrix = generate_design(cfg, seed=1)
    # q == 4 -> vertices + edges + faces + the overall (r=4) centroid.
    assert len(matrix.runs) == 4 + 6 + 4 + 1
    assert matrix.operation == "mixture_simplex_centroid"


# ---------------------------------------------------------------------------
# evaluate_design metric error handling
# ---------------------------------------------------------------------------

def test_evaluate_design_singular_matrix():
    """Lines 1222, 1229-1230: a rank-deficient design yields zero D/A efficiency."""
    cfg = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("B", ["0", "10"], type="continuous"),
        ],
        "full_factorial",
    )
    matrix = DesignMatrix(
        runs=[ExperimentRun(1, 1, {"A": "5", "B": "5"})],
        factor_names=["A", "B"],
        operation="full_factorial",
    )
    metrics = evaluate_design(matrix, cfg)
    assert metrics["d_efficiency"] == 0.0
    assert metrics["a_efficiency"] == 0.0


def test_evaluate_design_g_efficiency_failure(monkeypatch):
    """Lines 1238-1239: a failure inside the G-efficiency block is caught."""
    cfg = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("B", ["0", "10"], type="continuous"),
        ],
        "full_factorial",
    )
    matrix = generate_design(cfg, seed=1)

    def boom_pinv(_x):
        raise RuntimeError("pinv blew up")

    monkeypatch.setattr(np.linalg, "pinv", boom_pinv)
    metrics = evaluate_design(matrix, cfg)
    assert metrics["g_efficiency"] == 0.0


def test_evaluate_design_outer_failure(monkeypatch):
    """Lines 1241-1244: a failure computing det zeroes every metric."""
    cfg = _cfg(
        [
            Factor("A", ["0", "10"], type="continuous"),
            Factor("B", ["0", "10"], type="continuous"),
        ],
        "full_factorial",
    )
    matrix = generate_design(cfg, seed=1)

    def boom_det(_x):
        raise RuntimeError("det blew up")

    monkeypatch.setattr(np.linalg, "det", boom_det)
    metrics = evaluate_design(matrix, cfg)
    assert metrics == {
        "d_efficiency": 0.0,
        "a_efficiency": 0.0,
        "g_efficiency": 0.0,
    }
