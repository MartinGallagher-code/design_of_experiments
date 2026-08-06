# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import csv
import json
import math
import os
from typing import TYPE_CHECKING, cast

import numpy as np

if TYPE_CHECKING:
    from .rsm import ModelDiagnostics

from .models import (
    AnalysisReport, AnovaRow, AnovaTable,
    CrossValidation, DesignMatrix, DOEConfig,
    EffectResult, ExperimentRun, Factor, InteractionEffect, KneePointResult,
    ModelAdequacy, OrdinalTrendResult, ResponseAnalysis, StationaryPoint,
)


def _numeric_sort_key(x: str) -> tuple[int, float | str]:
    """Sort key that orders numeric strings numerically, falling back to lexicographic."""
    try:
        return (0, float(x))
    except (ValueError, TypeError):
        return (1, x)


def _coerce_response_value(
    data: dict[str, object], resp_name: str, run_id: int, results_dir: str,
) -> float | None:
    """Return a float response value, or None if missing/blank.

    Raises ValueError with a clear pointer to the offending file when the
    stored value is present but cannot be parsed as a number.
    """
    if resp_name not in data:
        return None
    raw = data[resp_name]
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip() == "":
        return None
    try:
        return float(cast("str | float", raw))
    except (TypeError, ValueError):
        path = os.path.join(results_dir, f"run_{run_id}.json")
        raise ValueError(
            f"Invalid value for response '{resp_name}' in '{path}': {raw!r}. "
            f"Expected a number. Edit the file or re-record the run."
        ) from None


