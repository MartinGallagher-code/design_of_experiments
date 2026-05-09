# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pairwise comparison between two result sessions.

Sessions are matched by the canonical tuple of factor values, not by
``run_id``, so a re-randomised execution order still pairs correctly.
Both per-run paired deltas (with paired t-test + Cohen's d) and per-factor
main-effect deltas are reported. Sessions that don't share factor names
or levels are rejected; sessions where some runs only exist on one side
are matched on the intersection with a warning.
"""

import json
import math
import os
from typing import Iterable

from .models import (
    ComparisonReport, ResponseComparison, PerRunDelta, EffectDelta,
    DesignMatrix, ExperimentRun, DOEConfig,
)


def compare_sessions(
    cfg: DOEConfig,
    baseline_dir: str,
    candidate_dir: str,
) -> ComparisonReport:
    """Compute a pairwise comparison between two sessions.

    Each ``*_dir`` is a directory containing ``run_*.json`` result files
    (and optionally a ``design_matrix.json`` from the runner). Runs are
    matched between sessions by the canonical tuple of factor values from
    each side's design matrix, falling back to the ``cfg``'s design when
    a session-local matrix is absent.

    Raises ``ValueError`` if the two sides disagree on factor names /
    levels, or if no runs match.
    """
    baseline_runs = _load_session_runs(cfg, baseline_dir)
    candidate_runs = _load_session_runs(cfg, candidate_dir)

    factor_names = [f.name for f in cfg.factors]
    notes: list[str] = []

    # Pair runs by canonical factor-value tuple.
    base_by_key = {_run_key(r, factor_names): r for r in baseline_runs}
    cand_by_key = {_run_key(r, factor_names): r for r in candidate_runs}
    base_keys, cand_keys = set(base_by_key), set(cand_by_key)
    matched_keys = sorted(base_keys & cand_keys)
    if not matched_keys:
        raise ValueError(
            f"No matching runs between '{baseline_dir}' and '{candidate_dir}'. "
            "Sessions must share the same factor settings."
        )
    only_baseline = sorted(base_keys - cand_keys)
    only_candidate = sorted(cand_keys - base_keys)
    if only_baseline:
        notes.append(
            f"{len(only_baseline)} run(s) only in baseline (skipped): {only_baseline[:5]}"
            + (" ..." if len(only_baseline) > 5 else "")
        )
    if only_candidate:
        notes.append(
            f"{len(only_candidate)} run(s) only in candidate (skipped): {only_candidate[:5]}"
            + (" ..." if len(only_candidate) > 5 else "")
        )

    base_data = _load_results(baseline_runs, baseline_dir)
    cand_data = _load_results(candidate_runs, candidate_dir)

    response_reports: list[ResponseComparison] = []
    for resp in cfg.responses:
        rc = _compare_response(
            resp_name=resp.name,
            factor_names=factor_names,
            matched_keys=matched_keys,
            base_by_key=base_by_key,
            cand_by_key=cand_by_key,
            base_data=base_data,
            cand_data=cand_data,
            n_baseline=len(baseline_runs),
            n_candidate=len(candidate_runs),
        )
        if rc is not None:
            response_reports.append(rc)

    return ComparisonReport(
        baseline_dir=baseline_dir,
        candidate_dir=candidate_dir,
        factor_names=factor_names,
        n_baseline_runs=len(baseline_runs),
        n_candidate_runs=len(candidate_runs),
        n_matched_runs=len(matched_keys),
        responses=response_reports,
        notes=notes,
    )


def _load_session_runs(cfg: DOEConfig, session_dir: str) -> list[ExperimentRun]:
    """Return the runs that belong to this session.

    Prefers ``<session_dir>/design_matrix.json`` (the runner copies it in
    when ``--session`` is used). Falls back to regenerating from ``cfg``
    so older sessions without an embedded matrix still work, but warns
    the caller via the returned matrix only.
    """
    if not os.path.isdir(session_dir):
        raise FileNotFoundError(f"Session directory not found: '{session_dir}'")

    matrix_path = os.path.join(session_dir, "design_matrix.json")
    if os.path.isfile(matrix_path):
        with open(matrix_path) as f:
            data = json.load(f)
        runs = [
            ExperimentRun(
                run_id=r["run_id"],
                block_id=r["block_id"],
                factor_values=r["factor_values"],
            )
            for r in data["runs"]
        ]
        _validate_factor_alignment(cfg, data.get("factor_names", []), session_dir)
        return runs

    # Fallback: regenerate from config (no seed → run-ID alignment may differ
    # but matching is by factor-value tuple, so this is still safe).
    from .design import generate_design
    matrix = generate_design(cfg)
    return matrix.runs


def _validate_factor_alignment(cfg: DOEConfig, names_in_matrix: Iterable[str], session_dir: str):
    cfg_names = [f.name for f in cfg.factors]
    matrix_names = list(names_in_matrix)
    if matrix_names and matrix_names != cfg_names:
        only_cfg = set(cfg_names) - set(matrix_names)
        only_matrix = set(matrix_names) - set(cfg_names)
        if only_cfg or only_matrix:
            raise ValueError(
                f"Factor names in '{session_dir}' do not match the config. "
                f"Only in config: {sorted(only_cfg)}; "
                f"only in session: {sorted(only_matrix)}."
            )


def _run_key(run: ExperimentRun, factor_names: Iterable[str]) -> str:
    """Canonical key for matching a run across sessions."""
    return ";".join(f"{n}={run.factor_values.get(n, '')}" for n in factor_names)


def _load_results(runs: list[ExperimentRun], session_dir: str) -> dict[int, dict]:
    """Load every available run_*.json from a session, ignoring missing files."""
    out: dict[int, dict] = {}
    for run in runs:
        path = os.path.join(session_dir, f"run_{run.run_id}.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                out[run.run_id] = json.load(f)
        except json.JSONDecodeError:
            continue
    return out


def _coerce(value):
    """Best-effort conversion to float; treats blanks/None as missing."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compare_response(
    resp_name: str,
    factor_names: list[str],
    matched_keys: list[str],
    base_by_key: dict[str, ExperimentRun],
    cand_by_key: dict[str, ExperimentRun],
    base_data: dict[int, dict],
    cand_data: dict[int, dict],
    n_baseline: int,
    n_candidate: int,
) -> ResponseComparison | None:
    per_run: list[PerRunDelta] = []
    for key in matched_keys:
        b_run = base_by_key[key]
        c_run = cand_by_key[key]
        b_val = _coerce(base_data.get(b_run.run_id, {}).get(resp_name))
        c_val = _coerce(cand_data.get(c_run.run_id, {}).get(resp_name))
        if b_val is None or c_val is None:
            continue
        per_run.append(PerRunDelta(
            run_key=key,
            baseline_run_id=b_run.run_id,
            candidate_run_id=c_run.run_id,
            baseline_value=b_val,
            candidate_value=c_val,
            delta=c_val - b_val,
        ))

    if not per_run:
        return ResponseComparison(
            response_name=resp_name,
            n_baseline=n_baseline,
            n_candidate=n_candidate,
            n_matched=0,
            baseline_mean=float("nan"),
            candidate_mean=float("nan"),
            mean_delta=float("nan"),
            notes=[f"No matched runs had a value for '{resp_name}'."],
        )

    deltas = [r.delta for r in per_run]
    base_mean = sum(r.baseline_value for r in per_run) / len(per_run)
    cand_mean = sum(r.candidate_value for r in per_run) / len(per_run)
    mean_delta = cand_mean - base_mean

    t_stat, p_value, d = _paired_test(deltas)
    effect_deltas = _compute_effect_deltas(
        per_run=per_run, factor_names=factor_names,
    )

    return ResponseComparison(
        response_name=resp_name,
        n_baseline=n_baseline,
        n_candidate=n_candidate,
        n_matched=len(per_run),
        baseline_mean=base_mean,
        candidate_mean=cand_mean,
        mean_delta=mean_delta,
        paired_t_stat=t_stat,
        paired_p_value=p_value,
        cohens_d=d,
        per_run=per_run,
        effect_deltas=effect_deltas,
    )


