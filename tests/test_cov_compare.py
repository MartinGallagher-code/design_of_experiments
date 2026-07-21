# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-coverage tests for doe/compare.py, doe/trend.py, and doe/calibrate.py.

These exercise the edge and error branches that the main suite leaves
uncovered: unmatched runs, missing/non-numeric responses, single-run and
insufficient-degrees-of-freedom regressions, absent optional dependencies
(numpy / scipy / matplotlib), singular-matrix fallbacks, and the HTML/CSV
export paths for empty or note-only results.

All fixtures are hermetic: on-disk sessions are built under ``tmp_path``,
numpy randomness is unused, and optional imports are toggled via monkeypatch.
"""

import json
import os
import sys

import numpy as np
import pytest

from doe.models import (
    DOEConfig, Factor, ResponseVar, ExperimentRun,
    ComparisonReport, ResponseComparison, PerRunDelta, EffectDelta,
    DeltaDecomposition, TrendReport, TrendResponse, SessionTrendEntry,
)
from doe import compare as compare_mod
from doe.compare import (
    compare_sessions, export_compare_csv, export_compare_html,
    _load_session_runs, _load_results, _coerce, _paired_test, _sort_key,
    _compute_effect_deltas, _decompose_delta, _render_delta_dotplot,
    _anchor_id_local,
)
from doe import trend as trend_mod
from doe.trend import (
    trend_sessions, export_trend_html, export_trend_csv,
    _trend_for_response, _render_means_lineplot,
)
from doe import calibrate as calibrate_mod
from doe.calibrate import (
    calibrate, CalibrationParam, load_observed,
    _weighted_sse, _residual_metrics,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(factor_levels, response_names):
    """Build a DOEConfig from {factor_name: [levels]} and a list of responses."""
    return DOEConfig(
        factors=[Factor(name=n, levels=list(lv)) for n, lv in factor_levels.items()],
        fixed_factors={},
        responses=[ResponseVar(name=r) for r in response_names],
        block_count=1,
        test_script="",
        operation="full_factorial",
        processed_directory="",
        out_directory="",
    )


def _write_session(session_dir, factor_names, runs, *, write_matrix=True):
    """Create a session directory on disk.

    ``runs`` is a list of dicts, each ``{"run_id", "factor_values",
    "responses"}`` where ``responses`` may be None (write no file), a dict
    (write JSON), or the literal string ``"__corrupt__"`` (write bad JSON).
    """
    os.makedirs(session_dir, exist_ok=True)
    if write_matrix:
        matrix = {
            "factor_names": list(factor_names),
            "runs": [
                {
                    "run_id": r["run_id"],
                    "block_id": r.get("block_id", 1),
                    "factor_values": r["factor_values"],
                }
                for r in runs
            ],
        }
        with open(os.path.join(session_dir, "design_matrix.json"), "w") as f:
            json.dump(matrix, f)
    for r in runs:
        resp = r["responses"]
        if resp is None:
            continue
        path = os.path.join(session_dir, f"run_{r['run_id']}.json")
        if resp == "__corrupt__":
            with open(path, "w") as f:
                f.write("{not valid json")
        else:
            with open(path, "w") as f:
                json.dump(resp, f)


def _run_key(factor_names, fv):
    return ";".join(f"{n}={fv.get(n, '')}" for n in factor_names)


def _per_run_2factor():
    """Four matched runs over factors A,B (both 2-level) for regression tests."""
    combos = [("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")]
    out = []
    for i, (a, b) in enumerate(combos):
        key = f"A={a};B={b}"
        base = 10.0 + i
        cand = 12.0 + 1.5 * i
        out.append(PerRunDelta(
            run_key=key, baseline_run_id=i + 1, candidate_run_id=i + 1,
            baseline_value=base, candidate_value=cand, delta=cand - base,
        ))
    return out


# ===========================================================================
# compare.py — happy path plus unmatched-run notes
# ===========================================================================

def test_compare_full_path_with_unmatched_and_empty_response(tmp_path):
    """Covers matched pairing, unmatched-run notes, full regression, and an
    empty response (no data) -> ResponseComparison with n_matched == 0."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y", "empty"])
    factor_names = ["A", "B"]
    combos = [("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")]

    base_runs = []
    for i, (a, b) in enumerate(combos):
        base_runs.append({
            "run_id": i + 1,
            "factor_values": {"A": a, "B": b},
            "responses": {"y": 10.0 + i + (2.0 if a == "1" else 0.0)},
        })
    # A run that exists only in the baseline session.
    base_runs.append({
        "run_id": 99, "factor_values": {"A": "9", "B": "0"},
        "responses": {"y": 5.0},
    })

    cand_runs = []
    for i, (a, b) in enumerate(combos):
        cand_runs.append({
            "run_id": i + 1,
            "factor_values": {"A": a, "B": b},
            "responses": {"y": 13.0 + 1.5 * i + (4.0 if a == "1" else 0.0)},
        })
    # A run that exists only in the candidate session.
    cand_runs.append({
        "run_id": 88, "factor_values": {"A": "8", "B": "0"},
        "responses": {"y": 6.0},
    })

    base_dir = str(tmp_path / "baseline")
    cand_dir = str(tmp_path / "candidate")
    _write_session(base_dir, factor_names, base_runs)
    _write_session(cand_dir, factor_names, cand_runs)

    report = compare_sessions(cfg, base_dir, cand_dir)

    assert report.n_matched_runs == 4
    # both "only in baseline" and "only in candidate" notes present
    assert any("only in baseline" in n for n in report.notes)
    assert any("only in candidate" in n for n in report.notes)

    by_name = {r.response_name: r for r in report.responses}
    assert by_name["y"].n_matched == 4
    assert by_name["y"].decomposition is not None
    assert by_name["y"].decomposition.df_error >= 1
    assert by_name["y"].paired_t_stat is not None
    # empty response: matched keys exist but no values -> n_matched 0
    assert by_name["empty"].n_matched == 0

    # Export both HTML and CSV (covers notes_html, empty-response block, csv skip)
    html_path = str(tmp_path / "cmp.html")
    export_compare_html(report, html_path)
    content = open(html_path, encoding="utf-8").read()
    assert "Comparison Summary" in content
    assert "only in baseline" in content  # notes_html branch

    csv_dir = str(tmp_path / "csv")
    created = export_compare_csv(report, csv_dir)
    assert any("compare_summary.csv" in p for p in created)


