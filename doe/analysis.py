import csv
import json
import math
import os
from .models import AnalysisReport, DesignMatrix, DOEConfig, EffectResult, ExperimentRun, InteractionEffect, ResponseAnalysis


def analyze(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    no_plots: bool = False,
    pareto_threshold: float = 80,
    partial: bool = False,
) -> AnalysisReport:
    results_dir = results_dir or cfg.out_directory or "results"
    processed_dir = cfg.processed_directory or results_dir

    all_data = _load_all_results(matrix.runs, results_dir, partial=partial)

    results_by_response: dict[str, ResponseAnalysis] = {}
    pareto_chart_paths: dict[str, str] = {}
    effects_plot_paths: dict[str, str] = {}

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
        effects = _compute_main_effects(valid_runs, responses, matrix.factor_names)
        interactions = _compute_interaction_effects(valid_runs, responses, matrix.factor_names)
        summary_stats = _compute_summary_stats(valid_runs, responses, matrix.factor_names)

        results_by_response[resp.name] = ResponseAnalysis(
            response_name=resp.name,
            effects=effects,
            summary_stats=summary_stats,
            interactions=interactions,
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
                plot_main_effects(valid_runs, responses, matrix.factor_names, effects_path, ylabel=ylabel)
                effects_plot_paths[resp.name] = effects_path

                # RSM surface plots for designs with continuous factors
                rsm_paths = plot_rsm_surface(
                    valid_runs, responses, cfg.factors, matrix.factor_names,
                    resp.name, processed_dir, response_unit=resp.unit,
                )
                for p in rsm_paths:
                    print(f"  RSM surface: {os.path.basename(p)}")

            except ImportError:
                print("Warning: matplotlib not available; skipping plots.")

    return AnalysisReport(
        results_by_response=results_by_response,
        pareto_chart_paths=pareto_chart_paths,
        effects_plot_paths=effects_plot_paths,
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
            result_data[run.run_id] = json.load(f)

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

        levels = sorted(level_responses.keys())
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
        levels_a = sorted(factor_levels[fa])
        levels_b = sorted(factor_levels[fb])

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
        for level, vals in sorted(level_responses.items()):
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

        levels = sorted(level_responses.keys())
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
                for level, s in sorted(levels.items()):
                    writer.writerow([factor, level, s["n"], s["mean"], s["std"], s["min"], s["max"]])
        created.append(stats_path)

    return created
