"""Optimization recommendations from DOE results."""

from .models import DesignMatrix, DOEConfig
from .analysis import _load_all_results, _compute_main_effects
from .rsm import fit_rsm


def recommend(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    response_name: str | None = None,
    partial: bool = False,
) -> None:
    """Print optimization recommendations based on DOE results.

    For each response (or the specified one):
    1. Best observed run
    2. RSM linear model fit with coefficients and R-squared
    3. Factor importance ranking
    """
    results_dir = results_dir or cfg.out_directory or "results"
    all_data = _load_all_results(matrix.runs, results_dir, partial=partial)

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

        # 2. RSM prediction — linear
        rsm_linear = fit_rsm(
            valid_runs, responses, matrix.factor_names, cfg.factors,
            model_type="linear",
        )
        rsm_linear.response_name = resp.name

        print(f"RSM Model (linear, R² = {rsm_linear.r_squared:.4f}, Adj R² = {rsm_linear.adj_r_squared:.4f}):")
        print("  Coefficients:")
        for name, coef in rsm_linear.coefficients.items():
            sign = "+" if coef >= 0 else ""
            print(f"    {name:30s} {sign}{coef:.4f}")
        print()

        # 3. RSM prediction — quadratic (if enough data points)
        n_factors = len(matrix.factor_names)
        n_quad_terms = 1 + n_factors + n_factors * (n_factors - 1) // 2 + n_factors
        rsm_quad = None
        if len(valid_runs) >= n_quad_terms + 1:
            try:
                rsm_quad = fit_rsm(
                    valid_runs, responses, matrix.factor_names, cfg.factors,
                    model_type="quadratic",
                )
                rsm_quad.response_name = resp.name

                print(f"RSM Model (quadratic, R² = {rsm_quad.r_squared:.4f}, Adj R² = {rsm_quad.adj_r_squared:.4f}):")
                print("  Coefficients:")
                for name, coef in rsm_quad.coefficients.items():
                    sign = "+" if coef >= 0 else ""
                    print(f"    {name:30s} {sign}{coef:.4f}")
                print()

                # Curvature analysis
                quad_terms = {k: v for k, v in rsm_quad.coefficients.items() if "^2" in k}
                if quad_terms:
                    print("  Curvature analysis:")
                    for term, coef in sorted(quad_terms.items(), key=lambda x: abs(x[1]), reverse=True):
                        factor = term.replace("^2", "")
                        if abs(coef) < 0.1:
                            shape = "negligible curvature"
                        elif coef < 0:
                            shape = "concave (has a maximum)"
                        else:
                            shape = "convex (has a minimum)"
                        print(f"    {factor:30s} coef={coef:+.4f}  {shape}")
                    print()

                # Interaction analysis
                ix_terms = {k: v for k, v in rsm_quad.coefficients.items() if "*" in k}
                if ix_terms:
                    sig_ix = {k: v for k, v in ix_terms.items() if abs(v) > 0.3}
                    if sig_ix:
                        print("  Notable interactions:")
                        for term, coef in sorted(sig_ix.items(), key=lambda x: abs(x[1]), reverse=True):
                            synergy = "synergistic" if coef > 0 else "antagonistic"
                            print(f"    {term:30s} coef={coef:+.4f}  ({synergy})")
                        print()

            except Exception:
                pass  # quadratic fit failed (e.g. singular matrix)

        # Pick best model for optimum prediction
        best_model = rsm_quad if (rsm_quad and rsm_quad.adj_r_squared > rsm_linear.adj_r_squared) else rsm_linear
        model_label = "quadratic" if best_model is rsm_quad else "linear"

        print(f"  Predicted optimum (from {model_label} model):")
        for fname, val in best_model.predicted_optimum.items():
            print(f"    {fname} = {val}")
        print(f"    Predicted value: {best_model.predicted_value:.4f}")
        print()

        # Model quality assessment
        r2 = best_model.r_squared
        if r2 > 0.9:
            quality = "Excellent fit — surface predictions are reliable."
        elif r2 > 0.7:
            quality = "Good fit — general trends are captured, some noise remains."
        elif r2 > 0.5:
            quality = "Moderate fit — use predictions directionally, not precisely."
        else:
            quality = "Weak fit — consider adding center points or using a different design."
        print(f"  Model quality: {quality}")
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
