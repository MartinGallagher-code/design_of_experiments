"""Generate self-contained interactive HTML report from DOE results."""

import base64
import html
import io
import json
import os
from datetime import datetime

from .models import DesignMatrix, DOEConfig
from .analysis import analyze
from .design import generate_design


def generate_report(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    output_path: str = "report.html",
) -> str:
    """Run analysis and generate a self-contained HTML report.

    Parameters
    ----------
    matrix : DesignMatrix
        The experiment design matrix.
    cfg : DOEConfig
        The experiment configuration.
    results_dir : str | None
        Directory containing run result JSON files.  Falls back to
        ``cfg.out_directory`` or ``"results"`` when *None*.
    output_path : str
        Path for the generated HTML file.

    Returns
    -------
    str
        The *output_path* that was written.
    """
    report = analyze(matrix, cfg, results_dir=results_dir, no_plots=False)

    # --- Encode plot images as base64 data URIs ---
    pareto_images: dict[str, str] = {}
    for resp_name, path in report.pareto_chart_paths.items():
        pareto_images[resp_name] = _encode_image(path)

    effects_images: dict[str, str] = {}
    for resp_name, path in report.effects_plot_paths.items():
        effects_images[resp_name] = _encode_image(path)

    # --- Build HTML sections ---
    plan_name = html.escape(cfg.metadata.get("name", "Unnamed Experiment"))
    plan_desc = html.escape(cfg.metadata.get("description", ""))
    timestamp = html.escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    header_html = _build_header(plan_name, plan_desc, timestamp)
    design_summary_html = _build_design_summary(matrix, cfg)
    results_html = _build_results(report, pareto_images, effects_images)
    design_matrix_html = _build_design_matrix(matrix)
    footer_html = _build_footer()

    page = _HTML_TEMPLATE.format(
        title=plan_name,
        css=_CSS,
        header=header_html,
        design_summary=design_summary_html,
        results=results_html,
        design_matrix=design_matrix_html,
        footer=footer_html,
    )

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(page)

    print(f"HTML report written to: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _encode_image(path: str) -> str:
    """Read a PNG file and return a base64 data URI string."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{data}"


def _build_header(name: str, description: str, timestamp: str) -> str:
    desc_block = f'<p class="description">{description}</p>' if description else ""
    return (
        f'<header>\n'
        f'  <h1>{name}</h1>\n'
        f'  {desc_block}\n'
        f'  <p class="timestamp">Generated: {timestamp}</p>\n'
        f'</header>\n'
    )


def _build_design_summary(matrix: DesignMatrix, cfg: DOEConfig) -> str:
    op = html.escape(matrix.operation)
    n_factors = matrix.metadata.get("n_factors", len(matrix.factor_names))
    n_runs = matrix.metadata.get("n_total_runs", len(matrix.runs))
    n_blocks = matrix.metadata.get("n_blocks", 1)

    factor_rows = ""
    for f in cfg.factors:
        fname = html.escape(f.name)
        ftype = html.escape(f.type)
        flevels = html.escape(", ".join(f.levels))
        funit = html.escape(f.unit) if f.unit else "&mdash;"
        factor_rows += (
            f"      <tr>"
            f"<td>{fname}</td>"
            f"<td>{ftype}</td>"
            f"<td class=\"mono\">{flevels}</td>"
            f"<td>{funit}</td>"
            f"</tr>\n"
        )

    return (
        '<details open>\n'
        '  <summary><h2>Design Summary</h2></summary>\n'
        '  <div class="section-body">\n'
        '  <table class="info-table">\n'
        f'    <tr><th>Operation</th><td>{op}</td></tr>\n'
        f'    <tr><th>Factors</th><td>{n_factors}</td></tr>\n'
        f'    <tr><th>Total Runs</th><td class="mono">{n_runs}</td></tr>\n'
        f'    <tr><th>Blocks</th><td class="mono">{n_blocks}</td></tr>\n'
        '  </table>\n'
        '  <h3>Factor Details</h3>\n'
        '  <table class="data-table">\n'
        '    <thead><tr><th>Name</th><th>Type</th><th>Levels</th><th>Unit</th></tr></thead>\n'
        '    <tbody>\n'
        f'{factor_rows}'
        '    </tbody>\n'
        '  </table>\n'
        '  </div>\n'
        '</details>\n'
    )


def _build_results(report, pareto_images, effects_images) -> str:
    if not report.results_by_response:
        return '<p class="muted">No analysis results available.</p>\n'

    sections = []
    for resp_name, analysis in report.results_by_response.items():
        safe_name = html.escape(resp_name)

        # --- Main effects table ---
        effect_rows = ""
        for e in analysis.effects:
            ci_str = f"{e.ci_low:.4f} &ndash; {e.ci_high:.4f}" if (e.ci_low or e.ci_high) else "&mdash;"
            effect_rows += (
                f"      <tr>"
                f"<td>{html.escape(e.factor_name)}</td>"
                f"<td class=\"mono\">{e.main_effect:.4f}</td>"
                f"<td class=\"mono\">{e.std_error:.4f}</td>"
                f"<td class=\"mono\">{ci_str}</td>"
                f"<td class=\"mono\">{e.pct_contribution:.1f}%</td>"
                f"</tr>\n"
            )

        main_effects_html = (
            '  <h3>Main Effects</h3>\n'
            '  <table class="data-table">\n'
            '    <thead><tr><th>Factor</th><th>Effect</th><th>Std Error</th>'
            '<th>95% CI</th><th>% Contribution</th></tr></thead>\n'
            '    <tbody>\n'
            f'{effect_rows}'
            '    </tbody>\n'
            '  </table>\n'
        )

        # --- Interaction effects table ---
        interaction_html = ""
        if analysis.interactions:
            ix_rows = ""
            for ix in analysis.interactions:
                ix_rows += (
                    f"      <tr>"
                    f"<td>{html.escape(ix.factor_a)}</td>"
                    f"<td>{html.escape(ix.factor_b)}</td>"
                    f"<td class=\"mono\">{ix.interaction_effect:.4f}</td>"
                    f"<td class=\"mono\">{ix.pct_contribution:.1f}%</td>"
                    f"</tr>\n"
                )
            interaction_html = (
                '  <h3>Interaction Effects</h3>\n'
                '  <table class="data-table">\n'
                '    <thead><tr><th>Factor A</th><th>Factor B</th>'
                '<th>Interaction</th><th>% Contribution</th></tr></thead>\n'
                '    <tbody>\n'
                f'{ix_rows}'
                '    </tbody>\n'
                '  </table>\n'
            )

        # --- Summary statistics ---
        summary_html = '  <h3>Summary Statistics</h3>\n'
        for factor, levels in analysis.summary_stats.items():
            safe_factor = html.escape(factor)
            stat_rows = ""
            for level, s in sorted(levels.items()):
                stat_rows += (
                    f"      <tr>"
                    f"<td class=\"mono\">{html.escape(str(level))}</td>"
                    f"<td class=\"mono\">{s['n']}</td>"
                    f"<td class=\"mono\">{s['mean']:.4f}</td>"
                    f"<td class=\"mono\">{s['std']:.4f}</td>"
                    f"<td class=\"mono\">{s['min']:.4f}</td>"
                    f"<td class=\"mono\">{s['max']:.4f}</td>"
                    f"</tr>\n"
                )
            summary_html += (
                f'  <h4>{safe_factor}</h4>\n'
                '  <table class="data-table">\n'
                '    <thead><tr><th>Level</th><th>N</th><th>Mean</th>'
                '<th>Std</th><th>Min</th><th>Max</th></tr></thead>\n'
                '    <tbody>\n'
                f'{stat_rows}'
                '    </tbody>\n'
                '  </table>\n'
            )

        # --- Plots ---
        plots_html = ""
        if resp_name in pareto_images:
            plots_html += (
                f'  <div class="plot"><img src="{pareto_images[resp_name]}" '
                f'alt="Pareto chart for {safe_name}"></div>\n'
            )
        if resp_name in effects_images:
            plots_html += (
                f'  <div class="plot"><img src="{effects_images[resp_name]}" '
                f'alt="Main effects plot for {safe_name}"></div>\n'
            )

        sections.append(
            f'<details open>\n'
            f'  <summary><h2>Results: {safe_name}</h2></summary>\n'
            f'  <div class="section-body">\n'
            f'{main_effects_html}'
            f'{interaction_html}'
            f'{summary_html}'
            f'{plots_html}'
            f'  </div>\n'
            f'</details>\n'
        )

    return "\n".join(sections)


def _build_design_matrix(matrix: DesignMatrix) -> str:
    header_cells = "<th>Run</th><th>Block</th>" + "".join(
        f"<th>{html.escape(f)}</th>" for f in matrix.factor_names
    )

    rows = ""
    for run in sorted(matrix.runs, key=lambda r: r.run_id):
        cells = (
            f"<td class=\"mono\">{run.run_id}</td>"
            f"<td class=\"mono\">{run.block_id}</td>"
        )
        for fname in matrix.factor_names:
            cells += f"<td class=\"mono\">{html.escape(str(run.factor_values[fname]))}</td>"
        rows += f"      <tr>{cells}</tr>\n"

    return (
        '<details>\n'
        '  <summary><h2>Design Matrix</h2></summary>\n'
        '  <div class="section-body">\n'
        '  <table class="data-table">\n'
        f'    <thead><tr>{header_cells}</tr></thead>\n'
        '    <tbody>\n'
        f'{rows}'
        '    </tbody>\n'
        '  </table>\n'
        '  </div>\n'
        '</details>\n'
    )


def _build_footer() -> str:
    return (
        '<footer>\n'
        '  <p>Generated by DOE Helper Tool</p>\n'
        '</footer>\n'
    )


# ---------------------------------------------------------------------------
# HTML / CSS templates  (plain Python strings, no Jinja)
# ---------------------------------------------------------------------------

_CSS = """\
:root {
  --accent: steelblue;
  --bg: #ffffff;
  --bg-alt: #f4f7fa;
  --text: #2c3e50;
  --border: #dce1e8;
  --mono: "SFMono-Regular", "Consolas", "Liberation Mono", "Menlo", monospace;
}
*, *::before, *::after { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--text);
  background: var(--bg);
  margin: 0;
  padding: 20px 40px;
  line-height: 1.6;
}
header {
  border-bottom: 3px solid var(--accent);
  padding-bottom: 12px;
  margin-bottom: 24px;
}
header h1 {
  margin: 0;
  color: var(--accent);
}
header .description {
  margin: 4px 0 0 0;
  color: #666;
}
header .timestamp {
  margin: 4px 0 0 0;
  font-size: 0.9em;
  color: #888;
}
details {
  margin-bottom: 20px;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
summary {
  cursor: pointer;
  background: var(--bg-alt);
  padding: 8px 16px;
  list-style: none;
}
summary::-webkit-details-marker { display: none; }
summary::before {
  content: "\\25B6";
  display: inline-block;
  margin-right: 8px;
  transition: transform 0.2s;
  font-size: 0.8em;
}
details[open] > summary::before {
  transform: rotate(90deg);
}
summary h2 {
  display: inline;
  font-size: 1.15em;
  margin: 0;
  color: var(--accent);
}
.section-body {
  padding: 12px 16px;
}
h3 { color: var(--accent); margin: 18px 0 8px 0; font-size: 1.05em; }
h4 { margin: 12px 0 4px 0; font-size: 0.95em; }
table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
.info-table th {
  text-align: left;
  padding: 6px 14px 6px 0;
  white-space: nowrap;
  color: #555;
  width: 140px;
}
.info-table td { padding: 6px 0; }
.data-table {
  font-size: 0.92em;
}
.data-table th {
  background: var(--accent);
  color: #fff;
  padding: 8px 12px;
  text-align: left;
}
.data-table td {
  padding: 6px 12px;
  border-bottom: 1px solid var(--border);
}
.data-table tbody tr:nth-child(even) { background: var(--bg-alt); }
.data-table tbody tr:hover { background: #e8eef5; }
.mono { font-family: var(--mono); }
.muted { color: #888; font-style: italic; }
.plot {
  margin: 16px 0;
  text-align: center;
}
.plot img {
  max-width: 100%;
  height: auto;
  border: 1px solid var(--border);
  border-radius: 4px;
}
footer {
  margin-top: 30px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  text-align: center;
  font-size: 0.85em;
  color: #999;
}
@media (max-width: 700px) {
  body { padding: 10px 12px; }
  .data-table { font-size: 0.82em; }
  .data-table th, .data-table td { padding: 4px 6px; }
}
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} &mdash; DOE Report</title>
  <style>
{css}
  </style>
</head>
<body>
{header}
{design_summary}
{results}
{design_matrix}
{footer}
</body>
</html>
"""