def test_compare_many_only_baseline_runs_truncates_note(tmp_path):
    """More than five unmatched baseline runs triggers the '...' suffix."""
    cfg = _make_config({"A": ["0", "1"]}, ["y"])
    factor_names = ["A"]
    base_runs = [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"y": 1.0}},
        {"run_id": 2, "factor_values": {"A": "1"}, "responses": {"y": 2.0}},
    ]
    # seven extra baseline-only runs
    for k in range(7):
        base_runs.append({
            "run_id": 100 + k, "factor_values": {"A": f"x{k}"},
            "responses": {"y": float(k)},
        })
    cand_runs = [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"y": 1.5}},
        {"run_id": 2, "factor_values": {"A": "1"}, "responses": {"y": 2.5}},
    ]
    base_dir = str(tmp_path / "b")
    cand_dir = str(tmp_path / "c")
    _write_session(base_dir, factor_names, base_runs)
    _write_session(cand_dir, factor_names, cand_runs)
    report = compare_sessions(cfg, base_dir, cand_dir)
    assert any("..." in n and "only in baseline" in n for n in report.notes)


def test_compare_no_matching_runs_raises(tmp_path):
    cfg = _make_config({"A": ["0", "1"]}, ["y"])
    base_dir = str(tmp_path / "b")
    cand_dir = str(tmp_path / "c")
    _write_session(base_dir, ["A"], [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"y": 1.0}},
    ])
    _write_session(cand_dir, ["A"], [
        {"run_id": 1, "factor_values": {"A": "9"}, "responses": {"y": 1.0}},
    ])
    with pytest.raises(ValueError, match="No matching runs"):
        compare_sessions(cfg, base_dir, cand_dir)