def analyze(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    no_plots: bool = False,
    pareto_threshold: float = 80,
    partial: bool = False,
    detect_knee: bool = False,
    filter_factors: list[str] | None = None,
    exclude_run_ids: list[int] | None = None,
    fit_rsm: bool = True,
    cv_folds: int | None = None,
) -> AnalysisReport:
    results_dir = results_dir or cfg.out_directory or "results"
    processed_dir = cfg.processed_directory or results_dir

    all_data = _load_all_results(matrix.runs, results_dir, partial=partial)

    # Apply run-id exclusion filter (used to drop outliers without editing
    # the on-disk result files). Exclusions apply to every response and
    # every analysis path that iterates matrix.runs below.
    excluded = set(exclude_run_ids or [])
    if excluded:
        unknown = excluded - {r.run_id for r in matrix.runs}
        if unknown:
            raise ValueError(
                f"Unknown run id(s) in exclude_run_ids: {sorted(unknown)}. "
                f"Available run ids: {sorted(r.run_id for r in matrix.runs)}"
            )
        # Build a filtered matrix; keep the original metadata for context.
        from .models import DesignMatrix as _DesignMatrix
        kept = [r for r in matrix.runs if r.run_id not in excluded]
        if not kept:
            raise ValueError(
                "exclude_run_ids removed every run; nothing left to analyse."
            )
        matrix = _DesignMatrix(
            runs=kept,
            factor_names=matrix.factor_names,
            operation=matrix.operation,
            metadata={**matrix.metadata, "excluded_run_ids": sorted(excluded)},
        )

    # Apply factor filter
    factor_names = matrix.factor_names
    if filter_factors:
        unknown_factors = [f for f in filter_factors if f not in factor_names]
        if unknown_factors:
            raise ValueError(
                f"Unknown factor(s): {', '.join(unknown_factors)}. "
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
            value = _coerce_response_value(data, resp.name, run.run_id, results_dir)
            if value is None:
                missing_keys.append(run.run_id)
            else:
                responses[run.run_id] = value

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

        # ANOVA table — split-plot designs need a two-error path
        anova_table = None
        if len(valid_runs) > len(factor_names):
            try:
                if cfg.operation == "split_plot":
                    anova_table = _compute_split_plot_anova(
                        valid_runs, responses, factor_names, cfg.factors,
                    )
                else:
                    anova_table = _compute_anova(
                        valid_runs, responses, factor_names, cfg.factors,
                    )
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

        # Model adequacy + stationary-point characterization. Quadratic where
        # the design supports it, linear otherwise.  Skipped when the caller
        # passed fit_rsm=False (e.g. on big designs where the quadratic refit
        # dominates analyze() runtime).
        if fit_rsm:
            model_adequacy, stationary_point = _compute_model_adequacy_and_stationary(
                valid_runs, responses, factor_names, cfg.factors,
            )
            cross_validation = _compute_cross_validation_safe(
                valid_runs, responses, factor_names, cfg.factors,
                model_adequacy.model_type if model_adequacy else "linear",
                k_folds=cv_folds,
            )
        else:
            model_adequacy, stationary_point = None, None
            cross_validation = None

        # Mixture-design Scheffé canonical fit (when the operation is mixture-style).
        scheffe = None
        try:
            from .mixture import fit_scheffe, is_mixture_operation
            if is_mixture_operation(cfg.operation):
                # Quadratic when the design supports it, else linear.
                q = len(factor_names)
                n_quad = q + q * (q - 1) // 2
                form = "quadratic" if len(valid_runs) >= n_quad + 1 else "linear"
                scheffe = fit_scheffe(
                    valid_runs, responses, factor_names,
                    response_name=resp.name, model_form=form,
                )
        except Exception:
            scheffe = None

        # Achieved-power retrospective from the actual residual MS.
        achieved_power_result = None
        if anova_table and anova_table.error_row and anova_table.error_row.df > 0:
            try:
                from .power import achieved_power as _achieved_power
                achieved_power_result = _achieved_power(
                    matrix=matrix,
                    factors=cfg.factors,
                    residual_ms=anova_table.error_row.ms,
                    df_error=anova_table.error_row.df,
                )
            except Exception:
                achieved_power_result = None

        results_by_response[resp.name] = ResponseAnalysis(
            response_name=resp.name,
            effects=effects,
            summary_stats=summary_stats,
            interactions=interactions,
            anova_table=anova_table,
            ordinal_trends=ordinal_trends,
            model_adequacy=model_adequacy,
            stationary_point=stationary_point,
            achieved_power=achieved_power_result,
            cross_validation=cross_validation,
            scheffe_model=scheffe,
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

    # Alias / confounding structure for screening designs
    alias_structure = None
    try:
        from .aliasing import compute_alias_structure
        alias_structure = compute_alias_structure(matrix, factor_names=factor_names)
    except Exception:
        pass

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
        alias_structure=alias_structure,
    )


def _load_all_results(runs: list[ExperimentRun], results_dir: str, partial: bool = False) -> dict[int, dict[str, object]]:
    """Load all run_{N}.json files.

    When *partial* is False (default), raises FileNotFoundError if any file
    is missing.  When *partial* is True, missing files are skipped with a
    warning and only existing results are returned.  An error is still raised
    if **no** result files exist at all.
    """
    result_data: dict[int, dict[str, object]] = {}
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


def _compute_model_adequacy_and_stationary(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list[Factor],
) -> tuple[ModelAdequacy | None, StationaryPoint | None]:
    """Fit an RSM (quadratic where supported, linear otherwise) and compute
    model-adequacy diagnostics and stationary-point characterization.

    Returns ``(ModelAdequacy | None, StationaryPoint | None)``. Failures
    are swallowed so analyze() always returns the rest of the report.
    """
    try:
        from .rsm import (
            fit_rsm, compute_model_adequacy, characterize_stationary_point,
        )
    except Exception:
        return None, None

    n = len(runs)
    k = len(factor_names)
    # Quadratic model has 1 + k + k*(k-1)/2 + k parameters.
    n_quad_params = 1 + 2 * k + k * (k - 1) // 2
    model_type = "quadratic" if n >= n_quad_params + 1 else "linear"

    try:
        model = fit_rsm(runs, responses, factor_names, factors, model_type=model_type)
    except Exception:
        return None, None

    run_order = [r.run_id for r in runs]
    try:
        adequacy = compute_model_adequacy(model, run_ids_in_order=run_order)
    except Exception:
        adequacy = None

    stationary = None
    if model_type == "quadratic":
        try:
            stationary = characterize_stationary_point(
                model, factor_names, factors,
            )
        except Exception:
            stationary = None

    return adequacy, stationary


def _compute_cross_validation_safe(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list[Factor],
    model_type: str,
    k_folds: int | None,
) -> CrossValidation | None:
    """Wrapper that swallows failures so analyze() always returns the rest."""
    try:
        from .rsm import compute_cross_validation
        return compute_cross_validation(
            runs=runs, responses=responses,
            factor_names=factor_names, factors=factors,
            model_type=model_type, k_folds=k_folds,
        )
    except Exception:
        return None


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
) -> dict[str, dict[str, dict[str, float | int]]]:
    stats: dict[str, dict[str, dict[str, float | int]]] = {}
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


