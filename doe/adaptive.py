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
    state_name: str | None = None,
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

    # Adaptive state lives at the BASE level (not in any rotating session
    # subdirectory) so phase history survives `--session` switches. The
    # caller can branch trajectories via state_name → adaptive_state_<name>.json.
    state_dir = cfg.out_directory or results_dir
    state = _load_state(state_dir, state_name=state_name)
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
        _save_state(state, state_dir, state_name=state_name)
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
    elif adaptive_cfg.strategy == "multi_objective":
        new_runs = _multi_objective_strategy(
            valid_runs, results_dir, cfg, matrix,
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
    _save_state(state, state_dir, state_name=state_name)

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


def _per_point_noise_from_replicates(
    valid_runs, responses, factor_names: list[str],
) -> np.ndarray | None:
    """Estimate variance per training point from replicate scatter.

    For each unique factor-setting tuple with k > 1 observations, compute
    the unbiased sample variance ``Var = sum((y - mean)^2) / (k - 1)`` and
    assign it to every replicate of that setting. Singletons fall back to
    the pooled variance across all replicate groups (or zero if there
    are no replicates at all → returns ``None`` so fit_gp uses a single
    homoscedastic σ_n²).
    """
    from collections import defaultdict
    groups: dict[tuple, list[int]] = defaultdict(list)
    for i, run in enumerate(valid_runs):
        key = tuple(run.factor_values.get(f, "") for f in factor_names)
        groups[key].append(i)

    has_replicate = any(len(idxs) > 1 for idxs in groups.values())
    if not has_replicate:
        return None

    n = len(valid_runs)
    noise = np.zeros(n)
    pooled_sq_dev = 0.0
    pooled_df = 0
    group_var: dict[tuple, float] = {}
    for key, idxs in groups.items():
        if len(idxs) <= 1:
            continue
        vals = np.asarray([float(responses[valid_runs[i].run_id]) for i in idxs])
        mean = vals.mean()
        sq_dev = float(np.sum((vals - mean) ** 2))
        var = sq_dev / (len(idxs) - 1)
        group_var[key] = var
        pooled_sq_dev += sq_dev
        pooled_df += len(idxs) - 1
    pooled_var = pooled_sq_dev / pooled_df if pooled_df > 0 else 0.0

    for key, idxs in groups.items():
        if key in group_var:
            for i in idxs:
                noise[i] = group_var[key]
        else:
            for i in idxs:
                noise[i] = pooled_var
    return noise


def _multi_objective_strategy(
    valid_runs, results_dir, cfg, matrix, batch_size, start_run_id,
    seed: int | None = None,
) -> list[ExperimentRun]:
    """Multi-objective BO across every response in ``cfg.responses``.

    Fits one GP per response and picks the batch via random Tchebycheff
    scalarisations of expected improvement. Falls back to ``model_guided``
    on the first response if the multi-objective fit fails (e.g. the
    user only declared one response, or there's not enough data per
    response).
    """
    from .bo import fit_gp, propose_batch_multi_objective

    if len(cfg.responses) < 2:
        # Reuse the single-response BO path for mono-objective cases.
        return _bayesian_strategy(
            valid_runs,
            _load_response_dict(matrix, results_dir, cfg.responses[0].name),
            cfg.responses[0], cfg, matrix,
            batch_size, start_run_id, seed=seed,
        )

    encoder = _build_factor_encoder(matrix.factor_names, cfg.factors)
    if encoder is None:
        return _model_guided_strategy(
            valid_runs,
            _load_response_dict(matrix, results_dir, cfg.responses[0].name),
            cfg.responses[0], cfg, matrix,
            batch_size, np.random.default_rng(seed), start_run_id,
        )

    X_train = np.array(
        [encoder.encode(run.factor_values) for run in valid_runs], dtype=float,
    )

    gps = []
    directions = []
    for resp in cfg.responses:
        responses = _load_response_dict(matrix, results_dir, resp.name)
        usable_idx = [i for i, run in enumerate(valid_runs)
                      if run.run_id in responses]
        if len(usable_idx) < 2:
            return _bayesian_strategy(
                valid_runs,
                _load_response_dict(matrix, results_dir, cfg.responses[0].name),
                cfg.responses[0], cfg, matrix,
                batch_size, start_run_id, seed=seed,
            )
        X_resp = X_train[usable_idx]
        y_resp = np.asarray(
            [responses[valid_runs[i].run_id] for i in usable_idx], dtype=float,
        )
        try:
            gp = fit_gp(X_resp, y_resp, seed=seed)
        except Exception:
            return _bayesian_strategy(
                valid_runs,
                _load_response_dict(matrix, results_dir, cfg.responses[0].name),
                cfg.responses[0], cfg, matrix,
                batch_size, start_run_id, seed=seed,
            )
        gps.append(gp)
        directions.append(resp.optimize)

    # Multi-objective candidate scoring needs raw bounds; we pass [-1, 1]
    # for numeric dims and let propose_batch_multi_objective fantasise on
    # the encoded space. Because each categorical block is a 1-of-k
    # indicator, treating it as continuous in [0, 1] still produces
    # legal one-hot vectors after we decode via argmax.
    bounds = np.array(
        [[-1.0, 1.0]] * encoder.n_numeric_dims +
        [[0.0, 1.0]] * (encoder.n_dims - encoder.n_numeric_dims)
    )
    try:
        proposed = propose_batch_multi_objective(
            gps, bounds, batch_size, directions, seed=seed,
        )
    except Exception:
        return _bayesian_strategy(
            valid_runs,
            _load_response_dict(matrix, results_dir, cfg.responses[0].name),
            cfg.responses[0], cfg, matrix,
            batch_size, start_run_id, seed=seed,
        )

    runs: list[ExperimentRun] = []
    run_id = start_run_id
    for coded_row in proposed:
        run_id += 1
        factor_values = encoder.decode(coded_row)
        runs.append(ExperimentRun(
            run_id=run_id, block_id=1, factor_values=factor_values,
        ))
    return runs


def _load_response_dict(matrix, results_dir, response_name) -> dict[int, float]:
    from .analysis import _load_all_results, _coerce_response_value
    all_data = _load_all_results(matrix.runs, results_dir, partial=True)
    out: dict[int, float] = {}
    for run in matrix.runs:
        data = all_data.get(run.run_id, {})
        v = _coerce_response_value(data, response_name, run.run_id, results_dir)
        if v is not None:
            out[run.run_id] = v
    return out


def _bayesian_strategy(
    valid_runs, responses, resp, cfg, matrix, batch_size, start_run_id,
    seed: int | None = None,
) -> list[ExperimentRun]:
    """Use a GP surrogate + Expected Improvement to pick the next batch.

    Encodes numeric factors to coded ``[-1, 1]`` and categorical factors
    to one-hot blocks so the GP can see both. Falls back to
    ``model_guided`` if no factor is usable or the GP fit fails outright.
    """
    from .bo import fit_gp

    encoder = _build_factor_encoder(matrix.factor_names, cfg.factors)
    if encoder is None or len(valid_runs) < 2:
        return _model_guided_strategy(
            valid_runs, responses, resp, cfg, matrix,
            batch_size, np.random.default_rng(seed), start_run_id,
        )

    X_train = np.array(
        [encoder.encode(run.factor_values) for run in valid_runs], dtype=float,
    )
    y_train = np.array(
        [float(responses[run.run_id]) for run in valid_runs], dtype=float,
    )

    noise = _per_point_noise_from_replicates(valid_runs, responses, matrix.factor_names)

    try:
        gp = fit_gp(X_train, y_train, seed=seed, noise_per_point=noise)
    except Exception:
        return _model_guided_strategy(
            valid_runs, responses, resp, cfg, matrix,
            batch_size, np.random.default_rng(seed), start_run_id,
        )

    try:
        proposed = encoder.propose_with_gp(
            gp, batch_size, direction=resp.optimize, seed=seed,
        )
    except Exception:
        return _model_guided_strategy(
            valid_runs, responses, resp, cfg, matrix,
            batch_size, np.random.default_rng(seed), start_run_id,
        )

    runs: list[ExperimentRun] = []
    run_id = start_run_id
    for coded_row in proposed:
        run_id += 1
        factor_values = encoder.decode(coded_row)
        runs.append(ExperimentRun(
            run_id=run_id, block_id=1, factor_values=factor_values,
        ))
    return runs


@dataclass
class _FactorEncoder:
    """Numeric-RBF + one-hot-categorical encoder for the GP surrogate.

    Numeric factors with a 2-element numeric range become one column in
    coded ``[-1, 1]`` space. Categorical factors with k levels become a
    block of k columns whose values are 1 / k-1 (one-hot scaled to keep
    Euclidean distances comparable across blocks). A factor with neither
    a numeric range nor categorical levels is ignored — the user can
    pin it via ``fixed_factors``.
    """
    factor_names: list[str]                              # original order
    numeric_names: list[str]
    numeric_bounds: list[tuple[float, float]]
    categorical_names: list[str]
    categorical_levels: list[list[str]]
    factor_map: dict
    n_numeric_dims: int
    cat_offsets: list[int]                               # start index per categorical block
    n_dims: int

    @classmethod
    def _build(cls, factor_names, factors):
        factor_map = {f.name: f for f in factors}
        numeric_names: list[str] = []
        numeric_bounds: list[tuple[float, float]] = []
        categorical_names: list[str] = []
        categorical_levels: list[list[str]] = []

        for fname in factor_names:
            f = factor_map[fname]
            if f.type in ("continuous", "ordinal"):
                try:
                    low = float(f.levels[0])
                    high = float(f.levels[1])
                except (TypeError, ValueError, IndexError):
                    continue
                if low == high:
                    continue
                numeric_names.append(fname)
                numeric_bounds.append((min(low, high), max(low, high)))
            else:
                lvls = list(dict.fromkeys(f.levels))  # preserve order, dedup
                if len(lvls) >= 2:
                    categorical_names.append(fname)
                    categorical_levels.append(lvls)

        if not numeric_names and not categorical_names:
            return None

        n_num = len(numeric_names)
        cat_offsets: list[int] = []
        running = n_num
        for lvls in categorical_levels:
            cat_offsets.append(running)
            running += len(lvls)
        return cls(
            factor_names=list(factor_names),
            numeric_names=numeric_names,
            numeric_bounds=numeric_bounds,
            categorical_names=categorical_names,
            categorical_levels=categorical_levels,
            factor_map=factor_map,
            n_numeric_dims=n_num,
            cat_offsets=cat_offsets,
            n_dims=running,
        )

    def encode(self, factor_values: dict[str, str]) -> list[float]:
        row = [0.0] * self.n_dims
        for j, fname in enumerate(self.numeric_names):
            low, high = self.numeric_bounds[j]
            try:
                v = float(factor_values[fname])
            except (TypeError, ValueError):
                v = (low + high) / 2.0
            row[j] = 2.0 * (v - low) / (high - low) - 1.0
        for j, fname in enumerate(self.categorical_names):
            lvls = self.categorical_levels[j]
            v = factor_values.get(fname, lvls[0])
            try:
                idx = lvls.index(v)
            except ValueError:
                idx = 0
            offset = self.cat_offsets[j]
            row[offset + idx] = 1.0
        return row

    def decode(self, coded_row: np.ndarray) -> dict[str, str]:
        from .rsm import _format_factor_value
        out: dict[str, str] = {}
        for j, fname in enumerate(self.numeric_names):
            low, high = self.numeric_bounds[j]
            cv = float(np.clip(coded_row[j], -1.0, 1.0))
            decoded = low + (cv + 1.0) / 2.0 * (high - low)
            out[fname] = _format_factor_value(self.factor_map[fname], decoded)
        for j, fname in enumerate(self.categorical_names):
            offset = self.cat_offsets[j]
            block = coded_row[offset:offset + len(self.categorical_levels[j])]
            idx = int(np.argmax(block))
            out[fname] = self.categorical_levels[j][idx]
        # Fill un-encoded factors with their first level (e.g. fixed factors).
        for fname in self.factor_names:
            if fname not in out:
                f = self.factor_map.get(fname)
                out[fname] = f.levels[0] if (f and f.levels) else ""
        return out

    def sample_candidate_set(
        self, n_candidates: int, rng: np.random.Generator,
    ) -> np.ndarray:
        """Random candidate matrix in the encoded space."""
        X = np.zeros((n_candidates, self.n_dims))
        if self.n_numeric_dims:
            X[:, :self.n_numeric_dims] = rng.uniform(
                -1.0, 1.0, size=(n_candidates, self.n_numeric_dims),
            )
        for j, fname in enumerate(self.categorical_names):
            offset = self.cat_offsets[j]
            n_lvls = len(self.categorical_levels[j])
            picks = rng.integers(low=0, high=n_lvls, size=n_candidates)
            for i, p in enumerate(picks):
                X[i, offset + int(p)] = 1.0
        return X

    def propose_with_gp(
        self,
        gp,
        batch_size: int,
        direction: str = "maximize",
        n_candidates: int = 2000,
        seed: int | None = None,
    ) -> np.ndarray:
        """Pick a batch by EI on a randomly sampled candidate set, with
        constant-liar fantasising. Same logic as :func:`doe.bo.propose_batch`
        but on the mixed candidate space — categorical levels are
        sampled discretely each iteration, numerics uniformly in [-1, 1]."""
        from .bo import expected_improvement, fit_gp, predict
        rng = np.random.default_rng(seed)
        chosen: list[np.ndarray] = []
        if direction == "minimize":
            best_norm = float(np.min(gp.y_train))
        else:
            best_norm = float(np.max(gp.y_train))
        best_orig = best_norm * gp.y_std + gp.y_mean

        current_gp = gp
        for _ in range(batch_size):
            candidates = self.sample_candidate_set(n_candidates, rng)
            ei = expected_improvement(
                current_gp, candidates, best_orig, direction=direction,
            )
            for c in chosen:
                dists = np.linalg.norm(candidates - c, axis=1)
                ei = ei * (1.0 - np.exp(-(dists ** 2) / 0.04))
            if not np.any(ei > 0):
                _, var = predict(current_gp, candidates)
                idx = int(np.argmax(var))
            else:
                idx = int(np.argmax(ei))
            chosen.append(candidates[idx].copy())

            X_new = np.vstack([current_gp.X_train, candidates[idx][None, :]])
            y_new_norm = np.append(current_gp.y_train, best_norm)
            y_new = y_new_norm * current_gp.y_std + current_gp.y_mean
            try:
                current_gp = fit_gp(X_new, y_new, seed=seed)
            except Exception:
                pass

        return np.vstack(chosen)


def _build_factor_encoder(factor_names, factors):
    return _FactorEncoder._build(factor_names, factors)


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


def _state_filename(state_name: str | None) -> str:
    if not state_name:
        return "adaptive_state.json"
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in state_name)
    safe = safe.strip("_") or "state"
    return f"adaptive_state_{safe}.json"


def _load_state(
    results_dir: str, state_name: str | None = None,
) -> AdaptiveState | None:
    """Load adaptive state from ``adaptive_state[_<name>].json`` in *results_dir*."""
    path = os.path.join(results_dir, _state_filename(state_name))
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


def _save_state(
    state: AdaptiveState, results_dir: str, state_name: str | None = None,
) -> None:
    """Save adaptive state to ``adaptive_state[_<name>].json`` in *results_dir*."""
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, _state_filename(state_name))
    with open(path, "w") as f:
        json.dump(asdict(state), f, indent=2)