def test_compare_single_matched_run_paired_test_none(tmp_path):
    """One matched run -> paired test returns None (n < 2) and decomposition
    is skipped with a note (each factor has one level)."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    factor_names = ["A", "B"]
    base_dir = str(tmp_path / "b")
    cand_dir = str(tmp_path / "c")
    shared = {"run_id": 1, "factor_values": {"A": "0", "B": "0"}}
    _write_session(base_dir, factor_names, [
        {**shared, "responses": {"y": 10.0}},
        {"run_id": 2, "factor_values": {"A": "1", "B": "1"}, "responses": {"y": 20.0}},
    ])
    _write_session(cand_dir, factor_names, [
        {**shared, "responses": {"y": 11.0}},
        {"run_id": 3, "factor_values": {"A": "1", "B": "0"}, "responses": {"y": 22.0}},
    ])
    report = compare_sessions(cfg, base_dir, cand_dir)
    rc = report.responses[0]
    assert rc.n_matched == 1
    assert rc.paired_t_stat is None
    assert rc.decomposition is not None
    assert rc.decomposition.df_error == 0  # skipped-> notes


def test_compare_constant_factor_effect_and_decomp_notes(tmp_path):
    """A factor held constant across matched runs: effect delta skips it
    (single level) and the decomposition returns a note (not 2-level)."""
    cfg = _make_config({"A": ["0", "1"], "B": ["7"]}, ["y"])
    factor_names = ["A", "B"]
    base_dir = str(tmp_path / "b")
    cand_dir = str(tmp_path / "c")
    runs_b = [
        {"run_id": 1, "factor_values": {"A": "0", "B": "7"}, "responses": {"y": 10.0}},
        {"run_id": 2, "factor_values": {"A": "1", "B": "7"}, "responses": {"y": 20.0}},
    ]
    runs_c = [
        {"run_id": 1, "factor_values": {"A": "0", "B": "7"}, "responses": {"y": 12.0}},
        {"run_id": 2, "factor_values": {"A": "1", "B": "7"}, "responses": {"y": 25.0}},
    ]
    _write_session(base_dir, factor_names, runs_b)
    _write_session(cand_dir, factor_names, runs_c)
    report = compare_sessions(cfg, base_dir, cand_dir)
    rc = report.responses[0]
    # effect delta computed for A only (B constant -> skipped)
    assert [e.factor_name for e in rc.effect_deltas] == ["A"]
    assert rc.decomposition is not None
    assert rc.decomposition.df_error < 1
    assert rc.decomposition.notes  # note-only decomposition

    # HTML export exercises the decomposition-notes (elif dc.notes) branch
    html_path = str(tmp_path / "c.html")
    export_compare_html(report, html_path)
    content = open(html_path, encoding="utf-8").read()
    assert "Decomposition skipped" in content


# ===========================================================================
# compare.py — _load_session_runs / _load_results / _coerce
# ===========================================================================

def test_compare_html_optional_none_branch(tmp_path, monkeypatch):
    """scipy absent with varying deltas -> p-values are None, exercising the
    fmt_optional '&mdash;' (None) branch during HTML export."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    factor_names = ["A", "B"]
    combos = [("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")]
    base_runs = [
        {"run_id": i + 1, "factor_values": {"A": a, "B": b},
         "responses": {"y": 10.0 + i}}
        for i, (a, b) in enumerate(combos)
    ]
    # Non-constant deltas so sd != 0: reach the scipy call (which fails).
    cand_runs = [
        {"run_id": i + 1, "factor_values": {"A": a, "B": b},
         "responses": {"y": 12.0 + 2.0 * i}}
        for i, (a, b) in enumerate(combos)
    ]
    base_dir = str(tmp_path / "b")
    cand_dir = str(tmp_path / "c")
    _write_session(base_dir, factor_names, base_runs)
    _write_session(cand_dir, factor_names, cand_runs)

    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.stats", None)
    report = compare_sessions(cfg, base_dir, cand_dir)
    rc = report.responses[0]
    assert rc.paired_t_stat is not None         # t computed
    assert rc.paired_p_value is None            # scipy missing -> p None

    out = str(tmp_path / "cmp.html")
    export_compare_html(report, out)
    content = open(out, encoding="utf-8").read()
    assert "&mdash;" in content   # None p-value rendered


def test_load_session_runs_missing_dir_raises():
    cfg = _make_config({"A": ["0", "1"]}, ["y"])
    with pytest.raises(FileNotFoundError, match="Session directory not found"):
        _load_session_runs(cfg, "/definitely/not/a/real/dir")


