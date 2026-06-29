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
from collections.abc import Iterable

from .models import (
    ComparisonReport, ResponseComparison, PerRunDelta, EffectDelta,
    DeltaDecomposition, ExperimentRun, DOEConfig,
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


def _validate_factor_alignment(cfg: DOEConfig, names_in_matrix: Iterable[str], session_dir: str) -> None:
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


def _load_results(runs: list[ExperimentRun], session_dir: str) -> dict[int, dict[str, object]]:
    """Load every available run_*.json from a session, ignoring missing files."""
    out: dict[int, dict[str, object]] = {}
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


def _coerce(value: object) -> float | None:
    """Best-effort conversion to float; treats blanks/None as missing."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _compare_response(
    resp_name: str,
    factor_names: list[str],
    matched_keys: list[str],
    base_by_key: dict[str, ExperimentRun],
    cand_by_key: dict[str, ExperimentRun],
    base_data: dict[int, dict[str, object]],
    cand_data: dict[int, dict[str, object]],
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
    decomposition = _decompose_delta(
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
        decomposition=decomposition,
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


def _sort_key(value: str) -> tuple[int, float | str]:
    try:
        return (0, float(value))
    except (TypeError, ValueError):
        return (1, value)


def _decompose_delta(
    per_run: list[PerRunDelta],
    factor_names: list[str],
) -> DeltaDecomposition | None:
    """Fit y = β0 + βs·s + Σ βi·xi + Σ γi·s·xi on the pooled matched data.

    s = -1 for baseline, +1 for candidate. xi is each factor's coded value
    in [-1, +1]. βs (intercept-shift coefficient) maps to a uniform 2·βs
    shift in mean response between sessions. γi (per-factor session
    interaction) maps to a 2·γi change in main-effect size.

    Returns None when the design isn't a 2-level layout (every factor
    must show exactly two distinct levels among matched runs) — the
    helper would otherwise have to encode multi-level factors with extra
    decisions out of scope here.
    """
    try:
        import numpy as np
    except ImportError:
        return None

    if not per_run:
        return None

    factor_values_by_key: dict[str, dict[str, str]] = {}
    for r in per_run:
        kv: dict[str, str] = {}
        for token in r.run_key.split(";"):
            if "=" in token:
                name, val = token.split("=", 1)
                kv[name] = val
        factor_values_by_key[r.run_key] = kv

    levels_per_factor: dict[str, list[str]] = {}
    for fname in factor_names:
        levels = sorted(
            {fvs[fname] for fvs in factor_values_by_key.values() if fname in fvs},
            key=_sort_key,
        )
        if len(levels) != 2:
            return DeltaDecomposition(
                n_observations=2 * len(per_run),
                df_error=0,
                intercept_shift=0.0,
                intercept_shift_p=None,
                notes=[
                    f"Decomposition skipped: factor '{fname}' has "
                    f"{len(levels)} distinct level(s) in matched runs (need 2)."
                ],
            )
        levels_per_factor[fname] = levels

    # Build the pooled design matrix X and response y.
    n_runs = len(per_run)
    n_obs = 2 * n_runs
    n_factors = len(factor_names)
    n_params = 1 + 1 + n_factors + n_factors  # intercept, s, mains, s*mains
    X = np.zeros((n_obs, n_params))
    y = np.zeros(n_obs)
    for i, r in enumerate(per_run):
        x_coded = []
        for fname in factor_names:
            low, _high = levels_per_factor[fname]
            v = factor_values_by_key[r.run_key].get(fname)
            x_coded.append(-1.0 if v == low else 1.0)
        for s_val, response_val in ((-1.0, r.baseline_value), (1.0, r.candidate_value)):
            row_idx = 2 * i + (0 if s_val < 0 else 1)
            X[row_idx, 0] = 1.0
            X[row_idx, 1] = s_val
            for j, xi in enumerate(x_coded):
                X[row_idx, 2 + j] = xi
                X[row_idx, 2 + n_factors + j] = s_val * xi
            y[row_idx] = response_val

    df_error = n_obs - n_params
    if df_error < 1:
        return DeltaDecomposition(
            n_observations=n_obs, df_error=df_error,
            intercept_shift=0.0, intercept_shift_p=None,
            notes=["Decomposition skipped: not enough runs for the regression."],
        )

    try:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    except np.linalg.LinAlgError:
        return DeltaDecomposition(
            n_observations=n_obs, df_error=df_error,
            intercept_shift=0.0, intercept_shift_p=None,
            notes=["Decomposition skipped: regression failed (singular matrix)."],
        )
    residuals = y - X @ beta
    sse = float(np.sum(residuals ** 2))
    mse = sse / df_error if df_error > 0 else 0.0

    try:
        cov = mse * np.linalg.pinv(X.T @ X)
    except np.linalg.LinAlgError:
        cov = None
    if cov is None:
        se: list[float | None] = [None] * n_params
    else:
        se = [float(std) if std > 0 else None for std in np.sqrt(np.diag(cov))]

    def _pvalue(b: float, s: float | None) -> float | None:
        if s is None or s == 0 or df_error <= 0:
            return None
        try:
            from scipy import stats as _stats
            return float(2.0 * (1.0 - _stats.t.cdf(abs(b / s), df=df_error)))
        except Exception:
            return None

    # With s ∈ {-1, +1} and x_i ∈ {-1, +1}:
    #   mean_candidate - mean_baseline = 2·β_s     (uniform offset)
    #   effect_candidate - effect_baseline = 4·γ_i (change in main-effect size)
    # The factor of 4 on γ_i comes from "main effect = mean(x=+1) - mean(x=-1)
    # = 2·β_i + 2·γ_i·s", so the candidate-minus-baseline difference is 4·γ_i.
    intercept_shift = 2.0 * float(beta[1])
    intercept_p = _pvalue(float(beta[1]), se[1])

    slope_shifts: list[tuple[str, float, float | None]] = []
    for j, fname in enumerate(factor_names):
        idx = 2 + n_factors + j
        gamma = float(beta[idx])
        slope_shifts.append((fname, 4.0 * gamma, _pvalue(gamma, se[idx])))

    return DeltaDecomposition(
        n_observations=n_obs,
        df_error=df_error,
        intercept_shift=intercept_shift,
        intercept_shift_p=intercept_p,
        slope_shifts=slope_shifts,
    )


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

        if rc.decomposition and rc.decomposition.df_error >= 1:
            decomp_path = os.path.join(output_dir, f"compare_decomposition_{safe}.csv")
            dc = rc.decomposition
            with open(decomp_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["term", "shift", "p_value"])
                writer.writerow([
                    "intercept_shift", dc.intercept_shift,
                    dc.intercept_shift_p if dc.intercept_shift_p is not None else "",
                ])
                for fname, shift, p in dc.slope_shifts:
                    writer.writerow([f"slope_shift_{fname}", shift,
                                     p if p is not None else ""])
            created.append(decomp_path)

    return created


def export_compare_html(report: ComparisonReport, output_path: str) -> str:
    """Render a self-contained HTML page for the comparison report.

    Reuses the same CSS as ``doe report`` so the look-and-feel is
    consistent. Each response gets its own collapsible block with a
    summary table, a paired-test row, and the per-factor effect-delta
    table; flipped signs are highlighted in red.
    """
    import datetime
    import html as _html
    from .report import _CSS  # reuse the report stylesheet

    def fmt_optional(v: object, fmt: str = ".4f") -> str:
        if v is None or (isinstance(v, float) and (v != v)):  # NaN check
            return "&mdash;"
        if isinstance(v, float) and not _isfinite(v):
            return "&infin;"
        return format(v, fmt) if isinstance(v, float) else _html.escape(str(v))

    sections: list[str] = []

    # Header / summary
    notes_html = ""
    if report.notes:
        items = "".join(f"<li>{_html.escape(n)}</li>" for n in report.notes)
        notes_html = f'<ul class="muted">{items}</ul>\n'

    sections.append(
        f'<details open id="compare-summary">\n'
        f'  <summary><h2>Comparison Summary</h2></summary>\n'
        f'  <div class="section-body">\n'
        f'  <table class="info-table">\n'
        f'    <tr><th>Baseline</th><td class="mono">{_html.escape(report.baseline_dir)}</td></tr>\n'
        f'    <tr><th>Candidate</th><td class="mono">{_html.escape(report.candidate_dir)}</td></tr>\n'
        f'    <tr><th>Factors</th><td>{_html.escape(", ".join(report.factor_names))}</td></tr>\n'
        f'    <tr><th>Runs (B / C / matched)</th>'
        f'<td class="mono">{report.n_baseline_runs} / {report.n_candidate_runs} / {report.n_matched_runs}</td></tr>\n'
        f'  </table>\n'
        f'  {notes_html}'
        f'  </div>\n'
        f'</details>\n'
    )

    for rc in report.responses:
        anchor = _anchor_id_local(rc.response_name)
        title = f"Response: {_html.escape(rc.response_name)}"
        if rc.n_matched == 0:
            body = "  <p class=\"muted\">" + "; ".join(_html.escape(n) for n in rc.notes) + "</p>\n"
            sections.append(
                f'<details open id="compare-{anchor}">\n'
                f'  <summary><h2>{title}</h2></summary>\n'
                f'  <div class="section-body">\n{body}  </div>\n</details>\n'
            )
            continue

        sig_class = ""
        if rc.paired_p_value is not None and rc.paired_p_value < 0.05:
            sig_class = ' style="color:#0a7;font-weight:bold;"'
        paired_row = ""
        if rc.paired_t_stat is not None:
            paired_row = (
                f'      <tr{sig_class}><td>Paired t-test</td>'
                f'<td class="mono">t = {fmt_optional(rc.paired_t_stat, ".3f")}, '
                f'p = {fmt_optional(rc.paired_p_value, ".4f")}, '
                f"Cohen's d = {fmt_optional(rc.cohens_d, '+.3f')}</td></tr>\n"
            )

        summary_table = (
            '  <table class="data-table">\n'
            '    <thead><tr><th>Metric</th><th>Value</th></tr></thead>\n'
            '    <tbody>\n'
            f'      <tr><td>Matched runs</td><td class="mono">{rc.n_matched}</td></tr>\n'
            f'      <tr><td>Baseline mean</td><td class="mono">{rc.baseline_mean:.4f}</td></tr>\n'
            f'      <tr><td>Candidate mean</td><td class="mono">{rc.candidate_mean:.4f}</td></tr>\n'
            f'      <tr><td>Δ mean</td><td class="mono">{rc.mean_delta:+.4f}</td></tr>\n'
            f'{paired_row}'
            '    </tbody>\n'
            '  </table>\n'
        )

        # Per-factor effect deltas
        effect_rows = ""
        for e in rc.effect_deltas:
            flag_class = ' style="color:#c00;font-weight:bold;"' if e.flipped_sign else ''
            flag_marker = '✱' if e.flipped_sign else ''
            effect_rows += (
                f'      <tr{flag_class}>'
                f'<td>{_html.escape(e.factor_name)}</td>'
                f'<td class="mono">{e.baseline_effect:+.4f}</td>'
                f'<td class="mono">{e.candidate_effect:+.4f}</td>'
                f'<td class="mono">{e.delta:+.4f}</td>'
                f'<td class="mono">{flag_marker}</td>'
                f'</tr>\n'
            )
        effects_table = ""
        if effect_rows:
            effects_table = (
                '  <h3>Main-Effect Changes</h3>\n'
                '  <table class="data-table">\n'
                '    <thead><tr><th>Factor</th><th>Baseline</th>'
                '<th>Candidate</th><th>Δ</th><th>Sign flip?</th></tr></thead>\n'
                '    <tbody>\n'
                f'{effect_rows}'
                '    </tbody>\n'
                '  </table>\n'
            )

        # Δ decomposition (regression-based)
        decomp_html = ""
        if rc.decomposition:
            dc = rc.decomposition
            if dc.df_error >= 1:
                p_intercept = fmt_optional(dc.intercept_shift_p, ".4f")
                shift_class = ' style="color:#0a7;font-weight:bold;"' if (
                    dc.intercept_shift_p is not None and dc.intercept_shift_p < 0.05
                ) else ""
                rows = (
                    f'      <tr{shift_class}><td>Intercept shift</td>'
                    f'<td class="mono">{dc.intercept_shift:+.4f}</td>'
                    f'<td class="mono">{p_intercept}</td></tr>\n'
                )
                for fname, shift, p in dc.slope_shifts:
                    p_disp = fmt_optional(p, ".4f")
                    sig_class = ' style="color:#0a7;font-weight:bold;"' if (
                        p is not None and p < 0.05
                    ) else ""
                    rows += (
                        f'      <tr{sig_class}><td>{_html.escape(fname)}</td>'
                        f'<td class="mono">{shift:+.4f}</td>'
                        f'<td class="mono">{p_disp}</td></tr>\n'
                    )
                decomp_html = (
                    '  <h3>Δ Decomposition</h3>\n'
                    '  <p class="muted">Regression of pooled matched runs: '
                    'y ~ session + Σ x<sub>i</sub> + Σ session·x<sub>i</sub>. '
                    'Intercept shift = uniform offset; slope shifts = per-factor '
                    'effect-size change between sessions.</p>\n'
                    '  <table class="data-table">\n'
                    '    <thead><tr><th>Term</th><th>Shift</th><th>p</th></tr></thead>\n'
                    '    <tbody>\n'
                    f'{rows}'
                    '    </tbody>\n'
                    '  </table>\n'
                )
            elif dc.notes:
                decomp_html = (
                    '  <h3>Δ Decomposition</h3>\n'
                    '  <p class="muted">' + "; ".join(_html.escape(n) for n in dc.notes) + '</p>\n'
                )

        # Per-run delta dotplot (inline base64 PNG, optional)
        plot_html = _render_delta_dotplot(rc) if rc.per_run else ""

        # Per-run paired deltas (collapsed by default)
        run_rows = ""
        for r in rc.per_run:
            run_rows += (
                f'      <tr><td class="mono">{_html.escape(r.run_key)}</td>'
                f'<td class="mono">{r.baseline_value:.4f}</td>'
                f'<td class="mono">{r.candidate_value:.4f}</td>'
                f'<td class="mono">{r.delta:+.4f}</td></tr>\n'
            )
        runs_table = (
            '  <details><summary>Per-run paired deltas</summary>\n'
            '  <table class="data-table">\n'
            '    <thead><tr><th>Run</th><th>Baseline</th>'
            '<th>Candidate</th><th>Δ</th></tr></thead>\n'
            '    <tbody>\n'
            f'{run_rows}'
            '    </tbody>\n'
            '  </table>\n  </details>\n'
        )

        sections.append(
            f'<details open id="compare-{anchor}">\n'
            f'  <summary><h2>{title}</h2></summary>\n'
            f'  <div class="section-body">\n'
            f'{summary_table}'
            f'{plot_html}'
            f'{effects_table}'
            f'{decomp_html}'
            f'{runs_table}'
            f'  </div>\n'
            f'</details>\n'
        )

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <title>DOE Comparison</title>\n'
        f'  <style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        '<header>\n'
        '  <h1>Session Comparison</h1>\n'
        f'  <p class="timestamp">Generated: {_html.escape(timestamp)}</p>\n'
        '</header>\n'
        + "\n".join(sections)
        + '\n<footer><p>Generated by DOE Helper Tool — doe compare</p></footer>\n'
        '</body>\n</html>\n'
    )

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return output_path


def _render_delta_dotplot(rc: ResponseComparison) -> str:
    """Inline a small dotplot of per-run deltas as a base64 PNG.

    Bails out silently (returns "") if matplotlib isn't available so HTML
    rendering still works on a slim install.
    """
    try:
        import io
        import base64
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    if not rc.per_run:
        return ""
    deltas = [r.delta for r in rc.per_run]
    n = len(deltas)
    fig, ax = plt.subplots(figsize=(7.5, 2.4 + 0.04 * n))
    y_positions = list(range(n))
    colors = ["#0a7" if d >= 0 else "#c33" for d in deltas]
    ax.scatter(deltas, y_positions, c=colors, s=42, edgecolor="white", linewidths=0.6)
    ax.axvline(0, color="#888", linewidth=0.8, zorder=0)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [f"#{r.baseline_run_id}↔{r.candidate_run_id}" for r in rc.per_run],
        fontsize=7,
    )
    ax.set_xlabel("Δ (candidate − baseline)")
    ax.set_title(f"Per-run paired deltas — {rc.response_name}")
    ax.invert_yaxis()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return (
        f'  <div class="plot">\n'
        f'    <img alt="Per-run delta dotplot" '
        f'src="data:image/png;base64,{encoded}">\n'
        f'  </div>\n'
    )


def _isfinite(x: float) -> bool:
    return x == x and x not in (float("inf"), float("-inf"))


def _anchor_id_local(name: str) -> str:
    out = []
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "."):
            out.append("-")
    cleaned = "".join(out).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "section"
