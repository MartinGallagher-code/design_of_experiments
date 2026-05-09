# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
import itertools
import random
from .models import DOEConfig, DesignMatrix, ExperimentRun, Factor


def _can_sweep(factor: Factor) -> bool:
    """True if this factor has exactly 2 numeric levels (a sweepable range).

    Categorical factors are never swept — their levels are discrete choices,
    not a numeric range, even when the values happen to be numbers.
    """
    if factor.type == "categorical":
        return False
    if len(factor.levels) != 2:
        return False
    try:
        float(factor.levels[0])
        float(factor.levels[1])
        return True
    except ValueError:
        return False


def generate_design(cfg: DOEConfig, seed: int | None = None) -> DesignMatrix:
    if cfg.operation == "full_factorial":
        base_runs = _full_factorial(cfg)
    elif cfg.operation == "plackett_burman":
        base_runs = _plackett_burman(cfg)
    elif cfg.operation == "latin_hypercube":
        base_runs = _latin_hypercube(cfg, seed=seed)
    elif cfg.operation == "central_composite":
        base_runs = _central_composite(cfg)
    elif cfg.operation == "fractional_factorial":
        base_runs = _fractional_factorial(cfg)
    elif cfg.operation == "box_behnken":
        base_runs = _box_behnken(cfg)
    elif cfg.operation == "definitive_screening":
        base_runs = _definitive_screening(cfg)
    elif cfg.operation == "taguchi":
        base_runs = _taguchi(cfg)
    elif cfg.operation == "d_optimal":
        base_runs = _d_optimal(cfg)
    elif cfg.operation == "mixture_simplex_lattice":
        base_runs = _mixture_simplex_lattice(cfg)
    elif cfg.operation == "mixture_simplex_centroid":
        base_runs = _mixture_simplex_centroid(cfg)
    elif cfg.operation == "linear_sweep":
        base_runs = _linear_sweep(cfg)
    elif cfg.operation == "log_sweep":
        base_runs = _log_sweep(cfg)
    elif cfg.operation == "split_plot":
        base_runs = _split_plot(cfg)
    else:
        raise ValueError(f"Unknown operation: {cfg.operation}")

    runs = _apply_blocks(base_runs, cfg.block_count)

    # Insert center-point replicates per block (when requested and feasible)
    n_center_replicates = max(0, int(getattr(cfg, "replicate_center", 0) or 0))
    if n_center_replicates > 0:
        runs = _add_center_point_replicates(
            runs, cfg.factors, n_center_replicates, cfg.block_count,
        )

    # Apply user-supplied constraints (e.g. "x + y <= 1"). Filtering before
    # randomisation keeps the seeded shuffle deterministic on whatever
    # subset survives.
    constraints = list(getattr(cfg, "constraints", []) or [])
    if constraints:
        from .constraints import filter_runs
        runs, dropped = filter_runs(runs, constraints)
        if not runs:
            raise ValueError(
                "All generated runs were filtered out by the constraints: "
                f"{constraints}. Loosen them or remove."
            )
        if dropped:
            print(
                f"Constraints removed {len(dropped)}/{len(dropped) + len(runs)} runs"
                f" — {len(runs)} remain."
            )
        # Renumber so run_ids are dense after filtering.
        for new_id, run in enumerate(runs, start=1):
            run.run_id = new_id

    # LHS already incorporates randomness via seed; all others randomize here.
    # Split-plot designs are randomised within each whole plot only — global
    # shuffling would break the whole-plot structure.
    if cfg.operation == "split_plot":
        runs = _randomize_within_whole_plots(runs, seed=seed)
    elif cfg.operation != "latin_hypercube":
        runs = _randomize_run_order(runs, seed=seed)

    factor_names = [f.name for f in cfg.factors]
    n_base = len(base_runs)

    metadata = {
        "n_factors": len(cfg.factors),
        "n_base_runs": n_base,
        "n_blocks": cfg.block_count,
        "n_total_runs": len(runs),
        "seed": seed,
    }

    # Include alias structure for fractional factorial designs
    if hasattr(cfg, '_alias_structure') and cfg._alias_structure:
        metadata["alias_structure"] = cfg._alias_structure

    return DesignMatrix(
        runs=runs,
        factor_names=factor_names,
        operation=cfg.operation,
        metadata=metadata,
    )


