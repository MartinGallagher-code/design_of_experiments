# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Adaptive / sequential experimentation support.

Allows multi-phase experiments where each phase is informed by previous
results.  After running an initial design, use ``plan_next_batch`` to
generate the next batch of runs based on model predictions.
"""

import json
import os
from dataclasses import dataclass, field, asdict

import numpy as np

from .models import DOEConfig, DesignMatrix, ExperimentRun


@dataclass
class AdaptiveConfig:
    strategy: str = "refine"        # refine | explore | balanced
    batch_size: int = 4
    stopping_effect_threshold: float = 0.0   # stop if max |effect| < threshold
    stopping_power_threshold: float = 0.0    # stop if power > threshold
    stopping_max_phases: int = 10
    response_name: str | None = None         # focus on specific response


@dataclass
class AdaptiveState:
    phase: int
    total_runs: int
    completed_phases: list[dict] = field(default_factory=list)
    should_stop: bool = False
    stop_reason: str = ""


def plan_next_batch(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    adaptive_cfg: AdaptiveConfig,
    results_dir: str | None = None,
    seed: int | None = None,
) -> tuple[DesignMatrix, AdaptiveState]:
    """Analyse existing results and generate the next batch of runs.

    Parameters
    ----------
    matrix : DesignMatrix
        The original design matrix.
    cfg : DOEConfig
        Experiment configuration.
    adaptive_cfg : AdaptiveConfig
        Adaptive strategy and stopping parameters.
    results_dir : str | None
        Directory with run result files.
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    tuple of (DesignMatrix, AdaptiveState)
        The new batch of runs and the current adaptive state.
    """
    results_dir = results_dir or cfg.out_directory or "results"

    # Load adaptive state
    state = _load_state(results_dir)
    if state is None:
        state = AdaptiveState(phase=0, total_runs=0)

    # Load existing results
    from .analysis import _load_all_results
    all_data = _load_all_results(matrix.runs, results_dir, partial=True)

    if not all_data:
        raise FileNotFoundError(
            f"No result files found in '{results_dir}'. "
            "Run the initial experiment first."
        )

    # Choose the response to optimize
    resp = None
    if adaptive_cfg.response_name:
        resp = next((r for r in cfg.responses if r.name == adaptive_cfg.response_name), None)
    if resp is None:
        resp = cfg.responses[0]

    # Build responses dict for the chosen response
    responses: dict[int, float] = {}
    for run in matrix.runs:
        data = all_data.get(run.run_id, {})
        if resp.name in data:
            responses[run.run_id] = float(data[resp.name])

    valid_runs = [r for r in matrix.runs if r.run_id in responses]
    if not valid_runs:
        raise FileNotFoundError(
            f"No data for response '{resp.name}' in '{results_dir}'."
        )

    # Check stopping criteria
    from .analysis import _compute_main_effects
    effects = _compute_main_effects(valid_runs, responses, matrix.factor_names)
    should_stop, stop_reason = _check_stopping(adaptive_cfg, state, effects)

    state.phase += 1
    state.total_runs = len(all_data)

    if should_stop:
        state.should_stop = True
        state.stop_reason = stop_reason
        _save_state(state, results_dir)
        return DesignMatrix(runs=[], factor_names=matrix.factor_names,
                           operation="adaptive", metadata={}), state

    # Generate next batch
    rng = np.random.default_rng(seed)
    max_run_id = max(r.run_id for r in matrix.runs)

    if adaptive_cfg.strategy == "refine":
        new_runs = _refine_strategy(
            valid_runs, responses, cfg, matrix, adaptive_cfg.batch_size, rng, max_run_id,
        )
    elif adaptive_cfg.strategy == "explore":
        new_runs = _explore_strategy(
            valid_runs, cfg, matrix, adaptive_cfg.batch_size, rng, max_run_id,
        )
    else:  # balanced
        half = adaptive_cfg.batch_size // 2
        refine_n = max(1, half)
        explore_n = max(1, adaptive_cfg.batch_size - refine_n)
        new_runs = _refine_strategy(
            valid_runs, responses, cfg, matrix, refine_n, rng, max_run_id,
        )
        max_id_after = max((r.run_id for r in new_runs), default=max_run_id)
        new_runs.extend(_explore_strategy(
            valid_runs, cfg, matrix, explore_n, rng, max_id_after,
        ))

    state.completed_phases.append({
        "phase": state.phase,
        "n_runs": len(new_runs),
        "strategy": adaptive_cfg.strategy,
    })
    _save_state(state, results_dir)

    new_matrix = DesignMatrix(
        runs=new_runs,
        factor_names=matrix.factor_names,
        operation=f"adaptive_phase_{state.phase}",
        metadata={
            "n_factors": len(cfg.factors),
            "n_base_runs": len(new_runs),
            "n_blocks": 1,
            "n_total_runs": len(new_runs),
            "phase": state.phase,
            "strategy": adaptive_cfg.strategy,
        },
    )

    return new_matrix, state


def _check_stopping(
    adaptive_cfg: AdaptiveConfig,
    state: AdaptiveState,
    effects,
) -> tuple[bool, str]:
    """Check if the adaptive experiment should stop."""
    if adaptive_cfg.stopping_max_phases > 0 and state.phase >= adaptive_cfg.stopping_max_phases:
        return True, f"Maximum phases reached ({adaptive_cfg.stopping_max_phases})"

    if adaptive_cfg.stopping_effect_threshold > 0 and effects:
        max_effect = max(abs(e.main_effect) for e in effects)
        if max_effect < adaptive_cfg.stopping_effect_threshold:
            return True, (
                f"Max effect ({max_effect:.4f}) below threshold "
                f"({adaptive_cfg.stopping_effect_threshold})"
            )

    return False, ""


def _refine_strategy(
    valid_runs, responses, cfg, matrix, batch_size, rng, start_run_id,
) -> list[ExperimentRun]:
    """Generate new runs near the current best observed region."""
    # Find best run
    best_run_id = max(responses, key=responses.get)
    best_run = next(r for r in valid_runs if r.run_id == best_run_id)

    factor_names = matrix.factor_names
    runs = []
    run_id = start_run_id

    for _ in range(batch_size):
        run_id += 1
        factor_values = {}
        for fname in factor_names:
            factor = next(f for f in cfg.factors if f.name == fname)
            best_val_str = best_run.factor_values[fname]

            if factor.type in ("continuous", "ordinal"):
                try:
                    low = float(factor.levels[0])
                    high = float(factor.levels[1])
                    best_val = float(best_val_str)
                    # Perturb within ±25% of original range, centered on best
                    half_range = (high - low) * 0.25
                    new_low = max(low, best_val - half_range)
                    new_high = min(high, best_val + half_range)
                    new_val = rng.uniform(new_low, new_high)
                    factor_values[fname] = f"{new_val:.6g}"
                    continue
                except ValueError:
                    pass

            # Categorical: keep best value
            factor_values[fname] = best_val_str

        runs.append(ExperimentRun(run_id=run_id, block_id=1, factor_values=factor_values))

    return runs


def _explore_strategy(
    valid_runs, cfg, matrix, batch_size, rng, start_run_id,
) -> list[ExperimentRun]:
    """Generate space-filling runs that are distant from existing points."""
    factor_names = matrix.factor_names

    # Encode existing runs to numeric space for distance calculations
    existing_points = []
    for run in valid_runs:
        point = []
        for fname in factor_names:
            factor = next(f for f in cfg.factors if f.name == fname)
            try:
                low = float(factor.levels[0])
                high = float(factor.levels[1])
                val = float(run.factor_values[fname])
                point.append((val - low) / (high - low) if high > low else 0.5)
            except ValueError:
                # Categorical: use index
                try:
                    idx = factor.levels.index(run.factor_values[fname])
                    point.append(idx / max(1, len(factor.levels) - 1))
                except ValueError:
                    point.append(0.5)
        existing_points.append(point)

    existing_arr = np.array(existing_points)

    runs = []
    run_id = start_run_id
    n_candidates = max(100, batch_size * 20)

    for _ in range(batch_size):
        run_id += 1

        # Generate random candidates and pick the one farthest from existing
        candidates = rng.uniform(0, 1, size=(n_candidates, len(factor_names)))
        # Minimum distance to any existing point
        min_dists = np.min(
            np.sqrt(np.sum((candidates[:, np.newaxis, :] - existing_arr[np.newaxis, :, :]) ** 2, axis=2)),
            axis=1,
        )
        best_idx = np.argmax(min_dists)
        best_candidate = candidates[best_idx]

        # Decode to factor values
        factor_values = {}
        for j, fname in enumerate(factor_names):
            factor = next(f for f in cfg.factors if f.name == fname)
            try:
                low = float(factor.levels[0])
                high = float(factor.levels[1])
                val = low + best_candidate[j] * (high - low)
                factor_values[fname] = f"{val:.6g}"
            except ValueError:
                idx = int(best_candidate[j] * len(factor.levels))
                idx = min(idx, len(factor.levels) - 1)
                factor_values[fname] = factor.levels[idx]

        runs.append(ExperimentRun(run_id=run_id, block_id=1, factor_values=factor_values))
        # Add new point to existing for subsequent distance calculations
        existing_arr = np.vstack([existing_arr, best_candidate])

    return runs


def _load_state(results_dir: str) -> AdaptiveState | None:
    """Load adaptive state from JSON file."""
    path = os.path.join(results_dir, "adaptive_state.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return AdaptiveState(
        phase=data.get("phase", 0),
        total_runs=data.get("total_runs", 0),
        completed_phases=data.get("completed_phases", []),
        should_stop=data.get("should_stop", False),
        stop_reason=data.get("stop_reason", ""),
    )


def _save_state(state: AdaptiveState, results_dir: str) -> None:
    """Save adaptive state to JSON file."""
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, "adaptive_state.json")
    with open(path, "w") as f:
        json.dump(asdict(state), f, indent=2)
