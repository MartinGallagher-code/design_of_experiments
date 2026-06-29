# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fit free parameters in a parametric simulator to observed data.

When a user has both:
  * a Python simulator they can control via parameters
    (e.g. a digital twin with knobs like noise_level, leak_rate)
  * real-world results from running the actual experiment

``calibrate`` finds the parameter values that minimise the weighted
sum of squared residuals between the simulator's output and the
observations, using ``scipy.optimize.minimize`` with bounds.

Example simulator signature::

    def simulate(factors, *, noise_level=0.1, leak_rate=0.05):
        return {"yield": ..., "purity": ...}

CLI::

    doe calibrate --config config.json \
        --func sim.py:simulate \
        --params noise_level:0.0:1.0 leak_rate:0.0:0.5 \
        --observed results/baseline-20260101 \
        --report calibration.json
"""

import json
import os
from dataclasses import dataclass, field, asdict
from collections.abc import Callable

import numpy as np
import numpy.typing as npt

from .models import ExperimentRun
from .simulate import _resolve_target


@dataclass
class CalibrationParam:
    name: str
    initial: float
    low: float
    high: float


@dataclass
class CalibrationResult:
    fitted_params: dict[str, float]
    initial_params: dict[str, float]
    bounds: dict[str, tuple[float, float]]
    rmse_before: float
    rmse_after: float
    converged: bool
    n_iterations: int
    per_response_rmse: dict[str, float] = field(default_factory=dict)


def calibrate(
    runs: list[ExperimentRun],
    observed: dict[int, dict[str, float]],
    func: Callable[..., dict[str, float]] | str,
    params: list[CalibrationParam],
    response_weights: dict[str, float] | None = None,
    seed: int | None = None,
) -> CalibrationResult:
    """Fit ``params`` so that ``func(factors, **params)`` matches ``observed``.

    Parameters
    ----------
    runs
        The runs whose factor settings are passed to the simulator.
    observed
        ``{run_id: {response_name: value}}`` — the ground-truth data.
    func
        Simulator (callable or ``module:function`` string). Must accept
        a factor dict plus the calibration parameters as keyword
        arguments and return a ``dict[str, float]`` of response values.
    params
        Parameter specs with bounds and initial values.
    response_weights
        Optional ``{response_name: weight}`` for weighting residuals.
        Missing weights default to 1.0.
    seed
        Reserved for future stochastic-simulator support; currently
        unused (the optimiser is deterministic given a deterministic
        simulator).
    """
    if isinstance(func, str):
        sim = _resolve_target(func)
    else:
        sim = func

    if not params:
        raise ValueError("calibrate requires at least one parameter.")

    weights = response_weights or {}
    runs_with_data = [r for r in runs if r.run_id in observed]
    if not runs_with_data:
        raise ValueError("No runs have observed values to calibrate against.")

    # Discover the response set from the observed data, intersected with what
    # the simulator returns at the initial parameters (so we don't ask the
    # optimiser to chase residuals on responses the simulator can't produce).
    initial_kwargs = {p.name: p.initial for p in params}
    sample = sim(dict(runs_with_data[0].factor_values), **initial_kwargs)
    if not isinstance(sample, dict):
        raise TypeError(
            f"Simulator returned {type(sample).__name__}; expected dict."
        )
    candidate_responses = set(sample.keys()) & {
        k for r in runs_with_data for k in observed[r.run_id]
    }
    if not candidate_responses:
        raise ValueError(
            "Simulator output and observed data have no responses in common."
        )
    response_names = sorted(candidate_responses)

    initial_params = {p.name: p.initial for p in params}
    rmse_before, _per_resp_before = _residual_metrics(
        sim, runs_with_data, observed, response_names, initial_params, weights,
    )

    # scipy.optimize.minimize works on a vector; assemble bounds + objective.
    x0 = np.array([p.initial for p in params], dtype=float)
    bounds = [(p.low, p.high) for p in params]

    def objective(x: npt.NDArray[np.float64]) -> float:
        kwargs = {p.name: float(v) for p, v in zip(params, x)}
        try:
            return _weighted_sse(
                sim, runs_with_data, observed, response_names, kwargs, weights,
            )
        except Exception:
            return 1e18

    n_iters = 0
    converged = False
    fitted_x = x0.copy()
    try:
        from scipy.optimize import minimize
        result = minimize(
            objective, x0, method="L-BFGS-B", bounds=bounds,
            options={"maxiter": 200, "ftol": 1e-9},
        )
        fitted_x = result.x
        converged = bool(result.success)
        n_iters = int(result.nit)
    except Exception:
        # Fallback: keep initial params if scipy fails outright
        converged = False

    fitted_params = {p.name: float(v) for p, v in zip(params, fitted_x)}
    rmse_after, per_resp_after = _residual_metrics(
        sim, runs_with_data, observed, response_names, fitted_params, weights,
    )

    return CalibrationResult(
        fitted_params=fitted_params,
        initial_params=initial_params,
        bounds={p.name: (p.low, p.high) for p in params},
        rmse_before=rmse_before,
        rmse_after=rmse_after,
        converged=converged,
        n_iterations=n_iters,
        per_response_rmse=per_resp_after,
    )


def _weighted_sse(
    sim: Callable[..., dict[str, float]],
    runs: list[ExperimentRun],
    observed: dict[int, dict[str, float]],
    response_names: list[str],
    kwargs: dict[str, float],
    weights: dict[str, float],
) -> float:
    total = 0.0
    for run in runs:
        result = sim(dict(run.factor_values), **kwargs)
        for name in response_names:
            if name not in observed[run.run_id] or name not in result:
                continue
            w = float(weights.get(name, 1.0))
            diff = float(result[name]) - float(observed[run.run_id][name])
            total += w * diff * diff
    return total


def _residual_metrics(
    sim: Callable[..., dict[str, float]],
    runs: list[ExperimentRun],
    observed: dict[int, dict[str, float]],
    response_names: list[str],
    kwargs: dict[str, float],
    weights: dict[str, float],
) -> tuple[float, dict[str, float]]:
    sq_total = 0.0
    n_total = 0
    per_resp: dict[str, list[float]] = {name: [] for name in response_names}
    for run in runs:
        try:
            result = sim(dict(run.factor_values), **kwargs)
        except Exception:
            continue
        for name in response_names:
            if name not in observed[run.run_id] or name not in result:
                continue
            diff = float(result[name]) - float(observed[run.run_id][name])
            per_resp[name].append(diff * diff)
            w = float(weights.get(name, 1.0))
            sq_total += w * diff * diff
            n_total += 1
    rmse = float(np.sqrt(sq_total / n_total)) if n_total else float("inf")
    per_rmse = {
        name: float(np.sqrt(np.mean(sq))) if sq else float("inf")
        for name, sq in per_resp.items()
    }
    return rmse, per_rmse


def parse_param_spec(spec: str) -> CalibrationParam:
    """Parse 'name:low:high' or 'name:initial:low:high'."""
    parts = spec.split(":")
    if len(parts) == 3:
        name, low, high = parts
        low_f, high_f = float(low), float(high)
        initial = (low_f + high_f) / 2.0
    elif len(parts) == 4:
        name, initial_str, low, high = parts
        low_f, high_f = float(low), float(high)
        initial = float(initial_str)
    else:
        raise ValueError(
            f"Param spec must be 'name:low:high' or 'name:initial:low:high', "
            f"got {spec!r}"
        )
    if low_f > high_f:
        raise ValueError(f"Param {name!r} bounds reversed: low={low_f} > high={high_f}")
    return CalibrationParam(name=name, initial=initial, low=low_f, high=high_f)


def load_observed(session_dir: str, runs: list[ExperimentRun]) -> dict[int, dict[str, float]]:
    """Load run_*.json from a session directory keyed by run_id."""
    if not os.path.isdir(session_dir):
        raise FileNotFoundError(
            f"Observed-data session directory not found: '{session_dir}'"
        )
    out: dict[int, dict[str, float]] = {}
    for run in runs:
        path = os.path.join(session_dir, f"run_{run.run_id}.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                payload = json.load(f)
        except json.JSONDecodeError:
            continue
        coerced: dict[str, float] = {}
        for k, v in payload.items():
            try:
                coerced[k] = float(v)
            except (TypeError, ValueError):
                continue
        if coerced:
            out[run.run_id] = coerced
    if not out:
        raise FileNotFoundError(
            f"No usable run_*.json files found in '{session_dir}'."
        )
    return out


def write_calibration_report(result: CalibrationResult, path: str) -> None:
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(result), f, indent=2)