def _compute_split_plot_anova(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list[Factor],
) -> AnovaTable:
    """Two-error-term ANOVA for split-plot designs.

    Whole-plot stratum: tests the hard-to-change (whole_plot) factor
    against between-whole-plot variation. Subplot stratum: tests every
    other factor (and HTC×subplot interactions) against within-whole-plot
    residual variation.

    The HTC factor F-test uses ``MS_whole_plot_error``, every other
    factor uses ``MS_subplot_error`` — pulling either out of the same
    pooled denominator (as the standard ANOVA path does) would give the
    HTC test more df than it actually has and inflate the false-positive
    rate.
    """
    try:
        from scipy.stats import f as f_dist
        _has_scipy = True
    except ImportError:
        _has_scipy = False

    valid_runs = [r for r in runs if r.run_id in responses]
    n = len(valid_runs)
    y = np.array([responses[r.run_id] for r in valid_runs])
    grand_mean = float(np.mean(y))
    ss_total = float(np.sum((y - grand_mean) ** 2))

    htc_factor = next((f for f in factors if f.role == "whole_plot"), None)
    if htc_factor is None:
        # Shouldn't happen — config validation prevents this — but degrade
        # gracefully to the standard pooled ANOVA.
        return _compute_anova(runs, responses, factor_names, factors)

    subplot_names = [f for f in factor_names if f != htc_factor.name]

    # Whole-plot SS = sum over whole plots of n_p * (mean_p - grand_mean)^2.
    by_plot: dict[int, list[float]] = {}
    plot_htc: dict[int, str] = {}
    for r in valid_runs:
        by_plot.setdefault(r.whole_plot_id, []).append(responses[r.run_id])
        plot_htc[r.whole_plot_id] = r.factor_values[htc_factor.name]
    plot_ids = sorted(by_plot.keys())
    plot_means = {pid: sum(vals) / len(vals) for pid, vals in by_plot.items()}
    ss_plots = sum(
        len(by_plot[pid]) * (plot_means[pid] - grand_mean) ** 2 for pid in plot_ids
    )
    df_plots = len(plot_ids) - 1

    # SS for the HTC factor (between HTC level means, weighted by run count).
    htc_levels = sorted({plot_htc[p] for p in plot_ids}, key=_numeric_sort_key)
    htc_means: dict[str, float] = {}
    for level in htc_levels:
        vals = [
            responses[r.run_id]
            for r in valid_runs if r.factor_values[htc_factor.name] == level
        ]
        htc_means[level] = sum(vals) / len(vals) if vals else grand_mean
    ss_htc = sum(
        sum(1 for r in valid_runs if r.factor_values[htc_factor.name] == lv)
        * (htc_means[lv] - grand_mean) ** 2
        for lv in htc_levels
    )
    df_htc = max(0, len(htc_levels) - 1)

    # Whole-plot error = between whole plots within an HTC level.
    ss_wp_error = max(0.0, ss_plots - ss_htc)
    df_wp_error = max(0, df_plots - df_htc)
    ms_wp_error = ss_wp_error / df_wp_error if df_wp_error > 0 else 0.0

    # Subplot stratum: every other factor, computed as in _compute_anova
    # using level means against the grand mean.
    rows: list[AnovaRow] = []
    if df_htc > 0:
        ms_htc = ss_htc / df_htc
        f_htc = ms_htc / ms_wp_error if ms_wp_error > 0 else None
        p_htc = None
        if f_htc is not None and _has_scipy and df_wp_error > 0:
            p_htc = float(f_dist.sf(f_htc, df_htc, df_wp_error))
        rows.append(AnovaRow(
            source=f"{htc_factor.name} (whole-plot)",
            df=df_htc, ss=ss_htc, ms=ms_htc,
            f_value=f_htc, p_value=p_htc,
        ))

    # Whole-plot error row, surfaced explicitly.
    rows.append(AnovaRow(
        source="Whole-Plot Error",
        df=df_wp_error, ss=ss_wp_error, ms=ms_wp_error,
    ))

    # Subplot main effects + HTC×subplot interactions
    ss_subplot_terms = 0.0
    for fname in subplot_names:
        levels = sorted({r.factor_values[fname] for r in valid_runs}, key=_numeric_sort_key)
        df_f = max(0, len(levels) - 1)
        ss_f = 0.0
        for lv in levels:
            vals = [responses[r.run_id]
                    for r in valid_runs if r.factor_values[fname] == lv]
            if vals:
                ss_f += len(vals) * (sum(vals) / len(vals) - grand_mean) ** 2
        ms_f = ss_f / df_f if df_f > 0 else 0.0
        ss_subplot_terms += ss_f
        rows.append(AnovaRow(
            source=fname, df=df_f, ss=ss_f, ms=ms_f,
        ))

    # HTC × each-subplot interaction
    for fname in subplot_names:
        if df_htc <= 0:
            continue
        levels_a = sorted({r.factor_values[htc_factor.name] for r in valid_runs}, key=_numeric_sort_key)
        levels_b = sorted({r.factor_values[fname] for r in valid_runs}, key=_numeric_sort_key)
        ss_ab_total = 0.0
        for la in levels_a:
            for lb in levels_b:
                cell = [responses[r.run_id] for r in valid_runs
                        if r.factor_values[htc_factor.name] == la
                        and r.factor_values[fname] == lb]
                if cell:
                    ss_ab_total += len(cell) * (sum(cell) / len(cell) - grand_mean) ** 2

        ss_a = sum(
            sum(1 for r in valid_runs if r.factor_values[htc_factor.name] == la)
            * (htc_means[la] - grand_mean) ** 2
            for la in levels_a
        )
        ss_b_levels = {}
        for lb in levels_b:
            vals = [responses[r.run_id]
                    for r in valid_runs if r.factor_values[fname] == lb]
            ss_b_levels[lb] = (
                len(vals) * (sum(vals) / len(vals) - grand_mean) ** 2 if vals else 0.0
            )
        ss_b = sum(ss_b_levels.values())

        ss_int = max(0.0, ss_ab_total - ss_a - ss_b)
        df_int = df_htc * max(0, len(levels_b) - 1)
        ms_int = ss_int / df_int if df_int > 0 else 0.0
        ss_subplot_terms += ss_int
        rows.append(AnovaRow(
            source=f"{htc_factor.name}*{fname}",
            df=df_int, ss=ss_int, ms=ms_int,
        ))

    # Subplot error = total residual after removing whole-plot stratum
    # plus subplot terms.
    ss_sp_error = max(0.0, ss_total - ss_plots - ss_subplot_terms)
    df_sp_error = max(0, n - 1 - df_plots - sum(r.df for r in rows[2:]))  # skip HTC + WP-error rows
    ms_sp_error = ss_sp_error / df_sp_error if df_sp_error > 0 else 0.0

    # F-tests for subplot terms
    if ms_sp_error > 0:
        for row in rows:
            if row.source in (f"{htc_factor.name} (whole-plot)", "Whole-Plot Error"):
                continue
            row.f_value = row.ms / ms_sp_error
            if _has_scipy and df_sp_error > 0:
                row.p_value = float(f_dist.sf(row.f_value, row.df, df_sp_error))

    error_row = AnovaRow(
        source="Subplot Error",
        df=df_sp_error, ss=ss_sp_error, ms=ms_sp_error,
    )
    total_row = AnovaRow(
        source="Total",
        df=n - 1, ss=ss_total, ms=ss_total / (n - 1) if n > 1 else 0.0,
    )

    return AnovaTable(
        rows=rows,
        error_row=error_row,
        total_row=total_row,
        error_method="split_plot",
    )


