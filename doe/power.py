# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Statistical power calculations for DOE main effects.

Two ways to use this module:

* ``achieved_power(...)`` — *post-hoc*. Given the residual MS observed in
  the experiment, compute per-factor power for a chosen effect size and
  the minimum detectable effect at a chosen power target. This is what
  ``doe analyze`` calls automatically.

* The ``doe power`` CLI subcommand still supports the *prospective* case
  (user-supplied ``--sigma`` and ``--delta`` before running anything)
  and uses the same primitives.
"""


from .models import AchievedPower, AchievedPowerEntry, DesignMatrix, Factor


def power_for_factor(
    n_runs: int,
    n_levels: int,
    df_error: int,
    delta: float,
    sigma: float,
    alpha: float = 0.05,
) -> float:
    """Power to detect an effect of size ``delta`` for a factor.

    Uses the standard non-central F formulation for balanced designs:
    ``ncp = r * delta**2 / sigma**2`` where ``r = n_runs // n_levels``
    is the (approximate) replicates-per-level. Returns 1.0 when residual
    MS is zero (no error → guaranteed detection).
    """
    if sigma <= 0:
        return 1.0
    if df_error < 1 or n_levels < 2:
        return 0.0
    from scipy.stats import f as _f, ncf as _ncf
    df_factor = n_levels - 1
    f_crit = _f.ppf(1.0 - alpha, df_factor, df_error)
    r = max(1, n_runs // n_levels)
    ncp = r * (delta ** 2) / (sigma ** 2)
    return float(1.0 - _ncf.cdf(f_crit, df_factor, df_error, ncp))


def mde_for_factor(
    n_runs: int,
    n_levels: int,
    df_error: int,
    sigma: float,
    target_power: float = 0.8,
    alpha: float = 0.05,
) -> float:
    """Minimum detectable effect to achieve ``target_power``.

    Returns 0.0 when residual MS is zero (no error → MDE collapses to 0).
    Uses bisection on ``delta`` so this stays light on dependencies.
    """
    if sigma <= 0:
        return 0.0
    if df_error < 1 or n_levels < 2:
        return float("inf")

    def _power(delta: float) -> float:
        return power_for_factor(n_runs, n_levels, df_error, delta, sigma, alpha)

    lo, hi = 0.0, max(8.0 * sigma, 1.0)
    # Expand `hi` until power is at or above target (cap to avoid infinite loop).
    for _ in range(20):
        if _power(hi) >= target_power:
            break
        hi *= 2.0
    else:
        return float("inf")

    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if _power(mid) < target_power:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-6 * sigma:
            break
    return float(0.5 * (lo + hi))


def achieved_power(
    matrix: DesignMatrix,
    factors: list[Factor],
    residual_ms: float,
    df_error: int,
    delta: float | None = None,
    target_power: float = 0.8,
    alpha: float = 0.05,
) -> AchievedPower | None:
    """Compute post-hoc power per factor and the minimum detectable effect.

    ``delta`` defaults to ``2 * sigma`` (where ``sigma = sqrt(residual_ms)``)
    so the report always has a "power at a generic 2σ effect" column.

    Returns ``None`` when ``df_error`` is zero (saturated design with no
    estimable error term).
    """
    if df_error < 1:
        return None
    sigma = float(residual_ms) ** 0.5
    chosen_delta = float(delta) if delta is not None else 2.0 * sigma

    n_runs = len(matrix.runs)
    entries: list[AchievedPowerEntry] = []
    for f in factors:
        n_levels = len(f.levels)
        if n_levels < 2:
            continue
        p = power_for_factor(n_runs, n_levels, df_error, chosen_delta, sigma, alpha)
        mde = mde_for_factor(n_runs, n_levels, df_error, sigma, target_power, alpha)
        entries.append(AchievedPowerEntry(
            factor_name=f.name,
            n_levels=n_levels,
            power_at_delta=p,
            mde_at_target=mde,
        ))

    return AchievedPower(
        n_runs=n_runs,
        df_error=df_error,
        residual_ms=float(residual_ms),
        sigma=sigma,
        alpha=alpha,
        delta=chosen_delta,
        target_power=target_power,
        per_factor=entries,
    )