def test_load_session_runs_fallback_generates_design(tmp_path):
    """No design_matrix.json -> fall back to generate_design(cfg)."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    session_dir = str(tmp_path / "no_matrix")
    os.makedirs(session_dir, exist_ok=True)
    runs = _load_session_runs(cfg, session_dir)
    # full factorial of 2x2 = 4 runs regenerated from config
    assert len(runs) == 4


def test_load_results_skips_missing_and_corrupt(tmp_path):
    cfg = _make_config({"A": ["0", "1"]}, ["y"])
    session_dir = str(tmp_path / "s")
    runs_spec = [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"y": 1.0}},
        {"run_id": 2, "factor_values": {"A": "1"}, "responses": "__corrupt__"},
        {"run_id": 3, "factor_values": {"A": "0"}, "responses": None},
    ]
    _write_session(session_dir, ["A"], runs_spec)
    runs = _load_session_runs(cfg, session_dir)
    data = _load_results(runs, session_dir)
    assert 1 in data          # good file loaded
    assert 2 not in data      # corrupt JSON skipped
    assert 3 not in data      # missing file skipped


def test_coerce_variants():
    assert _coerce(None) is None
    assert _coerce("   ") is None      # blank string
    assert _coerce("not-a-number") is None
    assert _coerce("3.5") == 3.5
    assert _coerce(4) == 4.0


# ===========================================================================
# compare.py — small helpers in isolation
# ===========================================================================

def test_paired_test_too_few():
    assert _paired_test([1.0]) == (None, None, None)


def test_paired_test_scipy_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.stats", None)
    t, p, d = _paired_test([1.0, 2.0, 3.0, 2.5])
    assert t is not None and d is not None
    assert p is None  # scipy import failed -> p is None


def test_sort_key_numeric_and_nonnumeric():
    assert _sort_key("2") == (0, 2.0)
    assert _sort_key("abc") == (1, "abc")


def test_compute_effect_deltas_empty():
    assert _compute_effect_deltas([], ["A"]) == []


def test_decompose_delta_empty_returns_none():
    assert _decompose_delta([], ["A"]) is None


def test_decompose_delta_numpy_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    assert _decompose_delta(_per_run_2factor(), ["A", "B"]) is None


def test_decompose_delta_lstsq_singular(monkeypatch):
    def _raise(*a, **k):
        raise np.linalg.LinAlgError("singular")
    monkeypatch.setattr(np.linalg, "lstsq", _raise)
    dc = _decompose_delta(_per_run_2factor(), ["A", "B"])
    assert dc is not None
    assert any("singular" in n for n in dc.notes)


def test_decompose_delta_pinv_failure_gives_no_pvalues(monkeypatch):
    real_pinv = np.linalg.pinv

    def _raise(*a, **k):
        raise np.linalg.LinAlgError("no pinv")
    monkeypatch.setattr(np.linalg, "pinv", _raise)
    dc = _decompose_delta(_per_run_2factor(), ["A", "B"])
    monkeypatch.setattr(np.linalg, "pinv", real_pinv)
    assert dc is not None
    # cov is None -> all standard errors None -> p-values None
    assert dc.intercept_shift_p is None
    assert all(p is None for _, _, p in dc.slope_shifts)


def test_decompose_delta_scipy_missing_pvalues_none(monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.stats", None)
    dc = _decompose_delta(_per_run_2factor(), ["A", "B"])
    assert dc is not None
    assert dc.df_error >= 1
    assert dc.intercept_shift_p is None


def test_render_delta_dotplot_no_matplotlib(monkeypatch):
    rc = ResponseComparison(
        response_name="y", n_baseline=2, n_candidate=2, n_matched=2,
        baseline_mean=1.0, candidate_mean=2.0, mean_delta=1.0,
        per_run=_per_run_2factor(),
    )
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", None)
    assert _render_delta_dotplot(rc) == ""


def test_render_delta_dotplot_empty_per_run():
    rc = ResponseComparison(
        response_name="y", n_baseline=0, n_candidate=0, n_matched=0,
        baseline_mean=float("nan"), candidate_mean=float("nan"),
        mean_delta=float("nan"), per_run=[],
    )
    assert _render_delta_dotplot(rc) == ""


def test_anchor_id_local_special_chars():
    assert _anchor_id_local("My  Response--Name..") == "my-response-name"
    assert _anchor_id_local("!!!") == "section"


# ===========================================================================
# trend.py — happy path plus notes
# ===========================================================================

def _trend_sessions_on_disk(tmp_path, factor_names, per_session_runs):
    dirs = []
    for i, runs in enumerate(per_session_runs):
        d = str(tmp_path / f"sess{i}")
        _write_session(d, factor_names, runs)
        dirs.append(d)
    return dirs


def test_trend_full_path_with_skipped_and_missing(tmp_path):
    """Three sessions, 2x2 design; one session has an extra unmatched run
    (note) and one matched key lacks a value in a session (skipped)."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    factor_names = ["A", "B"]
    combos = [("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")]

    def mk(offset, drop_key=None, extra=False):
        runs = []
        for i, (a, b) in enumerate(combos):
            resp = None if (a, b) == drop_key else {"y": 10.0 + i + offset}
            runs.append({
                "run_id": i + 1, "factor_values": {"A": a, "B": b},
                "responses": resp,
            })
        if extra:
            runs.append({
                "run_id": 50, "factor_values": {"A": "9", "B": "9"},
                "responses": {"y": 1.0},
            })
        return runs

    s0 = mk(0.0, extra=True)              # has an unmatched extra run -> note
    s1 = mk(1.0, drop_key=("1", "1"))     # one matched key missing a value
    s2 = mk(2.0)
    dirs = _trend_sessions_on_disk(tmp_path, factor_names, [s0, s1, s2])

    report = trend_sessions(cfg, dirs)
    assert any("were skipped" in n for n in report.notes)
    tr = report.responses[0]
    assert tr.n_matched_runs == 3   # (1,1) dropped
    assert len(tr.per_session_means) == 3
    assert tr.slope_drift  # two-level factors fitted

    # HTML + CSV export of a real report
    html_path = str(tmp_path / "t.html")
    export_trend_html(report, html_path)
    assert os.path.exists(html_path)
    csv_dir = str(tmp_path / "tcsv")
    created = export_trend_csv(report, csv_dir)
    assert any("trend_summary.csv" in p for p in created)


