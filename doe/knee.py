# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Knee-point (saturation point) detection via piecewise linear regression."""

from dataclasses import dataclass
import numpy as np


@dataclass
class _KneeResult:
    knee_value: float
    knee_response: float
    ci_low: float
    ci_high: float
    r_squared: float
    segment1_slope: float
    segment2_slope: float


def detect_knee_point(
    factor_values: list[float],
    response_values: list[float],
    n_bootstrap: int = 1000,
) -> _KneeResult | None:
    """Detect the knee/saturation point using piecewise linear regression.

    Tries each interior factor value as a candidate breakpoint, fits two
    linear segments, and picks the breakpoint that minimises total RSS.
    Bootstrap resampling provides a confidence interval on the knee location.

    Returns None if fewer than 3 data points or if no valid knee is found.
    """
    x = np.array(factor_values, dtype=float)
    y = np.array(response_values, dtype=float)
    n = len(x)

    if n < 3:
        return None

    order = np.argsort(x)
    x = x[order]
    y = y[order]

    best_bp, best_rss, best_s1, best_s2, best_y_bp = _fit_piecewise(x, y)
    if best_bp is None:
        return None

    # R-squared
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - best_rss / ss_tot if ss_tot > 0 else 0.0

    # Bootstrap confidence interval
    rng = np.random.default_rng(42)
    bp_samples = []
    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        xb = x[idx]
        yb = y[idx]
        # Sort for piecewise fit
        order_b = np.argsort(xb)
        xb = xb[order_b]
        yb = yb[order_b]
        bp, _, _, _, _ = _fit_piecewise(xb, yb)
        if bp is not None:
            bp_samples.append(bp)

    if bp_samples:
        ci_low = float(np.percentile(bp_samples, 2.5))
        ci_high = float(np.percentile(bp_samples, 97.5))
    else:
        ci_low = best_bp
        ci_high = best_bp

    return _KneeResult(
        knee_value=best_bp,
        knee_response=best_y_bp,
        ci_low=ci_low,
        ci_high=ci_high,
        r_squared=r_squared,
        segment1_slope=best_s1,
        segment2_slope=best_s2,
    )


def _fit_piecewise(x, y):
    """Find optimal breakpoint for piecewise linear fit.

    Returns (breakpoint_x, rss, slope1, slope2, y_at_breakpoint) or
    (None, ...) if no valid fit.
    """
    n = len(x)
    if n < 3:
        return None, np.inf, 0.0, 0.0, 0.0

    best_bp = None
    best_rss = np.inf
    best_s1 = 0.0
    best_s2 = 0.0
    best_y_bp = 0.0

    # Try each interior point as breakpoint
    for i in range(1, n - 1):
        bp = x[i]
        # Left segment: x <= bp
        mask_l = x <= bp
        mask_r = x >= bp
        n_l = np.sum(mask_l)
        n_r = np.sum(mask_r)
        if n_l < 2 or n_r < 2:
            continue

        # Fit left segment
        xl = x[mask_l]
        yl = y[mask_l]
        s1, b1 = _fit_line(xl, yl)

        # Fit right segment
        xr = x[mask_r]
        yr = y[mask_r]
        s2, b2 = _fit_line(xr, yr)

        # Total RSS
        rss = float(np.sum((yl - (s1 * xl + b1)) ** 2) +
                     np.sum((yr - (s2 * xr + b2)) ** 2))

        if rss < best_rss:
            best_rss = rss
            best_bp = float(bp)
            best_s1 = float(s1)
            best_s2 = float(s2)
            best_y_bp = float(s1 * bp + b1)

    return best_bp, best_rss, best_s1, best_s2, best_y_bp


def _fit_line(x, y):
    """Simple least-squares line fit. Returns (slope, intercept)."""
    n = len(x)
    if n < 2:
        return 0.0, float(np.mean(y)) if n > 0 else 0.0
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    denom = float(np.sum((x - x_mean) ** 2))
    if denom == 0:
        return 0.0, float(y_mean)
    slope = float(np.sum((x - x_mean) * (y - y_mean))) / denom
    intercept = float(y_mean - slope * x_mean)
    return slope, intercept


def plot_knee_point(
    factor_values: list[float],
    response_values: list[float],
    knee: _KneeResult,
    output_path: str,
    factor_name: str = "",
    response_name: str = "",
    factor_unit: str = "",
    response_unit: str = "",
) -> None:
    """Plot the saturation curve with annotated knee point."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = np.array(factor_values, dtype=float)
    y = np.array(response_values, dtype=float)
    order = np.argsort(x)
    x = x[order]
    y = y[order]

    fig, ax = plt.subplots(figsize=(8, 5))

    # Scatter observed data
    ax.scatter(x, y, c="steelblue", s=60, zorder=5, edgecolors="white", linewidths=0.5,
               label="Observed means")

    # Piecewise linear fit
    mask_l = x <= knee.knee_value
    mask_r = x >= knee.knee_value

    # Left segment line
    xl = x[mask_l]
    if len(xl) >= 2:
        _, b1 = _fit_line(xl, y[mask_l])
        x_left = np.linspace(x[0], knee.knee_value, 50)
        ax.plot(x_left, knee.segment1_slope * x_left + b1, "r-", linewidth=2, label="Segment 1")

    # Right segment line
    xr = x[mask_r]
    if len(xr) >= 2:
        _, b2 = _fit_line(xr, y[mask_r])
        x_right = np.linspace(knee.knee_value, x[-1], 50)
        ax.plot(x_right, knee.segment2_slope * x_right + b2, "g-", linewidth=2, label="Segment 2")

    # Knee point
    ax.axvline(knee.knee_value, color="orange", linestyle="--", linewidth=1.5, alpha=0.8,
               label=f"Knee = {knee.knee_value:.4g}")

    # CI shading
    ax.axvspan(knee.ci_low, knee.ci_high, alpha=0.15, color="orange", label="95% CI")

    fu = f" ({factor_unit})" if factor_unit else ""
    ru = f" ({response_unit})" if response_unit else ""
    ax.set_xlabel(f"{factor_name}{fu}")
    ax.set_ylabel(f"{response_name}{ru}")
    ax.set_title(f"Saturation Curve — {response_name} vs {factor_name}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