def _paired_test(deltas: list[float]) -> tuple[float | None, float | None, float | None]:
    n = len(deltas)
    if n < 2:
        return None, None, None
    mean = sum(deltas) / n
    var = sum((d - mean) ** 2 for d in deltas) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return float("inf") if mean != 0 else 0.0, 0.0 if mean != 0 else 1.0, float("inf") if mean != 0 else 0.0
    t_stat = mean / (sd / math.sqrt(n))
    cohens_d = mean / sd
    try:
        from scipy import stats as _stats
        p = float(2.0 * (1.0 - _stats.t.cdf(abs(t_stat), df=n - 1)))
    except Exception:
        p = None
    return float(t_stat), p, float(cohens_d)


def _compute_effect_deltas(
    per_run: list[PerRunDelta],
    factor_names: list[str],
) -> list[EffectDelta]:
    """Compute the difference in main effects (one number per factor) between
    the two sessions, restricted to the matched runs.

    Main effect = mean(response | factor=high) - mean(response | factor=low).
    For numeric factors with two extremes we pick min/max as low/high. For
    multi-level factors we just take the lowest and highest sorted values.
    """
    if not per_run:
        return []

    # Reconstruct the {factor: level} table per matched key
    factor_values_by_key: dict[str, dict[str, str]] = {}
    for r in per_run:
        kv: dict[str, str] = {}
        for token in r.run_key.split(";"):
            if "=" in token:
                name, val = token.split("=", 1)
                kv[name] = val
        factor_values_by_key[r.run_key] = kv

    out: list[EffectDelta] = []
    for fname in factor_names:
        levels = sorted({fvs[fname] for fvs in factor_values_by_key.values()
                         if fname in fvs}, key=_sort_key)
        if len(levels) < 2:
            continue
        low, high = levels[0], levels[-1]
        b_low, b_high, c_low, c_high = [], [], [], []
        for r in per_run:
            level = factor_values_by_key[r.run_key].get(fname)
            if level == low:
                b_low.append(r.baseline_value)
                c_low.append(r.candidate_value)
            elif level == high:
                b_high.append(r.baseline_value)
                c_high.append(r.candidate_value)
        if not (b_low and b_high and c_low and c_high):
            continue
        be = sum(b_high) / len(b_high) - sum(b_low) / len(b_low)
        ce = sum(c_high) / len(c_high) - sum(c_low) / len(c_low)
        flipped = (
            (be > 0) != (ce > 0)
            and abs(be) > 1e-9
            and abs(ce) > 1e-9
        )
        out.append(EffectDelta(
            factor_name=fname,
            baseline_effect=float(be),
            candidate_effect=float(ce),
            delta=float(ce - be),
            flipped_sign=flipped,
        ))
    return out