def test_trend_requires_two_sessions(tmp_path):
    cfg = _make_config({"A": ["0", "1"]}, ["y"])
    d = str(tmp_path / "one")
    _write_session(d, ["A"], [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"y": 1.0}},
    ])
    with pytest.raises(ValueError, match="at least two session"):
        trend_sessions(cfg, [d])


def test_trend_no_shared_keys_raises(tmp_path):
    cfg = _make_config({"A": ["0", "1"]}, ["y"])
    d0 = str(tmp_path / "a")
    d1 = str(tmp_path / "b")
    _write_session(d0, ["A"], [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"y": 1.0}},
    ])
    _write_session(d1, ["A"], [
        {"run_id": 1, "factor_values": {"A": "9"}, "responses": {"y": 1.0}},
    ])
    with pytest.raises(ValueError, match="shared across every session"):
        trend_sessions(cfg, [d0, d1])


def test_trend_no_matched_data(tmp_path):
    """Shared keys exist but the response is absent everywhere -> n_matched 0."""
    cfg = _make_config({"A": ["0", "1"]}, ["y"])
    factor_names = ["A"]
    runs = [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"other": 1.0}},
        {"run_id": 2, "factor_values": {"A": "1"}, "responses": {"other": 2.0}},
    ]
    d0 = str(tmp_path / "a")
    d1 = str(tmp_path / "b")
    _write_session(d0, factor_names, runs)
    _write_session(d1, factor_names, runs)
    report = trend_sessions(cfg, [d0, d1])
    tr = report.responses[0]
    assert tr.n_matched_runs == 0
    assert any("No matched runs" in n for n in tr.notes)


def test_trend_all_factors_non_two_level(tmp_path):
    """A single 3-level factor -> no two-level factors -> slope fit skipped."""
    cfg = _make_config({"A": ["0", "1", "2"]}, ["y"])
    factor_names = ["A"]
    runs = [
        {"run_id": 1, "factor_values": {"A": "0"}, "responses": {"y": 1.0}},
        {"run_id": 2, "factor_values": {"A": "1"}, "responses": {"y": 2.0}},
        {"run_id": 3, "factor_values": {"A": "2"}, "responses": {"y": 3.0}},
    ]
    d0 = str(tmp_path / "a")
    d1 = str(tmp_path / "b")
    _write_session(d0, factor_names, runs)
    _write_session(d1, factor_names, [dict(r, responses={"y": r["responses"]["y"] + 1}) for r in runs])
    report = trend_sessions(cfg, [d0, d1])
    tr = report.responses[0]
    assert any("slope-drift fit skipped" in n for n in tr.notes)
    assert tr.slope_drift == []


