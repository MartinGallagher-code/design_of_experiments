import json
import math
import os
from .models import AnalysisReport, DesignMatrix, DOEConfig, EffectResult, ExperimentRun


def analyze(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
) -> AnalysisReport:
    results_dir = results_dir or cfg.out_directory or "results"
    responses = _load_results(matrix.runs, results_dir)

    effects = _compute_main_effects(matrix.runs, responses, matrix.factor_names)
    summary_stats = _compute_summary_stats(matrix.runs, responses, matrix.factor_names)

    processed_dir = cfg.processed_directory or results_dir
    os.makedirs(processed_dir, exist_ok=True)

    pareto_path = None
    effects_path = None

    try:
        import matplotlib
        matplotlib.use("Agg")

        pareto_path = os.path.join(processed_dir, "pareto_chart.png")
        plot_pareto(effects, pareto_path)

        effects_path = os.path.join(processed_dir, "main_effects.png")
        plot_main_effects(matrix.runs, responses, matrix.factor_names, effects_path)
    except ImportError:
        print("Warning: matplotlib not available; skipping plots.")

    return AnalysisReport(
        effects=effects,
        summary_stats=summary_stats,
        pareto_chart_path=pareto_path,
        effects_plot_path=effects_path,
    )


def _load_results(runs: list[ExperimentRun], results_dir: str) -> dict[int, float]:
    responses = {}
    missing = []
    for run in runs:
        path = os.path.join(results_dir, f"run_{run.run_id}.json")
        if not os.path.exists(path):
            missing.append(run.run_id)
            continue
        with open(path) as f:
            data = json.load(f)
        if "response" not in data:
            raise ValueError(f"run_{run.run_id}.json is missing 'response' key.")
        responses[run.run_id] = float(data["response"])

    if missing:
        raise FileNotFoundError(
            f"Missing result files for run IDs: {missing}. "
            f"Expected in: {results_dir}"
        )
    return responses


def _compute_main_effects(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
) -> list[EffectResult]:
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
            grand_mean = sum(responses.values()) / len(responses)
            all_means = [
                sum(vals) / len(vals) for vals in level_responses.values()
            ]
            effect = max(all_means) - min(all_means)

        # std error across all responses for this factor
        all_vals = [v for vals in level_responses.values() for v in vals]
        n = len(all_vals)
        mean = sum(all_vals) / n
        variance = sum((v - mean) ** 2 for v in all_vals) / max(n - 1, 1)
        std_error = math.sqrt(variance / n)

        effects.append(EffectResult(
            factor_name=factor_name,
            main_effect=effect,
            std_error=std_error,
            pct_contribution=0.0,  # filled in below
        ))

    total_abs = sum(abs(e.main_effect) for e in effects) or 1.0
    for e in effects:
        e.pct_contribution = abs(e.main_effect) / total_abs * 100

    return sorted(effects, key=lambda e: abs(e.main_effect), reverse=True)


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


def plot_pareto(effects: list[EffectResult], output_path: str) -> None:
    import matplotlib.pyplot as plt

    sorted_effects = sorted(effects, key=lambda e: abs(e.main_effect), reverse=True)
    names = [e.factor_name for e in sorted_effects]
    values = [abs(e.main_effect) for e in sorted_effects]
    total = sum(values) or 1.0
    cumulative = [sum(values[:i+1]) / total * 100 for i in range(len(values))]

    fig, ax1 = plt.subplots(figsize=(max(6, len(names) * 1.2), 5))
    ax1.barh(names[::-1], values[::-1], color="steelblue")
    ax1.set_xlabel("Absolute Main Effect")
    ax1.set_title("Pareto Chart of Main Effects")

    ax2 = ax1.twiny()
    ax2.plot(cumulative[::-1], range(len(names)), "o-", color="red", markersize=4)
    ax2.axvline(80, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
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
        ax.set_ylabel("Mean Response")
        ax.grid(True, alpha=0.3)

    # hide unused axes
    for idx in range(n, rows * cols):
        axes[idx // cols][idx % cols].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