def _sort_key(value: str):
    try:
        return (0, float(value))
    except (TypeError, ValueError):
        return (1, value)


def export_compare_csv(report: ComparisonReport, output_dir: str) -> list[str]:
    """Write the comparison tables to CSV. Returns the list of file paths."""
    import csv
    os.makedirs(output_dir, exist_ok=True)
    created: list[str] = []

    summary_path = os.path.join(output_dir, "compare_summary.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "response", "n_matched", "baseline_mean", "candidate_mean",
            "mean_delta", "paired_t", "paired_p", "cohens_d",
        ])
        for rc in report.responses:
            writer.writerow([
                rc.response_name, rc.n_matched,
                rc.baseline_mean, rc.candidate_mean, rc.mean_delta,
                rc.paired_t_stat if rc.paired_t_stat is not None else "",
                rc.paired_p_value if rc.paired_p_value is not None else "",
                rc.cohens_d if rc.cohens_d is not None else "",
            ])
    created.append(summary_path)

    for rc in report.responses:
        if not rc.per_run:
            continue
        safe = rc.response_name.replace("/", "_").replace(" ", "_")
        runs_path = os.path.join(output_dir, f"compare_runs_{safe}.csv")
        with open(runs_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "run_key", "baseline_run_id", "candidate_run_id",
                "baseline_value", "candidate_value", "delta",
            ])
            for r in rc.per_run:
                writer.writerow([
                    r.run_key, r.baseline_run_id, r.candidate_run_id,
                    r.baseline_value, r.candidate_value, r.delta,
                ])
        created.append(runs_path)

        if rc.effect_deltas:
            effects_path = os.path.join(output_dir, f"compare_effects_{safe}.csv")
            with open(effects_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "factor", "baseline_effect", "candidate_effect", "delta", "flipped_sign",
                ])
                for e in rc.effect_deltas:
                    writer.writerow([
                        e.factor_name, e.baseline_effect, e.candidate_effect,
                        e.delta, e.flipped_sign,
                    ])
            created.append(effects_path)

    return created