def test_trend_mixed_two_level_and_multilevel(tmp_path):
    """One 2-level and one 3-level factor: 2-level fitted, other noted."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1", "2"]}, ["y"])
    factor_names = ["A", "B"]
    combos = [(a, b) for a in ("0", "1") for b in ("0", "1", "2")]
    runs = [
        {"run_id": i + 1, "factor_values": {"A": a, "B": b},
         "responses": {"y": 10.0 + i}}
        for i, (a, b) in enumerate(combos)
    ]
    d0 = str(tmp_path / "a")
    d1 = str(tmp_path / "b")
    _write_session(d0, factor_names, runs)
    _write_session(d1, factor_names, [dict(r, responses={"y": r["responses"]["y"] + 2}) for r in runs])
    report = trend_sessions(cfg, [d0, d1])
    tr = report.responses[0]
    assert any("non-2-level factor" in n for n in tr.notes)
    assert [e.factor_name for e in tr.slope_drift] == ["A"]


def test_trend_insufficient_dof(tmp_path):
    """Two sessions, three matched 2-level keys -> df_error < 1, fit skipped."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    factor_names = ["A", "B"]
    combos = [("0", "0"), ("0", "1"), ("1", "0")]  # only 3 keys
    runs = [
        {"run_id": i + 1, "factor_values": {"A": a, "B": b},
         "responses": {"y": 10.0 + i}}
        for i, (a, b) in enumerate(combos)
    ]
    d0 = str(tmp_path / "a")
    d1 = str(tmp_path / "b")
    _write_session(d0, factor_names, runs)
    _write_session(d1, factor_names, [dict(r, responses={"y": r["responses"]["y"] + 1}) for r in runs])
    report = trend_sessions(cfg, [d0, d1])
    tr = report.responses[0]
    assert any("degrees of freedom" in n for n in tr.notes)


def test_trend_numpy_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    assert _trend_for_response("y", ["A"], [], [], []) is None


def test_trend_lstsq_singular(monkeypatch, tmp_path):
    """Force a singular-matrix path in the trend regression."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    factor_names = ["A", "B"]
    combos = [("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")]
    runs = [
        {"run_id": i + 1, "factor_values": {"A": a, "B": b},
         "responses": {"y": 10.0 + i}}
        for i, (a, b) in enumerate(combos)
    ]
    dirs = _trend_sessions_on_disk(
        tmp_path, factor_names,
        [runs, [dict(r, responses={"y": r["responses"]["y"] + 1}) for r in runs]],
    )

    def _raise(*a, **k):
        raise np.linalg.LinAlgError("singular")
    monkeypatch.setattr(np.linalg, "lstsq", _raise)
    report = trend_sessions(cfg, dirs)
    tr = report.responses[0]
    assert any("singular matrix" in n for n in tr.notes)


def _trend_2x2_dirs(tmp_path):
    factor_names = ["A", "B"]
    combos = [("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")]
    runs = [
        {"run_id": i + 1, "factor_values": {"A": a, "B": b},
         "responses": {"y": 10.0 + i}}
        for i, (a, b) in enumerate(combos)
    ]
    return _trend_sessions_on_disk(
        tmp_path, factor_names,
        [runs, [dict(r, responses={"y": r["responses"]["y"] + 1}) for r in runs]],
    )


def test_trend_pinv_failure_gives_none_se(monkeypatch, tmp_path):
    """pinv failure -> None standard errors -> no p-values (early return)."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    dirs = _trend_2x2_dirs(tmp_path)

    real_pinv = np.linalg.pinv

    def _raise(*a, **k):
        raise np.linalg.LinAlgError("no pinv")
    monkeypatch.setattr(np.linalg, "pinv", _raise)
    report = trend_sessions(cfg, dirs)
    monkeypatch.setattr(np.linalg, "pinv", real_pinv)
    tr = report.responses[0]
    assert tr.intercept_drift_p is None
    assert all(e.p_value is None for e in tr.slope_drift)


def test_trend_scipy_missing_pvalues_none(monkeypatch, tmp_path):
    """Valid standard errors but scipy absent -> _pvalue hits its except."""
    cfg = _make_config({"A": ["0", "1"], "B": ["0", "1"]}, ["y"])
    dirs = _trend_2x2_dirs(tmp_path)
    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.stats", None)
    report = trend_sessions(cfg, dirs)
    tr = report.responses[0]
    assert tr.intercept_drift_p is None
    assert all(e.p_value is None for e in tr.slope_drift)


# ===========================================================================
# trend.py — HTML/CSV export edge branches
# ===========================================================================

