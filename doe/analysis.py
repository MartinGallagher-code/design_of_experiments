# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
import csv
import json
import math
import os
import numpy as np

from .models import (
    AnalysisReport, AnovaRow, AnovaTable, DesignMatrix, DOEConfig,
    EffectResult, ExperimentRun, InteractionEffect, KneePointResult,
    OrdinalTrendResult, ResponseAnalysis,
)


def _numeric_sort_key(x):
    """Sort key that orders numeric strings numerically, falling back to lexicographic."""
    try:
        return (0, float(x))
    except (ValueError, TypeError):
        return (1, x)


def analyze(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    no_plots: bool = False,
    pareto_threshold: float = 80,
    partial: bool = False,
    detect_knee: bool = False,
    filter_factors: list[str] | None = None,
) -> AnalysisReport:
    results_dir = results_dir or cfg.out_directory or "results"
    processed_dir = cfg.processed_directory or results_dir

    all_data = _load_all_results(matrix.runs, results_dir, partial=partial)

    # Apply factor filter
    factor_names = matrix.factor_names
    if filter_factors:
        unknown = [f for f in filter_factors if f not in factor_names]
        if unknown:
            raise ValueError(
                f"Unknown factor(s): {', '.join(unknown)}. "
                f"Available factors: {', '.join(factor_names)}"
            )
        factor_names = [f for f in factor_names if f in filter_factors]

    results_by_response: dict[str, ResponseAnalysis] = {}
    pareto_chart_paths: dict[str, str] = {}
    effects_plot_paths: dict[str, str] = {}
    normal_plot_paths: dict[str, str] = {}
    half_normal_plot_paths: dict[str, str] = {}
    diagnostics_plot_paths: dict[str, str] = {}
    knee_point_results: dict[str, list[KneePointResult]] = {}
    knee_point_plot_paths: dict[str, str] = {}
    ordinal_trend_plot_paths: dict[str, str] = {}

    for resp in cfg.responses:
        responses: dict[int, float] = {}
        missing_keys: list[int] = []

        for run in matrix.runs:
            data = all_data.get(run.run_id, {})
            if resp.name in data:
                responses[run.run_id] = float(data[resp.name])
            else:
                missing_keys.append(run.run_id)

        if missing_keys:
            print(
                f"Warning: response '{resp.name}' missing in result files for "
                f"run IDs: {missing_keys}. Those runs will be excluded."
            )

        if not responses:
            print(f"Warning: no data found for response '{resp.name}', skipping.")
            continue

        valid_runs = [r for r in matrix.runs if r.run_id in responses]
        effects = _compute_main_effects(valid_runs, responses, factor_names)
        interactions = _compute_interaction_effects(valid_runs, responses, factor_names)
        summary_stats = _compute_summary_stats(valid_runs, responses, factor_names)

        # ANOVA table
        anova_table = None
        if len(valid_runs) > len(factor_names):
            try:
                anova_table = _compute_anova(valid_runs, responses, factor_names, cfg.factors)
            except Exception:
                pass  # graceful fallback if ANOVA fails

        # Ordinal trend analysis
        ms_error = 0.0
        df_error = 0
        if anova_table and anova_table.error_row:
            ms_error = anova_table.error_row.ms
            df_error = anova_table.error_row.df
        ordinal_trends = _compute_ordinal_trends(
            valid_runs, responses, cfg.factors, factor_names,
            resp.name, ms_error, df_error,
        )

        # Knee-point detection
        if detect_knee:
            knee_results = _detect_knee_points(
                valid_runs, responses, cfg.factors, factor_names, resp.name,
            )
            if knee_results:
                knee_point_results[resp.name] = knee_results

        results_by_response[resp.name] = ResponseAnalysis(
            response_name=resp.name,
            effects=effects,
            summary_stats=summary_stats,
            interactions=interactions,
            anova_table=anova_table,
            ordinal_trends=ordinal_trends,
        )

        if not no_plots:
            try:
                import matplotlib
                matplotlib.use("Agg")
                os.makedirs(processed_dir, exist_ok=True)

                safe = resp.name.replace("/", "_").replace(" ", "_")
                unit_label = f" ({resp.unit})" if resp.unit else ""
                ylabel = f"Mean {resp.name}{unit_label}"
                title = f"Pareto Chart — {resp.name}{unit_label}"

                pareto_path = os.path.join(processed_dir, f"pareto_{safe}.png")
                plot_pareto(effects, pareto_path, title=title, threshold=pareto_threshold)
                pareto_chart_paths[resp.name] = pareto_path

                effects_path = os.path.join(processed_dir, f"main_effects_{safe}.png")
                plot_main_effects(valid_runs, responses, factor_names, effects_path, ylabel=ylabel)
                effects_plot_paths[resp.name] = effects_path

                # Normal/half-normal probability plots of effects
                try:
                    from scipy.stats import norm as _norm_check  # noqa: F401
                    normal_path = os.path.join(processed_dir, f"normal_effects_{safe}.png")
                    plot_normal_effects(effects, normal_path,
                                       title=f"Normal Probability Plot — {resp.name}{unit_label}")
                    normal_plot_paths[resp.name] = normal_path

                    half_normal_path = os.path.join(processed_dir, f"half_normal_effects_{safe}.png")
                    plot_half_normal_effects(effects, half_normal_path,
                                           title=f"Half-Normal Plot — {resp.name}{unit_label}")
                    half_normal_plot_paths[resp.name] = half_normal_path
                except ImportError:
                    pass  # scipy not available

                # RSM surface plots for designs with continuous factors
                rsm_paths = plot_rsm_surface(
                    valid_runs, responses, cfg.factors, factor_names,
                    resp.name, processed_dir, response_unit=resp.unit,
                )
                for p in rsm_paths:
                    print(f"  RSM surface: {os.path.basename(p)}")

                # Model diagnostic plots (fit RSM and plot residuals)
                try:
                    from .rsm import fit_rsm as _fit_rsm
                    valid_runs_for_rsm = [r for r in matrix.runs if r.run_id in responses]
                    diag_model = _fit_rsm(valid_runs_for_rsm, responses, factor_names, cfg.factors, model_type="linear")
                    if diag_model.diagnostics and len(diag_model.diagnostics.residuals) >= 3:
                        diag_path = os.path.join(processed_dir, f"diagnostics_{safe}.png")
                        plot_diagnostics(diag_model.diagnostics, diag_path,
                                        title=f"Model Diagnostics — {resp.name}{unit_label}")
                        diagnostics_plot_paths[resp.name] = diag_path
                except Exception:
                    pass

            except ImportError:
                print("Warning: matplotlib not available; skipping plots.")

    return AnalysisReport(
        results_by_response=results_by_response,
        pareto_chart_paths=pareto_chart_paths,
        effects_plot_paths=effects_plot_paths,
        normal_plot_paths=normal_plot_paths,
        half_normal_plot_paths=half_normal_plot_paths,
        diagnostics_plot_paths=diagnostics_plot_paths,
        knee_point_results=knee_point_results,
        knee_point_plot_paths=knee_point_plot_paths,
        ordinal_trend_plot_paths=ordinal_trend_plot_paths,
    )


