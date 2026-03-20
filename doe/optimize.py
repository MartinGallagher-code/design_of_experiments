"""Optimization recommendations from DOE results."""

from .models import DesignMatrix, DOEConfig
from .analysis import _load_all_results, _compute_main_effects
from .rsm import fit_rsm


def recommend(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    response_name: str | None = None,
) -> None:
    """Print optimization recommendations based on DOE results.

    For each response (or the specified one):
    1. Best observed run
    2. RSM linear model fit with coefficients and R-squared
    3. Factor importance ranking
    """
    results_dir = results_dir or cfg.out_directory or "results"
    all_data = _load_all_results(matrix.runs, results_dir)

    target_responses = cfg.responses
    if response_name:
        target_responses = [r for r in cfg.responses if r.name == response_name]
        if not target_responses:
            print(f"Error: response '{response_name}' not found in config.")
            return

    for resp in target_responses:
        # Collect response values
        responses: dict[int, float] = {}
        for run in matrix.runs:
            data = all_data.get(run.run_id, {})
            if resp.name in data:
                responses[run.run_id] = float(data[resp.name])

        if not responses:
            print(f"Warning: no data found for response '{resp.name}', skipping.")
            continue

        direction = resp.optimize  # "maximize" or "minimize"
        print(f"=== Optimization: {resp.name} ===")
        print(f"Direction: {direction}")
        print()

        # 1. Best observed run
        valid_runs = [r for r in matrix.runs if r.run_id in responses]
        if direction == "minimize":
            best_run = min(valid_runs, key=lambda r: responses[r.run_id])
        else:
            best_run = max(valid_runs, key=lambda r: responses[r.run_id])

        print(f"Best observed run: #{best_run.run_id}")
        for fname in matrix.factor_names:
            print(f"  {fname} = {best_run.factor_values[fname]}")
        print(f"  Value: {responses[best_run.run_id]}")
        print()

        # 2. RSM prediction
        rsm_model = fit_rsm(
            valid_runs,
            responses,
            matrix.factor_names,
            cfg.factors,
            model_type="linear",
        )
        rsm_model.response_name = resp.name

        print(f"RSM Model (linear, R² = {rsm_model.r_squared:.2f}):")
        print("  Coefficients:")
        for name, coef in rsm_model.coefficients.items():
            sign = "+" if coef >= 0 else ""
            print(f"    {name}:  {sign}{coef:.4f}")

        print("  Predicted optimum:")
        for fname, val in rsm_model.predicted_optimum.items():
            print(f"    {fname} = {val}")
        print(f"    Predicted value: {rsm_model.predicted_value:.4f}")
        print()

        # 3. Factor importance ranking
        effects = _compute_main_effects(valid_runs, responses, matrix.factor_names)
        total_abs = sum(abs(e.main_effect) for e in effects) or 1.0

        print("Factor importance:")
        for i, e in enumerate(effects, 1):
            contribution = abs(e.main_effect) / total_abs * 100
            print(
                f"  {i}. {e.factor_name}  "
                f"(effect: {e.main_effect:.1f}, contribution: {contribution:.1f}%)"
            )
        print()