def test_export_trend_html_all_branches(tmp_path):
    """Report-level notes, an empty response, and a note-carrying response
    with a special-character name (anchor path)."""
    empty_resp = TrendResponse(
        response_name="empty", n_sessions=2, n_matched_runs=0,
        per_session_means=[float("nan"), float("nan")],
        intercept_drift_per_session=float("nan"), intercept_drift_p=None,
        notes=["No matched runs had a value for 'empty'."],
    )
    full_resp = TrendResponse(
        response_name="Wall Clock -- Time",
        n_sessions=2, n_matched_runs=2,
        per_session_means=[1.0, 2.0],
        intercept_drift_per_session=1.0, intercept_drift_p=0.01,
        slope_drift=[SessionTrendEntry(factor_name="A",
                                       slope_drift_per_session=0.5, p_value=0.2)],
        notes=["a trailing note"],
    )
    report = TrendReport(
        session_dirs=[str(tmp_path / "s0"), str(tmp_path / "s1")],
        factor_names=["A"],
        n_runs_per_session=[2, 2],
        n_matched_runs=2,
        responses=[empty_resp, full_resp],
        notes=["a report-level note"],
    )
    out = str(tmp_path / "trend.html")
    export_trend_html(report, out)
    content = open(out, encoding="utf-8").read()
    assert "a report-level note" in content        # notes_html
    assert "No matched runs" in content            # empty-response block
    assert "a trailing note" in content            # note_html on full response
    assert 'id="trend-wall-clock-time"' in content  # anchor of special name


def test_render_means_lineplot_no_matplotlib(monkeypatch):
    tr = TrendResponse(
        response_name="y", n_sessions=2, n_matched_runs=2,
        per_session_means=[1.0, 2.0],
        intercept_drift_per_session=1.0, intercept_drift_p=None,
    )
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", None)
    assert _render_means_lineplot(tr) == ""


def test_render_means_lineplot_empty_means():
    tr = TrendResponse(
        response_name="y", n_sessions=0, n_matched_runs=0,
        per_session_means=[],
        intercept_drift_per_session=float("nan"), intercept_drift_p=None,
    )
    assert _render_means_lineplot(tr) == ""


# ===========================================================================
# calibrate.py
# ===========================================================================

def _mk_runs(specs):
    return [ExperimentRun(run_id=rid, block_id=1, factor_values=fv)
            for rid, fv in specs]


def test_calibrate_no_params_raises():
    runs = _mk_runs([(1, {"x": "1"})])
    observed = {1: {"y": 1.0}}
    with pytest.raises(ValueError, match="at least one parameter"):
        calibrate(runs, observed, lambda f, **k: {"y": 1.0}, [])


def test_calibrate_no_observed_runs_raises():
    runs = _mk_runs([(1, {"x": "1"})])
    params = [CalibrationParam("k", 0.5, 0.0, 1.0)]
    with pytest.raises(ValueError, match="No runs have observed values"):
        calibrate(runs, {}, lambda f, **k: {"y": 1.0}, params)


def test_calibrate_non_dict_simulator_raises():
    runs = _mk_runs([(1, {"x": "1"})])
    observed = {1: {"y": 1.0}}
    params = [CalibrationParam("k", 0.5, 0.0, 1.0)]
    with pytest.raises(TypeError, match="expected dict"):
        calibrate(runs, observed, lambda f, **k: 5.0, params)


def test_calibrate_no_common_responses_raises():
    runs = _mk_runs([(1, {"x": "1"})])
    observed = {1: {"bar": 1.0}}
    params = [CalibrationParam("k", 0.5, 0.0, 1.0)]
    with pytest.raises(ValueError, match="no responses in common"):
        calibrate(runs, observed, lambda f, **k: {"foo": 1.0}, params)


def test_calibrate_happy_path_converges():
    """Simulator y = k; observed y = 3 -> optimiser drives k toward 3."""
    runs = _mk_runs([(1, {"x": "1"}), (2, {"x": "2"}), (3, {"x": "3"})])
    observed = {i: {"y": 3.0} for i in (1, 2, 3)}
    params = [CalibrationParam("k", 0.0, 0.0, 10.0)]

    def sim(factors, *, k=0.0):
        return {"y": float(k)}

    result = calibrate(runs, observed, sim, params)
    assert result.rmse_after <= result.rmse_before
    assert abs(result.fitted_params["k"] - 3.0) < 0.1
    assert "y" in result.per_response_rmse


