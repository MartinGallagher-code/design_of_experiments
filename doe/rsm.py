"""Response Surface Modeling for DOE results."""

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from .models import DesignMatrix, DOEConfig, ExperimentRun


@dataclass
class RSMModel:
    response_name: str
    coefficients: dict[str, float]  # {"intercept": ..., "A": ..., "B": ..., "A*B": ..., "A^2": ...}
    r_squared: float
    adj_r_squared: float
    predicted_optimum: dict[str, str]  # factor_name -> level_value
    predicted_value: float


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

    return RSMModel(
        response_name="",
        coefficients=coefficients,
        r_squared=r_squared,
        adj_r_squared=adj_r_squared,
        predicted_optimum=predicted_optimum,
        predicted_value=predicted_value,
    )
