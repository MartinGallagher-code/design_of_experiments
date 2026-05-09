# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Minimal Gaussian-process surrogate + Expected-Improvement acquisition.

Self-contained Bayesian-optimization helpers used by the ``bayesian``
adaptive strategy. Stays on numpy + scipy (already required) — no
sklearn dependency.

Pipeline:
1. Standardise observations to zero mean / unit variance.
2. Fit an isotropic RBF kernel ``k(x, x') = σ_f² · exp(-||x - x'||² / (2 ℓ²))``
   plus a homoscedastic noise term ``σ_n² · I``. Hyperparameters
   ``(log ℓ, log σ_f, log σ_n)`` are chosen by maximising the log
   marginal likelihood with ``scipy.optimize.minimize`` (L-BFGS-B).
3. Predict mean and variance at any query point in the same standardised
   space.
4. Pick the next query point by maximising Expected Improvement under
   the standard Gaussian formula. For batches, use the *Constant Liar*
   strategy: after the first pick, fantasise its response = current best
   and re-fit cheaply.

This is a working, well-defined BO loop — limited to the cases where
RBF + isotropic length scale is a reasonable choice. For radically
different scales between factors, consider scaling the inputs to
``[-1, 1]`` first (which we do automatically in the adaptive driver).
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class GPModel:
    """Fitted GP. ``X_train`` and ``y_train`` are kept in standardised space."""
    X_train: np.ndarray             # (n, d), standardised inputs in [-1, 1]
    y_train: np.ndarray             # (n,), standardised outputs (zero mean, unit var)
    log_length_scale: float
    log_signal_var: float
    log_noise_var: float
    y_mean: float
    y_std: float
    L: np.ndarray                   # cholesky of K + σ_n²I
    alpha: np.ndarray               # K_inv @ y_train


def fit_gp(
    X: np.ndarray,
    y: np.ndarray,
    seed: int | None = None,
) -> GPModel:
    """Fit an RBF GP via marginal-likelihood maximisation."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).ravel()
    n, d = X.shape
    if n < 2:
        raise ValueError("Need at least 2 observations to fit a GP.")

    y_mean = float(np.mean(y))
    y_std = float(np.std(y, ddof=0))
    if y_std == 0:
        y_std = 1.0  # constant data — degenerate but proceed
    y_norm = (y - y_mean) / y_std

    rng = np.random.default_rng(seed)

    def neg_log_marginal(theta):
        log_l, log_sf, log_sn = theta
        K = _rbf_kernel(X, X, np.exp(log_l), np.exp(log_sf))
        K += np.exp(log_sn) ** 2 * np.eye(n)
        try:
            L = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            return 1e12
        alpha = np.linalg.solve(L.T, np.linalg.solve(L, y_norm))
        nll = 0.5 * y_norm @ alpha + np.sum(np.log(np.diag(L))) + 0.5 * n * np.log(2 * np.pi)
        return float(nll)

    # Multi-start so the optimiser doesn't get stuck on tiny n
    best = (None, np.inf)
    starts = [
        np.array([0.0, 0.0, np.log(0.1)]),    # ℓ=1, σ_f=1, σ_n=0.1
        np.array([np.log(2.0), 0.0, np.log(0.05)]),
        np.array([np.log(0.5), 0.0, np.log(0.2)]),
    ]
    starts.extend(rng.normal(0.0, 0.5, size=(3, 3)) for _ in range(3))
    for x0 in starts:
        try:
            from scipy.optimize import minimize
            result = minimize(
                neg_log_marginal, x0, method="L-BFGS-B",
                bounds=[(-4.0, 4.0), (-4.0, 4.0), (-6.0, 2.0)],
            )
            if result.fun < best[1]:
                best = (result.x, result.fun)
        except Exception:
            continue

    if best[0] is None:
        # Fallback: reasonable defaults
        theta = np.array([0.0, 0.0, np.log(0.1)])
    else:
        theta = best[0]
    log_l, log_sf, log_sn = theta
    K = _rbf_kernel(X, X, np.exp(log_l), np.exp(log_sf))
    K += np.exp(log_sn) ** 2 * np.eye(n)
    L = np.linalg.cholesky(K)
    alpha = np.linalg.solve(L.T, np.linalg.solve(L, y_norm))

    return GPModel(
        X_train=X.copy(), y_train=y_norm.copy(),
        log_length_scale=float(log_l),
        log_signal_var=float(log_sf),
        log_noise_var=float(log_sn),
        y_mean=y_mean, y_std=y_std,
        L=L, alpha=alpha,
    )


def predict(gp: GPModel, X_star: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Posterior mean and variance at ``X_star`` (in original response units)."""
    X_star = np.asarray(X_star, dtype=float)
    if X_star.ndim == 1:
        X_star = X_star.reshape(1, -1)
    length = np.exp(gp.log_length_scale)
    sf = np.exp(gp.log_signal_var)
    sn = np.exp(gp.log_noise_var)

    K_s = _rbf_kernel(X_star, gp.X_train, length, sf)
    mean_norm = K_s @ gp.alpha
    v = np.linalg.solve(gp.L, K_s.T)
    var_norm = sf ** 2 - np.sum(v ** 2, axis=0) + sn ** 2
    var_norm = np.maximum(var_norm, 1e-10)

    mean = mean_norm * gp.y_std + gp.y_mean
    var = var_norm * (gp.y_std ** 2)
    return mean, var