def test_calibrate_objective_exception_returns_penalty():
    """Simulator raises for perturbed params: objective catches -> penalty."""
    runs = _mk_runs([(1, {"x": "1"}), (2, {"x": "2"})])
    observed = {1: {"y": 10.0}, 2: {"y": 10.0}}
    params = [CalibrationParam("k", 0.5, 0.0, 1.0)]

    def sim(factors, *, k=0.5):
        if abs(k - 0.5) > 1e-9:
            raise RuntimeError("only defined at k=0.5")
        return {"y": 10.0}

    result = calibrate(runs, observed, sim, params)
    # It never improves, but it must not crash.
    assert result.fitted_params["k"] == pytest.approx(0.5)


def test_calibrate_scipy_minimize_failure(monkeypatch):
    """If scipy.optimize.minimize raises, calibrate falls back to initials."""
    runs = _mk_runs([(1, {"x": "1"}), (2, {"x": "2"})])
    observed = {1: {"y": 10.0}, 2: {"y": 10.0}}
    params = [CalibrationParam("k", 0.5, 0.0, 1.0)]

    def _raise(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr("scipy.optimize.minimize", _raise)

    def sim(factors, *, k=0.5):
        return {"y": float(k)}

    result = calibrate(runs, observed, sim, params)
    assert result.converged is False
    assert result.n_iterations == 0
    assert result.fitted_params["k"] == pytest.approx(0.5)


def test_weighted_sse_skips_missing_response():
    runs = _mk_runs([(1, {"x": "1"}), (2, {"x": "2"})])
    observed = {1: {"y": 1.0, "z": 2.0}, 2: {"y": 1.0}}  # run 2 lacks z

    def sim(factors, *, k=0.0):
        return {"y": 1.5, "z": 2.5}

    val = _weighted_sse(sim, runs, observed, ["y", "z"], {"k": 0.0}, {})
    # run1: (0.5)^2 + (0.5)^2 ; run2: only y (z skipped) -> (0.5)^2
    assert val == pytest.approx(0.25 * 3)


def test_residual_metrics_simulator_exception_skips_run():
    runs = _mk_runs([(1, {"bad": "0"}), (2, {"bad": "1"})])
    observed = {1: {"y": 1.0}, 2: {"y": 1.0}}

    def sim(factors, *, k=0.0):
        if factors.get("bad") == "1":
            raise RuntimeError("cannot simulate")
        return {"y": 1.5}

    rmse, per_resp = _residual_metrics(sim, runs, observed, ["y"], {"k": 0.0}, {})
    # only run 1 contributes -> single residual of 0.5
    assert rmse == pytest.approx(0.5)
    assert per_resp["y"] == pytest.approx(0.5)


def test_residual_metrics_skips_missing_response():
    """A response name absent from a run's observed/result is skipped."""
    runs = _mk_runs([(1, {"x": "1"}), (2, {"x": "2"})])
    observed = {1: {"y": 1.0, "z": 2.0}, 2: {"y": 1.0}}  # run 2 lacks z

    def sim(factors, *, k=0.0):
        return {"y": 1.5, "z": 2.5}

    rmse, per_resp = _residual_metrics(sim, runs, observed, ["y", "z"], {"k": 0.0}, {})
    # z only contributes for run 1
    assert per_resp["z"] == pytest.approx(0.5)


def test_load_observed_skips_corrupt_and_nonnumeric(tmp_path):
    runs = _mk_runs([(1, {"x": "1"}), (2, {"x": "2"}), (3, {"x": "3"})])
    session = str(tmp_path / "obs")
    os.makedirs(session, exist_ok=True)
    # run 1: corrupt JSON
    with open(os.path.join(session, "run_1.json"), "w") as f:
        f.write("{not json")
    # run 2: mix of non-numeric and numeric
    with open(os.path.join(session, "run_2.json"), "w") as f:
        json.dump({"y": "abc", "z": 1.5}, f)
    # run 3: absent entirely
    out = load_observed(session, runs)
    assert 1 not in out          # corrupt skipped
    assert out[2] == {"z": 1.5}  # non-numeric y dropped, z kept
    assert 3 not in out


def test_load_observed_missing_dir_raises():
    runs = _mk_runs([(1, {"x": "1"})])
    with pytest.raises(FileNotFoundError, match="session directory not found"):
        load_observed("/no/such/observed/dir", runs)
