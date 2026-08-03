# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Multi-session trend analysis.

Given N (>= 2) sessions of the same experiment in chronological order,
``trend_sessions`` regresses each response against a session index plus
the coded factor values and their session interactions. The intercept
drift coefficient measures uniform shift per session step; the per-factor
interaction coefficients measure how each factor's effect drifts over time.

This is the natural multi-session extension of ``doe compare``, but the
two commands stay separate: pairwise comparison produces paired t-tests
that don't generalise neatly to N sessions, while a regression makes
sense for any N >= 2.
"""

from __future__ import annotations

import os

from .compare import (
    _load_session_runs,
    _load_results,
    _run_key,
    _coerce,
    _sort_key,
)
from .models import (
    DOEConfig, ExperimentRun, SessionTrendEntry, TrendReport, TrendResponse,
)


def trend_sessions(cfg: DOEConfig, session_dirs: list[str]) -> TrendReport:
    """Fit y ~ session + Σ x_i + Σ session·x_i across N sessions.

    Sessions are aligned by canonical factor-value tuples (same as
    ``doe compare``). Only matched runs that exist in *every* session
    contribute to the regression. Two-level factors only — multi-level
    factors are reported via per-session means but skip the per-factor
    drift fit (matches the ``doe compare`` decomposition behaviour).

    Raises ``ValueError`` when fewer than two sessions are passed or
    no factor settings are common to every session.
    """
    if len(session_dirs) < 2:
        raise ValueError("trend_sessions requires at least two session directories.")

    factor_names = [f.name for f in cfg.factors]
    n_runs_per_session: list[int] = []

    session_runs = []
    session_data = []
    keysets: list[set[str]] = []
    for d in session_dirs:
        runs = _load_session_runs(cfg, d)
        n_runs_per_session.append(len(runs))
        data = _load_results(runs, d)
        by_key = {_run_key(r, factor_names): r for r in runs}
        session_runs.append(by_key)
        session_data.append(data)
        keysets.append(set(by_key))

    matched_keys = sorted(set.intersection(*keysets)) if keysets else []
    if not matched_keys:
        raise ValueError(
            "No factor-value tuple is shared across every session. "
            "Sessions must run the same design."
        )

    notes: list[str] = []
    skipped_per_session = [
        sorted(by_key.keys() - set(matched_keys)) for by_key in session_runs
    ]
    for i, skipped in enumerate(skipped_per_session):
        if skipped:
            notes.append(
                f"Session {i + 1} ({session_dirs[i]}): "
                f"{len(skipped)} run(s) without a counterpart in every session "
                "were skipped."
            )

    response_reports: list[TrendResponse] = []
    for resp in cfg.responses:
        tr = _trend_for_response(
            resp_name=resp.name,
            factor_names=factor_names,
            matched_keys=matched_keys,
            session_runs=session_runs,
            session_data=session_data,
        )
        if tr is not None:
            response_reports.append(tr)

    return TrendReport(
        session_dirs=list(session_dirs),
        factor_names=factor_names,
        n_runs_per_session=n_runs_per_session,
        n_matched_runs=len(matched_keys),
        responses=response_reports,
        notes=notes,
    )


def _trend_for_response(
    resp_name: str,
    factor_names: list[str],
    matched_keys: list[str],
    session_runs: list[dict[str, ExperimentRun]],
    session_data: list[dict[int, dict[str, object]]],
) -> TrendResponse | None:
    try:
        import numpy as np
    except ImportError:
        return None

    n_sessions = len(session_runs)

    # Per-session means and per-session value vectors over matched_keys.
    per_session_values: list[list[float]] = [[] for _ in range(n_sessions)]
    matched_keys_with_data: list[str] = []
    for key in matched_keys:
        per_run_values: list[float | None] = []
        for s in range(n_sessions):
            run = session_runs[s][key]
            v = _coerce(session_data[s].get(run.run_id, {}).get(resp_name))
            per_run_values.append(v)
        if any(v is None for v in per_run_values):
            continue
        matched_keys_with_data.append(key)
        for s, v in enumerate(per_run_values):
            if v is not None:
                per_session_values[s].append(float(v))

    if not matched_keys_with_data:
        return TrendResponse(
            response_name=resp_name,
            n_sessions=n_sessions,
            n_matched_runs=0,
            per_session_means=[float("nan")] * n_sessions,
            intercept_drift_per_session=float("nan"),
            intercept_drift_p=None,
            notes=[f"No matched runs had a value for '{resp_name}'."],
        )

    per_session_means = [
        sum(vals) / len(vals) for vals in per_session_values
    ]

    # Reconstruct factor settings for matched_keys_with_data.
    factor_values_by_key: dict[str, dict[str, str]] = {}
    for k in matched_keys_with_data:
        kv = {}
        for token in k.split(";"):
            if "=" in token:
                name, val = token.split("=", 1)
                kv[name] = val
        factor_values_by_key[k] = kv

    # Decide which factors can participate in the slope-drift fit:
    # every two-level factor with both levels present in matched data.
    levels_per_factor: dict[str, list[str]] = {}
    twolevel_names: list[str] = []
    for fname in factor_names:
        levels = sorted(
            {factor_values_by_key[k][fname] for k in matched_keys_with_data
             if fname in factor_values_by_key[k]},
            key=_sort_key,
        )
        levels_per_factor[fname] = levels
        if len(levels) == 2:
            twolevel_names.append(fname)

    # Build pooled regression:
    #   y ~ β0 + β_t · t + Σ β_i · x_i + Σ γ_i · t · x_i
    # where t = session_index (0..K-1) and x_i ∈ {-1, +1} for each
    # two-level factor (other factors are dropped from the slope fit
    # but still factor into the per-session means table above).
    notes: list[str] = []
    if not twolevel_names and len(factor_names) > 0:
        notes.append(
            "All factors have unequal level counts across sessions or are not 2-level; "
            "slope-drift fit skipped."
        )
        return TrendResponse(
            response_name=resp_name,
            n_sessions=n_sessions,
            n_matched_runs=len(matched_keys_with_data),
            per_session_means=per_session_means,
            intercept_drift_per_session=float("nan"),
            intercept_drift_p=None,
            notes=notes,
        )
    if len(twolevel_names) < len(factor_names):
        notes.append(
            f"{len(factor_names) - len(twolevel_names)} non-2-level factor(s) "
            "skipped from the slope-drift fit."
        )

    n_obs = n_sessions * len(matched_keys_with_data)
    n_params = 1 + 1 + len(twolevel_names) + len(twolevel_names)  # intercept, t, mains, t*mains
    df_error = n_obs - n_params
    if df_error < 1:
        return TrendResponse(
            response_name=resp_name,
            n_sessions=n_sessions,
            n_matched_runs=len(matched_keys_with_data),
            per_session_means=per_session_means,
            intercept_drift_per_session=float("nan"),
            intercept_drift_p=None,
            notes=notes + ["Not enough degrees of freedom for the trend regression."],
        )

    X = np.zeros((n_obs, n_params))
    y = np.zeros(n_obs)
    row_idx = 0
    for s, vals in enumerate(per_session_values):
        for k_idx, key in enumerate(matched_keys_with_data):
            x_coded = []
            for fname in twolevel_names:
                low, _high = levels_per_factor[fname]
                v_str = factor_values_by_key[key].get(fname)
                x_coded.append(-1.0 if v_str == low else 1.0)
            X[row_idx, 0] = 1.0
            X[row_idx, 1] = float(s)
            for j, xi in enumerate(x_coded):
                X[row_idx, 2 + j] = xi
                X[row_idx, 2 + len(twolevel_names) + j] = float(s) * xi
            y[row_idx] = vals[k_idx]
            row_idx += 1

    try:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    except np.linalg.LinAlgError:
        return TrendResponse(
            response_name=resp_name,
            n_sessions=n_sessions,
            n_matched_runs=len(matched_keys_with_data),
            per_session_means=per_session_means,
            intercept_drift_per_session=float("nan"),
            intercept_drift_p=None,
            notes=notes + ["Regression failed (singular matrix)."],
        )
    residuals = y - X @ beta
    sse = float(np.sum(residuals ** 2))
    mse = sse / df_error
    try:
        cov = mse * np.linalg.pinv(X.T @ X)
        se = [float(s) if s > 0 else None for s in np.sqrt(np.diag(cov))]
    except np.linalg.LinAlgError:
        se = [None] * n_params

    def _pvalue(b: float, s: float | None) -> float | None:
        if s is None or s == 0 or df_error <= 0:
            return None
        try:
            from scipy import stats as _stats
            return float(2.0 * (1.0 - _stats.t.cdf(abs(b / s), df=df_error)))
        except Exception:
            return None

    # Intercept drift = β_t per session step (no factor of 2 because
    # the design here is on session index, not ±1).
    intercept_drift = float(beta[1])
    intercept_p = _pvalue(intercept_drift, se[1])

    slope_drift: list[SessionTrendEntry] = []
    # γ_i scales the change in slope per session step. Effect size is
    # 2·slope, so per-session change in main effect is 2·γ_i.
    for j, fname in enumerate(twolevel_names):
        idx = 2 + len(twolevel_names) + j
        gamma = float(beta[idx])
        slope_drift.append(SessionTrendEntry(
            factor_name=fname,
            slope_drift_per_session=2.0 * gamma,
            p_value=_pvalue(gamma, se[idx]),
        ))

    return TrendResponse(
        response_name=resp_name,
        n_sessions=n_sessions,
        n_matched_runs=len(matched_keys_with_data),
        per_session_means=per_session_means,
        intercept_drift_per_session=intercept_drift,
        intercept_drift_p=intercept_p,
        slope_drift=slope_drift,
        notes=notes,
    )


def export_trend_html(report: TrendReport, output_path: str) -> str:
    """Render the trend report as a self-contained HTML page.

    Reuses the same CSS as ``doe report`` / ``doe compare`` so the look
    is consistent. One collapsible block per response, with the
    per-session means table, intercept-drift summary, and per-factor
    slope-drift table.
    """
    import datetime
    import html as _html
    from .report import _CSS

    def fmt_p(p: float | None) -> str:
        return "&mdash;" if p is None else f"{p:.4f}"

    def _anchor(name: str) -> str:
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

    sections: list[str] = []

    # Summary block
    notes_html = ""
    if report.notes:
        items = "".join(f"<li>{_html.escape(n)}</li>" for n in report.notes)
        notes_html = f'  <ul class="muted">{items}</ul>\n'
    session_rows = ""
    for i, (d, n) in enumerate(zip(report.session_dirs, report.n_runs_per_session)):
        session_rows += (
            f'      <tr><td class="mono">{i}</td>'
            f'<td class="mono">{_html.escape(d)}</td>'
            f'<td class="mono">{n}</td></tr>\n'
        )
    sections.append(
        '<details open id="trend-summary">\n'
        '  <summary><h2>Trend Summary</h2></summary>\n'
        '  <div class="section-body">\n'
        f'  <table class="info-table">\n'
        f'    <tr><th>Sessions</th><td class="mono">{len(report.session_dirs)}</td></tr>\n'
        f'    <tr><th>Factors</th><td>{_html.escape(", ".join(report.factor_names))}</td></tr>\n'
        f'    <tr><th>Matched in every session</th><td class="mono">{report.n_matched_runs}</td></tr>\n'
        '  </table>\n'
        '  <h3>Sessions (chronological)</h3>\n'
        '  <table class="data-table">\n'
        '    <thead><tr><th>Index</th><th>Path</th><th>Runs</th></tr></thead>\n'
        f'    <tbody>\n{session_rows}    </tbody>\n'
        '  </table>\n'
        f'  {notes_html}'
        '  </div>\n'
        '</details>\n'
    )

    # Per-response block
    for tr in report.responses:
        anchor = _anchor(tr.response_name)
        if tr.n_matched_runs == 0:
            note_items = "".join(f"<li>{_html.escape(n)}</li>" for n in tr.notes)
            sections.append(
                f'<details open id="trend-{anchor}">\n'
                f'  <summary><h2>Response: {_html.escape(tr.response_name)}</h2></summary>\n'
                f'  <div class="section-body">\n'
                f'  <ul class="muted">{note_items}</ul>\n'
                '  </div>\n</details>\n'
            )
            continue

        means_rows = ""
        for i, mean in enumerate(tr.per_session_means):
            means_rows += (
                f'      <tr><td class="mono">{i}</td>'
                f'<td class="mono">{mean:.4f}</td></tr>\n'
            )
        means_table = (
            '  <h3>Per-Session Means</h3>\n'
            '  <table class="data-table">\n'
            '    <thead><tr><th>Session</th><th>Mean</th></tr></thead>\n'
            f'    <tbody>\n{means_rows}    </tbody>\n'
            '  </table>\n'
        )
        means_plot = _render_means_lineplot(tr)

        intercept_html = ""
        if tr.intercept_drift_per_session == tr.intercept_drift_per_session:
            sig = (' style="color:#0a7;font-weight:bold;"'
                   if tr.intercept_drift_p is not None and tr.intercept_drift_p < 0.05
                   else "")
            intercept_html = (
                '  <table class="info-table">\n'
                f'    <tr{sig}><th>Intercept drift / session</th>'
                f'<td class="mono">{tr.intercept_drift_per_session:+.4f}</td>'
                f'<td class="mono">p = {fmt_p(tr.intercept_drift_p)}</td></tr>\n'
                '  </table>\n'
            )

        slope_html = ""
        if tr.slope_drift:
            slope_rows = ""
            for entry in tr.slope_drift:
                sig = (' style="color:#0a7;font-weight:bold;"'
                       if entry.p_value is not None and entry.p_value < 0.05
                       else "")
                slope_rows += (
                    f'      <tr{sig}><td>{_html.escape(entry.factor_name)}</td>'
                    f'<td class="mono">{entry.slope_drift_per_session:+.4f}</td>'
                    f'<td class="mono">{fmt_p(entry.p_value)}</td></tr>\n'
                )
            slope_html = (
                '  <h3>Slope Drift / Session</h3>\n'
                '  <p class="muted">Change in main-effect size per session step.</p>\n'
                '  <table class="data-table">\n'
                '    <thead><tr><th>Factor</th><th>Shift</th><th>p</th></tr></thead>\n'
                f'    <tbody>\n{slope_rows}    </tbody>\n'
                '  </table>\n'
            )

        note_html = ""
        if tr.notes:
            items = "".join(f"<li>{_html.escape(n)}</li>" for n in tr.notes)
            note_html = f'  <ul class="muted">{items}</ul>\n'

        sections.append(
            f'<details open id="trend-{anchor}">\n'
            f'  <summary><h2>Response: {_html.escape(tr.response_name)}</h2></summary>\n'
            f'  <div class="section-body">\n'
            f'{means_table}'
            f'{means_plot}'
            f'{intercept_html}'
            f'{slope_html}'
            f'{note_html}'
            '  </div>\n</details>\n'
        )

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <title>DOE Trend</title>\n'
        f'  <style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        '<header>\n'
        '  <h1>Multi-Session Trend</h1>\n'
        f'  <p class="timestamp">Generated: {_html.escape(timestamp)}</p>\n'
        '</header>\n'
        + "\n".join(sections)
        + '\n<footer><p>Generated by DOE Helper Tool — doe trend</p></footer>\n'
        '</body>\n</html>\n'
    )

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return output_path


def _render_means_lineplot(tr: TrendResponse) -> str:
    """Inline a per-session-mean line plot as base64 PNG. Returns "" if
    matplotlib isn't available."""
    try:
        import io
        import base64
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    if not tr.per_session_means:
        return ""
    xs = list(range(len(tr.per_session_means)))
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    ax.plot(xs, tr.per_session_means, marker="o", color="steelblue",
            linewidth=1.4)
    if tr.intercept_drift_per_session == tr.intercept_drift_per_session:
        # Overlay the regression line implied by intercept-drift.
        if len(tr.per_session_means) >= 2:
            base = tr.per_session_means[0]
            line = [base + i * tr.intercept_drift_per_session for i in xs]
            ax.plot(xs, line, linestyle="--", color="#c33", linewidth=1.0,
                    label=f"drift slope {tr.intercept_drift_per_session:+.3f}/session")
            ax.legend(loc="best", fontsize=8, frameon=False)
    ax.set_xlabel("Session index (chronological)")
    ax.set_ylabel(f"Mean {tr.response_name}")
    ax.set_title(f"Per-session mean — {tr.response_name}")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return (
        f'  <div class="plot">\n'
        f'    <img alt="Per-session mean trend" '
        f'src="data:image/png;base64,{encoded}">\n'
        f'  </div>\n'
    )