def _full_factorial(cfg: DOEConfig) -> list[ExperimentRun]:
    level_lists = [f.levels for f in cfg.factors]
    factor_names = [f.name for f in cfg.factors]
    runs = []
    for i, combo in enumerate(itertools.product(*level_lists)):
        factor_values = dict(zip(factor_names, combo))
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _plackett_burman(cfg: DOEConfig) -> list[ExperimentRun]:
    try:
        import pyDOE3
    except ImportError:
        raise ImportError(
            "pyDOE3 is required for Plackett-Burman designs. "
            "Install it with: pip install pyDOE3"
        )

    n_factors = len(cfg.factors)
    matrix = pyDOE3.pbdesign(n_factors)
    factor_names = [f.name for f in cfg.factors]

    runs = []
    for i, row in enumerate(matrix):
        factor_values = {}
        for j, val in enumerate(row):
            factor = cfg.factors[j]
            level = factor.levels[0] if val < 0 else factor.levels[1]
            factor_values[factor_names[j]] = level
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _latin_hypercube(cfg: DOEConfig, seed: int | None = None) -> list[ExperimentRun]:
    try:
        import pyDOE3
    except ImportError:
        raise ImportError(
            "pyDOE3 is required for Latin Hypercube designs. "
            "Install it with: pip install pyDOE3"
        )

    n_factors = len(cfg.factors)
    n_samples = cfg.lhs_samples if cfg.lhs_samples > 0 else max(10, 2 * n_factors)

    if seed is not None:
        import numpy as np
        np.random.seed(seed)

    try:
        matrix = pyDOE3.lhs(n_factors, samples=n_samples, criterion="maximin")
    except TypeError:
        matrix = pyDOE3.lhs(n_factors, samples=n_samples)

    runs = []
    for i, row in enumerate(matrix):
        factor_values = {
            cfg.factors[j].name: _decode_lhs_value(x, cfg.factors[j])
            for j, x in enumerate(row)
        }
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _decode_lhs_value(x: float, factor) -> str:
    """Map a [0, 1] LHS sample to a factor level string."""
    n = len(factor.levels)
    if factor.type == "continuous" and n == 2:
        try:
            low = float(factor.levels[0])
            high = float(factor.levels[1])
            return f"{low + x * (high - low):.6g}"
        except ValueError:
            pass
    # categorical / ordinal / non-numeric: bin into levels
    return factor.levels[min(int(x * n), n - 1)]


def _central_composite(cfg: DOEConfig) -> list[ExperimentRun]:
    try:
        import pyDOE3
    except ImportError:
        raise ImportError(
            "pyDOE3 is required for Central Composite designs. "
            "Install it with: pip install pyDOE3"
        )

    n_factors = len(cfg.factors)
    # circumscribed CCD: star points outside the factorial cube
    matrix = pyDOE3.ccdesign(n_factors, center=(4, 4), alpha="orthogonal", face="circumscribed")

    runs = []
    for i, row in enumerate(matrix):
        factor_values = {
            cfg.factors[j].name: _decode_coded_value(code, cfg.factors[j])
            for j, code in enumerate(row)
        }
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _decode_coded_value(code: float, factor) -> str:
    """Map a coded CCD value (±1 factorial, ±alpha star, 0 center) to a string."""
    low = float(factor.levels[0])
    high = float(factor.levels[1])
    center = (low + high) / 2.0
    half_range = (high - low) / 2.0
    return f"{center + code * half_range:.6g}"


def _best_generator_choice(
    base_letters: list[str],
    interactions: list[str],
    n_extra: int,
    factor_names: list[str],
) -> list[str]:
    """Pick generators for the extra factors that maximise the design's resolution.

    Searches over candidate combinations of interaction terms (drawn from
    *interactions*, already ordered longest-first), constructs the implied
    fractional factorial via pyDOE3, and scores it by computing the minimum
    correlation magnitude between every (main effect, 2FI) pair and between
    distinct 2FIs. The combination with the lowest such correlation — i.e.
    the highest resolution — wins. Ties are broken by preferring assignments
    that came earlier (longer-order interactions first).

    The search space is bounded: we cap the number of candidates considered
    per ``r`` to keep this tractable for designs up to ~12 factors, which
    is well past the practical use case for fractional factorials.
    """
    import pyDOE3
    from itertools import combinations as _combinations

    # All candidate combinations of size n_extra from the interaction pool.
    # The pool is already sorted longest-first, so iterating in itertools
    # order naturally prefers higher-order interactions.
    pool = interactions[:]
    if n_extra >= len(pool):
        return pool[:n_extra]

    # Cap candidate count to avoid blow-up on large pools.
    MAX_CANDIDATES = 200
    candidates: list[tuple[str, ...]] = []
    for combo in _combinations(pool, n_extra):
        candidates.append(combo)
        if len(candidates) >= MAX_CANDIDATES:
            break

    base_runs_per_candidate = []
    for combo in candidates:
        gen_string = " ".join(list(base_letters) + list(combo))
        try:
            mat = pyDOE3.fracfact(gen_string)
        except Exception:
            continue
        base_runs_per_candidate.append((combo, mat))

    if not base_runs_per_candidate:
        # Fall back to the longest-first greedy assignment
        return pool[:n_extra]

    # Score each candidate lexicographically by:
    #   1. max |correlation| between a main effect and a 2FI  (lower -> higher resolution)
    #   2. max |correlation| between two distinct 2FIs        (tie-breaker)
    # This separates Resolution III, IV, and V cleanly.
    n_factors = len(factor_names)
    best_key: tuple[float, float] = (float("inf"), float("inf"))
    best_combo = base_runs_per_candidate[0][0]
    for combo, mat in base_runs_per_candidate:
        me_2fi, twofi = _resolution_diagnostics(mat[:, :n_factors])
        key = (me_2fi, twofi)
        if key < best_key:
            best_key = key
            best_combo = combo
    return list(best_combo)