def _compute_anova(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list[Factor],
) -> AnovaTable:
    """Compute ANOVA table using Type I (sequential) SS decomposition.

    For unreplicated designs, uses Lenth's pseudo-standard-error to construct
    an error estimate from the median of absolute effects (same approach as
    R's FrF2 package).
    """

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

    # Detect replicates (runs with identical factor settings).
    # When the design has multiple blocks, a "pure-error replicate" must
    # match on BOTH block_id and factor settings — otherwise block-induced
    # variation contaminates the pure-error estimate.
    from collections import Counter
    from typing import Any
    has_blocks_for_replicates = len({r.block_id for r in valid_runs}) > 1
    setting_counts: Counter[tuple[Any, ...]] = Counter()
    setting_responses: dict[tuple[Any, ...], list[float]] = {}
    for run in valid_runs:
        if has_blocks_for_replicates:
            key = (run.block_id,) + tuple(run.factor_values[f] for f in factor_names)
        else:
            key = tuple(run.factor_values[f] for f in factor_names)
        setting_counts[key] += 1
        setting_responses.setdefault(key, []).append(responses[run.run_id])

    has_replicates = any(c > 1 for c in setting_counts.values())


    # Compute SS for each factor using Type I approach
    # Build X column by column, compute sequential SS
    anova_rows: list[AnovaRow] = []

    # Block effect: when the design was split into more than one block,
    # absorb that variance into its own ANOVA term so it doesn't leak
    # into the residual MS used as the F-test denominator.
    block_ids = sorted({r.block_id for r in valid_runs})
    ss_block = 0.0
    if len(block_ids) > 1:
        block_groups: dict[int, list[float]] = {}
        for run in valid_runs:
            block_groups.setdefault(run.block_id, []).append(responses[run.run_id])
        for vals in block_groups.values():
            if vals:
                block_mean = sum(vals) / len(vals)
                ss_block += len(vals) * (block_mean - grand_mean) ** 2
        df_block = len(block_ids) - 1
        ms_block = ss_block / df_block if df_block > 0 else 0.0
        anova_rows.append(AnovaRow(
            source="Block", df=df_block, ss=ss_block, ms=ms_block,
        ))

    # Identify factor levels for each factor
    factor_level_map: dict[str, list[str]] = {}
    for fname in factor_names:
        levels: set[str] = set()
        for run in valid_runs:
            levels.add(run.factor_values[fname])
        factor_level_map[fname] = sorted(levels)

    # Compute SS for each main effect factor. Start ss_model at the block
    # SS so the residual error is computed correctly when a block term
    # is present.
    ss_model = ss_block
    for fname in factor_names:
        level_list = factor_level_map[fname]
        df_factor = len(level_list) - 1

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
        combo_vals: dict[tuple[str, str], list[float]] = {}
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
        # F-tests of model terms use pure error as the denominator: keep
        # the headline Error row coherent with that choice.
        ms_error = ms_pure_error
        df_error = df_pure_error
        ss_error = ss_pure_error
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
    factors: list[Factor],
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
    factors: list[Factor],
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
    factors: list[Factor],
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

        def encode(fname: str, raw_val: np.ndarray) -> np.ndarray | float:
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
    diagnostics: ModelDiagnostics,
    output_path: str,
    title: str = "Model Diagnostics",
) -> None:
    """Generate a 2x2 diagnostic plot panel: residuals vs fitted, normal probability,
    residuals vs run order, and predicted vs actual."""
    import matplotlib.pyplot as plt
    from scipy.stats import probplot

    resid = diagnostics.residuals
    fitted = diagnostics.fitted_values
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

    if report.alias_structure is not None:
        alias_path = os.path.join(output_dir, "alias_structure.csv")
        with open(alias_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["effect_kind", "effect", "aliased_with", "abs_correlation"])
            for entry in report.alias_structure.main_effects:
                if not entry.aliased_with:
                    writer.writerow(["main", entry.effect, "", ""])
                    continue
                for partner, corr in entry.aliased_with:
                    writer.writerow(["main", entry.effect, partner, f"{corr:.6f}"])
            for entry in report.alias_structure.two_factor_interactions:
                if not entry.aliased_with:
                    continue
                for partner, corr in entry.aliased_with:
                    writer.writerow(["two_factor", entry.effect, partner, f"{corr:.6f}"])
        created.append(alias_path)

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

        # Model adequacy CSV (one row per response that has it)
        if analysis.model_adequacy:
            ma = analysis.model_adequacy
            adequacy_path = os.path.join(output_dir, f"model_adequacy_{safe}.csv")
            with open(adequacy_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "value"])
                writer.writerow(["model_type", ma.model_type])
                writer.writerow(["n_observations", ma.n_observations])
                writer.writerow(["n_parameters", ma.n_parameters])
                writer.writerow(["r_squared", ma.r_squared])
                writer.writerow(["adj_r_squared", ma.adj_r_squared])
                writer.writerow(["predicted_r_squared", ma.predicted_r_squared])
                writer.writerow(["press", ma.press])
                writer.writerow(["shapiro_w", ma.shapiro_w if ma.shapiro_w is not None else ""])
                writer.writerow(["shapiro_p", ma.shapiro_p if ma.shapiro_p is not None else ""])
                writer.writerow(["durbin_watson", ma.durbin_watson if ma.durbin_watson is not None else ""])
                writer.writerow(["runorder_drift_slope", ma.runorder_drift_slope if ma.runorder_drift_slope is not None else ""])
                writer.writerow(["runorder_drift_p", ma.runorder_drift_p if ma.runorder_drift_p is not None else ""])
                writer.writerow(["max_leverage", ma.max_leverage])
                writer.writerow(["leverage_threshold", ma.leverage_threshold])
                writer.writerow(["high_leverage_run_ids", ";".join(str(r) for r in ma.high_leverage_run_ids)])
                writer.writerow(["max_cooks_distance", ma.max_cooks_distance])
                writer.writerow(["cooks_threshold", ma.cooks_threshold])
                writer.writerow(["high_influence_run_ids", ";".join(str(r) for r in ma.high_influence_run_ids)])
            created.append(adequacy_path)

        # Achieved-power CSV
        if analysis.achieved_power:
            from .models import AchievedPower
            ap: AchievedPower = analysis.achieved_power
            ap_path = os.path.join(output_dir, f"achieved_power_{safe}.csv")
            with open(ap_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["scope", "factor", "n_levels", "power_at_delta", "mde_at_target"])
                writer.writerow(["__summary__", "", "", "", ""])
                writer.writerow(["n_runs", "", "", ap.n_runs, ""])
                writer.writerow(["df_error", "", "", ap.df_error, ""])
                writer.writerow(["sigma", "", "", ap.sigma, ""])
                writer.writerow(["residual_ms", "", "", ap.residual_ms, ""])
                writer.writerow(["alpha", "", "", ap.alpha, ""])
                writer.writerow(["delta", "", "", ap.delta, ""])
                writer.writerow(["target_power", "", "", ap.target_power, ""])
                for power_entry in ap.per_factor:
                    mde = power_entry.mde_at_target if power_entry.mde_at_target != float("inf") else ""
                    writer.writerow(["per_factor", power_entry.factor_name, power_entry.n_levels,
                                     power_entry.power_at_delta, mde])
            created.append(ap_path)

        # Cross-validation CSV: summary header + per-fold predicted-vs-actual
        if analysis.cross_validation:
            cv = analysis.cross_validation
            cv_path = os.path.join(output_dir, f"cross_validation_{safe}.csv")
            with open(cv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["scope", "fold", "run_id", "predicted", "actual", "absolute_error"])
                writer.writerow(["__summary__", "", "", "", "", ""])
                writer.writerow(["model_type", "", "", cv.model_type, "", ""])
                writer.writerow(["k", "", "", cv.k, "", ""])
                writer.writerow(["n_observations", "", "", cv.n_observations, "", ""])
                writer.writerow(["rmse_cv", "", "", cv.rmse, "", ""])
                writer.writerow(["mae_cv", "", "", cv.mae, "", ""])
                writer.writerow(["r_squared_cv", "", "", cv.r_squared_cv, "", ""])
                for fold in cv.folds:
                    for run_id, pred, actual in zip(
                        fold.held_out_run_ids, fold.predictions, fold.actuals,
                    ):
                        writer.writerow([
                            "fold", fold.fold_index, run_id, pred, actual,
                            abs(pred - actual),
                        ])
            created.append(cv_path)

        # Stationary point CSV
        if analysis.stationary_point:
            sp = analysis.stationary_point
            sp_path = os.path.join(output_dir, f"stationary_point_{safe}.csv")
            with open(sp_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "value"])
                writer.writerow(["nature", sp.nature])
                writer.writerow(["predicted_value", sp.predicted_value])
                writer.writerow(["inside_design_region", sp.inside_design_region])
                writer.writerow(["eigenvalues", ";".join(f"{v:.6g}" for v in sp.eigenvalues)])
                for fname in sp.factor_order:
                    writer.writerow([f"coded[{fname}]", sp.coded_location.get(fname, 0.0)])
                    writer.writerow([f"natural[{fname}]", sp.natural_location.get(fname, "")])
                if sp.ridge_direction:
                    for fname, v in sp.ridge_direction.items():
                        writer.writerow([f"ridge_axis[{fname}]", v])
            created.append(sp_path)

    return created
