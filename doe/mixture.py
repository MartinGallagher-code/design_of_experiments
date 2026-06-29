# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scheffé canonical-form analysis for mixture designs.

For a mixture experiment the components are constrained to sum to 1
(``x_1 + x_2 + ... + x_q = 1``), so the standard linear model
``y = β_0 + Σ β_i x_i`` has a column-space collinearity — the intercept
is linearly dependent on the component columns. The canonical Scheffé
forms drop the intercept and write the model entirely in components:

* **linear**     ``y = Σ β_i x_i``
* **quadratic**  ``y = Σ β_i x_i + Σ_{i<j} β_{ij} x_i x_j``

Each coefficient β_i can then be interpreted as the predicted response
at the *pure i-th component*, and β_{ij} captures the synergistic /
antagonistic effect of blending i and j.
"""

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from .models import ExperimentRun


@dataclass
class ScheffeTerm:
    label: str                 # "x1", "x1*x2", ...
    coefficient: float
    std_error: float | None = None
    t_value: float | None = None
    p_value: float | None = None


@dataclass
class ScheffeModel:
    response_name: str
    model_form: str            # "linear" | "quadratic"
    component_names: list[str]
    n_observations: int
    n_parameters: int
    r_squared: float
    adj_r_squared: float
    residual_ms: float
    terms: list[ScheffeTerm] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def fit_scheffe(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    component_names: list[str],
    response_name: str = "",
    model_form: str = "quadratic",
) -> ScheffeModel | None:
    """Fit a Scheffé canonical form (no intercept) to mixture runs.

    Parameters
    ----------
    runs
        ExperimentRun list — only those whose ``run_id`` is in
        ``responses`` are used.
    responses
        Mapping ``run_id -> y``.
    component_names
        Mixture component names in the order their coefficients should
        appear in the report.
    model_form
        ``"linear"`` (one term per component) or ``"quadratic"`` (linear
        plus all binary blends).
    """
    if model_form not in ("linear", "quadratic"):
        raise ValueError(
            f"model_form must be 'linear' or 'quadratic', got {model_form!r}"
        )

    valid = [r for r in runs if r.run_id in responses]
    if not valid:
        return None
    q = len(component_names)
    if q < 2:
        return None

    # Each row: x_i values (treated as floats) and binary x_i*x_j products
    rows = np.zeros((len(valid), q + (q * (q - 1) // 2 if model_form == "quadratic" else 0)))
    y = np.zeros(len(valid))
    for i, run in enumerate(valid):
        try:
            x = np.array([float(run.factor_values[c]) for c in component_names])
        except (TypeError, ValueError, KeyError):
            return None
        rows[i, :q] = x
        if model_form == "quadratic":
            offset = q
            for a, b in combinations(range(q), 2):
                rows[i, offset] = x[a] * x[b]
                offset += 1
        y[i] = float(responses[run.run_id])

    # Least-squares fit (no intercept — the constraint absorbs it)
    try:
        beta, *_ = np.linalg.lstsq(rows, y, rcond=None)
    except np.linalg.LinAlgError:
        return None
    n = len(valid)
    p = rows.shape[1]
    if n <= p:
        return ScheffeModel(
            response_name=response_name,
            model_form=model_form,
            component_names=list(component_names),
            n_observations=n, n_parameters=p,
            r_squared=float("nan"),
            adj_r_squared=float("nan"),
            residual_ms=float("nan"),
            notes=[
                f"Saturated fit (n={n} <= p={p}); coefficients reported "
                "without t-tests."
            ],
        )

    y_pred = rows @ beta
    residuals = y - y_pred
    sse = float(np.sum(residuals ** 2))
    sst = float(np.sum((y - np.mean(y)) ** 2))
    df_error = n - p
    mse = sse / df_error if df_error > 0 else 0.0
    r2 = 1.0 - sse / sst if sst > 0 else 0.0
    adj_r2 = 1.0 - (sse / df_error) / (sst / (n - 1)) if sst > 0 and df_error > 0 and n > 1 else r2

    # Standard errors via (X'X)^-1 * MSE
    try:
        cov = mse * np.linalg.pinv(rows.T @ rows)
        se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)

    try:
        from scipy.stats import t as _t
    except Exception:
        _t = None

    labels: list[str] = list(component_names)
    if model_form == "quadratic":
        for a, b in combinations(range(q), 2):
            labels.append(f"{component_names[a]}*{component_names[b]}")

    terms: list[ScheffeTerm] = []
    for i, label in enumerate(labels):
        s = float(se[i]) if np.isfinite(se[i]) else None
        t_val = (float(beta[i] / s) if s and s > 0 else None)
        p_val = None
        if _t is not None and t_val is not None and df_error > 0:
            p_val = float(2.0 * (1.0 - _t.cdf(abs(t_val), df=df_error)))
        terms.append(ScheffeTerm(
            label=label,
            coefficient=float(beta[i]),
            std_error=s,
            t_value=t_val,
            p_value=p_val,
        ))

    return ScheffeModel(
        response_name=response_name,
        model_form=model_form,
        component_names=list(component_names),
        n_observations=n,
        n_parameters=p,
        r_squared=r2,
        adj_r_squared=adj_r2,
        residual_ms=mse,
        terms=terms,
    )


def is_mixture_operation(operation: str) -> bool:
    return operation in ("mixture_simplex_lattice", "mixture_simplex_centroid")
