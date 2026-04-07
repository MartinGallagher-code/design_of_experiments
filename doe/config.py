# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
from .models import DOEConfig, Factor, ResponseVar, RunnerConfig

SUPPORTED_OPERATIONS = {
    "full_factorial",
    "plackett_burman",
    "latin_hypercube",
    "central_composite",
    "fractional_factorial",
    "box_behnken",
    "definitive_screening",
    "taguchi",
    "d_optimal",
    "mixture_simplex_lattice",
    "mixture_simplex_centroid",
    "linear_sweep",
    "log_sweep",
}


def load_config(path: str, strict: bool = True) -> DOEConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: '{path}'")
    with open(path) as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in '{path}': {e.msg}", e.doc, e.pos
            ) from None

    factors = _parse_factors(raw.get("factors", []))
    fixed_factors = _parse_fixed_factors(raw)
    responses = _parse_responses(raw.get("responses", []))
    settings = raw.get("settings", {})
    metadata = raw.get("metadata", {})
    runner = _parse_runner(raw.get("runner", {}))

    adaptive = _parse_adaptive(raw.get("adaptive", None))

    cfg = DOEConfig(
        factors=factors,
        fixed_factors=fixed_factors,
        responses=responses,
        block_count=settings.get("block_count", 1),
        test_script=settings.get("test_script", ""),
        operation=settings.get("operation", "full_factorial"),
        processed_directory=settings.get("processed_directory", ""),
        out_directory=settings.get("out_directory", ""),
        lhs_samples=settings.get("lhs_samples", 0),
        sweep_points=settings.get("sweep_points", 0),
        metadata=metadata,
        runner=runner,
        adaptive=adaptive,
    )

    _validate_config(cfg, strict=strict)
    return cfg


def _parse_factors(raw: list) -> list[Factor]:
    factors = []
    for item in raw:
        if isinstance(item, dict):
            name = item.get("name")
            levels = item.get("levels", [])
            if not name or len(levels) < 2:
                raise ValueError(f"Factor must have a name and at least 2 levels: {item}")
            factors.append(Factor(
                name=name,
                levels=[str(l) for l in levels],
                type=item.get("type", "categorical"),
                description=item.get("description", ""),
                unit=item.get("unit", ""),
                dtype=item.get("dtype", ""),
            ))
        elif isinstance(item, list):
            # legacy array format: ["name", "val1", "val2", ...]
            if not item or len(item) < 2:
                raise ValueError(f"Factor must have a name and at least one level: {item}")
            factors.append(Factor(name=item[0], levels=list(item[1:])))
        else:
            raise ValueError(f"Unexpected factor format: {item}")
    return factors


def _parse_fixed_factors(raw: dict) -> dict[str, str]:
    if "fixed_factors" in raw:
        return {k: str(v) for k, v in raw["fixed_factors"].items()}
    # Legacy: convert static_settings list of "--key=value" strings
    result = {}
    for s in raw.get("static_settings", []):
        s = s.strip()
        if s.startswith("--"):
            s = s[2:]
        if "=" in s:
            k, v = s.split("=", 1)
            result[k] = v
    return result


def _parse_responses(raw: list) -> list[ResponseVar]:
    if not raw:
        return [ResponseVar(name="response")]
    responses = []
    for item in raw:
        if isinstance(item, dict):
            name = item.get("name")
            if not name:
                raise ValueError(f"Response must have a name: {item}")
            responses.append(ResponseVar(
                name=name,
                optimize=item.get("optimize", "maximize"),
                unit=item.get("unit", ""),
                description=item.get("description", ""),
                weight=float(item.get("weight", 1.0)),
                bounds=item.get("bounds"),
            ))
        elif isinstance(item, str):
            responses.append(ResponseVar(name=item))
        else:
            raise ValueError(f"Unexpected response format: {item}")
    return responses


def _parse_runner(raw: dict) -> RunnerConfig:
    return RunnerConfig(
        arg_style=raw.get("arg_style", "double-dash"),
        result_file=raw.get("result_file", "json"),
    )


def _parse_adaptive(raw) -> object:
    """Parse optional adaptive experimentation settings."""
    if raw is None:
        return None
    from doe.adaptive import AdaptiveConfig
    return AdaptiveConfig(
        strategy=raw.get("strategy", "refine"),
        batch_size=raw.get("batch_size", 4),
        stopping_effect_threshold=float(raw.get("stopping_effect_threshold", 0.0)),
        stopping_power_threshold=float(raw.get("stopping_power_threshold", 0.0)),
        stopping_max_phases=int(raw.get("stopping_max_phases", 10)),
        response_name=raw.get("response_name"),
    )


def _is_sweep_factor(f: Factor) -> bool:
    """Return True if this factor should be expanded by a sweep operation.

    A factor is swept when it has exactly 2 levels that can be interpreted
    as a numeric (min, max) range.  Categorical factors are never swept —
    their levels are discrete choices.  Factors with >2 levels or
    non-numeric levels are kept as-is (passed through to the full factorial
    cross).
    """
    if f.type == "categorical":
        return False
    if len(f.levels) != 2:
        return False
    try:
        float(f.levels[0])
        float(f.levels[1])
        return True
    except ValueError:
        return False


