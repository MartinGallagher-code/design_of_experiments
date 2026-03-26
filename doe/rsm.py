"""Response Surface Modeling for DOE results."""

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from .models import DesignMatrix, DOEConfig, ExperimentRun, Factor


@dataclass
class ModelDiagnostics:
    residuals: list[float]
    fitted_values: list[float]
    hat_matrix_diag: list[float]  # leverage values
    press: float  # PRESS statistic
    predicted_r_squared: float
    run_ids: list[int] = field(default_factory=list)


@dataclass
class RSMModel:
    response_name: str
    coefficients: dict[str, float]  # {"intercept": ..., "A": ..., "B": ..., "A*B": ..., "A^2": ...}
    r_squared: float
    adj_r_squared: float
    predicted_optimum: dict[str, str]  # factor_name -> level_value
    predicted_value: float
    diagnostics: ModelDiagnostics | None = None


def _encode_factor_value(value: str, factor) -> float:
    """Encode a factor value as a numeric value for regression.

    - For continuous/ordinal factors: normalize as (value - center) / half_range
    - For categorical factors with 2 levels: encode as -1/+1
    - For categorical factors with >2 levels: encode as index (fallback)
    """
    levels = factor.levels
    if factor.type in ("continuous", "ordinal"):
        try:
            numeric_vals = [float(lv) for lv in levels]
            val = float(value)
            center = (max(numeric_vals) + min(numeric_vals)) / 2.0
            half_range = (max(numeric_vals) - min(numeric_vals)) / 2.0
            if half_range == 0:
                return 0.0
            return (val - center) / half_range
        except ValueError:
            pass

    # Categorical encoding
    sorted_levels = sorted(levels)
    if len(sorted_levels) == 2:
        return -1.0 if value == sorted_levels[0] else 1.0
    else:
        # Multi-level categorical: use index-based encoding centered around 0
        idx = sorted_levels.index(value) if value in sorted_levels else 0
        center = (len(sorted_levels) - 1) / 2.0
        half_range = (len(sorted_levels) - 1) / 2.0
        if half_range == 0:
            return 0.0
        return (idx - center) / half_range


def _build_design_matrix(
    runs: list[ExperimentRun],
    factor_names: list[str],
    factors: list,
    model_type: str = "linear",
) -> tuple[np.ndarray, list[str]]:
    """Build the design matrix X and return column names.

    For "linear": columns are [1, x1, x2, ...]
    For "quadratic": columns are [1, x1, x2, ..., x1*x2, ..., x1^2, x2^2, ...]
    """
    factor_map = {f.name: f for f in factors}
    n_runs = len(runs)
    n_factors = len(factor_names)

    # Encode raw factor values
    raw = np.zeros((n_runs, n_factors))
    for i, run in enumerate(runs):
        for j, fname in enumerate(factor_names):
            raw[i, j] = _encode_factor_value(
                run.factor_values[fname], factor_map[fname]
            )

    col_names = ["intercept"] + list(factor_names)
    X = np.column_stack([np.ones(n_runs), raw])

    if model_type == "quadratic":
        # Interaction terms
        for a, b in combinations(range(n_factors), 2):
            col_names.append(f"{factor_names[a]}*{factor_names[b]}")
            X = np.column_stack([X, raw[:, a] * raw[:, b]])
        # Squared terms
        for j in range(n_factors):
            col_names.append(f"{factor_names[j]}^2")
            X = np.column_stack([X, raw[:, j] ** 2])

    return X, col_names


def fit_rsm(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list,  # list of Factor objects
    model_type: str = "linear",  # "linear" or "quadratic"
) -> RSMModel:
    """Fit a polynomial regression model to DOE results.

    Parameters
    ----------
    runs : list of ExperimentRun
        The experiment runs (only those with response data).
    responses : dict mapping run_id -> response value
    factor_names : ordered list of factor names
    factors : list of Factor objects (for encoding info)
    model_type : "linear" or "quadratic"

    Returns
    -------
    RSMModel with coefficients, R-squared, and predicted optimum.
    """
    # Filter to runs that have response data
    valid_runs = [r for r in runs if r.run_id in responses]
    if not valid_runs:
        return RSMModel(
            response_name="",
            coefficients={"intercept": 0.0},
            r_squared=0.0,
            adj_r_squared=0.0,
            predicted_optimum={},
            predicted_value=0.0,
        )

    X, col_names = _build_design_matrix(valid_runs, factor_names, factors, model_type)
    y = np.array([responses[r.run_id] for r in valid_runs])

    # Least-squares fit
    beta, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)

    # Predictions and R-squared
    y_pred = X @ beta
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    n = len(y)
    p = len(beta) - 1  # number of predictors (excluding intercept)
    if n - p - 1 > 0 and ss_tot > 0:
        adj_r_squared = 1.0 - (ss_res / (n - p - 1)) / (ss_tot / (n - 1))
    else:
        adj_r_squared = r_squared

    # Build coefficients dict
    coefficients = {col_names[i]: float(beta[i]) for i in range(len(beta))}

    # Find predicted optimum: evaluate all observed factor combinations
    best_idx = int(np.argmax(y_pred))
    best_run = valid_runs[best_idx]
    predicted_optimum = {fname: best_run.factor_values[fname] for fname in factor_names}
    predicted_value = float(y_pred[best_idx])

    # Model diagnostics: hat matrix, leverage, PRESS
    diagnostics = None
    try:
        XtX_inv = np.linalg.pinv(X.T @ X)
        H = X @ XtX_inv @ X.T
        h_diag = np.diag(H)
        resid = y - y_pred

        # PRESS: leave-one-out via algebraic shortcut
        press_residuals = resid / (1.0 - h_diag + 1e-12)
        press = float(np.sum(press_residuals ** 2))
        predicted_r_squared = 1.0 - press / ss_tot if ss_tot > 0 else 0.0

        diagnostics = ModelDiagnostics(
            residuals=[float(r) for r in resid],
            fitted_values=[float(f) for f in y_pred],
            hat_matrix_diag=[float(h) for h in h_diag],
            press=press,
            predicted_r_squared=predicted_r_squared,
            run_ids=[r.run_id for r in valid_runs],
        )
    except Exception:
        pass  # graceful fallback if diagnostics fail

    return RSMModel(
        response_name="",
        coefficients=coefficients,
        r_squared=r_squared,
        adj_r_squared=adj_r_squared,
        predicted_optimum=predicted_optimum,
        predicted_value=predicted_value,
        diagnostics=diagnostics,
    )


