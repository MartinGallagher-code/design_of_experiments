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

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt


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
    predictor: Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]],
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


def export_sensitivity_html(
    results: list[SensitivityResult], output_path: str,
) -> str:
    """Render a self-contained HTML page with one stacked-bar chart per
    response. First-order indices are drawn as the bottom bar segment;
    the interaction share (S_T - S_i) sits on top in a lighter shade,
    so the total bar height equals the total-order index.
    """
    import datetime
    import html as _html
    import os
    from .report import _CSS

    sections: list[str] = []
    for result in results:
        if not result.indices:
            sections.append(
                f'<details open><summary><h2>{_html.escape(result.response_name)}</h2></summary>\n'
                f'  <div class="section-body">\n'
                + ("  <p class=\"muted\">"
                   + "; ".join(_html.escape(n) for n in result.notes)
                   + "</p>\n")
                + '  </div>\n</details>\n'
            )
            continue

        plot_html = _render_sobol_stacked_bar(result)
        rows = ""
        for entry in result.indices:
            rows += (
                f'      <tr><td>{_html.escape(entry.factor_name)}</td>'
                f'<td class="mono">{entry.first_order:.4f}</td>'
                f'<td class="mono">{entry.total_order:.4f}</td>'
                f'<td class="mono">{entry.interaction_share:.4f}</td></tr>\n'
            )
        sections.append(
            f'<details open id="sensitivity-{_anchor_id(result.response_name)}">\n'
            f'  <summary><h2>Response: {_html.escape(result.response_name)}</h2></summary>\n'
            f'  <div class="section-body">\n'
            f'  <p class="muted">'
            f'Saltelli sampling, {result.n_evaluations} surrogate evaluations '
            f'(N={result.n_base_samples}). Bar = total-order S<sub>T</sub>; '
            f'lower segment = first-order S<sub>i</sub>; upper = interaction '
            f'share max(0, S<sub>T</sub> - S<sub>i</sub>).</p>\n'
            f'{plot_html}'
            f'  <table class="data-table">\n'
            '    <thead><tr><th>Factor</th><th>S<sub>i</sub></th>'
            '<th>S<sub>T</sub></th><th>Interaction share</th></tr></thead>\n'
            f'    <tbody>\n{rows}    </tbody>\n'
            '  </table>\n'
            '  </div>\n</details>\n'
        )

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <title>DOE Sensitivity</title>\n'
        f'  <style>{_CSS}</style>\n'
        '</head>\n<body>\n'
        '<header>\n'
        '  <h1>Sobol Sensitivity</h1>\n'
        f'  <p class="timestamp">Generated: {_html.escape(timestamp)}</p>\n'
        '</header>\n'
        + "\n".join(sections)
        + '\n<footer><p>Generated by DOE Helper Tool — doe sensitivity</p></footer>\n'
        '</body>\n</html>\n'
    )

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return output_path


def _render_sobol_stacked_bar(result: SensitivityResult) -> str:
    """Inline a stacked bar chart of (first-order, interaction share)
    as base64 PNG. Returns "" if matplotlib isn't available."""
    try:
        import io
        import base64
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    if not result.indices:
        return ""
    factors = [idx.factor_name for idx in result.indices]
    first_order = np.array([idx.first_order for idx in result.indices])
    interaction = np.array([idx.interaction_share for idx in result.indices])
    fig, ax = plt.subplots(figsize=(7.0, 0.5 + 0.4 * len(factors)))
    y = np.arange(len(factors))
    ax.barh(y, first_order, color="#3a7bd5", label="First-order S$_i$")
    ax.barh(y, interaction, left=first_order, color="#a5c8f0",
            label="Interaction share")
    ax.set_yticks(y)
    ax.set_yticklabels(factors)
    ax.invert_yaxis()
    ax.set_xlabel("Variance share (0–1)")
    ax.set_xlim(0, max(1.0, float(np.max(first_order + interaction)) * 1.05))
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return (
        '  <div class="plot">\n'
        '    <img alt="Sobol indices stacked bar" '
        f'src="data:image/png;base64,{encoded}">\n'
        '  </div>\n'
    )


def _anchor_id(name: str) -> str:
    out = []
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "."):
            out.append("-")
    cleaned = "".join(out).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "section"


def make_rsm_predictor(
    coefs: dict[str, float], factor_names: list[str], bounds: list[tuple[float, float]],
) -> Callable[[np.ndarray], np.ndarray]:
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
