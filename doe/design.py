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
    else:
        raise ValueError(f"Unknown operation: {cfg.operation}")

    runs = _apply_blocks(base_runs, cfg.block_count)

    # LHS already incorporates randomness via seed; all others randomize here
    if cfg.operation != "latin_hypercube":
        runs = _randomize_run_order(runs, seed=seed)

    factor_names = [f.name for f in cfg.factors]
    n_base = len(base_runs)

    return DesignMatrix(
        runs=runs,
        factor_names=factor_names,
        operation=cfg.operation,
        metadata={
            "n_factors": len(cfg.factors),
            "n_base_runs": n_base,
            "n_blocks": cfg.block_count,
            "n_total_runs": len(runs),
            "seed": seed,
        },
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
