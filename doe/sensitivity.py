# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Variance-based sensitivity analysis (Sobol indices).

Reuses the quadratic RSM that ``analyze`` already fits as the surrogate;
samples Saltelli's design over the surrogate to estimate first-order and
total-order Sobol indices. This complements the existing ANOVA's
``% contribution`` column — ANOVA partitions the *observed* response
variance over discrete factor levels, while Sobol indices partition the
*surrogate* response variance over the continuous factor space.

Saltelli's algorithm uses two N×k input matrices A and B drawn from a
quasi-random low-discrepancy sequence (Sobol sequence) and constructs
N(k+2) model evaluations. We use ``scipy.stats.qmc.Sobol`` (already a
dependency).
"""

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


@dataclass
class SobolIndex:
    factor_name: str
    first_order: float        # S_i: fraction of variance from this factor alone
    total_order: float        # S_T_i: includes interactions involving this factor
    interaction_share: float  # max(0, S_T_i - S_i)


@dataclass
class SensitivityResult:
    response_name: str
    n_base_samples: int       # N (the per-matrix sample count)
    n_evaluations: int        # N * (k + 2)
    indices: list[SobolIndex] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def sobol_indices(
    predictor,
    factor_names: list[str],
    bounds: list[tuple[float, float]],
    response_name: str = "",
    n_base_samples: int = 256,
    seed: int | None = None,
) -> SensitivityResult:
    """Compute first-order and total-order Sobol indices for ``predictor``.

    Parameters
    ----------
    predictor
        Callable ``f(X)`` mapping an ``(m, k)`` numpy array of factor
        values to an ``(m,)`` array of response values. The factor
        ordering must match ``factor_names``.
    factor_names
        Ordered factor names — purely for the report.
    bounds
        ``(low, high)`` tuples per factor. The Sobol sequence is rescaled
        from ``[0, 1]`` into these bounds.
    n_base_samples
        ``N`` in Saltelli's notation. Total evaluations = ``N (k + 2)``.
    """
    k = len(factor_names)
    if k != len(bounds):
        raise ValueError("factor_names and bounds must have equal length")
    if k == 0:
        return SensitivityResult(
            response_name=response_name,
            n_base_samples=n_base_samples, n_evaluations=0,
            notes=["No factors to analyse."],
        )

    bounds_arr = np.asarray(bounds, dtype=float)
    rng_seed = 0 if seed is None else int(seed)

    # Two Sobol matrices A, B in [0, 1]^k, scaled into the factor bounds.
    try:
        from scipy.stats.qmc import Sobol
    except Exception:
        return SensitivityResult(
            response_name=response_name,
            n_base_samples=n_base_samples, n_evaluations=0,
            notes=["scipy.stats.qmc.Sobol not available; skipped."],
        )

    sampler = Sobol(d=2 * k, scramble=True, seed=rng_seed)
    raw = sampler.random(n=n_base_samples)
    A = raw[:, :k]
    B = raw[:, k:]
    # Scale into bounds
    A_scaled = bounds_arr[:, 0] + A * (bounds_arr[:, 1] - bounds_arr[:, 0])
    B_scaled = bounds_arr[:, 0] + B * (bounds_arr[:, 1] - bounds_arr[:, 0])

    # Evaluate base matrices
    fA = predictor(A_scaled).ravel()
    fB = predictor(B_scaled).ravel()

    # For each factor i, build C_i = A with column i replaced by B's column i;
    # this is the standard Saltelli replacement.
    indices: list[SobolIndex] = []
    var_y = float(np.var(np.concatenate([fA, fB]), ddof=1))
    if var_y < 1e-12:
        return SensitivityResult(
            response_name=response_name,
            n_base_samples=n_base_samples,
            n_evaluations=int(n_base_samples * (k + 2)),
            notes=[
                "Surrogate response is essentially constant; Sobol indices "
                "are not meaningful."
            ],
        )

    for i, fname in enumerate(factor_names):
        Ci = A_scaled.copy()
        Ci[:, i] = B_scaled[:, i]
        fCi = predictor(Ci).ravel()

        # Saltelli (2010) estimators
        s_i = float(np.mean(fB * (fCi - fA)) / var_y)
        s_ti = float(0.5 * np.mean((fA - fCi) ** 2) / var_y)
        # Clamp to [0, 1] — sampling noise can push indices slightly out
        s_i = float(np.clip(s_i, 0.0, 1.0))
        s_ti = float(np.clip(s_ti, 0.0, 1.0))
        indices.append(SobolIndex(
            factor_name=fname,
            first_order=s_i,
            total_order=s_ti,
            interaction_share=max(0.0, s_ti - s_i),
        ))

    return SensitivityResult(
        response_name=response_name,
        n_base_samples=n_base_samples,
        n_evaluations=int(n_base_samples * (k + 2)),
        indices=indices,
    )


def make_rsm_predictor(
    coefs: dict[str, float], factor_names: list[str], bounds: list[tuple[float, float]],
):
    """Build a numpy-vectorised predictor from a fitted RSM's coefficients.

    Inputs are expected in *natural* units; the predictor maps them to
    coded ``[-1, 1]`` (using the supplied bounds) before applying the
    polynomial.
    """
    bounds_arr = np.asarray(bounds, dtype=float)

    def predictor(X_natural: np.ndarray) -> np.ndarray:
        X = np.asarray(X_natural, dtype=float)
        # Scale to coded space
        center = (bounds_arr[:, 0] + bounds_arr[:, 1]) / 2.0
        half_range = (bounds_arr[:, 1] - bounds_arr[:, 0]) / 2.0
        with np.errstate(divide="ignore", invalid="ignore"):
            coded = np.where(half_range > 0, (X - center) / half_range, 0.0)
        y = np.full(coded.shape[0], coefs.get("intercept", 0.0), dtype=float)
        for i, fname in enumerate(factor_names):
            y = y + coefs.get(fname, 0.0) * coded[:, i]
        for i, fi in enumerate(factor_names):
            for j in range(i + 1, len(factor_names)):
                fj = factor_names[j]
                cross = coefs.get(f"{fi}*{fj}",
                                  coefs.get(f"{fj}*{fi}", 0.0))
                y = y + cross * coded[:, i] * coded[:, j]
            y = y + coefs.get(f"{fi}^2", 0.0) * coded[:, i] ** 2
        return y

    return predictor