def _load_all_results(runs: list[ExperimentRun], results_dir: str, partial: bool = False) -> dict[int, dict]:
    """Load all run_{N}.json files.

    When *partial* is False (default), raises FileNotFoundError if any file
    is missing.  When *partial* is True, missing files are skipped with a
    warning and only existing results are returned.  An error is still raised
    if **no** result files exist at all.
    """
    result_data: dict[int, dict] = {}
    missing: list[int] = []

    for run in runs:
        path = os.path.join(results_dir, f"run_{run.run_id}.json")
        if not os.path.exists(path):
            missing.append(run.run_id)
            continue
        with open(path) as f:
            try:
                result_data[run.run_id] = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Corrupt result file '{path}': {e}. "
                    f"Delete or fix this file and re-run the experiment for run {run.run_id}."
                ) from None

    if missing and partial:
        n_completed = len(result_data)
        n_total = len(runs)
        missing_str = ", ".join(str(m) for m in missing)
        print(
            f"Partial mode: analyzing {n_completed}/{n_total} completed runs "
            f"(missing: {missing_str})"
        )
        if n_completed == 0:
            raise FileNotFoundError(
                f"No result files found in: {results_dir}. "
                f"Cannot perform partial analysis with zero results."
            )
    elif missing:
        raise FileNotFoundError(
            f"Missing result files for run IDs: {missing}. "
            f"Expected in: {results_dir}"
        )
    return result_data


def _compute_main_effects(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
) -> list[EffectResult]:
    # Try to import scipy for confidence intervals
    try:
        from scipy.stats import t as t_dist
        _has_scipy = True
    except ImportError:
        _has_scipy = False

    effects = []
    for factor_name in factor_names:
        level_responses: dict[str, list[float]] = {}
        for run in runs:
            level = run.factor_values[factor_name]
            level_responses.setdefault(level, []).append(responses[run.run_id])

        levels = sorted(level_responses.keys(), key=_numeric_sort_key)
        if len(levels) == 2:
            low_mean = sum(level_responses[levels[0]]) / len(level_responses[levels[0]])
            high_mean = sum(level_responses[levels[1]]) / len(level_responses[levels[1]])
            effect = high_mean - low_mean
        else:
            all_means = [sum(vals) / len(vals) for vals in level_responses.values()]
            effect = max(all_means) - min(all_means)

        all_vals = [v for vals in level_responses.values() for v in vals]
        n = len(all_vals)
        mean = sum(all_vals) / n
        variance = sum((v - mean) ** 2 for v in all_vals) / max(n - 1, 1)
        std_error = math.sqrt(variance / n)

        # Compute 95% confidence intervals for 2-level factors
        ci_low = 0.0
        ci_high = 0.0
        if _has_scipy and len(levels) == 2:
            n_low = len(level_responses[levels[0]])
            n_high = len(level_responses[levels[1]])
            # Pooled standard error
            var_low = sum((v - low_mean) ** 2 for v in level_responses[levels[0]]) / max(n_low - 1, 1)
            var_high = sum((v - high_mean) ** 2 for v in level_responses[levels[1]]) / max(n_high - 1, 1)
            df = n_low + n_high - 2
            if df > 0:
                pooled_var = ((n_low - 1) * var_low + (n_high - 1) * var_high) / df
                pooled_se = math.sqrt(pooled_var)
                se_effect = pooled_se * math.sqrt(1.0 / n_low + 1.0 / n_high)
                t_crit = t_dist.ppf(0.975, df)
                ci_low = effect - t_crit * se_effect
                ci_high = effect + t_crit * se_effect

        effects.append(EffectResult(
            factor_name=factor_name,
            main_effect=effect,
            std_error=std_error,
            pct_contribution=0.0,
            ci_low=ci_low,
            ci_high=ci_high,
        ))

    total_abs = sum(abs(e.main_effect) for e in effects) or 1.0
    for e in effects:
        e.pct_contribution = abs(e.main_effect) / total_abs * 100

    return sorted(effects, key=lambda e: abs(e.main_effect), reverse=True)


