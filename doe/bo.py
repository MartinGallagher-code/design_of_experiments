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
import numpy.typing as npt


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
    noise_per_point: np.ndarray | None = None,
) -> GPModel:
    """Fit an RBF GP via marginal-likelihood maximisation.

    Parameters
    ----------
    X, y
        Inputs and outputs.
    seed
        RNG seed for the multi-start in hyperparameter optimisation.
    noise_per_point
        Optional per-point variance. When provided, each diagonal entry
        of ``K`` becomes ``σ_n² + var_i`` and the marginal likelihood is
        maximised over the *floor* ``σ_n²`` only — i.e., the user-supplied
        variance accounts for known measurement scatter (e.g., from
        replicates) and ``σ_n²`` absorbs any residual jitter.
    """
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

    if noise_per_point is not None:
        noise_per_point = np.asarray(noise_per_point, dtype=float).ravel()
        if noise_per_point.shape != (n,):
            raise ValueError(
                f"noise_per_point shape {noise_per_point.shape} != ({n},)"
            )
        # Standardise the supplied variance to the same y-scale used for fitting.
        diag_noise = noise_per_point / (y_std ** 2)
    else:
        diag_noise = np.zeros(n)

    rng = np.random.default_rng(seed)

    def neg_log_marginal(theta: npt.NDArray[np.float64]) -> float:
        log_l, log_sf, log_sn = theta
        K = _rbf_kernel(X, X, np.exp(log_l), np.exp(log_sf))
        # Diagonal noise: per-point known + a homoscedastic floor.
        K = K + np.diag(diag_noise) + (np.exp(log_sn) ** 2) * np.eye(n)
        try:
            L = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            return 1e12
        alpha = np.linalg.solve(L.T, np.linalg.solve(L, y_norm))
        nll = 0.5 * y_norm @ alpha + np.sum(np.log(np.diag(L))) + 0.5 * n * np.log(2 * np.pi)
        return float(nll)

    # Multi-start so the optimiser doesn't get stuck on tiny n
    best: tuple[npt.NDArray[np.float64] | None, float] = (None, np.inf)
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
    K = K + np.diag(diag_noise) + (np.exp(log_sn) ** 2) * np.eye(n)
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


def is_pareto_front(Y: np.ndarray, directions: list[str]) -> np.ndarray:
    """Boolean mask of Pareto-optimal rows for a (n, m) objective matrix.

    A row is Pareto-optimal iff no other row dominates it. Domination is
    decided per-objective using ``directions[k] in {'maximize','minimize'}``.
    """
    Y = np.atleast_2d(Y)
    n, m = Y.shape
    if len(directions) != m:
        raise ValueError(
            f"directions has length {len(directions)} but Y has {m} columns"
        )
    # Flip minimisation columns so we can treat everything as maximisation.
    Y_max = Y.copy()
    for k, d in enumerate(directions):
        if d == "minimize":
            Y_max[:, k] = -Y_max[:, k]

    on_front = np.ones(n, dtype=bool)
    for i in range(n):
        if not on_front[i]:  # pragma: no cover - defensive; only index i is
            continue         # ever cleared, so this is always still True here
        diffs = Y_max - Y_max[i]
        # j dominates i iff every coord >= and at least one >
        dominated_by_j = np.all(diffs >= 0, axis=1) & np.any(diffs > 0, axis=1)
        if np.any(dominated_by_j):
            on_front[i] = False
    return on_front