def optimize_surface(
    model: RSMModel,
    factor_names: list[str],
    factors: list,
    direction: str = "maximize",
    n_restarts: int = 10,
) -> dict:
    """Find the true optimum of a fitted RSM surface using scipy.optimize.

    Uses L-BFGS-B with multiple random restarts to avoid local optima.
    Operates in coded space [-1, 1] then decodes to natural units.

    Returns dict with 'optimal_settings', 'predicted_value', 'converged'.
    """
    from scipy.optimize import minimize as scipy_minimize

    coefs = model.coefficients
    n_factors = len(factor_names)

    def predict_coded(x_coded):
        """Evaluate the polynomial at coded values."""
        val = coefs.get("intercept", 0.0)
        for i, fname in enumerate(factor_names):
            val += coefs.get(fname, 0.0) * x_coded[i]
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                key = f"{factor_names[i]}*{factor_names[j]}"
                val += coefs.get(key, 0.0) * x_coded[i] * x_coded[j]
            key = f"{factor_names[i]}^2"
            val += coefs.get(key, 0.0) * x_coded[i] ** 2
        return val

    def objective(x_coded):
        val = predict_coded(x_coded)
        return -val if direction == "maximize" else val

    bounds = [(-1.0, 1.0)] * n_factors
    rng = np.random.default_rng(42)

    best_result = None
    best_obj = float('inf')

    for _ in range(n_restarts):
        x0 = rng.uniform(-1, 1, size=n_factors)
        try:
            result = scipy_minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
            if result.fun < best_obj:
                best_obj = result.fun
                best_result = result
        except Exception:
            continue

    if best_result is None:
        return {"optimal_settings": {}, "predicted_value": 0.0, "converged": False}

    # Decode coded values back to natural units
    factor_map = {f.name: f for f in factors}
    optimal_settings = {}
    for i, fname in enumerate(factor_names):
        factor = factor_map[fname]
        coded_val = best_result.x[i]
        if factor.type in ("continuous", "ordinal"):
            try:
                low = float(factor.levels[0])
                high = float(factor.levels[1])
                center = (low + high) / 2.0
                half_range = (high - low) / 2.0
                optimal_settings[fname] = f"{center + coded_val * half_range:.6g}"
            except ValueError:
                optimal_settings[fname] = f"{coded_val:.4f}"
        else:
            optimal_settings[fname] = factor.levels[1] if coded_val > 0 else factor.levels[0]

    predicted_value = predict_coded(best_result.x)

    return {
        "optimal_settings": optimal_settings,
        "predicted_value": float(predicted_value),
        "converged": bool(best_result.success),
    }


def steepest_ascent(
    model: RSMModel,
    factor_names: list[str],
    factors: list,
    direction: str = "maximize",
    n_steps: int = 10,
) -> list[dict]:
    """Generate a steepest ascent/descent pathway from a linear RSM model.

    The gradient in coded space is the vector of linear coefficients.
    Returns a list of dicts, each with factor settings at that step.
    """
    coefs = model.coefficients
    factor_map = {f.name: f for f in factors}

    # Gradient = linear coefficients
    gradient = np.array([coefs.get(fname, 0.0) for fname in factor_names])
    if direction == "minimize":
        gradient = -gradient

    # Normalize so the largest step equals 1 coded unit
    max_grad = np.max(np.abs(gradient))
    if max_grad == 0:
        return []
    step_vector = gradient / max_grad

    pathway = []
    for step in range(n_steps + 1):
        coded_point = step_vector * step * 0.5  # 0.5 coded units per step
        settings = {}
        predicted = coefs.get("intercept", 0.0)
        for i, fname in enumerate(factor_names):
            factor = factor_map[fname]
            coded_val = coded_point[i]
            predicted += coefs.get(fname, 0.0) * coded_val

            # Decode to natural units
            if factor.type in ("continuous", "ordinal"):
                try:
                    low = float(factor.levels[0])
                    high = float(factor.levels[1])
                    center = (low + high) / 2.0
                    half_range = (high - low) / 2.0
                    settings[fname] = f"{center + coded_val * half_range:.6g}"
                except ValueError:
                    settings[fname] = f"{coded_val:.4f}"
            else:
                settings[fname] = factor.levels[1] if coded_val > 0 else factor.levels[0]

        pathway.append({
            "step": step,
            "settings": settings,
            "predicted_value": float(predicted),
        })

    return pathway
