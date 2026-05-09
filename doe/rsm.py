# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Response Surface Modeling for DOE results."""

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from .models import (
    CrossValidation, CrossValidationFold,
    DesignMatrix, DOEConfig, ExperimentRun, Factor,
    ModelAdequacy, StationaryPoint,
)


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


def _format_factor_value(factor, decoded_value: float) -> str:
    """Format a decoded numeric value for the factor.

    Honors ``factor.dtype == 'int'`` by rounding to the nearest integer
    and clamping to the original level range (or whatever min/max the
    user supplied). Continuous factors fall back to ``%.6g`` formatting,
    matching the long-standing behaviour for non-integer factors.
    """
    dtype = (getattr(factor, "dtype", "") or "").lower()
    if dtype == "int":
        try:
            low = int(round(float(factor.levels[0])))
            high = int(round(float(factor.levels[-1])))
        except (TypeError, ValueError, IndexError):
            low, high = None, None
        rounded = int(round(decoded_value))
        if low is not None and high is not None:
            lo, hi = (low, high) if low <= high else (high, low)
            rounded = max(lo, min(hi, rounded))
        return str(rounded)
    return f"{decoded_value:.6g}"


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
                optimal_settings[fname] = _format_factor_value(
                    factor, center + coded_val * half_range,
                )
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


def compute_model_adequacy(
    model: RSMModel,
    run_ids_in_order: list[int] | None = None,
) -> ModelAdequacy | None:
    """Compute post-fit adequacy statistics for a fitted RSM.

    Parameters
    ----------
    model : RSMModel
        The fitted model. ``model.diagnostics`` must already contain
        residuals, fitted values, leverages and the PRESS statistic
        (populated by ``fit_rsm``).
    run_ids_in_order : list[int] | None
        Run IDs in physical execution order. When provided, used to
        align residuals so the Durbin-Watson and run-order-drift stats
        reflect time order rather than the order they happen to sit in
        ``model.diagnostics``.
    """
    diag = model.diagnostics
    if diag is None or not diag.residuals:
        return None

    n = len(diag.residuals)
    p = len(model.coefficients)
    if n <= p:
        return None  # no degrees of freedom to compute meaningful stats

    # Optionally reorder residuals by physical run order so DW reflects
    # autocorrelation along execution time rather than diagnostic ordering.
    resid_arr = np.array(diag.residuals, dtype=float)
    leverages = np.array(diag.hat_matrix_diag, dtype=float)
    diag_run_ids = list(diag.run_ids) if diag.run_ids else list(range(n))
    if run_ids_in_order:
        position = {rid: i for i, rid in enumerate(diag_run_ids)}
        order_idx = [position[r] for r in run_ids_in_order if r in position]
        if len(order_idx) == n:
            resid_ordered = resid_arr[order_idx]
        else:
            resid_ordered = resid_arr
    else:
        resid_ordered = resid_arr

    notes: list[str] = []
    sse = float(np.sum(resid_arr ** 2))
    mse = sse / (n - p)

    # Durbin-Watson on time-ordered residuals
    if n >= 2 and sse > 0:
        diffs = np.diff(resid_ordered)
        dw = float(np.sum(diffs ** 2) / np.sum(resid_ordered ** 2)) if np.sum(resid_ordered ** 2) > 0 else None
    else:
        dw = None

    # Run-order drift: regress residuals against time index
    drift_slope = None
    drift_p = None
    if n >= 4 and np.std(resid_ordered) > 0:
        try:
            from scipy import stats as _stats
            t = np.arange(n, dtype=float)
            res = _stats.linregress(t, resid_ordered)
            drift_slope = float(res.slope)
            drift_p = float(res.pvalue)
        except Exception:
            pass

    # Shapiro-Wilk on raw residuals
    shapiro_w = None
    shapiro_p = None
    if 3 <= n <= 5000 and np.std(resid_arr) > 0:
        try:
            from scipy import stats as _stats
            w_stat, w_p = _stats.shapiro(resid_arr)
            shapiro_w = float(w_stat)
            shapiro_p = float(w_p)
        except Exception:
            pass

    # Leverage flags: rule of thumb is h_i > 2*p/n
    leverage_threshold = 2.0 * p / n
    high_leverage = [
        diag_run_ids[i] for i, h in enumerate(leverages) if h > leverage_threshold
    ]

    # Cook's distance: D_i = (e_i^2 / (p * MSE)) * (h_i / (1 - h_i)^2)
    cooks: list[float] = []
    if mse > 0:
        for e, h in zip(resid_arr, leverages):
            denom = (1.0 - h) ** 2
            if denom > 0:
                d = (e ** 2 / (p * mse)) * (h / denom)
            else:
                d = float("inf")
            cooks.append(float(d))
    else:
        cooks = [0.0] * n
        notes.append("Residual MS is zero; Cook's distance not meaningful.")

    # F-distribution threshold: F(0.5, p, n-p). This is the well-known
    # "possibly influential" cutoff (Cook & Weisberg) and stays sensible
    # on small designs where the 4/n rule of thumb flags most points.
    # Falls back to 4/n only when scipy's F-distribution isn't usable.
    df_resid = n - p
    cooks_threshold = 4.0 / n
    if df_resid >= 1:
        try:
            from scipy.stats import f as _f
            cooks_threshold = float(_f.ppf(0.5, p, df_resid))
        except Exception:
            pass
    high_influence = [
        diag_run_ids[i] for i, d in enumerate(cooks) if d > cooks_threshold
    ]

    if dw is not None and (dw < 1.0 or dw > 3.0):
        notes.append(
            f"Durbin-Watson {dw:.2f} is far from 2.0; check for run-order autocorrelation."
        )
    if drift_p is not None and drift_p < 0.05:
        notes.append(
            f"Residuals trend with run order (p={drift_p:.3f}); "
            "the experiment may have drifted in time."
        )
    if shapiro_p is not None and shapiro_p < 0.05:
        notes.append(
            f"Residuals fail Shapiro-Wilk normality (p={shapiro_p:.3f})."
        )
    if model.diagnostics is not None and model.diagnostics.predicted_r_squared < model.r_squared - 0.2:
        notes.append(
            "Predicted R² is much lower than R² — model may be over-fit."
        )

    return ModelAdequacy(
        model_type="quadratic" if any("^2" in k or "*" in k for k in model.coefficients) else "linear",
        n_observations=n,
        n_parameters=p,
        r_squared=model.r_squared,
        adj_r_squared=model.adj_r_squared,
        predicted_r_squared=model.diagnostics.predicted_r_squared,
        press=model.diagnostics.press,
        shapiro_w=shapiro_w,
        shapiro_p=shapiro_p,
        durbin_watson=dw,
        runorder_drift_slope=drift_slope,
        runorder_drift_p=drift_p,
        max_leverage=float(np.max(leverages)) if len(leverages) else 0.0,
        leverage_threshold=float(leverage_threshold),
        high_leverage_run_ids=high_leverage,
        max_cooks_distance=float(max(cooks)) if cooks else 0.0,
        cooks_threshold=float(cooks_threshold),
        high_influence_run_ids=high_influence,
        notes=notes,
    )