def _compute_interaction_effects(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
) -> list[InteractionEffect]:
    """Compute two-factor interaction effects for all pairs of 2-level factors."""
    from itertools import combinations

    # Identify which factors have exactly 2 levels
    factor_levels: dict[str, set[str]] = {}
    for run in runs:
        for fname in factor_names:
            factor_levels.setdefault(fname, set()).add(run.factor_values[fname])

    two_level_factors = [f for f in factor_names if len(factor_levels[f]) == 2]

    interactions: list[InteractionEffect] = []
    for fa, fb in combinations(two_level_factors, 2):
        levels_a = sorted(factor_levels[fa], key=_numeric_sort_key)
        levels_b = sorted(factor_levels[fb], key=_numeric_sort_key)

        # Both high or both low (concordant) vs one high one low (discordant)
        concordant: list[float] = []
        discordant: list[float] = []
        for run in runs:
            val_a = run.factor_values[fa]
            val_b = run.factor_values[fb]
            y = responses[run.run_id]
            # "low" = levels[0], "high" = levels[1]
            a_is_high = (val_a == levels_a[1])
            b_is_high = (val_b == levels_b[1])
            if a_is_high == b_is_high:
                concordant.append(y)
            else:
                discordant.append(y)

        if concordant and discordant:
            effect = (sum(concordant) / len(concordant)) - (sum(discordant) / len(discordant))
        else:
            effect = 0.0

        interactions.append(InteractionEffect(
            factor_a=fa,
            factor_b=fb,
            interaction_effect=effect,
            pct_contribution=0.0,
        ))

    total_abs = sum(abs(ix.interaction_effect) for ix in interactions) or 1.0
    for ix in interactions:
        ix.pct_contribution = abs(ix.interaction_effect) / total_abs * 100

    return sorted(interactions, key=lambda ix: abs(ix.interaction_effect), reverse=True)


def _compute_summary_stats(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
) -> dict:
    stats = {}
    for factor_name in factor_names:
        level_responses: dict[str, list[float]] = {}
        for run in runs:
            level = run.factor_values[factor_name]
            level_responses.setdefault(level, []).append(responses[run.run_id])

        stats[factor_name] = {}
        for level, vals in sorted(level_responses.items(), key=lambda item: _numeric_sort_key(item[0])):
            n = len(vals)
            mean = sum(vals) / n
            variance = sum((v - mean) ** 2 for v in vals) / max(n - 1, 1)
            stats[factor_name][level] = {
                "n": n,
                "mean": mean,
                "std": math.sqrt(variance),
                "min": min(vals),
                "max": max(vals),
            }
    return stats