def _design_resolution(coded_design) -> int:
    """Estimate the resolution of a 2-level coded design.

    Resolution III: main effects fully aliased with at least one 2FI.
    Resolution IV : main effects clean of 2FIs, but 2FIs aliased in pairs.
    Resolution V+ : all 2FIs orthogonal to each other.
    """
    score_me_2fi, score_2fi_2fi = _resolution_diagnostics(coded_design)
    if score_me_2fi > 1.0 - 1e-6:
        return 3
    if score_2fi_2fi > 1.0 - 1e-6:
        return 4
    return 5


def _resolution_diagnostics(coded_design):
    """Return (max |corr| ME-vs-2FI, max |corr| between 2FIs)."""
    import numpy as np
    from itertools import combinations as _combinations
    n, k = coded_design.shape
    if k < 2:
        return 0.0, 0.0
    twofi_pairs = list(_combinations(range(k), 2))
    twofi = np.column_stack([coded_design[:, a] * coded_design[:, b]
                             for a, b in twofi_pairs])
    cols = np.column_stack([coded_design, twofi])
    norms = np.linalg.norm(cols, axis=0)
    if not np.all(norms > 0):
        return 1.0, 1.0
    R = np.abs((cols.T @ cols) / np.outer(norms, norms))
    np.fill_diagonal(R, 0.0)
    me_2fi = float(R[:k, k:].max()) if R[:k, k:].size else 0.0
    twofi_block = R[k:, k:]
    twofi_max = float(twofi_block.max()) if twofi_block.size else 0.0
    return me_2fi, twofi_max


def _alias_score(coded_design) -> float:
    """Maximum absolute correlation between (ME, 2FI) and (2FI, 2FI) pairs.

    A score of 0 means a clean Resolution-V or higher design; 1.0 means
    full aliasing somewhere (Resolution III). Smaller is better.
    Kept as a public helper for compatibility; new code should use
    ``_resolution_diagnostics`` for finer-grained comparisons.
    """
    me_2fi, twofi = _resolution_diagnostics(coded_design)
    return max(me_2fi, twofi)


