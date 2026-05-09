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
    from .analysis import _load_all_results, _coerce_response_value
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
        value = _coerce_response_value(data, resp.name, run.run_id, results_dir)
        if value is not None:
            responses[run.run_id] = value

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
    elif adaptive_cfg.strategy == "model_guided":
        new_runs = _model_guided_strategy(
            valid_runs, responses, resp, cfg, matrix,
            adaptive_cfg.batch_size, rng, max_run_id,
        )
    elif adaptive_cfg.strategy == "bayesian":
        new_runs = _bayesian_strategy(
            valid_runs, responses, resp, cfg, matrix,
            adaptive_cfg.batch_size, max_run_id, seed=seed,
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


def _bayesian_strategy(
    valid_runs, responses, resp, cfg, matrix, batch_size, start_run_id,
    seed: int | None = None,
) -> list[ExperimentRun]:
    """Use a GP surrogate + Expected Improvement to pick the next batch.

    Encodes existing runs to coded ``[-1, 1]`` space (numeric factors)
    and skips factors without a numeric range — those don't fit the GP
    cleanly and would need a separate kernel; the user can keep them
    fixed or set them via ``fixed_factors``.

    Falls back to ``model_guided`` if the GP fit fails outright.
    """
    from .bo import fit_gp, propose_batch

    factor_names = matrix.factor_names
    factor_map = {f.name: f for f in cfg.factors}

    # Identify numeric factors with a usable range
    numeric_names: list[str] = []
    bounds_natural: list[tuple[float, float]] = []
    for fname in factor_names:
        f = factor_map[fname]
        if f.type not in ("continuous", "ordinal"):
            continue
        try:
            low = float(f.levels[0])
            high = float(f.levels[1])
        except (TypeError, ValueError, IndexError):
            continue
        if low == high:
            continue
        numeric_names.append(fname)
        bounds_natural.append((min(low, high), max(low, high)))

    if not numeric_names or len(valid_runs) < 2:
        # Cannot fit a GP — fall back to the leverage-based picker.
        return _model_guided_strategy(
            valid_runs, responses, resp, cfg, matrix,
            batch_size, np.random.default_rng(seed), start_run_id,
        )

    # Encode training X into coded space and y in original units.
    X_train = np.zeros((len(valid_runs), len(numeric_names)))
    y_train = np.zeros(len(valid_runs))
    for i, run in enumerate(valid_runs):
        for j, fname in enumerate(numeric_names):
            low, high = bounds_natural[j]
            try:
                v = float(run.factor_values[fname])
            except (TypeError, ValueError):
                v = (low + high) / 2.0
            X_train[i, j] = 2.0 * (v - low) / (high - low) - 1.0
        y_train[i] = float(responses[run.run_id])

    try:
        gp = fit_gp(X_train, y_train, seed=seed)
    except Exception:
        return _model_guided_strategy(
            valid_runs, responses, resp, cfg, matrix,
            batch_size, np.random.default_rng(seed), start_run_id,
        )

    bounds = np.tile([-1.0, 1.0], (len(numeric_names), 1))
    try:
        proposed = propose_batch(
            gp, bounds, batch_size,
            direction=resp.optimize, seed=seed,
        )
    except Exception:
        return _model_guided_strategy(
            valid_runs, responses, resp, cfg, matrix,
            batch_size, np.random.default_rng(seed), start_run_id,
        )

    from .rsm import _format_factor_value
    runs: list[ExperimentRun] = []
    run_id = start_run_id
    for coded_row in proposed:
        run_id += 1
        factor_values: dict[str, str] = {}
        for j, fname in enumerate(numeric_names):
            low, high = bounds_natural[j]
            decoded = low + (coded_row[j] + 1.0) / 2.0 * (high - low)
            factor_values[fname] = _format_factor_value(factor_map[fname], decoded)
        # Fill in non-numeric / fixed factors at their first level
        for fname in factor_names:
            if fname in factor_values:
                continue
            f = factor_map[fname]
            factor_values[fname] = f.levels[0] if f.levels else ""
        runs.append(ExperimentRun(
            run_id=run_id, block_id=1, factor_values=factor_values,
        ))
    return runs


def _model_guided_strategy(
    valid_runs, responses, resp, cfg, matrix, batch_size, rng, start_run_id,
) -> list[ExperimentRun]:
    """Pick a batch combining model-optimum and max-uncertainty candidates.

    Fits a quadratic RSM on the existing results (linear if the design
    can't support quadratic), finds the predicted optimum via
    ``optimize_surface``, and adds runs at points with the highest
    leverage-scaled prediction variance — i.e. the locations the current
    model is least sure about. Uses no new dependencies (the GP-style
    acquisition functions of full Bayesian optimization are out of
    scope; this is a pragmatic surrogate that uses what we already
    compute).
    """
    from .rsm import fit_rsm, optimize_surface

    factor_names = matrix.factor_names
    runs: list[ExperimentRun] = []
    run_id = start_run_id
    if not valid_runs:
        return runs

    # Pick model order based on whether we have enough runs for quadratic.
    n = len(valid_runs)
    k = len(factor_names)
    n_quad_params = 1 + 2 * k + k * (k - 1) // 2
    model_type = "quadratic" if n >= n_quad_params + 1 else "linear"

    try:
        model = fit_rsm(valid_runs, responses, factor_names, cfg.factors,
                        model_type=model_type)
    except Exception:
        # Fall back to refine if the fit fails outright.
        return _refine_strategy(
            valid_runs, responses, cfg, matrix, batch_size, rng, start_run_id,
        )

    # 1) Model-predicted optimum
    opt_runs: list[ExperimentRun] = []
    try:
        opt = optimize_surface(model, factor_names, cfg.factors,
                               direction=resp.optimize)
        if opt.get("optimal_settings"):
            run_id += 1
            opt_runs.append(ExperimentRun(
                run_id=run_id, block_id=1,
                factor_values=dict(opt["optimal_settings"]),
            ))
    except Exception:
        pass

    n_remaining = max(0, batch_size - len(opt_runs))

    # 2) Max-uncertainty candidates: sample many random points in coded space,
    # score each by predicted variance proxy = (x' (X'X)^-1 x), and pick the
    # ones with the largest values that are also distant from each other.
    try:
        X_existing = _coded_matrix(valid_runs, factor_names, cfg.factors,
                                   model_type=model_type)
        XtX_inv = _safe_pinv(X_existing.T @ X_existing)
    except Exception:
        XtX_inv = None

    if n_remaining and XtX_inv is not None:
        n_candidates = max(200, n_remaining * 50)
        candidate_coded = rng.uniform(-1.0, 1.0, size=(n_candidates, k))
        # Build candidate design rows in the same coded basis as X_existing.
        candidate_X = _build_candidate_X(candidate_coded, model_type, k)
        leverages = np.einsum("ij,jk,ik->i", candidate_X, XtX_inv, candidate_X)
        order = np.argsort(-leverages)
        chosen_idx: list[int] = []
        chosen_coded: list[np.ndarray] = []
        # Greedy: pick top-leverage points but enforce a minimum spacing
        # so we don't waste the batch on a single high-uncertainty cluster.
        for idx in order:
            cand = candidate_coded[idx]
            if all(np.linalg.norm(cand - other) > 0.4 for other in chosen_coded):
                chosen_idx.append(int(idx))
                chosen_coded.append(cand)
                if len(chosen_idx) >= n_remaining:
                    break
        # If spacing was too aggressive, top up with remaining best leverages.
        if len(chosen_idx) < n_remaining:
            for idx in order:
                if int(idx) in chosen_idx:
                    continue
                chosen_idx.append(int(idx))
                if len(chosen_idx) >= n_remaining:
                    break
        for idx in chosen_idx:
            run_id += 1
            opt_runs.append(_decoded_run(
                run_id=run_id,
                coded=candidate_coded[idx],
                factor_names=factor_names,
                factors=cfg.factors,
            ))

    # If we still don't have a full batch (e.g. on tiny designs), pad with
    # explore-style runs.
    while len(opt_runs) < batch_size:
        max_id = max((r.run_id for r in opt_runs), default=start_run_id)
        opt_runs.extend(_explore_strategy(
            valid_runs, cfg, matrix, batch_size - len(opt_runs), rng, max_id,
        ))

    return opt_runs[:batch_size]


def _coded_matrix(runs, factor_names, factors, model_type):
    """Build the same coded design matrix the RSM fitter uses (no intercept-stripping)."""
    from .rsm import _build_design_matrix
    X, _names = _build_design_matrix(runs, factor_names, factors, model_type=model_type)
    return X


def _build_candidate_X(candidate_coded, model_type, k):
    """Construct the design-row matrix for candidate coded points so we can
    apply the same X'X^-1 used to score leverage."""
    n = candidate_coded.shape[0]
    cols = [np.ones((n, 1))]
    cols.append(candidate_coded)
    if model_type == "quadratic":
        # Interaction columns
        for i in range(k):
            for j in range(i + 1, k):
                cols.append((candidate_coded[:, i] * candidate_coded[:, j]).reshape(-1, 1))
        # Squared columns
        for i in range(k):
            cols.append((candidate_coded[:, i] ** 2).reshape(-1, 1))
    return np.hstack(cols)


def _safe_pinv(M):
    return np.linalg.pinv(M)


def _decoded_run(run_id, coded, factor_names, factors):
    factor_map = {f.name: f for f in factors}
    factor_values: dict[str, str] = {}
    for i, fname in enumerate(factor_names):
        f = factor_map[fname]
        cv = float(coded[i])
        if f.type in ("continuous", "ordinal"):
            try:
                low = float(f.levels[0])
                high = float(f.levels[1])
                center = (low + high) / 2.0
                half_range = (high - low) / 2.0
                from .rsm import _format_factor_value
                factor_values[fname] = _format_factor_value(
                    f, center + cv * half_range,
                )
                continue
            except (ValueError, IndexError):
                pass
        # Categorical: snap to nearest level
        sorted_levels = sorted(f.levels)
        if len(sorted_levels) == 2:
            factor_values[fname] = sorted_levels[1] if cv > 0 else sorted_levels[0]
        else:
            half_range = (len(sorted_levels) - 1) / 2.0
            center = (len(sorted_levels) - 1) / 2.0
            idx = int(round(center + cv * half_range))
            idx = max(0, min(len(sorted_levels) - 1, idx))
            factor_values[fname] = sorted_levels[idx]
    return ExperimentRun(run_id=run_id, block_id=1, factor_values=factor_values)


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
                    from .rsm import _format_factor_value
                    factor_values[fname] = _format_factor_value(factor, new_val)
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
                from .rsm import _format_factor_value
                factor_values[fname] = _format_factor_value(factor, val)
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