def _compute_anova(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list,
) -> AnovaTable:
    """Compute ANOVA table using Type I (sequential) SS decomposition.

    For unreplicated designs, uses Lenth's pseudo-standard-error to construct
    an error estimate from the median of absolute effects (same approach as
    R's FrF2 package).
    """
    from .rsm import _build_design_matrix, _encode_factor_value

    try:
        from scipy.stats import f as f_dist
        _has_scipy = True
    except ImportError:
        _has_scipy = False

    valid_runs = [r for r in runs if r.run_id in responses]
    n = len(valid_runs)
    y = np.array([responses[r.run_id] for r in valid_runs])
    grand_mean = np.mean(y)
    ss_total = float(np.sum((y - grand_mean) ** 2))

    # Detect replicates (runs with identical factor settings)
    from collections import Counter
    setting_counts = Counter()
    setting_responses: dict[tuple, list[float]] = {}
    for run in valid_runs:
        key = tuple(run.factor_values[f] for f in factor_names)
        setting_counts[key] += 1
        setting_responses.setdefault(key, []).append(responses[run.run_id])

    has_replicates = any(c > 1 for c in setting_counts.values())

    # Build full design matrix (linear model with main effects only)
    factor_map = {f.name: f for f in factors}

    # Compute SS for each factor using Type I approach
    # Build X column by column, compute sequential SS
    anova_rows: list[AnovaRow] = []

    # Identify factor levels for each factor
    factor_level_map: dict[str, list[str]] = {}
    for fname in factor_names:
        levels = set()
        for run in valid_runs:
            levels.add(run.factor_values[fname])
        factor_level_map[fname] = sorted(levels)

    # Compute SS for each main effect factor
    ss_model = 0.0
    for fname in factor_names:
        levels = factor_level_map[fname]
        df_factor = len(levels) - 1

        # Group responses by level
        level_vals: dict[str, list[float]] = {}
        for run in valid_runs:
            lv = run.factor_values[fname]
            level_vals.setdefault(lv, []).append(responses[run.run_id])

        # SS = sum over levels of n_i * (mean_i - grand_mean)^2
        ss_factor = 0.0
        for lv, vals in level_vals.items():
            lv_mean = sum(vals) / len(vals)
            ss_factor += len(vals) * (lv_mean - grand_mean) ** 2

        ss_model += ss_factor
        ms_factor = ss_factor / df_factor if df_factor > 0 else 0.0

        anova_rows.append(AnovaRow(
            source=fname,
            df=df_factor,
            ss=ss_factor,
            ms=ms_factor,
        ))

    # Compute interaction SS for 2-level factor pairs
    two_level_factors = [f for f in factor_names if len(factor_level_map[f]) == 2]
    from itertools import combinations
    for fa, fb in combinations(two_level_factors, 2):
        levels_a = factor_level_map[fa]
        levels_b = factor_level_map[fb]

        # Group by (level_a, level_b) combination
        combo_vals: dict[tuple, list[float]] = {}
        for run in valid_runs:
            key = (run.factor_values[fa], run.factor_values[fb])
            combo_vals.setdefault(key, []).append(responses[run.run_id])

        # SS_interaction = SS_AB_total - SS_A - SS_B
        # where SS_AB_total = sum n_ij * (mean_ij - grand_mean)^2
        ss_ab_total = 0.0
        for key, vals in combo_vals.items():
            combo_mean = sum(vals) / len(vals)
            ss_ab_total += len(vals) * (combo_mean - grand_mean) ** 2

        # Get individual SS for A and B
        ss_a = 0.0
        for lv in levels_a:
            vals_a = []
            for run in valid_runs:
                if run.factor_values[fa] == lv:
                    vals_a.append(responses[run.run_id])
            if vals_a:
                ss_a += len(vals_a) * (sum(vals_a) / len(vals_a) - grand_mean) ** 2

        ss_b = 0.0
        for lv in levels_b:
            vals_b = []
            for run in valid_runs:
                if run.factor_values[fb] == lv:
                    vals_b.append(responses[run.run_id])
            if vals_b:
                ss_b += len(vals_b) * (sum(vals_b) / len(vals_b) - grand_mean) ** 2

        ss_interaction = max(0.0, ss_ab_total - ss_a - ss_b)
        df_interaction = 1  # (2-1)(2-1) = 1
        ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0.0
        ss_model += ss_interaction

        anova_rows.append(AnovaRow(
            source=f"{fa}*{fb}",
            df=df_interaction,
            ss=ss_interaction,
            ms=ms_interaction,
        ))

    # Error estimation
    ss_error = max(0.0, ss_total - ss_model)
    df_model = sum(row.df for row in anova_rows)
    df_error = n - 1 - df_model

    error_method = "pooled"
    lack_of_fit_row = None
    pure_error_row = None

    if has_replicates:
        # Pure error from replicates
        ss_pure_error = 0.0
        df_pure_error = 0
        for key, vals in setting_responses.items():
            if len(vals) > 1:
                group_mean = sum(vals) / len(vals)
                ss_pure_error += sum((v - group_mean) ** 2 for v in vals)
                df_pure_error += len(vals) - 1

        ss_lack_of_fit = max(0.0, ss_error - ss_pure_error)
        n_unique = len(setting_responses)
        df_lack_of_fit = max(0, n_unique - 1 - df_model)

        ms_pure_error = ss_pure_error / df_pure_error if df_pure_error > 0 else 0.0
        ms_lack_of_fit = ss_lack_of_fit / df_lack_of_fit if df_lack_of_fit > 0 else 0.0

        # Lack-of-fit F-test
        lof_f = ms_lack_of_fit / ms_pure_error if ms_pure_error > 0 else None
        lof_p = None
        if lof_f is not None and _has_scipy and df_lack_of_fit > 0 and df_pure_error > 0:
            lof_p = float(f_dist.sf(lof_f, df_lack_of_fit, df_pure_error))

        lack_of_fit_row = AnovaRow(
            source="Lack of Fit", df=df_lack_of_fit,
            ss=ss_lack_of_fit, ms=ms_lack_of_fit,
            f_value=lof_f, p_value=lof_p,
        )
        pure_error_row = AnovaRow(
            source="Pure Error", df=df_pure_error,
            ss=ss_pure_error, ms=ms_pure_error,
        )
        ms_error = ms_pure_error
        error_method = "replicates"
    elif df_error > 0:
        ms_error = ss_error / df_error
        error_method = "pooled"
    else:
        # Unreplicated design — use Lenth's pseudo-standard-error
        all_effects = [row.ms for row in anova_rows if row.df == 1]
        if all_effects:
            s0 = 1.5 * float(np.median(np.abs(all_effects)))
            # Trim effects larger than 2.5*s0 and recompute
            trimmed = [e for e in all_effects if abs(e) < 2.5 * s0]
            pse = 1.5 * float(np.median(np.abs(trimmed))) if trimmed else s0
            ms_error = pse
            # Approximate df using Lenth's method: df ≈ n_effects / 3
            df_error = max(1, len(all_effects) // 3)
            ss_error = ms_error * df_error
        else:
            ms_error = 0.0
            df_error = 0
        error_method = "lenth"

    # Compute F-values and p-values for each term
    if ms_error > 0:
        for row in anova_rows:
            row.f_value = row.ms / ms_error
            if _has_scipy and df_error > 0:
                row.p_value = float(f_dist.sf(row.f_value, row.df, df_error))

    error_row = AnovaRow(
        source="Error" if error_method != "lenth" else "Error (Lenth PSE)",
        df=df_error,
        ss=ss_error,
        ms=ms_error,
    )
    total_row = AnovaRow(
        source="Total",
        df=n - 1,
        ss=ss_total,
        ms=ss_total / (n - 1) if n > 1 else 0.0,
    )

    return AnovaTable(
        rows=anova_rows,
        error_row=error_row,
        total_row=total_row,
        lack_of_fit_row=lack_of_fit_row,
        pure_error_row=pure_error_row,
        error_method=error_method,
    )


def _compute_ordinal_trends(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factors: list,
    factor_names: list[str],
    response_name: str,
    ms_error: float = 0.0,
    df_error: int = 0,
) -> list[OrdinalTrendResult]:
    """Compute linear and quadratic trend tests for ordinal factors with 3+ levels."""
    try:
        from scipy.stats import f as f_dist
        _has_scipy = True
    except ImportError:
        _has_scipy = False

    factor_map = {f.name: f for f in factors}
    results = []

    for fname in factor_names:
        factor = factor_map.get(fname)
        if not factor or factor.type != "ordinal":
            continue

        # Group responses by level
        level_responses: dict[str, list[float]] = {}
        for run in runs:
            level = run.factor_values[fname]
            level_responses.setdefault(level, []).append(responses[run.run_id])

        levels = sorted(level_responses.keys(), key=_numeric_sort_key)
        k = len(levels)
        if k < 3:
            continue

        means = [sum(level_responses[lv]) / len(level_responses[lv]) for lv in levels]
        ns = [len(level_responses[lv]) for lv in levels]
        n_total = sum(ns)

        # Orthogonal polynomial contrasts for equally-spaced ordinal levels
        # Use integer positions as the ordinal encoding
        positions = list(range(k))
        pos_mean = sum(positions) / k

        # Linear contrast coefficients: centered positions
        linear_c = [p - pos_mean for p in positions]
        # Quadratic contrast: c_i = x_i^2 - mean(x^2)
        sq_mean = sum(p ** 2 for p in positions) / k
        quadratic_c = [p ** 2 - sq_mean for p in positions]

        # SS_contrast = (sum(c_i * mean_i))^2 * n_per / sum(c_i^2)
        # For unbalanced, use weighted version
        linear_sum = sum(c * m for c, m in zip(linear_c, means))
        linear_c_ss = sum(c ** 2 for c in linear_c)
        n_harm = k / sum(1.0 / ni for ni in ns) if all(ni > 0 for ni in ns) else min(ns)

        linear_ss = (linear_sum ** 2) * n_harm / linear_c_ss if linear_c_ss > 0 else 0.0
        linear_coeff = linear_sum / linear_c_ss if linear_c_ss > 0 else 0.0

        quadratic_sum = sum(c * m for c, m in zip(quadratic_c, means))
        quadratic_c_ss = sum(c ** 2 for c in quadratic_c)
        quadratic_ss = (quadratic_sum ** 2) * n_harm / quadratic_c_ss if quadratic_c_ss > 0 else 0.0
        quadratic_coeff = quadratic_sum / quadratic_c_ss if quadratic_c_ss > 0 else 0.0

        # R-squared values
        grand_mean = sum(m * n for m, n in zip(means, ns)) / n_total
        ss_total = sum(n * (m - grand_mean) ** 2 for m, n in zip(means, ns))
        r2_lin = linear_ss / ss_total if ss_total > 0 else 0.0
        r2_quad = (linear_ss + quadratic_ss) / ss_total if ss_total > 0 else 0.0

        # F-tests
        linear_f = None
        linear_p = None
        quadratic_f = None
        quadratic_p = None
        if ms_error > 0 and df_error > 0:
            linear_f = linear_ss / ms_error
            quadratic_f = quadratic_ss / ms_error
            if _has_scipy:
                linear_p = float(f_dist.sf(linear_f, 1, df_error))
                quadratic_p = float(f_dist.sf(quadratic_f, 1, df_error))

        results.append(OrdinalTrendResult(
            factor_name=fname,
            response_name=response_name,
            linear_coefficient=linear_coeff,
            linear_ss=linear_ss,
            linear_f_value=linear_f,
            linear_p_value=linear_p,
            quadratic_coefficient=quadratic_coeff,
            quadratic_ss=quadratic_ss,
            quadratic_f_value=quadratic_f,
            quadratic_p_value=quadratic_p,
            r_squared_linear=r2_lin,
            r_squared_quadratic=r2_quad,
        ))

    return results


def _detect_knee_points(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factors: list,
    factor_names: list[str],
    response_name: str,
) -> list[KneePointResult]:
    """Detect saturation/knee points for ordinal/continuous factors with 3+ levels."""
    from .knee import detect_knee_point

    factor_map = {f.name: f for f in factors}
    results = []

    for fname in factor_names:
        factor = factor_map.get(fname)
        if not factor or factor.type not in ("ordinal", "continuous"):
            continue

        # Group responses by level
        level_responses: dict[str, list[float]] = {}
        for run in runs:
            level = run.factor_values[fname]
            level_responses.setdefault(level, []).append(responses[run.run_id])

        # Need 3+ distinct levels
        if len(level_responses) < 3:
            continue

        # Try to convert levels to numeric
        try:
            numeric_levels = [(float(lv), sum(vals) / len(vals))
                              for lv, vals in level_responses.items()]
        except ValueError:
            continue

        numeric_levels.sort(key=lambda x: x[0])
        factor_values = [x[0] for x in numeric_levels]
        response_values = [x[1] for x in numeric_levels]

        knee = detect_knee_point(factor_values, response_values)
        if knee is not None:
            results.append(KneePointResult(
                factor_name=fname,
                response_name=response_name,
                knee_value=knee.knee_value,
                knee_response=knee.knee_response,
                ci_low=knee.ci_low,
                ci_high=knee.ci_high,
                r_squared=knee.r_squared,
                segment1_slope=knee.segment1_slope,
                segment2_slope=knee.segment2_slope,
            ))

    return results


def plot_pareto(
    effects: list[EffectResult],
    output_path: str,
    title: str = "Pareto Chart of Main Effects",
    threshold: float = 80,
) -> None:
    import matplotlib.pyplot as plt

    sorted_effects = sorted(effects, key=lambda e: abs(e.main_effect), reverse=True)
    names = [e.factor_name for e in sorted_effects]
    values = [abs(e.main_effect) for e in sorted_effects]
    total = sum(values) or 1.0
    cumulative = [sum(values[:i + 1]) / total * 100 for i in range(len(values))]

    fig, ax1 = plt.subplots(figsize=(max(6, len(names) * 1.2), 5))
    ax1.barh(names[::-1], values[::-1], color="steelblue")
    ax1.set_xlabel("Absolute Main Effect")
    ax1.set_title(title)

    ax2 = ax1.twiny()
    ax2.plot(cumulative[::-1], range(len(names)), "o-", color="red", markersize=4)
    ax2.axvline(threshold, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
    ax2.set_xlabel("Cumulative % Contribution")
    ax2.set_xlim(0, 105)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_main_effects(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    output_path: str,
    ylabel: str = "Mean Response",
) -> None:
    import matplotlib.pyplot as plt

    n = len(factor_names)
    cols = min(3, n)
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3), squeeze=False)
    fig.suptitle("Main Effects Plot", fontsize=13)

    for idx, factor_name in enumerate(factor_names):
        ax = axes[idx // cols][idx % cols]
        level_responses: dict[str, list[float]] = {}
        for run in runs:
            level = run.factor_values[factor_name]
            level_responses.setdefault(level, []).append(responses[run.run_id])

        levels = sorted(level_responses.keys(), key=_numeric_sort_key)
        means = [sum(level_responses[lv]) / len(level_responses[lv]) for lv in levels]

        ax.plot(levels, means, "o-", color="steelblue", linewidth=2, markersize=6)
        ax.set_title(factor_name)
        ax.set_xlabel("Level")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    for idx in range(n, rows * cols):
        axes[idx // cols][idx % cols].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_rsm_surface(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factors: list,
    factor_names: list[str],
    response_name: str,
    output_dir: str,
    response_unit: str = "",
) -> list[str]:
    """Generate 3D response surface plots for each pair of continuous factors.

    Fits a quadratic RSM model and plots the predicted surface while holding
    other factors at their center values.  Returns list of created file paths.
    """
    from .rsm import fit_rsm

    # Identify continuous factors (need numeric levels)
    continuous = []
    for fname in factor_names:
        fac = next((f for f in factors if f.name == fname), None)
        if fac and fac.type in ("continuous", "ordinal"):
            try:
                vals = [float(lv) for lv in fac.levels]
                if len(set(vals)) >= 2:
                    continuous.append(fname)
            except ValueError:
                pass

    if len(continuous) < 2:
        return []

    # Fit quadratic model
    valid_runs = [r for r in runs if r.run_id in responses]
    try:
        model = fit_rsm(valid_runs, responses, factor_names, factors, model_type="quadratic")
    except Exception:
        # Fall back to linear if quadratic fails (e.g. singular matrix)
        try:
            model = fit_rsm(valid_runs, responses, factor_names, factors, model_type="linear")
        except Exception:
            return []

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    import numpy as np
    from itertools import combinations

    os.makedirs(output_dir, exist_ok=True)
    created = []

    factor_map = {f.name: f for f in factors}

    for fa, fb in combinations(continuous, 2):
        fac_a = factor_map[fa]
        fac_b = factor_map[fb]

        try:
            a_vals = [float(lv) for lv in fac_a.levels]
            b_vals = [float(lv) for lv in fac_b.levels]
        except ValueError:
            continue

        a_min, a_max = min(a_vals), max(a_vals)
        b_min, b_max = min(b_vals), max(b_vals)
        # Extend range slightly for CCD star points
        a_range = a_max - a_min
        b_range = b_max - b_min
        a_lo = a_min - 0.1 * a_range
        a_hi = a_max + 0.1 * a_range
        b_lo = b_min - 0.1 * b_range
        b_hi = b_max + 0.1 * b_range

        grid_n = 40
        a_grid = np.linspace(a_lo, a_hi, grid_n)
        b_grid = np.linspace(b_lo, b_hi, grid_n)
        A, B = np.meshgrid(a_grid, b_grid)

        # Predict at each grid point using model coefficients
        Z = np.full_like(A, model.coefficients.get("intercept", 0.0))
        coefs = model.coefficients

        # Center and half-range for encoding
        centers = {}
        half_ranges = {}
        for fname in factor_names:
            fac = factor_map[fname]
            try:
                num = [float(lv) for lv in fac.levels]
                centers[fname] = (max(num) + min(num)) / 2.0
                half_ranges[fname] = (max(num) - min(num)) / 2.0
            except ValueError:
                centers[fname] = 0.0
                half_ranges[fname] = 1.0

        def encode(fname, raw_val):
            hr = half_ranges.get(fname, 1.0)
            if hr == 0:
                return 0.0
            return (raw_val - centers.get(fname, 0.0)) / hr

        # Encoded grids for the two plotted factors
        A_enc = encode(fa, A)
        B_enc = encode(fb, B)

        # Other factors held at center (encoded = 0)
        # Add linear terms
        for fname in factor_names:
            if fname == fa:
                Z += coefs.get(fname, 0.0) * A_enc
            elif fname == fb:
                Z += coefs.get(fname, 0.0) * B_enc
            # else: encoded = 0, so contribution = 0

        # Add interaction and squared terms
        for key, val in coefs.items():
            if key == "intercept" or key in factor_names:
                continue
            if "*" in key:
                f1, f2 = key.split("*")
                if f1 == fa and f2 == fb:
                    Z += val * A_enc * B_enc
                elif f1 == fb and f2 == fa:
                    Z += val * A_enc * B_enc
                # Other interactions with held-at-center factors contribute 0
            elif "^2" in key:
                base = key.replace("^2", "")
                if base == fa:
                    Z += val * A_enc ** 2
                elif base == fb:
                    Z += val * B_enc ** 2

        # Create the 3D plot
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection="3d")

        surf = ax.plot_surface(A, B, Z, cmap="viridis", alpha=0.85,
                               edgecolor="none", antialiased=True)

        # Scatter the actual data points on top
        for run in valid_runs:
            try:
                xa = float(run.factor_values[fa])
                xb = float(run.factor_values[fb])
                y = responses[run.run_id]
                ax.scatter([xa], [xb], [y], c="red", s=30, zorder=5, edgecolors="darkred", linewidths=0.5)
            except (ValueError, KeyError):
                pass

        unit_label = f" ({response_unit})" if response_unit else ""
        unit_a = f" ({fac_a.unit})" if fac_a.unit else ""
        unit_b = f" ({fac_b.unit})" if fac_b.unit else ""
        ax.set_xlabel(f"{fa}{unit_a}", fontsize=9, labelpad=8)
        ax.set_ylabel(f"{fb}{unit_b}", fontsize=9, labelpad=8)
        ax.set_zlabel(f"{response_name}{unit_label}", fontsize=9, labelpad=8)
        ax.set_title(f"Response Surface: {response_name}\n{fa} vs {fb}", fontsize=11)

        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, pad=0.12)

        safe_resp = response_name.replace("/", "_").replace(" ", "_")
        safe_fa = fa.replace("/", "_")
        safe_fb = fb.replace("/", "_")
        path = os.path.join(output_dir, f"rsm_{safe_resp}_{safe_fa}_vs_{safe_fb}.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        created.append(path)

    return created


def plot_diagnostics(
    diagnostics,
    output_path: str,
    title: str = "Model Diagnostics",
) -> None:
    """Generate a 2x2 diagnostic plot panel: residuals vs fitted, normal probability,
    residuals vs run order, and predicted vs actual."""
    import matplotlib.pyplot as plt
    from scipy.stats import probplot

    resid = diagnostics.residuals
    fitted = diagnostics.fitted_values
    run_ids = diagnostics.run_ids
    n = len(resid)
    if n < 3:
        return

    actual = [f + r for f, r in zip(fitted, resid)]

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle(title, fontsize=13)

    # 1. Residuals vs Fitted
    ax = axes[0][0]
    ax.scatter(fitted, resid, c="steelblue", s=30, edgecolors="white", linewidths=0.5)
    ax.axhline(0, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.set_xlabel("Fitted Values")
    ax.set_ylabel("Residuals")
    ax.set_title("Residuals vs Fitted")
    ax.grid(True, alpha=0.3)

    # 2. Normal Probability Plot of Residuals
    ax = axes[0][1]
    probplot(resid, plot=ax)
    ax.set_title("Normal Probability Plot")
    ax.grid(True, alpha=0.3)

    # 3. Residuals vs Run Order
    ax = axes[1][0]
    ax.scatter(range(1, n + 1), resid, c="steelblue", s=30, edgecolors="white", linewidths=0.5)
    ax.axhline(0, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.set_xlabel("Run Order")
    ax.set_ylabel("Residuals")
    ax.set_title("Residuals vs Run Order")
    ax.grid(True, alpha=0.3)

    # 4. Predicted vs Actual
    ax = axes[1][1]
    ax.scatter(actual, fitted, c="steelblue", s=30, edgecolors="white", linewidths=0.5)
    lims = [min(min(actual), min(fitted)), max(max(actual), max(fitted))]
    margin = (lims[1] - lims[0]) * 0.05
    ax.plot([lims[0] - margin, lims[1] + margin], [lims[0] - margin, lims[1] + margin],
            "r--", linewidth=0.8, alpha=0.7)
    ax.set_xlabel("Actual")
    ax.set_ylabel("Predicted")
    ax.set_title("Predicted vs Actual")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_normal_effects(
    effects: list[EffectResult],
    output_path: str,
    title: str = "Normal Probability Plot of Effects",
) -> None:
    """Plot effects against normal quantiles. Significant effects deviate from the line."""
    import matplotlib.pyplot as plt
    from scipy.stats import norm

    sorted_effects = sorted(effects, key=lambda e: e.main_effect)
    n = len(sorted_effects)
    if n < 2:
        return

    values = [e.main_effect for e in sorted_effects]
    names = [e.factor_name for e in sorted_effects]
    # Filliben approximation for expected normal order statistics
    quantiles = [norm.ppf((i + 1 - 0.375) / (n + 0.25)) for i in range(n)]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(quantiles, values, c="steelblue", s=50, zorder=5, edgecolors="white", linewidths=0.5)

    # Reference line through Q1/Q3
    q1_idx, q3_idx = n // 4, 3 * n // 4
    if q3_idx > q1_idx and quantiles[q3_idx] != quantiles[q1_idx]:
        slope = (values[q3_idx] - values[q1_idx]) / (quantiles[q3_idx] - quantiles[q1_idx])
        intercept = values[q1_idx] - slope * quantiles[q1_idx]
        x_line = [quantiles[0] - 0.5, quantiles[-1] + 0.5]
        ax.plot(x_line, [slope * x + intercept for x in x_line], "r--", alpha=0.6, linewidth=1)

        # Label points that deviate significantly from the line
        residuals = [abs(v - (slope * q + intercept)) for v, q in zip(values, quantiles)]
        threshold = 1.5 * (sum(residuals) / len(residuals)) if residuals else 0
        for i, (q, v, name) in enumerate(zip(quantiles, values, names)):
            if residuals[i] > threshold:
                ax.annotate(name, (q, v), textcoords="offset points",
                           xytext=(5, 5), fontsize=8, color="red", fontweight="bold")

    ax.set_xlabel("Theoretical Quantiles")
    ax.set_ylabel("Effects")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_half_normal_effects(
    effects: list[EffectResult],
    output_path: str,
    title: str = "Half-Normal Probability Plot of Effects",
) -> None:
    """Plot absolute effects against half-normal quantiles. Significant effects are labeled."""
    import matplotlib.pyplot as plt
    from scipy.stats import halfnorm

    abs_effects = sorted([(abs(e.main_effect), e.factor_name) for e in effects])
    n = len(abs_effects)
    if n < 2:
        return

    values = [v for v, _ in abs_effects]
    names = [name for _, name in abs_effects]
    quantiles = [halfnorm.ppf((i + 1 - 0.375) / (n + 0.25)) for i in range(n)]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(quantiles, values, c="steelblue", s=50, zorder=5, edgecolors="white", linewidths=0.5)

    # Reference line through origin and median point
    mid = n // 2
    if quantiles[mid] > 0:
        slope = values[mid] / quantiles[mid]
        x_line = [0, quantiles[-1] + 0.3]
        ax.plot(x_line, [slope * x for x in x_line], "r--", alpha=0.6, linewidth=1)

        # Label points deviating from line
        residuals = [abs(v - slope * q) for v, q in zip(values, quantiles)]
        threshold = 1.5 * (sum(residuals) / len(residuals)) if residuals else 0
        for i, (q, v, name) in enumerate(zip(quantiles, values, names)):
            if residuals[i] > threshold:
                ax.annotate(name, (q, v), textcoords="offset points",
                           xytext=(5, 5), fontsize=8, color="red", fontweight="bold")

    ax.set_xlabel("Half-Normal Quantiles")
    ax.set_ylabel("|Effect|")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def export_csv(report: AnalysisReport, output_dir: str) -> list[str]:
    """Export analysis results to CSV files. Returns list of created file paths."""
    os.makedirs(output_dir, exist_ok=True)
    created = []

    for resp_name, analysis in report.results_by_response.items():
        safe = resp_name.replace("/", "_").replace(" ", "_")

        # Main effects CSV
        effects_path = os.path.join(output_dir, f"main_effects_{safe}.csv")
        with open(effects_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["factor_name", "main_effect", "std_error", "pct_contribution", "ci_low", "ci_high"])
            for e in analysis.effects:
                writer.writerow([e.factor_name, e.main_effect, e.std_error, e.pct_contribution, e.ci_low, e.ci_high])
        created.append(effects_path)

        # Summary stats CSV
        stats_path = os.path.join(output_dir, f"summary_stats_{safe}.csv")
        with open(stats_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["factor", "level", "n", "mean", "std", "min", "max"])
            for factor, levels in analysis.summary_stats.items():
                for level, s in sorted(levels.items(), key=lambda item: _numeric_sort_key(item[0])):
                    writer.writerow([factor, level, s["n"], s["mean"], s["std"], s["min"], s["max"]])
        created.append(stats_path)

    return created