def _fractional_factorial(cfg: DOEConfig) -> list[ExperimentRun]:
    try:
        import pyDOE3
    except ImportError:
        raise ImportError(
            "pyDOE3 is required for Fractional Factorial designs. "
            "Install it with: pip install pyDOE3"
        )

    n_factors = len(cfg.factors)
    from itertools import combinations

    factor_names = [f.name for f in cfg.factors]
    min_res = max(0, int(getattr(cfg, "min_resolution", 0) or 0))

    # Determine the smallest k whose run budget supports the user's
    # min_resolution (or just enough columns when min_resolution is 0).
    # We try increasing k and search generator combinations; the first
    # k that satisfies the resolution target wins.
    matrix = None
    gen_string = ""
    for candidate_k in range(2, n_factors + 1):
        # Need candidate_k + interactions >= n_factors columns
        n_interactions = sum(
            len(list(combinations(range(candidate_k), r)))
            for r in range(2, candidate_k + 1)
        )
        if candidate_k + n_interactions < n_factors:
            continue

        base_letters = [chr(ord('a') + i) for i in range(candidate_k)]
        interactions: list[str] = []
        for r in range(candidate_k, 1, -1):
            for combo in combinations(base_letters, r):
                interactions.append("".join(combo))

        if n_factors == candidate_k:
            extras: list[str] = []
        else:
            extras = _best_generator_choice(
                base_letters, interactions, n_factors - candidate_k, factor_names,
            )

        gen_string = " ".join(base_letters + extras)
        candidate_matrix = pyDOE3.fracfact(gen_string)
        candidate_resolution = _design_resolution(candidate_matrix[:, :n_factors])

        # Either no minimum was requested, or this k achieves it.
        if min_res == 0 or candidate_resolution >= min_res:
            matrix = candidate_matrix
            break

    if matrix is None:
        # min_resolution not achievable even with k = n_factors (full factorial).
        # Fall back to full factorial (the user gets Resolution >> requested).
        base_letters = [chr(ord('a') + i) for i in range(n_factors)]
        gen_string = " ".join(base_letters)
        matrix = pyDOE3.fracfact(gen_string)

    # Compute alias structure
    try:
        alias_info = pyDOE3.fracfact_aliasing(matrix)
        if isinstance(alias_info, tuple) and len(alias_info) >= 1:
            # alias_info may be (alias_map, alias_vectors) or just alias_map
            cfg._alias_structure = alias_info[0] if isinstance(alias_info[0], list) else list(alias_info[0])
        elif isinstance(alias_info, list):
            cfg._alias_structure = alias_info
    except Exception:
        pass  # alias analysis is optional

    runs = []
    for i, row in enumerate(matrix):
        factor_values = {}
        for j, val in enumerate(row):
            factor = cfg.factors[j]
            level = factor.levels[0] if val < 0 else factor.levels[1]
            factor_values[factor_names[j]] = level
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _box_behnken(cfg: DOEConfig) -> list[ExperimentRun]:
    try:
        import pyDOE3
    except ImportError:
        raise ImportError(
            "pyDOE3 is required for Box-Behnken designs. "
            "Install it with: pip install pyDOE3"
        )

    n_factors = len(cfg.factors)
    matrix = pyDOE3.bbdesign(n_factors, center=3)
    factor_names = [f.name for f in cfg.factors]

    runs = []
    for i, row in enumerate(matrix):
        factor_values = {}
        for j, code in enumerate(row):
            factor = cfg.factors[j]
            low = float(factor.levels[0])
            high = float(factor.levels[1])
            center = (low + high) / 2.0
            half_range = (high - low) / 2.0
            factor_values[factor_names[j]] = f"{center + code * half_range:.6g}"
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _split_plot(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a split-plot design.

    Exactly one factor must carry ``role='whole_plot'`` (the hard-to-change
    factor). For each level of the whole-plot factor — repeated
    ``cfg.whole_plot_replicates`` times — every combination of the
    subplot (easy-to-change) factors is run inside a single whole plot.
    Whole plots are randomised at outer order and subplot runs at inner.

    Returned runs carry both ``whole_plot_id`` (1..n_whole_plots) and a
    ``block_id`` of 1; the block subsystem stays orthogonal so users can
    still ask for explicit blocks of split-plot designs by setting
    ``block_count > 1`` (each whole plot is then replicated per block).
    """
    whole_plot_factors = [f for f in cfg.factors if f.role == "whole_plot"]
    subplot_factors = [f for f in cfg.factors if f.role != "whole_plot"]
    htc = whole_plot_factors[0]

    # All combinations of subplot factor levels (full factorial inside the plot)
    subplot_combos: list[dict[str, str]] = [{}]
    for f in subplot_factors:
        next_combos: list[dict[str, str]] = []
        for combo in subplot_combos:
            for lv in f.levels:
                merged = dict(combo)
                merged[f.name] = lv
                next_combos.append(merged)
        subplot_combos = next_combos

    n_replicates = max(1, int(getattr(cfg, "whole_plot_replicates", 1) or 1))

    runs: list[ExperimentRun] = []
    run_id = 1
    whole_plot_id = 1
    for htc_level in htc.levels:
        for _replicate in range(n_replicates):
            for sub in subplot_combos:
                fv = {htc.name: htc_level}
                fv.update(sub)
                runs.append(ExperimentRun(
                    run_id=run_id,
                    block_id=1,
                    factor_values=fv,
                    whole_plot_id=whole_plot_id,
                ))
                run_id += 1
            whole_plot_id += 1
    return runs


def _add_center_point_replicates(
    runs: list[ExperimentRun],
    factors: list[Factor],
    n_per_block: int,
    block_count: int,
) -> list[ExperimentRun]:
    """Append N center-point runs to each block.

    A center point sits at the numeric midpoint of every factor with
    exactly 2 numeric levels. Factors with non-numeric levels or more
    than 2 levels keep their first level (deterministic but not the
    classical "0" coded centre — not all factor types have a meaningful
    centre). Bails out with a no-op when no factor has a numeric range,
    since center points would be indistinguishable from the corners.
    """
    centre_values: dict[str, str] = {}
    has_numeric_range = False
    for f in factors:
        if len(f.levels) == 2:
            try:
                low = float(f.levels[0])
                high = float(f.levels[1])
                mid = (low + high) / 2.0
                # Format without trailing zeros / scientific notation noise.
                centre_values[f.name] = f"{mid:g}"
                has_numeric_range = True
                continue
            except (TypeError, ValueError):
                pass
        # Fallback: keep the first level for non-numeric / multi-level factors.
        centre_values[f.name] = f.levels[0] if f.levels else ""

    if not has_numeric_range:
        # Every factor is categorical or single-level — center points
        # would just duplicate corner runs.  Skip silently.
        return runs

    next_id = max((r.run_id for r in runs), default=0) + 1
    out = list(runs)
    for block_id in range(1, max(1, block_count) + 1):
        for _ in range(n_per_block):
            out.append(ExperimentRun(
                run_id=next_id,
                block_id=block_id,
                factor_values=dict(centre_values),
            ))
            next_id += 1
    return out


def _apply_blocks(base_runs: list[ExperimentRun], block_count: int) -> list[ExperimentRun]:
    all_runs = []
    run_id = 1
    for block_id in range(1, block_count + 1):
        for base in base_runs:
            all_runs.append(
                ExperimentRun(
                    run_id=run_id,
                    block_id=block_id,
                    factor_values=dict(base.factor_values),
                    whole_plot_id=base.whole_plot_id,
                )
            )
            run_id += 1
    return all_runs


def _definitive_screening(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a Definitive Screening Design (Jones-Nachtsheim 2011).

    For k factors, creates a design with 2k+1 runs (odd k) or 2k+3 runs
    (even k) at 3 levels (-1, 0, +1). Conference-matrix construction.
    """
    import numpy as np

    n_factors = len(cfg.factors)

    # Build the DSD matrix using conference matrix approach
    # Create an identity-based fold structure
    # Top half: +I, bottom half: -I, center row: zeros
    I = np.eye(n_factors)
    top = I.copy()
    bottom = -I.copy()

    # For each pair of columns in the top half, randomly assign signs
    # to ensure orthogonality of main effects and minimize confounding
    rng = np.random.default_rng(42)  # deterministic for reproducibility
    for i in range(n_factors):
        for j in range(i + 1, n_factors):
            if rng.random() > 0.5:
                top[i, j] = -1
                bottom[i, j] = 1
            else:
                top[i, j] = 1
                bottom[i, j] = -1
            if rng.random() > 0.5:
                top[j, i] = -1
                bottom[j, i] = 1
            else:
                top[j, i] = 1
                bottom[j, i] = -1

    center = np.zeros((1, n_factors))
    matrix = np.vstack([top, bottom, center])

    # For even k, add extra center points for better estimation
    if n_factors % 2 == 0:
        matrix = np.vstack([matrix, center, center])

    factor_names = [f.name for f in cfg.factors]
    runs = []
    for i, row in enumerate(matrix):
        factor_values = {
            cfg.factors[j].name: _decode_coded_value(code, cfg.factors[j])
            for j, code in enumerate(row)
        }
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _taguchi(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a Taguchi orthogonal array design."""
    try:
        import pyDOE3
    except ImportError:
        raise ImportError(
            "pyDOE3 is required for Taguchi designs. "
            "Install it with: pip install pyDOE3"
        )

    n_factors = len(cfg.factors)
    levels_per_factor = [len(f.levels) for f in cfg.factors]

    # Try to find a suitable orthogonal array
    try:
        available = pyDOE3.list_orthogonal_arrays()
        # Find smallest OA that accommodates all factors
        best_oa = None
        best_runs = float('inf')
        for oa_name in available:
            try:
                oa = pyDOE3.get_orthogonal_array(oa_name)
                if oa.shape[1] >= n_factors:
                    max_level_in_oa = int(oa.max()) + 1
                    if max_level_in_oa >= max(levels_per_factor) and oa.shape[0] < best_runs:
                        best_runs = oa.shape[0]
                        best_oa = oa_name
            except Exception:
                continue

        if best_oa:
            matrix = pyDOE3.get_orthogonal_array(best_oa)[:, :n_factors]
        else:
            # Fallback: use taguchi_design directly
            matrix = pyDOE3.taguchi_design(levels_per_factor)
    except (AttributeError, TypeError):
        # Older pyDOE3 versions may not have list_orthogonal_arrays
        matrix = pyDOE3.taguchi_design(levels_per_factor)

    factor_names = [f.name for f in cfg.factors]
    runs = []
    for i, row in enumerate(matrix):
        factor_values = {}
        for j, val in enumerate(row):
            factor = cfg.factors[j]
            level_idx = int(val) % len(factor.levels)
            factor_values[factor_names[j]] = factor.levels[level_idx]
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _d_optimal(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a D-optimal design using coordinate exchange algorithm.

    Maximizes det(X'X) to get the most information-rich design for a
    given number of runs.
    """
    import numpy as np
    from .rsm import _build_design_matrix, _encode_factor_value

    n_factors = len(cfg.factors)
    # Default n_runs: 2 * n_terms for linear model
    n_runs = cfg.lhs_samples if cfg.lhs_samples > 0 else max(n_factors + 2, 2 * n_factors)

    # Build a candidate set. For continuous factors with only 2 levels we'd
    # otherwise be stuck with corner-only candidates, so add interior points
    # at low / mid / high to give the coordinate-exchange algorithm room to
    # pick a more information-rich design.
    enriched_levels = []
    for f in cfg.factors:
        if f.type in ("continuous", "ordinal") and len(f.levels) == 2:
            try:
                low = float(f.levels[0])
                high = float(f.levels[1])
                mid = (low + high) / 2.0
                enriched_levels.append([
                    f"{low:g}", f"{mid:g}", f"{high:g}",
                ])
                continue
            except (TypeError, ValueError):
                pass
        enriched_levels.append(list(f.levels))
    level_lists = enriched_levels
    all_candidates = list(itertools.product(*level_lists))

    if len(all_candidates) <= n_runs:
        # If fewer candidates than runs, just use all of them
        factor_names = [f.name for f in cfg.factors]
        runs = []
        for i, combo in enumerate(all_candidates):
            factor_values = dict(zip(factor_names, combo))
            runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
        return runs

    rng = np.random.default_rng(42)

    # Start with random subset
    indices = rng.choice(len(all_candidates), size=n_runs, replace=False)
    current_design = [all_candidates[i] for i in indices]

    factor_names = [f.name for f in cfg.factors]
    factor_map = {f.name: f for f in cfg.factors}

    def design_to_runs(design):
        return [
            ExperimentRun(run_id=i + 1, block_id=1,
                         factor_values=dict(zip(factor_names, combo)))
            for i, combo in enumerate(design)
        ]

    def compute_d_criterion(design):
        runs_list = design_to_runs(design)
        X, _ = _build_design_matrix(runs_list, factor_names, cfg.factors, model_type="linear")
        try:
            return np.linalg.det(X.T @ X)
        except Exception:
            return 0.0

    # Row exchange: iteratively swap rows to maximize D-criterion
    best_d = compute_d_criterion(current_design)
    improved = True
    max_iters = 100

    for iteration in range(max_iters):
        if not improved:
            break
        improved = False
        for i in range(n_runs):
            current_row = current_design[i]
            best_row = current_row
            for candidate in all_candidates:
                if candidate == current_row:
                    continue
                # Skip if candidate already in design
                if candidate in current_design:
                    continue
                current_design[i] = candidate
                d_val = compute_d_criterion(current_design)
                if d_val > best_d:
                    best_d = d_val
                    best_row = candidate
                    improved = True
                current_design[i] = current_row
            current_design[i] = best_row

    return design_to_runs(current_design)


def augment_design(
    existing_matrix: DesignMatrix,
    cfg: DOEConfig,
    augment_type: str = "fold_over",
) -> DesignMatrix:
    """Augment an existing design with additional runs.

    Parameters
    ----------
    existing_matrix : DesignMatrix
        The existing design to augment.
    cfg : DOEConfig
        The experiment configuration.
    augment_type : str
        One of "fold_over", "star_points", "center_points".

    Returns
    -------
    DesignMatrix with additional runs appended.
    """
    import numpy as np

    existing_runs = existing_matrix.runs
    max_run_id = max(r.run_id for r in existing_runs)
    max_block_id = max(r.block_id for r in existing_runs)
    factor_names = existing_matrix.factor_names
    new_runs = list(existing_runs)

    if augment_type == "fold_over":
        # Mirror each run: swap high/low levels for 2-level factors
        factor_levels = {}
        for f in cfg.factors:
            if len(f.levels) == 2:
                factor_levels[f.name] = f.levels

        for run in existing_runs:
            max_run_id += 1
            new_vals = {}
            for fname in factor_names:
                if fname in factor_levels:
                    levels = factor_levels[fname]
                    new_vals[fname] = levels[1] if run.factor_values[fname] == levels[0] else levels[0]
                else:
                    new_vals[fname] = run.factor_values[fname]
            new_runs.append(ExperimentRun(
                run_id=max_run_id,
                block_id=max_block_id + 1,
                factor_values=new_vals,
            ))

    elif augment_type == "star_points":
        # Add axial (star) points for continuous factors
        for j, factor in enumerate(cfg.factors):
            if factor.type not in ("continuous", "ordinal"):
                continue
            try:
                low = float(factor.levels[0])
                high = float(factor.levels[1])
            except ValueError:
                continue

            center = (low + high) / 2.0
            half_range = (high - low) / 2.0
            alpha = np.sqrt(len(cfg.factors))  # rotatable alpha

            for sign in [-1, 1]:
                max_run_id += 1
                vals = {}
                for fname in factor_names:
                    if fname == factor.name:
                        vals[fname] = f"{center + sign * alpha * half_range:.6g}"
                    else:
                        # Other factors at center
                        f2 = next(f for f in cfg.factors if f.name == fname)
                        try:
                            c2 = (float(f2.levels[0]) + float(f2.levels[1])) / 2.0
                            vals[fname] = f"{c2:.6g}"
                        except (ValueError, IndexError):
                            vals[fname] = f2.levels[0]
                new_runs.append(ExperimentRun(
                    run_id=max_run_id,
                    block_id=max_block_id + 1,
                    factor_values=vals,
                ))

    elif augment_type == "center_points":
        # Add 3 center points
        for _ in range(3):
            max_run_id += 1
            vals = {}
            for factor in cfg.factors:
                try:
                    center = (float(factor.levels[0]) + float(factor.levels[1])) / 2.0
                    vals[factor.name] = f"{center:.6g}"
                except (ValueError, IndexError):
                    vals[factor.name] = factor.levels[0]
            new_runs.append(ExperimentRun(
                run_id=max_run_id,
                block_id=max_block_id + 1,
                factor_values=vals,
            ))

    else:
        raise ValueError(f"Unknown augment_type: {augment_type}. Choose from: fold_over, star_points, center_points")

    return DesignMatrix(
        runs=new_runs,
        factor_names=factor_names,
        operation=f"{existing_matrix.operation}+{augment_type}",
        metadata={
            "n_factors": len(factor_names),
            "n_base_runs": len(existing_runs),
            "n_augmented_runs": len(new_runs) - len(existing_runs),
            "n_blocks": max_block_id + 1,
            "n_total_runs": len(new_runs),
            "augment_type": augment_type,
        },
    )


def _linear_sweep(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a full factorial design using linearly-spaced levels.

    Factors with exactly 2 numeric levels are expanded:
      - dtype="int": every integer between low and high inclusive.
      - otherwise: *sweep_points* evenly-spaced points.

    Factors with >2 levels or non-numeric levels are kept as-is and
    crossed with the expanded factors (full factorial).
    """
    import numpy as np

    n_points = cfg.sweep_points if cfg.sweep_points > 0 else (
        cfg.lhs_samples if cfg.lhs_samples > 0 else 8
    )

    expanded_levels = []
    for factor in cfg.factors:
        if not _can_sweep(factor):
            expanded_levels.append(list(factor.levels))
            continue
        low = float(factor.levels[0])
        high = float(factor.levels[1])
        if factor.dtype == "int":
            int_low = int(round(low))
            int_high = int(round(high))
            expanded_levels.append([str(v) for v in range(int_low, int_high + 1)])
        else:
            pts = np.linspace(low, high, n_points)
            expanded_levels.append([f"{v:.6g}" for v in pts])

    factor_names = [f.name for f in cfg.factors]
    runs = []
    for i, combo in enumerate(itertools.product(*expanded_levels)):
        factor_values = dict(zip(factor_names, combo))
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _log_sweep(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a full factorial design using logarithmically-spaced levels.

    Factors with exactly 2 numeric levels are expanded to *n* log-spaced
    points.  Factors with >2 levels or non-numeric levels are kept as-is
    and crossed with the expanded factors (full factorial).
    """
    import numpy as np

    n_points = cfg.sweep_points if cfg.sweep_points > 0 else (
        cfg.lhs_samples if cfg.lhs_samples > 0 else 8
    )

    expanded_levels = []
    for factor in cfg.factors:
        if not _can_sweep(factor):
            expanded_levels.append(list(factor.levels))
            continue
        low = float(factor.levels[0])
        high = float(factor.levels[1])
        log_levels = np.logspace(np.log10(low), np.log10(high), n_points)
        if factor.dtype == "int":
            int_levels = sorted(set(int(round(v)) for v in log_levels))
            expanded_levels.append([str(v) for v in int_levels])
        else:
            expanded_levels.append([f"{v:.6g}" for v in log_levels])

    factor_names = [f.name for f in cfg.factors]
    runs = []
    for i, combo in enumerate(itertools.product(*expanded_levels)):
        factor_values = dict(zip(factor_names, combo))
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _mixture_simplex_lattice(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a simplex-lattice design for mixture experiments.

    For q components with degree m, generates all points where each
    component takes values 0, 1/m, 2/m, ..., 1 subject to sum = 1.
    Uses degree 2 (quadratic) by default.
    """
    from itertools import combinations_with_replacement

    q = len(cfg.factors)
    m = 2  # quadratic lattice

    # Generate all compositions of m into q parts
    points = []
    for combo in combinations_with_replacement(range(q), m):
        point = [0.0] * q
        for idx in combo:
            point[idx] += 1.0 / m
        # Check for duplicates
        if point not in points:
            points.append(point)

    factor_names = [f.name for f in cfg.factors]
    runs = []
    for i, point in enumerate(points):
        factor_values = {}
        for j, proportion in enumerate(point):
            factor = cfg.factors[j]
            # Map proportion [0,1] to factor levels
            if len(factor.levels) >= 2:
                try:
                    low = float(factor.levels[0])
                    high = float(factor.levels[1])
                    val = low + proportion * (high - low)
                    factor_values[factor_names[j]] = f"{val:.6g}"
                except ValueError:
                    factor_values[factor_names[j]] = f"{proportion:.4f}"
            else:
                factor_values[factor_names[j]] = f"{proportion:.4f}"
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def _mixture_simplex_centroid(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a simplex-centroid design for mixture experiments.

    Includes: vertices, edge midpoints, face centroids, and overall centroid.
    For q components: q vertices + q*(q-1)/2 edge midpoints + ... + 1 centroid.
    """
    from itertools import combinations

    q = len(cfg.factors)
    points = []

    # Vertices: one component = 1, others = 0
    for i in range(q):
        point = [0.0] * q
        point[i] = 1.0
        points.append(point)

    # Edge midpoints: two components = 0.5 each
    for combo in combinations(range(q), 2):
        point = [0.0] * q
        for idx in combo:
            point[idx] = 0.5
        points.append(point)

    # Face centroids: three components = 1/3 each (if q >= 3)
    if q >= 3:
        for combo in combinations(range(q), 3):
            point = [0.0] * q
            for idx in combo:
                point[idx] = 1.0 / 3.0
            points.append(point)

    # Higher-order centroids up to overall centroid
    for r in range(4, q + 1):
        for combo in combinations(range(q), r):
            point = [0.0] * q
            for idx in combo:
                point[idx] = 1.0 / r
            points.append(point)

    factor_names = [f.name for f in cfg.factors]
    runs = []
    for i, point in enumerate(points):
        factor_values = {}
        for j, proportion in enumerate(point):
            factor = cfg.factors[j]
            if len(factor.levels) >= 2:
                try:
                    low = float(factor.levels[0])
                    high = float(factor.levels[1])
                    val = low + proportion * (high - low)
                    factor_values[factor_names[j]] = f"{val:.6g}"
                except ValueError:
                    factor_values[factor_names[j]] = f"{proportion:.4f}"
            else:
                factor_values[factor_names[j]] = f"{proportion:.4f}"
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values))
    return runs


def evaluate_design(matrix: DesignMatrix, cfg: DOEConfig) -> dict:
    """Compute design evaluation metrics: D-efficiency, A-efficiency, G-efficiency.

    Returns dict with metric names and values.
    """
    import numpy as np
    from .rsm import _build_design_matrix

    X, col_names = _build_design_matrix(matrix.runs, matrix.factor_names, cfg.factors, model_type="linear")
    n = X.shape[0]  # number of runs
    p = X.shape[1]  # number of parameters

    metrics = {}
    try:
        XtX = X.T @ X
        det_XtX = np.linalg.det(XtX)

        # D-efficiency: (|X'X|^(1/p) / n) * 100
        if det_XtX > 0:
            metrics["d_efficiency"] = float((det_XtX ** (1.0 / p)) / n * 100)
        else:
            metrics["d_efficiency"] = 0.0

        # A-efficiency: p / trace((X'X)^-1)
        try:
            XtX_inv = np.linalg.inv(XtX)
            trace_inv = np.trace(XtX_inv)
            metrics["a_efficiency"] = float(p / trace_inv) if trace_inv > 0 else 0.0
        except np.linalg.LinAlgError:
            metrics["a_efficiency"] = 0.0

        # G-efficiency: p / (n * max(h_ii)) * 100
        try:
            XtX_inv = np.linalg.pinv(XtX)
            H = X @ XtX_inv @ X.T
            max_leverage = float(np.max(np.diag(H)))
            metrics["g_efficiency"] = float(p / (n * max_leverage) * 100) if max_leverage > 0 else 0.0
        except Exception:
            metrics["g_efficiency"] = 0.0

    except Exception:
        metrics["d_efficiency"] = 0.0
        metrics["a_efficiency"] = 0.0
        metrics["g_efficiency"] = 0.0

    return metrics


def _randomize_within_whole_plots(
    runs: list[ExperimentRun],
    seed: int | None = None,
) -> list[ExperimentRun]:
    """Shuffle runs only within each whole plot. Whole-plot order itself
    is preserved so the user runs all subplots of one HTC setting before
    switching to the next."""
    rng = random.Random(seed)
    by_plot: dict[int, list[ExperimentRun]] = {}
    plot_order: list[int] = []
    for run in runs:
        if run.whole_plot_id not in by_plot:
            plot_order.append(run.whole_plot_id)
            by_plot[run.whole_plot_id] = []
        by_plot[run.whole_plot_id].append(run)

    result: list[ExperimentRun] = []
    run_id = 1
    for wp in plot_order:
        plot_runs = by_plot[wp]
        rng.shuffle(plot_runs)
        for r in plot_runs:
            r.run_id = run_id
            run_id += 1
        result.extend(plot_runs)
    return result


def _randomize_run_order(runs: list[ExperimentRun], seed: int | None = None) -> list[ExperimentRun]:
    rng = random.Random(seed)
    blocks: dict[int, list[ExperimentRun]] = {}
    for run in runs:
        blocks.setdefault(run.block_id, []).append(run)

    result = []
    run_id = 1
    for block_id in sorted(blocks.keys()):
        block_runs = blocks[block_id]
        rng.shuffle(block_runs)
        for run in block_runs:
            run.run_id = run_id
            run_id += 1
        result.extend(block_runs)
    return result