def export_trend_csv(report: TrendReport, output_dir: str) -> list[str]:
    import csv
    os.makedirs(output_dir, exist_ok=True)
    created: list[str] = []

    summary_path = os.path.join(output_dir, "trend_summary.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "response", "n_matched", "intercept_drift_per_session",
            "intercept_drift_p",
        ])
        for tr in report.responses:
            writer.writerow([
                tr.response_name, tr.n_matched_runs,
                tr.intercept_drift_per_session,
                tr.intercept_drift_p if tr.intercept_drift_p is not None else "",
            ])
    created.append(summary_path)

    for tr in report.responses:
        safe = tr.response_name.replace("/", "_").replace(" ", "_")
        means_path = os.path.join(output_dir, f"trend_means_{safe}.csv")
        with open(means_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["session_index", "session_dir", "mean"])
            for i, (mean, d) in enumerate(zip(tr.per_session_means, report.session_dirs)):
                writer.writerow([i, d, mean])
        created.append(means_path)

        if tr.slope_drift:
            slope_path = os.path.join(output_dir, f"trend_slopes_{safe}.csv")
            with open(slope_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["factor", "slope_drift_per_session", "p_value"])
                for entry in tr.slope_drift:
                    writer.writerow([
                        entry.factor_name, entry.slope_drift_per_session,
                        entry.p_value if entry.p_value is not None else "",
                    ])
            created.append(slope_path)

    return created
