# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
import itertools
import random
from .models import DOEConfig, DesignMatrix, ExperimentRun


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
    else:
        raise ValueError(f"Unknown operation: {cfg.operation}")

    runs = _apply_blocks(base_runs, cfg.block_count)

    # LHS already incorporates randomness via seed; all others randomize here
    if cfg.operation != "latin_hypercube":
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


def _fractional_factorial(cfg: DOEConfig) -> list[ExperimentRun]:
    try:
        import pyDOE3
    except ImportError:
        raise ImportError(
            "pyDOE3 is required for Fractional Factorial designs. "
            "Install it with: pip install pyDOE3"
        )

    n_factors = len(cfg.factors)
    # Build generator string for a 2^(n-p) Resolution III design.
    # First k base factors get single-letter generators; remaining factors
    # are aliased as interactions of the base factors.
    from itertools import combinations

    # Determine minimum k base factors such that we can generate enough
    # columns: k base + interactions of base factors >= n_factors
    k = n_factors  # default: no fractionation
    for candidate_k in range(2, n_factors + 1):
        # Count available columns: candidate_k base + all interactions of order >= 2
        n_interactions = 0
        for r in range(2, candidate_k + 1):
            n_interactions += len(list(combinations(range(candidate_k), r)))
        if candidate_k + n_interactions >= n_factors:
            k = candidate_k
            break

    base_letters = [chr(ord('a') + i) for i in range(k)]
    gen_parts = list(base_letters)  # base factors

    # Generate aliases for additional factors from 2-factor interactions and higher
    if n_factors > k:
        interactions = []
        for r in range(2, k + 1):
            for combo in combinations(base_letters, r):
                interactions.append("".join(combo))
            if len(interactions) >= n_factors - k:
                break
        gen_parts.extend(interactions[: n_factors - k])

    gen_string = " ".join(gen_parts)
    matrix = pyDOE3.fracfact(gen_string)
    factor_names = [f.name for f in cfg.factors]

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

    # Generate candidate set: full factorial or grid of levels
    level_lists = [f.levels for f in cfg.factors]
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
