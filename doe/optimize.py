"""Optimization recommendations from DOE results."""

from itertools import combinations

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


def multi_objective(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    results_dir: str | None = None,
    partial: bool = False,
) -> None:
    """Multi-objective optimization using Derringer-Suich desirability functions.

    For each response, computes an individual desirability d_i in [0, 1].
    Combines them into an overall desirability D via weighted geometric mean.
    Finds the factor settings that maximize D.
    """
    import numpy as np
    from .rsm import _encode_factor_value

    results_dir = results_dir or cfg.out_directory or "results"
    all_data = _load_all_results(matrix.runs, results_dir, partial=partial)

    if len(cfg.responses) < 2:
        print("Multi-objective optimization requires at least 2 responses.")
        print("Use 'doe optimize' without --multi for single-response optimization.")
        return

    # Collect all response data and fit RSM models
    response_data = {}  # resp_name -> {run_id: value}
    rsm_models = {}     # resp_name -> RSMModel
    valid_runs_all = None

    for resp in cfg.responses:
        responses = {}
        for run in matrix.runs:
            data = all_data.get(run.run_id, {})
            if resp.name in data:
                responses[run.run_id] = float(data[resp.name])

        if not responses:
            print(f"Warning: no data for response '{resp.name}', skipping.")
            continue

        response_data[resp.name] = responses
        valid_runs = [r for r in matrix.runs if r.run_id in responses]

        if valid_runs_all is None:
            valid_runs_all = set(r.run_id for r in valid_runs)
        else:
            valid_runs_all &= set(r.run_id for r in valid_runs)

        # Fit best RSM model
        n_factors = len(matrix.factor_names)
        n_quad_terms = 1 + n_factors + n_factors * (n_factors - 1) // 2 + n_factors

        rsm = fit_rsm(valid_runs, responses, matrix.factor_names, cfg.factors, model_type="linear")

        if len(valid_runs) >= n_quad_terms + 1:
            try:
                rsm_quad = fit_rsm(valid_runs, responses, matrix.factor_names, cfg.factors, model_type="quadratic")
                if rsm_quad.adj_r_squared > rsm.adj_r_squared:
                    rsm = rsm_quad
            except Exception:
                pass

        rsm.response_name = resp.name
        rsm_models[resp.name] = rsm

    if len(response_data) < 2:
        print("Not enough responses with data for multi-objective optimization.")
        return

    # Only use runs that have data for ALL responses
    common_runs = [r for r in matrix.runs if r.run_id in valid_runs_all]

    # Compute desirability bounds for each response
    resp_bounds = {}
    for resp in cfg.responses:
        if resp.name not in response_data:
            continue
        values = list(response_data[resp.name].values())
        if resp.bounds:
            low, high = resp.bounds[0], resp.bounds[1]
        else:
            # Auto-compute from observed data with 5% margin
            low = min(values)
            high = max(values)
            margin = (high - low) * 0.05
            low -= margin
            high += margin
        resp_bounds[resp.name] = (low, high)

    # Individual desirability function
    def _desirability(value, low, high, direction):
        """Compute individual desirability d in [0, 1]."""
        if high == low:
            return 1.0
        if direction == "maximize":
            if value <= low:
                return 0.0
            elif value >= high:
                return 1.0
            else:
                return (value - low) / (high - low)
        else:  # minimize
            if value >= high:
                return 0.0
            elif value <= low:
                return 1.0
            else:
                return (high - value) / (high - low)

    # Evaluate overall desirability for each observed run
    run_desirabilities = []
    for run in common_runs:
        individual_d = {}
        for resp in cfg.responses:
            if resp.name not in response_data:
                continue
            val = response_data[resp.name].get(run.run_id)
            if val is None:
                continue
            low, high = resp_bounds[resp.name]
            d = _desirability(val, low, high, resp.optimize)
            individual_d[resp.name] = d

        # Weighted geometric mean
        if individual_d:
            total_weight = sum(resp.weight for resp in cfg.responses if resp.name in individual_d)
            if total_weight > 0 and all(d > 0 for d in individual_d.values()):
                log_d = sum(
                    resp.weight * np.log(individual_d[resp.name])
                    for resp in cfg.responses
                    if resp.name in individual_d
                )
                overall_d = np.exp(log_d / total_weight)
            elif any(d == 0 for d in individual_d.values()):
                overall_d = 0.0
            else:
                overall_d = 0.0

            run_desirabilities.append((run, overall_d, individual_d))

    if not run_desirabilities:
        print("No runs with complete data for all responses.")
        return

    # Find best run by overall desirability
    run_desirabilities.sort(key=lambda x: x[1], reverse=True)
    best_run, best_D, best_individual = run_desirabilities[0]

    # Also try to find a better point using RSM models on a grid
    # Generate a grid of candidate points in coded space
    factor_map = {f.name: f for f in cfg.factors}

    # Build grid: for each factor, sample 11 points between its levels
    grid_points_per_factor = []
    for fname in matrix.factor_names:
        factor = factor_map[fname]
        if factor.type == "continuous":
            try:
                lo, hi = float(factor.levels[0]), float(factor.levels[-1])
                grid_points_per_factor.append(np.linspace(lo, hi, 11))
            except ValueError:
                grid_points_per_factor.append(np.array([float(l) for l in factor.levels]))
        else:
            grid_points_per_factor.append(np.array(factor.levels))

    # For manageable grid size, use meshgrid for <=3 factors, random sampling for more
    n_factors = len(matrix.factor_names)
    if n_factors <= 3:
        mesh = np.meshgrid(*grid_points_per_factor, indexing='ij')
        grid = np.column_stack([m.ravel() for m in mesh])
    else:
        # Latin hypercube-style random sampling
        n_samples = 5000
        grid = np.column_stack([
            np.random.choice(pts, size=n_samples) if pts.dtype.kind in ('U', 'S', 'O')
            else np.random.uniform(pts.min(), pts.max(), size=n_samples)
            for pts in grid_points_per_factor
        ])

    # Evaluate RSM predictions at each grid point
    best_grid_D = best_D
    best_grid_point = None
    best_grid_individual = None
    best_grid_predictions = None

    for i in range(len(grid)):
        point = grid[i]
        predictions = {}
        individual_d = {}

        all_valid = True
        for resp in cfg.responses:
            if resp.name not in rsm_models:
                all_valid = False
                break

            model = rsm_models[resp.name]
            # Build prediction from coefficients
            coded_vals = {}
            for j, fname in enumerate(matrix.factor_names):
                factor = factor_map[fname]
                val_str = str(point[j]) if not isinstance(point[j], str) else point[j]
                coded_vals[fname] = _encode_factor_value(val_str, factor)

            # Evaluate model
            pred = model.coefficients.get("intercept", 0.0)
            for fname in matrix.factor_names:
                pred += model.coefficients.get(fname, 0.0) * coded_vals[fname]
            # Interaction terms
            for a, b in combinations(matrix.factor_names, 2):
                key = f"{a}*{b}"
                pred += model.coefficients.get(key, 0.0) * coded_vals[a] * coded_vals[b]
            # Quadratic terms
            for fname in matrix.factor_names:
                key = f"{fname}^2"
                pred += model.coefficients.get(key, 0.0) * coded_vals[fname] ** 2

            predictions[resp.name] = pred
            low, high = resp_bounds[resp.name]
            d = _desirability(pred, low, high, resp.optimize)
            individual_d[resp.name] = d

        if not all_valid:
            continue

        # Overall desirability
        total_weight = sum(resp.weight for resp in cfg.responses if resp.name in individual_d)
        if total_weight > 0 and all(d > 0 for d in individual_d.values()):
            log_d = sum(
                resp.weight * np.log(individual_d[resp.name])
                for resp in cfg.responses
                if resp.name in individual_d
            )
            overall_d = np.exp(log_d / total_weight)
        else:
            overall_d = 0.0

        if overall_d > best_grid_D:
            best_grid_D = overall_d
            best_grid_point = point
            best_grid_individual = individual_d
            best_grid_predictions = predictions

    # Print results
    print("=" * 60)
    print("MULTI-OBJECTIVE OPTIMIZATION")
    print("Method: Derringer-Suich Desirability Function")
    print("=" * 60)
    print()

    # Use grid result if better, otherwise use best observed
    if best_grid_point is not None and best_grid_D > best_D:
        use_grid = True
        final_D = best_grid_D
        final_individual = best_grid_individual
        final_predictions = best_grid_predictions
    else:
        use_grid = False
        final_D = best_D
        final_individual = best_individual
        final_predictions = {
            resp.name: response_data[resp.name][best_run.run_id]
            for resp in cfg.responses
            if resp.name in response_data and best_run.run_id in response_data[resp.name]
        }

    print(f"Overall desirability: D = {final_D:.4f}")
    print()

    # Response table
    header = f"{'Response':<25} {'Weight':>6} {'Desirability':>12} {'Predicted':>12} {'Direction':>10}"
    print(header)
    print("-" * len(header))
    for resp in cfg.responses:
        if resp.name not in final_individual:
            continue
        d = final_individual[resp.name]
        pred = final_predictions.get(resp.name, 0.0)
        unit_str = f" {resp.unit}" if resp.unit else ""
        print(f"{resp.name:<25} {resp.weight:>6.1f} {d:>12.4f} {pred:>11.2f}{unit_str} {'↑' if resp.optimize == 'maximize' else '↓':>3}")
    print()

    # Recommended settings
    print("Recommended settings:")
    if use_grid:
        for j, fname in enumerate(matrix.factor_names):
            factor = factor_map[fname]
            val = best_grid_point[j]
            unit_str = f" {factor.unit}" if factor.unit else ""
            if factor.type == "continuous":
                print(f"  {fname} = {float(val):.4g}{unit_str}")
            else:
                print(f"  {fname} = {val}{unit_str}")
        print(f"  (from RSM model prediction)")
    else:
        for fname in matrix.factor_names:
            factor = factor_map[fname]
            unit_str = f" {factor.unit}" if factor.unit else ""
            print(f"  {fname} = {best_run.factor_values[fname]}{unit_str}")
        print(f"  (from observed run #{best_run.run_id})")
    print()

    # Trade-off summary
    print("Trade-off summary:")
    for resp in cfg.responses:
        if resp.name not in response_data:
            continue
        values = list(response_data[resp.name].values())
        pred = final_predictions.get(resp.name, 0.0)
        if resp.optimize == "maximize":
            best_obs = max(values)
            sacrifice = best_obs - pred
            print(f"  {resp.name}: {pred:.2f} (best observed: {best_obs:.2f}, sacrifice: {sacrifice:+.2f})")
        else:
            best_obs = min(values)
            sacrifice = pred - best_obs
            print(f"  {resp.name}: {pred:.2f} (best observed: {best_obs:.2f}, sacrifice: {sacrifice:+.2f})")
    print()

    # RSM model quality
    print("Model quality:")
    for resp in cfg.responses:
        if resp.name in rsm_models:
            m = rsm_models[resp.name]
            model_type = "quadratic" if any("^2" in k for k in m.coefficients) else "linear"
            print(f"  {resp.name}: R² = {m.r_squared:.4f} ({model_type})")
    print()

    # Top 3 runs by desirability
    print("Top 3 observed runs by overall desirability:")
    for rank, (run, d_val, ind_d) in enumerate(run_desirabilities[:3], 1):
        factors_str = ", ".join(f"{fn}={run.factor_values[fn]}" for fn in matrix.factor_names)
        print(f"  {rank}. Run #{run.run_id} (D={d_val:.4f}): {factors_str}")
