"""Generate self-contained interactive HTML report from DOE results."""

import base64
import html
import io
import json
import os
from datetime import datetime

from .models import DesignMatrix, DOEConfig
from .analysis import analyze, _load_all_results, _compute_main_effects
from .design import generate_design
from .rsm import fit_rsm


def generate_report(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    output_path: str = "report.html",
    partial: bool = False,
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
    partial : bool
        When True, skip missing result files and analyze only completed runs.

    Returns
    -------
    str
        The *output_path* that was written.
    """
    results_dir_resolved = results_dir or cfg.out_directory or "results"
    report = analyze(matrix, cfg, results_dir=results_dir, no_plots=False, partial=partial)

    # --- Encode plot images as base64 data URIs ---
    pareto_images: dict[str, str] = {}
    for resp_name, path in report.pareto_chart_paths.items():
        pareto_images[resp_name] = _encode_image(path)

    effects_images: dict[str, str] = {}
    for resp_name, path in report.effects_plot_paths.items():
        effects_images[resp_name] = _encode_image(path)

    # --- Collect RSM surface plot images ---
    rsm_images: dict[str, list[tuple[str, str]]] = {}  # resp_name -> [(label, data_uri)]
    processed_dir = cfg.processed_directory or results_dir_resolved
    if os.path.isdir(processed_dir):
        import glob as _glob
        for resp in cfg.responses:
            safe = resp.name.replace("/", "_").replace(" ", "_")
            rsm_files = sorted(_glob.glob(os.path.join(processed_dir, f"rsm_{safe}_*.png")))
            if rsm_files:
                rsm_images[resp.name] = []
                for rsm_path in rsm_files:
                    fname = os.path.basename(rsm_path).replace(".png", "")
                    # Extract label from filename like rsm_yield_temperature_vs_pressure
                    parts = fname.split("_", 2)
                    label = parts[2].replace("_vs_", " vs ").replace("_", " ") if len(parts) >= 3 else fname
                    rsm_images[resp.name].append((label, _encode_image(rsm_path)))

    # --- Run optimization analysis ---
    optimization_data = _run_optimization(matrix, cfg, results_dir_resolved, partial=partial)

    # --- Build HTML sections ---
    plan_name = html.escape(cfg.metadata.get("name", "Unnamed Experiment"))
    plan_desc = html.escape(cfg.metadata.get("description", ""))
    timestamp = html.escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    header_html = _build_header(plan_name, plan_desc, timestamp, partial=partial)
    design_summary_html = _build_design_summary(matrix, cfg)
    normal_images: dict[str, str] = {}
    for resp_name, path in report.normal_plot_paths.items():
        if os.path.exists(path):
            normal_images[resp_name] = _encode_image(path)

    half_normal_images: dict[str, str] = {}
    for resp_name, path in report.half_normal_plot_paths.items():
        if os.path.exists(path):
            half_normal_images[resp_name] = _encode_image(path)

    diagnostics_images: dict[str, str] = {}
    for resp_name, path in report.diagnostics_plot_paths.items():
        if os.path.exists(path):
            diagnostics_images[resp_name] = _encode_image(path)

    results_html = _build_results(report, pareto_images, effects_images, rsm_images,
                                  normal_images, half_normal_images, diagnostics_images)
    optimization_html = _build_optimization(optimization_data, cfg)
    design_matrix_html = _build_design_matrix(matrix)
    footer_html = _build_footer()

    page = _HTML_TEMPLATE.format(
        title=plan_name,
        css=_CSS,
        header=header_html,
        design_summary=design_summary_html,
        results=results_html,
        optimization=optimization_html,
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


def _build_header(name: str, description: str, timestamp: str, partial: bool = False) -> str:
    desc_block = f'<p class="description">{description}</p>' if description else ""
    partial_block = (
        '  <p style="color: #b8860b; font-weight: bold; margin-top: 8px;">'
        'Note: This is a partial analysis based on incomplete experiment data.</p>\n'
    ) if partial else ""
    return (
        f'<header>\n'
        f'  <h1>{name}</h1>\n'
        f'  {desc_block}\n'
        f'  <p class="timestamp">Generated: {timestamp}</p>\n'
        f'{partial_block}'
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


def _run_optimization(matrix, cfg, results_dir, partial=False):
    """Run optimization analysis and return structured data."""
    all_data = _load_all_results(matrix.runs, results_dir, partial=partial)
    results = []

    for resp in cfg.responses:
        responses = {}
        for run in matrix.runs:
            data = all_data.get(run.run_id, {})
            if resp.name in data:
                responses[run.run_id] = float(data[resp.name])
        if not responses:
            continue

        valid_runs = [r for r in matrix.runs if r.run_id in responses]
        direction = resp.optimize or "maximize"

        # Best observed run
        if direction == "minimize":
            best_run = min(valid_runs, key=lambda r: responses[r.run_id])
        else:
            best_run = max(valid_runs, key=lambda r: responses[r.run_id])

        best_settings = {fname: best_run.factor_values[fname] for fname in matrix.factor_names}
        best_value = responses[best_run.run_id]

        # RSM models
        rsm_linear = fit_rsm(valid_runs, responses, matrix.factor_names, cfg.factors, model_type="linear")
        rsm_quad = None
        n_factors = len(matrix.factor_names)
        n_quad_terms = 1 + n_factors + n_factors * (n_factors - 1) // 2 + n_factors
        if len(valid_runs) >= n_quad_terms + 1:
            try:
                rsm_quad = fit_rsm(valid_runs, responses, matrix.factor_names, cfg.factors, model_type="quadratic")
            except Exception:
                pass

        best_model = rsm_quad if (rsm_quad and rsm_quad.adj_r_squared > rsm_linear.adj_r_squared) else rsm_linear
        model_label = "quadratic" if best_model is rsm_quad else "linear"

        # Factor importance
        effects = _compute_main_effects(valid_runs, responses, matrix.factor_names)
        total_abs = sum(abs(e.main_effect) for e in effects) or 1.0
        importance = [(e.factor_name, e.main_effect, abs(e.main_effect) / total_abs * 100) for e in effects]

        # R² quality
        r2 = best_model.r_squared
        if r2 > 0.9:
            quality = "Excellent fit — surface predictions are reliable."
        elif r2 > 0.7:
            quality = "Good fit — general trends are captured, some noise remains."
        elif r2 > 0.5:
            quality = "Moderate fit — use predictions directionally, not precisely."
        else:
            quality = "Weak fit — consider adding center points or using a different design."

        results.append({
            "response_name": resp.name,
            "direction": direction,
            "unit": resp.unit or "",
            "best_run_id": best_run.run_id,
            "best_settings": best_settings,
            "best_value": best_value,
            "linear_r2": rsm_linear.r_squared,
            "linear_adj_r2": rsm_linear.adj_r_squared,
            "linear_coeffs": rsm_linear.coefficients,
            "quad_r2": rsm_quad.r_squared if rsm_quad else None,
            "quad_adj_r2": rsm_quad.adj_r_squared if rsm_quad else None,
            "quad_coeffs": rsm_quad.coefficients if rsm_quad else None,
            "best_model_label": model_label,
            "predicted_optimum": best_model.predicted_optimum,
            "predicted_value": best_model.predicted_value,
            "quality": quality,
            "importance": importance,
        })

    return results


def _build_optimization(opt_data, cfg) -> str:
    if not opt_data:
        return ""

    sections = []
    for opt in opt_data:
        safe_name = html.escape(opt["response_name"])
        direction = html.escape(opt["direction"])
        unit = f' ({html.escape(opt["unit"])})' if opt["unit"] else ""

        # Best observed run
        settings_rows = "".join(
            f'      <tr><td>{html.escape(k)}</td><td class="mono">{html.escape(str(v))}</td></tr>\n'
            for k, v in opt["best_settings"].items()
        )
        best_html = (
            f'  <h3>Best Observed Run (#{opt["best_run_id"]})</h3>\n'
            f'  <table class="info-table">\n'
            f'{settings_rows}'
            f'      <tr><td><strong>Value</strong></td><td class="mono"><strong>{opt["best_value"]:.4f}</strong></td></tr>\n'
            f'  </table>\n'
        )

        # RSM model coefficients (best model)
        coeffs = opt["quad_coeffs"] if opt["best_model_label"] == "quadratic" else opt["linear_coeffs"]
        r2 = opt["quad_r2"] if opt["best_model_label"] == "quadratic" else opt["linear_r2"]
        adj_r2 = opt["quad_adj_r2"] if opt["best_model_label"] == "quadratic" else opt["linear_adj_r2"]

        coeff_rows = ""
        for name, coef in coeffs.items():
            sign = "+" if coef >= 0 else ""
            coeff_rows += f'      <tr><td>{html.escape(name)}</td><td class="mono">{sign}{coef:.4f}</td></tr>\n'

        model_html = (
            f'  <h3>RSM Model ({html.escape(opt["best_model_label"])}, R&sup2; = {r2:.4f}, Adj R&sup2; = {adj_r2:.4f})</h3>\n'
            f'  <table class="data-table">\n'
            f'    <thead><tr><th>Term</th><th>Coefficient</th></tr></thead>\n'
            f'    <tbody>\n'
            f'{coeff_rows}'
            f'    </tbody>\n'
            f'  </table>\n'
        )

        # Predicted optimum
        pred_rows = "".join(
            f'      <tr><td>{html.escape(k)}</td><td class="mono">{html.escape(str(v))}</td></tr>\n'
            for k, v in opt["predicted_optimum"].items()
        )
        pred_html = (
            f'  <h3>Predicted Optimum</h3>\n'
            f'  <table class="info-table">\n'
            f'{pred_rows}'
            f'      <tr><td><strong>Predicted Value</strong></td><td class="mono"><strong>{opt["predicted_value"]:.4f}</strong></td></tr>\n'
            f'  </table>\n'
            f'  <p class="muted">{html.escape(opt["quality"])}</p>\n'
        )

        # Factor importance
        imp_rows = ""
        for i, (fname, effect, pct) in enumerate(opt["importance"], 1):
            imp_rows += (
                f'      <tr><td class="mono">{i}</td><td>{html.escape(fname)}</td>'
                f'<td class="mono">{effect:.2f}</td><td class="mono">{pct:.1f}%</td></tr>\n'
            )
        imp_html = (
            '  <h3>Factor Importance Ranking</h3>\n'
            '  <table class="data-table">\n'
            '    <thead><tr><th>#</th><th>Factor</th><th>Effect</th><th>Contribution</th></tr></thead>\n'
            '    <tbody>\n'
            f'{imp_rows}'
            '    </tbody>\n'
            '  </table>\n'
        )

        sections.append(
            f'<details open>\n'
            f'  <summary><h2>Optimization: {safe_name}{unit} ({direction})</h2></summary>\n'
            f'  <div class="section-body">\n'
            f'{best_html}'
            f'{model_html}'
            f'{pred_html}'
            f'{imp_html}'
            f'  </div>\n'
            f'</details>\n'
        )

    return "\n".join(sections)


def _build_results(report, pareto_images, effects_images, rsm_images=None,
                    normal_images=None, half_normal_images=None,
                    diagnostics_images=None) -> str:
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

        # --- ANOVA table ---
        anova_html = ""
        if analysis.anova_table:
            anova = analysis.anova_table
            anova_rows_html = ""
            for row in anova.rows:
                f_str = f"{row.f_value:.3f}" if row.f_value is not None else "&mdash;"
                p_str = f"{row.p_value:.4f}" if row.p_value is not None else "&mdash;"
                # Highlight significant terms
                sig_class = ""
                if row.p_value is not None and row.p_value < 0.05:
                    sig_class = ' style="font-weight:bold;"'
                anova_rows_html += (
                    f'      <tr{sig_class}>'
                    f'<td>{html.escape(row.source)}</td>'
                    f'<td class="mono">{row.df}</td>'
                    f'<td class="mono">{row.ss:.4f}</td>'
                    f'<td class="mono">{row.ms:.4f}</td>'
                    f'<td class="mono">{f_str}</td>'
                    f'<td class="mono">{p_str}</td>'
                    f'</tr>\n'
                )
            # Error rows
            if anova.lack_of_fit_row:
                lof = anova.lack_of_fit_row
                f_str = f"{lof.f_value:.3f}" if lof.f_value is not None else "&mdash;"
                p_str = f"{lof.p_value:.4f}" if lof.p_value is not None else "&mdash;"
                anova_rows_html += (
                    f'      <tr><td>{html.escape(lof.source)}</td>'
                    f'<td class="mono">{lof.df}</td><td class="mono">{lof.ss:.4f}</td>'
                    f'<td class="mono">{lof.ms:.4f}</td><td class="mono">{f_str}</td>'
                    f'<td class="mono">{p_str}</td></tr>\n'
                )
            if anova.pure_error_row:
                pe = anova.pure_error_row
                anova_rows_html += (
                    f'      <tr><td>{html.escape(pe.source)}</td>'
                    f'<td class="mono">{pe.df}</td><td class="mono">{pe.ss:.4f}</td>'
                    f'<td class="mono">{pe.ms:.4f}</td><td class="mono">&mdash;</td>'
                    f'<td class="mono">&mdash;</td></tr>\n'
                )
            if anova.error_row:
                err = anova.error_row
                anova_rows_html += (
                    f'      <tr><td>{html.escape(err.source)}</td>'
                    f'<td class="mono">{err.df}</td><td class="mono">{err.ss:.4f}</td>'
                    f'<td class="mono">{err.ms:.4f}</td><td class="mono">&mdash;</td>'
                    f'<td class="mono">&mdash;</td></tr>\n'
                )
            if anova.total_row:
                tot = anova.total_row
                anova_rows_html += (
                    f'      <tr style="border-top:2px solid var(--border);"><td><strong>{html.escape(tot.source)}</strong></td>'
                    f'<td class="mono"><strong>{tot.df}</strong></td><td class="mono"><strong>{tot.ss:.4f}</strong></td>'
                    f'<td class="mono"><strong>{tot.ms:.4f}</strong></td><td class="mono">&mdash;</td>'
                    f'<td class="mono">&mdash;</td></tr>\n'
                )
            note = ""
            if anova.error_method == "lenth":
                note = '  <p class="muted">Error estimated using Lenth\'s pseudo-standard-error (unreplicated design)</p>\n'
            anova_html = (
                '  <h3>ANOVA</h3>\n'
                '  <table class="data-table">\n'
                '    <thead><tr><th>Source</th><th>DF</th><th>SS</th>'
                '<th>MS</th><th>F</th><th>p-value</th></tr></thead>\n'
                '    <tbody>\n'
                f'{anova_rows_html}'
                '    </tbody>\n'
                '  </table>\n'
                f'{note}'
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

        # --- Normal/half-normal plots ---
        if normal_images and resp_name in normal_images:
            plots_html += (
                f'  <div class="plot"><img src="{normal_images[resp_name]}" '
                f'alt="Normal probability plot for {safe_name}"></div>\n'
            )
        if half_normal_images and resp_name in half_normal_images:
            plots_html += (
                f'  <div class="plot"><img src="{half_normal_images[resp_name]}" '
                f'alt="Half-normal plot for {safe_name}"></div>\n'
            )

        # --- Diagnostics plots ---
        if diagnostics_images and resp_name in diagnostics_images:
            plots_html += (
                f'  <div class="plot"><img src="{diagnostics_images[resp_name]}" '
                f'alt="Model diagnostics for {safe_name}"></div>\n'
            )

        # --- RSM surface plots ---
        rsm_html = ""
        if rsm_images and resp_name in rsm_images:
            rsm_html = '  <h3>Response Surface Plots</h3>\n'
            for label, data_uri in rsm_images[resp_name]:
                safe_label = html.escape(label)
                rsm_html += (
                    f'  <div class="plot">\n'
                    f'    <p class="plot-label">{safe_label}</p>\n'
                    f'    <img src="{data_uri}" alt="RSM: {safe_label}">\n'
                    f'  </div>\n'
                )

        sections.append(
            f'<details open>\n'
            f'  <summary><h2>Results: {safe_name}</h2></summary>\n'
            f'  <div class="section-body">\n'
            f'{main_effects_html}'
            f'{anova_html}'
            f'{interaction_html}'
            f'{summary_html}'
            f'{plots_html}'
            f'{rsm_html}'
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
.plot-label {
  font-size: 0.85em;
  color: #666;
  margin: 4px 0;
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
{optimization}
{design_matrix}
{footer}
</body>
</html>
"""
