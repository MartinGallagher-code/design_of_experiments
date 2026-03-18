import itertools
import random
from .models import DOEConfig, DesignMatrix, ExperimentRun


def generate_design(cfg: DOEConfig, seed: int | None = None) -> DesignMatrix:
    if cfg.operation == "full_factorial":
        base_runs = _full_factorial(cfg)
    elif cfg.operation == "plackett_burman":
        base_runs = _plackett_burman(cfg)
    else:
        raise ValueError(f"Unknown operation: {cfg.operation}")

    runs = _apply_blocks(base_runs, cfg.block_count, cfg.static_settings)
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
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values, static_settings=[]))
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
        runs.append(ExperimentRun(run_id=i + 1, block_id=1, factor_values=factor_values, static_settings=[]))
    return runs


def _apply_blocks(
    base_runs: list[ExperimentRun],
    block_count: int,
    static_settings: list[str],
) -> list[ExperimentRun]:
    all_runs = []
    run_id = 1
    for block_id in range(1, block_count + 1):
        for base in base_runs:
            all_runs.append(
                ExperimentRun(
                    run_id=run_id,
                    block_id=block_id,
                    factor_values=dict(base.factor_values),
                    static_settings=list(static_settings),
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