def compute_cross_validation(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list,
    model_type: str = "linear",
    k_folds: int | None = None,
    seed: int | None = None,
) -> CrossValidation | None:
    """k-fold cross-validation for the same RSM that ``analyze`` fits.

    Each fold trains on (n - n/k) runs and predicts the held-out runs.
    Aggregated RMSE / MAE / R²_cv plus the per-fold predicted-vs-actual
    table go into the returned ``CrossValidation`` so downstream surfaces
    (printout, HTML, CSV) can render them.

    Returns ``None`` if there isn't enough data for at least 2 folds with
    1+ training observation each. ``k_folds=None`` chooses ``min(n, 5)``;
    pass ``k_folds=n`` for true leave-one-out (which usually matches the
    PRESS-based predicted_r_squared up to numeric noise).
    """
    valid_runs = [r for r in runs if r.run_id in responses]
    n = len(valid_runs)
    if n < 4:
        return None

    if k_folds is None:
        k_folds = min(n, 5)
    k_folds = max(2, min(k_folds, n))

    # Trial fit just to discover the parameter count and bail out if the
    # design can't support the requested model on a *training* subset.
    full_model = fit_rsm(valid_runs, responses, factor_names, factors,
                         model_type=model_type)
    n_params = len(full_model.coefficients)
    # Each fold trains on roughly (k-1)/k of n. Need at least n_params + 1.
    min_train = n - (n // k_folds + (1 if n % k_folds else 0))
    if min_train <= n_params:
        return CrossValidation(
            model_type=model_type, k=k_folds, n_observations=n,
            rmse=float("nan"), mae=float("nan"), r_squared_cv=float("nan"),
            notes=[
                f"Skipped: training fold size {min_train} <= parameters {n_params}. "
                "Use --no-rsm or supply more runs."
            ],
        )

    rng = _np.random.default_rng(seed)
    indices = _np.arange(n)
    rng.shuffle(indices)
    fold_assignments = _np.array_split(indices, k_folds)

    grand_mean = float(_np.mean([responses[r.run_id] for r in valid_runs]))
    ss_total = float(_np.sum(
        (_np.array([responses[r.run_id] for r in valid_runs]) - grand_mean) ** 2
    ))

    fold_records: list[CrossValidationFold] = []
    pred_errs_squared = 0.0
    abs_errs_total = 0.0
    n_predicted = 0
    for fold_idx, holdout_idx in enumerate(fold_assignments):
        train_runs = [valid_runs[i] for i in indices if i not in set(holdout_idx)]
        test_runs = [valid_runs[i] for i in holdout_idx]
        if not train_runs or not test_runs:
            continue
        try:
            train_model = fit_rsm(train_runs, responses, factor_names, factors,
                                   model_type=model_type)
        except Exception:
            continue
        # Predict each test run via the model's prediction in coded space.
        coefs = train_model.coefficients
        preds: list[float] = []
        actuals: list[float] = []
        held_ids: list[int] = []
        for run in test_runs:
            x = _np.array([
                _encode_factor_value(run.factor_values[f], _factor_lookup(factors)[f])
                for f in factor_names
            ])
            pred = coefs.get("intercept", 0.0)
            for i, fname in enumerate(factor_names):
                pred += coefs.get(fname, 0.0) * x[i]
            if model_type == "quadratic":
                for i, fi in enumerate(factor_names):
                    for j in range(i + 1, len(factor_names)):
                        fj = factor_names[j]
                        cross_key = coefs.get(f"{fi}*{fj}",
                                              coefs.get(f"{fj}*{fi}", 0.0))
                        pred += cross_key * x[i] * x[j]
                    pred += coefs.get(f"{fi}^2", 0.0) * x[i] ** 2
            actual = float(responses[run.run_id])
            preds.append(float(pred))
            actuals.append(actual)
            held_ids.append(run.run_id)
            err = pred - actual
            pred_errs_squared += err * err
            abs_errs_total += abs(err)
            n_predicted += 1
        fold_records.append(CrossValidationFold(
            fold_index=fold_idx,
            held_out_run_ids=held_ids,
            predictions=preds,
            actuals=actuals,
        ))

    if n_predicted == 0:
        return None
    rmse = float(_np.sqrt(pred_errs_squared / n_predicted))
    mae = abs_errs_total / n_predicted
    r_squared_cv = 1.0 - pred_errs_squared / ss_total if ss_total > 0 else 0.0

    return CrossValidation(
        model_type=model_type,
        k=k_folds,
        n_observations=n,
        rmse=rmse,
        mae=mae,
        r_squared_cv=float(r_squared_cv),
        folds=fold_records,
    )


def _factor_lookup(factors: list) -> dict:
    return {f.name: f for f in factors}


# numpy already imported at module top
_np = np


def characterize_stationary_point(
    model: RSMModel,
    factor_names: list[str],
    factors: list,
    ridge_tolerance: float = 0.05,
) -> StationaryPoint | None:
    """Classify the stationary point of a fitted quadratic RSM.

    The fit is taken in coded space (each factor in [-1, 1]). The
    stationary point x* satisfies ∇y(x*) = 0; its nature is decided by
    the eigenvalues of the Hessian H of the quadratic form.

    Returns ``None`` if the model has no quadratic terms (so no
    characterization is possible).
    """
    coefs = model.coefficients
    n = len(factor_names)
    if n == 0:
        return None

    # Hessian: H_ii = 2 * coef of x_i^2;  H_ij = coef of x_i*x_j  (i!=j)
    H = np.zeros((n, n), dtype=float)
    has_quadratic_term = False
    for i, fi in enumerate(factor_names):
        sq = coefs.get(f"{fi}^2")
        if sq is not None:
            H[i, i] = 2.0 * sq
            has_quadratic_term = True
        for j in range(i + 1, n):
            fj = factor_names[j]
            cross = coefs.get(f"{fi}*{fj}")
            if cross is None:
                cross = coefs.get(f"{fj}*{fi}")
            if cross is not None:
                H[i, j] = float(cross)
                H[j, i] = float(cross)
                has_quadratic_term = True
    if not has_quadratic_term:
        return None

    b = np.array([coefs.get(fname, 0.0) for fname in factor_names], dtype=float)

    # Solve H x* = -b. Use pseudo-inverse so a flat / ridge direction
    # produces the minimum-norm stationary point along the well-defined axes.
    try:
        x_star = -np.linalg.pinv(H) @ b
    except np.linalg.LinAlgError:
        return None

    # Predicted value at x*: y0 + b·x* + 0.5 x*ᵀ H x*
    y0 = coefs.get("intercept", 0.0)
    y_star = float(y0 + b @ x_star + 0.5 * x_star @ H @ x_star)

    eigvals, eigvecs = np.linalg.eigh(H)  # H is symmetric, eigvals real & sorted ascending
    eigvals = np.real(eigvals)

    max_abs = float(np.max(np.abs(eigvals))) if eigvals.size else 0.0
    if max_abs == 0:
        return StationaryPoint(
            nature="flat",
            coded_location={f: 0.0 for f in factor_names},
            natural_location=_decode_settings({f: 0.0 for f in factor_names}, factor_names, factors),
            predicted_value=y_star,
            eigenvalues=[0.0] * n,
            eigenvectors=eigvecs.tolist(),
            factor_order=list(factor_names),
            inside_design_region=True,
            ridge_direction=None,
        )

    # Threshold for "near-zero" eigenvalue → ridge.
    near_zero = np.abs(eigvals) < ridge_tolerance * max_abs
    pos = (eigvals > 0) & ~near_zero
    neg = (eigvals < 0) & ~near_zero

    ridge_direction = None
    if near_zero.any():
        # Pick the eigenvector with the smallest |λ| as the ridge axis.
        idx = int(np.argmin(np.abs(eigvals)))
        ridge_vec = eigvecs[:, idx]
        ridge_direction = {fname: float(ridge_vec[i]) for i, fname in enumerate(factor_names)}
        if pos.any() and not neg.any():
            nature = "ridge"  # min along well-defined axes, indeterminate elsewhere
        elif neg.any() and not pos.any():
            nature = "rising_ridge"
        else:
            nature = "saddle"
    else:
        if pos.all():
            nature = "minimum"
        elif neg.all():
            nature = "maximum"
        else:
            nature = "saddle"

    coded_location = {fname: float(x_star[i]) for i, fname in enumerate(factor_names)}
    inside = bool(np.all(np.abs(x_star) <= 1.0 + 1e-9))

    return StationaryPoint(
        nature=nature,
        coded_location=coded_location,
        natural_location=_decode_settings(coded_location, factor_names, factors),
        predicted_value=y_star,
        eigenvalues=[float(v) for v in eigvals],
        eigenvectors=eigvecs.T.tolist(),  # row i is eigenvector i, aligned with eigvals[i]
        factor_order=list(factor_names),
        inside_design_region=inside,
        ridge_direction=ridge_direction,
    )


def _decode_settings(
    coded: dict[str, float],
    factor_names: list[str],
    factors: list,
) -> dict[str, str]:
    """Convert coded-space coordinates [-1, 1] back to natural factor units."""
    factor_map = {f.name: f for f in factors}
    out: dict[str, str] = {}
    for fname in factor_names:
        factor = factor_map.get(fname)
        coded_val = coded.get(fname, 0.0)
        if factor is None:
            out[fname] = f"{coded_val:.4f}"
            continue
        if factor.type in ("continuous", "ordinal"):
            try:
                low = float(factor.levels[0])
                high = float(factor.levels[1])
                center = (low + high) / 2.0
                half_range = (high - low) / 2.0
                out[fname] = _format_factor_value(
                    factor, center + coded_val * half_range,
                )
            except (ValueError, IndexError):
                out[fname] = f"{coded_val:.4f}"
        else:
            sorted_levels = sorted(factor.levels)
            if len(sorted_levels) == 2:
                out[fname] = sorted_levels[1] if coded_val > 0 else sorted_levels[0]
            else:
                # Multi-level categorical: snap to nearest index
                center = (len(sorted_levels) - 1) / 2.0
                half_range = (len(sorted_levels) - 1) / 2.0
                if half_range == 0:
                    out[fname] = sorted_levels[0]
                else:
                    idx = int(round(center + coded_val * half_range))
                    idx = max(0, min(len(sorted_levels) - 1, idx))
                    out[fname] = sorted_levels[idx]
    return out


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
                    settings[fname] = _format_factor_value(
                        factor, center + coded_val * half_range,
                    )
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
