import json
import os
from .models import DOEConfig, Factor

SUPPORTED_OPERATIONS = {"full_factorial", "plackett_burman"}


def load_config(path: str, strict: bool = True) -> DOEConfig:
    with open(path) as f:
        raw = json.load(f)

    factors = _parse_factors(raw.get("factors", []))
    static_settings = raw.get("static_settings", [])
    settings = raw.get("settings", {})

    cfg = DOEConfig(
        factors=factors,
        static_settings=static_settings,
        block_count=settings.get("block_count", 1),
        test_script=settings.get("test_script", ""),
        operation=settings.get("operation", "full_factorial"),
        processed_directory=settings.get("processed_directory", ""),
        out_directory=settings.get("out_directory", ""),
    )

    _validate_config(cfg, strict=strict)
    return cfg


def _parse_factors(raw: list) -> list[Factor]:
    factors = []
    for item in raw:
        if not item or len(item) < 2:
            raise ValueError(f"Factor must have a name and at least one level: {item}")
        factors.append(Factor(name=item[0], levels=list(item[1:])))
    return factors


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

    if strict and cfg.test_script and not os.path.exists(cfg.test_script):
        print(
            f"Warning: test_script '{cfg.test_script}' does not exist. "
            "The generated script may not run correctly."
        )