def _validate_config(cfg: DOEConfig, strict: bool = True) -> None:
    if cfg.operation not in SUPPORTED_OPERATIONS:
        raise ValueError(
            f"Unsupported operation '{cfg.operation}'. "
            f"Choose from: {sorted(SUPPORTED_OPERATIONS)}"
        )

    if not cfg.factors:
        raise ValueError("At least one factor is required.")

    names = [f.name for f in cfg.factors]
    if len(names) != len(set(names)):
        raise ValueError(f"Factor names must be unique, got: {names}")

    if cfg.block_count < 1:
        raise ValueError(f"block_count must be >= 1, got {cfg.block_count}")

    if cfg.operation == "plackett_burman":
        for f in cfg.factors:
            if len(f.levels) != 2:
                raise ValueError(
                    f"Plackett-Burman requires exactly 2 levels per factor, "
                    f"but factor '{f.name}' has {len(f.levels)}: {f.levels}"
                )

    if cfg.operation == "fractional_factorial":
        for f in cfg.factors:
            if len(f.levels) != 2:
                raise ValueError(
                    f"Fractional factorial requires exactly 2 levels per factor, "
                    f"but factor '{f.name}' has {len(f.levels)}: {f.levels}"
                )

    if cfg.operation == "box_behnken":
        if len(cfg.factors) < 3:
            raise ValueError(
                f"Box-Behnken requires at least 3 factors, "
                f"but only {len(cfg.factors)} were provided."
            )
        for f in cfg.factors:
            if len(f.levels) != 2:
                raise ValueError(
                    f"Box-Behnken requires exactly 2 levels (low, high) per factor, "
                    f"but factor '{f.name}' has {len(f.levels)}: {f.levels}"
                )
            try:
                float(f.levels[0])
                float(f.levels[1])
            except ValueError:
                raise ValueError(
                    f"Box-Behnken requires numeric levels, "
                    f"but factor '{f.name}' has non-numeric levels: {f.levels}"
                )

    if cfg.operation == "central_composite":
        for f in cfg.factors:
            if len(f.levels) != 2:
                raise ValueError(
                    f"Central composite requires exactly 2 levels (low, high) per factor, "
                    f"but factor '{f.name}' has {len(f.levels)}: {f.levels}"
                )
            try:
                float(f.levels[0])
                float(f.levels[1])
            except ValueError:
                raise ValueError(
                    f"Central composite requires numeric levels, "
                    f"but factor '{f.name}' has non-numeric levels: {f.levels}"
                )

    if cfg.operation == "definitive_screening":
        if len(cfg.factors) < 3:
            raise ValueError(
                f"Definitive Screening Design requires at least 3 factors, "
                f"but only {len(cfg.factors)} were provided."
            )
        for f in cfg.factors:
            if len(f.levels) != 2:
                raise ValueError(
                    f"Definitive Screening Design requires exactly 2 levels (low, high) per factor, "
                    f"but factor '{f.name}' has {len(f.levels)}: {f.levels}"
                )
            try:
                float(f.levels[0])
                float(f.levels[1])
            except ValueError:
                raise ValueError(
                    f"Definitive Screening Design requires numeric levels, "
                    f"but factor '{f.name}' has non-numeric levels: {f.levels}"
                )

    if cfg.operation == "linear_sweep":
        for f in cfg.factors:
            if not _is_sweep_factor(f):
                continue  # non-numeric or >2 levels pass through as-is
            try:
                float(f.levels[0])
                float(f.levels[1])
            except ValueError:
                raise ValueError(
                    f"linear_sweep requires numeric levels for 2-level factors, "
                    f"but factor '{f.name}' has non-numeric levels: {f.levels}"
                )

    if cfg.operation == "log_sweep":
        for f in cfg.factors:
            if not _is_sweep_factor(f):
                continue  # non-numeric or >2 levels pass through as-is
            try:
                low = float(f.levels[0])
                high = float(f.levels[1])
                if low <= 0 or high <= 0:
                    raise ValueError(
                        f"log_sweep requires positive levels, "
                        f"but factor '{f.name}' has levels: {f.levels}"
                    )
            except ValueError as e:
                if "log_sweep requires positive" in str(e):
                    raise
                raise ValueError(
                    f"log_sweep requires numeric positive levels, "
                    f"but factor '{f.name}' has non-numeric levels: {f.levels}"
                )

    response_names = [r.name for r in cfg.responses]
    if len(response_names) != len(set(response_names)):
        raise ValueError(f"Response names must be unique, got: {response_names}")

    valid_optimize = {"maximize", "minimize"}
    for r in cfg.responses:
        if r.optimize not in valid_optimize:
            raise ValueError(
                f"Response '{r.name}' has invalid optimize='{r.optimize}'. "
                f"Choose from: {sorted(valid_optimize)}"
            )

    valid_arg_styles = {"double-dash", "env", "positional"}
    if cfg.runner.arg_style not in valid_arg_styles:
        raise ValueError(
            f"runner.arg_style '{cfg.runner.arg_style}' is invalid. "
            f"Choose from: {sorted(valid_arg_styles)}"
        )

    if strict and cfg.test_script and not os.path.exists(cfg.test_script):
        print(
            f"Warning: test_script '{cfg.test_script}' does not exist. "
            "The generated script may not run correctly."
        )