def expected_improvement(
    gp: GPModel,
    X_star: np.ndarray,
    best_y: float,
    direction: str = "maximize",
    xi: float = 0.0,
) -> np.ndarray:
    """Standard EI under a Gaussian posterior.

    For maximisation::
        EI(x) = (μ(x) - best - xi) · Φ(z) + σ(x) · φ(z)
    with z = (μ(x) - best - xi) / σ(x) and ``best`` the incumbent.
    """
    mean, var = predict(gp, X_star)
    sigma = np.sqrt(var)
    if direction == "minimize":
        improvement = best_y - mean - xi
    else:
        improvement = mean - best_y - xi
    z = np.where(sigma > 1e-9, improvement / sigma, 0.0)
    from scipy.stats import norm
    ei = improvement * norm.cdf(z) + sigma * norm.pdf(z)
    return np.maximum(ei, 0.0)


def propose_batch(
    gp: GPModel,
    bounds: np.ndarray,             # (d, 2) — [-1, 1] in each coded dim
    batch_size: int,
    direction: str = "maximize",
    n_candidates: int = 2000,
    seed: int | None = None,
) -> np.ndarray:
    """Pick ``batch_size`` next points using EI + constant-liar fantasising.

    Random candidate set inside ``bounds`` is scored by EI; the highest-EI
    point is selected, the GP is refit with the fantasy ``y = best``, and
    the loop repeats until the batch is filled.
    """
    rng = np.random.default_rng(seed)
    d = gp.X_train.shape[1]
    candidates = rng.uniform(
        low=bounds[:, 0], high=bounds[:, 1], size=(n_candidates, d),
    )
    chosen: list[np.ndarray] = []

    # We work in standardised y-space; use the standardised incumbent.
    if direction == "minimize":
        best_norm = float(np.min(gp.y_train))
    else:
        best_norm = float(np.max(gp.y_train))
    best_orig = best_norm * gp.y_std + gp.y_mean

    current_gp = gp
    for _ in range(batch_size):
        ei = expected_improvement(
            current_gp, candidates, best_orig, direction=direction,
        )
        # Penalise candidates close to already-chosen points so the batch
        # doesn't collapse to a tight cluster.
        for c in chosen:
            dists = np.linalg.norm(candidates - c, axis=1)
            ei = ei * (1.0 - np.exp(-(dists ** 2) / 0.04))
        if not np.any(ei > 0):
            # Fallback to maximum predictive variance
            _, var = predict(current_gp, candidates)
            idx = int(np.argmax(var))
        else:
            idx = int(np.argmax(ei))
        chosen.append(candidates[idx].copy())

        # Constant-liar refit: append fantasy observation = incumbent
        X_new = np.vstack([current_gp.X_train, candidates[idx][None, :]])
        y_new_norm = np.append(current_gp.y_train, best_norm)
        y_new = y_new_norm * current_gp.y_std + current_gp.y_mean
        try:
            current_gp = fit_gp(X_new, y_new, seed=seed)
        except Exception:
            # If the refit fails (e.g. duplicate points), keep going with
            # the current GP — EI will naturally be small at the duplicate.
            pass

    return np.vstack(chosen)


def _rbf_kernel(A: np.ndarray, B: np.ndarray, length: float, signal: float) -> np.ndarray:
    """Isotropic RBF kernel ``signal² · exp(-||a - b||² / (2 length²))``."""
    A = np.atleast_2d(A)
    B = np.atleast_2d(B)
    diff = A[:, None, :] - B[None, :, :]
    sq = np.sum(diff ** 2, axis=2)
    return (signal ** 2) * np.exp(-0.5 * sq / (length ** 2))