def propose_batch_multi_objective(
    gps: list[GPModel],
    bounds: np.ndarray,
    batch_size: int,
    directions: list[str],
    n_candidates: int = 2000,
    n_scalarizations: int = 16,
    seed: int | None = None,
) -> np.ndarray:
    """Pick a batch via random Tchebycheff scalarisation across objectives.

    For each batch member:
      1. Draw a random weight vector ``w`` from a (m-1)-simplex.
      2. Reward each candidate by its EI under
         ``T(x) = max_k w_k · normalised_improvement_k(x)``.
      3. Pick the highest-EI candidate, fantasise its objective vector at the
         current Pareto-incumbent values, and refit each GP for the next pick.
    Same same-batch repulsion logic as ``propose_batch``.
    """
    if not gps:
        raise ValueError("Need at least one GP for multi-objective batching.")
    if len(gps) != len(directions):
        raise ValueError("len(gps) must equal len(directions)")
    rng = np.random.default_rng(seed)
    d = gps[0].X_train.shape[1]
    candidates = rng.uniform(
        low=bounds[:, 0], high=bounds[:, 1], size=(n_candidates, d),
    )
    chosen: list[np.ndarray] = []
    current_gps = list(gps)

    # Pre-compute per-objective scaling so weights act on comparable units.
    obj_scales: list[float] = []
    for gp in current_gps:
        scale = max(gp.y_std, 1e-9)
        obj_scales.append(scale)

    for _ in range(batch_size):
        # Posterior μ and σ for every objective at every candidate.
        means = []
        sigmas = []
        for gp in current_gps:
            mean, var = predict(gp, candidates)
            means.append(mean)
            sigmas.append(np.sqrt(np.maximum(var, 1e-12)))
        means = np.column_stack(means)
        sigmas = np.column_stack(sigmas)

        # Per-objective incumbent (best so far in the GP's own training set).
        incumbents = []
        for k, gp in enumerate(current_gps):
            best_norm = (
                float(np.min(gp.y_train)) if directions[k] == "minimize"
                else float(np.max(gp.y_train))
            )
            incumbents.append(best_norm * gp.y_std + gp.y_mean)
        incumbents = np.asarray(incumbents)

        # Random Tchebycheff scalarisations
        m = len(current_gps)
        weights = rng.dirichlet(alpha=np.ones(m), size=n_scalarizations)
        ei_per_scalarization = np.zeros((n_scalarizations, n_candidates))
        for s_idx, w in enumerate(weights):
            # Per-objective improvement (positive when better than incumbent)
            improvements = np.zeros_like(means)
            for k in range(m):
                if directions[k] == "minimize":
                    improvements[:, k] = (incumbents[k] - means[:, k]) / obj_scales[k]
                else:
                    improvements[:, k] = (means[:, k] - incumbents[k]) / obj_scales[k]
            # Weighted improvement; Tchebycheff = min over weighted gain
            weighted = improvements * w[None, :]
            tcheby = np.min(weighted, axis=1)
            # Treat tcheby as the improvement metric for an EI-like score:
            # use a Gaussian approximation with σ scaled by weight too.
            sigma_eff = np.sqrt(np.sum((sigmas / np.array(obj_scales)) ** 2 * (w[None, :] ** 2), axis=1))
            sigma_eff = np.maximum(sigma_eff, 1e-9)
            z = tcheby / sigma_eff
            from scipy.stats import norm
            ei = tcheby * norm.cdf(z) + sigma_eff * norm.pdf(z)
            ei_per_scalarization[s_idx] = np.maximum(ei, 0.0)

        ei_score = ei_per_scalarization.mean(axis=0)
        for c in chosen:
            dists = np.linalg.norm(candidates - c, axis=1)
            ei_score = ei_score * (1.0 - np.exp(-(dists ** 2) / 0.04))

        if not np.any(ei_score > 0):
            idx = int(np.argmax(np.linalg.norm(candidates - candidates.mean(axis=0), axis=1)))
        else:
            idx = int(np.argmax(ei_score))
        chosen.append(candidates[idx].copy())

        # Constant-liar refit: append fantasy at incumbent for every objective.
        for k, gp in enumerate(current_gps):
            X_new = np.vstack([gp.X_train, candidates[idx][None, :]])
            best_norm = (
                float(np.min(gp.y_train)) if directions[k] == "minimize"
                else float(np.max(gp.y_train))
            )
            y_new_norm = np.append(gp.y_train, best_norm)
            y_new = y_new_norm * gp.y_std + gp.y_mean
            try:
                current_gps[k] = fit_gp(X_new, y_new, seed=seed)
            except Exception:
                pass

    return np.vstack(chosen)
