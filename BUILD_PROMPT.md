# Build Prompt: Design of Experiments (DOE) Helper Tool

Use this prompt with an AI coding assistant to recreate this project from scratch.
Every source file is included verbatim below — copy them into the specified paths.

---

## Project Overview

- **Package name:** `doehelper`
- **Version:** 0.1.0
- **License:** GPL-3.0-or-later
- **Author:** Martin J. Gallagher
- **Python:** >=3.10
- **Entry point:** `doe` (maps to `doe.cli:main`)
- **Repository:** https://github.com/MartinGallagher-code/design_of_experiments
- **Homepage:** https://doehelper.com

---

## Directory Structure

```
design_of_experiments/
├── .github/workflows/
│   ├── ci.yml
│   ├── pages.yml
│   └── publish.yml
├── doe/
│   ├── __init__.py
│   ├── models.py
│   ├── config.py
│   ├── design.py
│   ├── analysis.py
│   ├── rsm.py
│   ├── optimize.py
│   ├── report.py
│   ├── codegen.py
│   ├── cli.py
│   ├── templates/
│   │   ├── __init__.py          (empty)
│   │   ├── runner_sh.j2
│   │   └── runner_py.j2
│   └── use_cases/
│       ├── __init__.py          (empty)
│       └── 01_reactor_optimization/  (+ 220 more use cases)
│           ├── config.json
│           ├── sim.sh
│           └── README.md
├── tests/
│   ├── __init__.py              (empty)
│   └── test_doe.py
├── website/
│   ├── css/style.css
│   ├── css/usecase.css
│   ├── js/
│   ├── images/                  (~4,981 PNG plot files)
│   ├── use-cases/               (221 HTML pages)
│   ├── index.html
│   ├── book.html
│   ├── howto.html
│   ├── quickstart.html
│   ├── ai-prompts.html
│   ├── ai-config-prompt.txt
│   ├── ai-testscript-prompt.txt
│   ├── logo.svg
│   ├── logo-light.svg
│   ├── CNAME
│   └── .nojekyll
├── training/
│   ├── generate_slides.py
│   ├── exercises.md
│   ├── teaching_notes.md
│   └── slides/                  (8 PowerPoint modules)
├── docs/
│   ├── book/
│   │   ├── doe_guide.tex
│   │   ├── doe_guide.pdf
│   │   ├── user_guide.tex
│   │   └── user_guide.pdf
│   └── doe_fundamentals.md
├── doe.py
├── add_multi_opt.py
├── generate_new_plots.py
├── generate_website_pages.py
├── pyproject.toml
├── requirements.txt
├── MANIFEST.in
├── README.md
├── CHANGELOG.md
├── LICENSE
└── build_prompt.md
```

---

## Step 1: Configuration Files

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "doehelper"
version = "0.1.0"
description = "A Design of Experiments (DOE) helper tool"
readme = "README.md"
authors = [{name = "Martin J. Gallagher"}]
requires-python = ">=3.10"
license = "GPL-3.0-or-later"
keywords = [
    "doe",
    "doehelper",
    "experiment",
    "factorial",
    "statistics",
    "anova",
    "response-surface",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering",
]
dependencies = [
    "pyDOE3>=1.0.0",
    "numpy>=1.26.0",
    "pandas>=2.0.0",
    "matplotlib>=3.7.0",
    "scipy>=1.11.0",
    "Jinja2>=3.1.0",
]

[project.urls]
Homepage = "https://doehelper.com"
Documentation = "https://doehelper.com"
Repository = "https://github.com/MartinGallagher-code/design_of_experiments"
"Bug Tracker" = "https://github.com/MartinGallagher-code/design_of_experiments/issues"

[project.scripts]
doe = "doe.cli:main"

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov"]

[tool.setuptools.packages.find]
where = ["."]
include = ["doe*"]

[tool.setuptools.package-data]
doe = ["templates/*.j2", "use_cases/*/config.json", "use_cases/*/sim.sh", "use_cases/*/README.md"]
```

### `requirements.txt`

```
pyDOE3>=1.0.0
numpy>=1.26.0
pandas>=2.0.0
matplotlib>=3.7.0
scipy>=1.11.0
Jinja2>=3.1.0
```

### `MANIFEST.in`

```
include LICENSE
include README.md
recursive-include doe/templates *.j2
recursive-include doe/use_cases *.json *.sh *.md
recursive-include tests *
```

### `doe.py` (thin CLI wrapper)

```python
#!/usr/bin/env python3
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Design of Experiments helper tool — thin wrapper for direct execution."""

from doe.cli import main

if __name__ == "__main__":
    main()
```

---

## Step 2: Core Library (`doe/` package)

### `doe/__init__.py`

```python
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Design of Experiments (DOE) helper tool."""

__version__ = "0.1.0"
```

### `doe/models.py`

```python
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass, field


@dataclass
class Factor:
    name: str
    levels: list[str]
    type: str = "categorical"   # categorical | continuous | ordinal
    description: str = ""
    unit: str = ""


@dataclass
class ResponseVar:
    name: str
    optimize: str = "maximize"  # maximize | minimize
    unit: str = ""
    description: str = ""
    weight: float = 1.0
    bounds: list[float] | None = None  # [low, high] for desirability


@dataclass
class RunnerConfig:
    arg_style: str = "double-dash"  # double-dash | env | positional
    result_file: str = "json"


@dataclass
class DOEConfig:
    factors: list[Factor]
    fixed_factors: dict[str, str]
    responses: list[ResponseVar]
    block_count: int
    test_script: str
    operation: str
    processed_directory: str
    out_directory: str
    lhs_samples: int = 0                    # 0 = auto: max(10, 2 * n_factors)
    metadata: dict = field(default_factory=dict)
    runner: RunnerConfig = field(default_factory=RunnerConfig)


@dataclass
class ExperimentRun:
    run_id: int
    block_id: int
    factor_values: dict[str, str]


@dataclass
class DesignMatrix:
    runs: list[ExperimentRun]
    factor_names: list[str]
    operation: str
    metadata: dict = field(default_factory=dict)


@dataclass
class EffectResult:
    factor_name: str
    main_effect: float
    std_error: float
    pct_contribution: float
    ci_low: float = 0.0
    ci_high: float = 0.0


@dataclass
class InteractionEffect:
    factor_a: str
    factor_b: str
    interaction_effect: float
    pct_contribution: float


@dataclass
class AnovaRow:
    source: str
    df: int
    ss: float
    ms: float
    f_value: float | None = None
    p_value: float | None = None


@dataclass
class AnovaTable:
    rows: list[AnovaRow]
    error_row: AnovaRow | None = None
    total_row: AnovaRow | None = None
    lack_of_fit_row: AnovaRow | None = None
    pure_error_row: AnovaRow | None = None
    error_method: str = "pooled"  # "pooled", "lenth", "replicates"


@dataclass
class ResponseAnalysis:
    response_name: str
    effects: list[EffectResult]
    summary_stats: dict
    interactions: list[InteractionEffect] = field(default_factory=list)
    anova_table: AnovaTable | None = None


@dataclass
class AnalysisReport:
    results_by_response: dict[str, ResponseAnalysis]
    pareto_chart_paths: dict[str, str] = field(default_factory=dict)
    effects_plot_paths: dict[str, str] = field(default_factory=dict)
    normal_plot_paths: dict[str, str] = field(default_factory=dict)
    half_normal_plot_paths: dict[str, str] = field(default_factory=dict)
    diagnostics_plot_paths: dict[str, str] = field(default_factory=dict)
```

### `doe/config.py`

```python
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
        metadata=metadata,
        runner=runner,
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
```

### `doe/design.py`

```python
# Copyright (C) 2026 Martin J. Gallagher
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
    from itertools import combinations

    # Determine minimum k base factors such that we can generate enough
    # columns: k base + interactions of base factors >= n_factors
    k = n_factors  # default: no fractionation
    for candidate_k in range(2, n_factors + 1):
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
    I = np.eye(n_factors)
    top = I.copy()
    bottom = -I.copy()

    # For each pair of columns, randomly assign signs
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
            matrix = pyDOE3.taguchi_design(levels_per_factor)
    except (AttributeError, TypeError):
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
    n_runs = cfg.lhs_samples if cfg.lhs_samples > 0 else max(n_factors + 2, 2 * n_factors)

    # Generate candidate set: full factorial or grid of levels
    level_lists = [f.levels for f in cfg.factors]
    all_candidates = list(itertools.product(*level_lists))

    if len(all_candidates) <= n_runs:
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

    points = []
    for combo in combinations_with_replacement(range(q), m):
        point = [0.0] * q
        for idx in combo:
            point[idx] += 1.0 / m
        if point not in points:
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


def _mixture_simplex_centroid(cfg: DOEConfig) -> list[ExperimentRun]:
    """Generate a simplex-centroid design for mixture experiments.

    Includes: vertices, edge midpoints, face centroids, and overall centroid.
    """
    from itertools import combinations

    q = len(cfg.factors)
    points = []

    # Vertices
    for i in range(q):
        point = [0.0] * q
        point[i] = 1.0
        points.append(point)

    # Edge midpoints
    for combo in combinations(range(q), 2):
        point = [0.0] * q
        for idx in combo:
            point[idx] = 0.5
        points.append(point)

    # Face centroids (if q >= 3)
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
    """Compute design evaluation metrics: D-efficiency, A-efficiency, G-efficiency."""
    import numpy as np
    from .rsm import _build_design_matrix

    X, col_names = _build_design_matrix(matrix.runs, matrix.factor_names, cfg.factors, model_type="linear")
    n = X.shape[0]
    p = X.shape[1]

    metrics = {}
    try:
        XtX = X.T @ X
        det_XtX = np.linalg.det(XtX)

        if det_XtX > 0:
            metrics["d_efficiency"] = float((det_XtX ** (1.0 / p)) / n * 100)
        else:
            metrics["d_efficiency"] = 0.0

        try:
            XtX_inv = np.linalg.inv(XtX)
            trace_inv = np.trace(XtX_inv)
            metrics["a_efficiency"] = float(p / trace_inv) if trace_inv > 0 else 0.0
        except np.linalg.LinAlgError:
            metrics["a_efficiency"] = 0.0

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
```

### `doe/rsm.py`

```python
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Response Surface Modeling for DOE results."""

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from .models import DesignMatrix, DOEConfig, ExperimentRun, Factor


@dataclass
class ModelDiagnostics:
    residuals: list[float]
    fitted_values: list[float]
    hat_matrix_diag: list[float]  # leverage values
    press: float  # PRESS statistic
    predicted_r_squared: float
    run_ids: list[int] = field(default_factory=list)


@dataclass
class RSMModel:
    response_name: str
    coefficients: dict[str, float]  # {"intercept": ..., "A": ..., "B": ..., "A*B": ..., "A^2": ...}
    r_squared: float
    adj_r_squared: float
    predicted_optimum: dict[str, str]  # factor_name -> level_value
    predicted_value: float
    diagnostics: ModelDiagnostics | None = None


def _encode_factor_value(value: str, factor) -> float:
    """Encode a factor value as a numeric value for regression.

    - For continuous/ordinal factors: normalize as (value - center) / half_range
    - For categorical factors with 2 levels: encode as -1/+1
    - For categorical factors with >2 levels: encode as index (fallback)
    """
    levels = factor.levels
    if factor.type in ("continuous", "ordinal"):
        try:
            numeric_vals = [float(lv) for lv in levels]
            val = float(value)
            center = (max(numeric_vals) + min(numeric_vals)) / 2.0
            half_range = (max(numeric_vals) - min(numeric_vals)) / 2.0
            if half_range == 0:
                return 0.0
            return (val - center) / half_range
        except ValueError:
            pass

    # Categorical encoding
    sorted_levels = sorted(levels)
    if len(sorted_levels) == 2:
        return -1.0 if value == sorted_levels[0] else 1.0
    else:
        idx = sorted_levels.index(value) if value in sorted_levels else 0
        center = (len(sorted_levels) - 1) / 2.0
        half_range = (len(sorted_levels) - 1) / 2.0
        if half_range == 0:
            return 0.0
        return (idx - center) / half_range


def _build_design_matrix(
    runs: list[ExperimentRun],
    factor_names: list[str],
    factors: list,
    model_type: str = "linear",
) -> tuple[np.ndarray, list[str]]:
    """Build the design matrix X and return column names.

    For "linear": columns are [1, x1, x2, ...]
    For "quadratic": columns are [1, x1, x2, ..., x1*x2, ..., x1^2, x2^2, ...]
    """
    factor_map = {f.name: f for f in factors}
    n_runs = len(runs)
    n_factors = len(factor_names)

    raw = np.zeros((n_runs, n_factors))
    for i, run in enumerate(runs):
        for j, fname in enumerate(factor_names):
            raw[i, j] = _encode_factor_value(
                run.factor_values[fname], factor_map[fname]
            )

    col_names = ["intercept"] + list(factor_names)
    X = np.column_stack([np.ones(n_runs), raw])

    if model_type == "quadratic":
        for a, b in combinations(range(n_factors), 2):
            col_names.append(f"{factor_names[a]}*{factor_names[b]}")
            X = np.column_stack([X, raw[:, a] * raw[:, b]])
        for j in range(n_factors):
            col_names.append(f"{factor_names[j]}^2")
            X = np.column_stack([X, raw[:, j] ** 2])

    return X, col_names


def fit_rsm(
    runs: list[ExperimentRun],
    responses: dict[int, float],
    factor_names: list[str],
    factors: list,
    model_type: str = "linear",
) -> RSMModel:
    """Fit a polynomial regression model to DOE results."""
    valid_runs = [r for r in runs if r.run_id in responses]
    if not valid_runs:
        return RSMModel(
            response_name="",
            coefficients={"intercept": 0.0},
            r_squared=0.0,
            adj_r_squared=0.0,
            predicted_optimum={},
            predicted_value=0.0,
        )

    X, col_names = _build_design_matrix(valid_runs, factor_names, factors, model_type)
    y = np.array([responses[r.run_id] for r in valid_runs])

    beta, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)

    y_pred = X @ beta
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    n = len(y)
    p = len(beta) - 1
    if n - p - 1 > 0 and ss_tot > 0:
        adj_r_squared = 1.0 - (ss_res / (n - p - 1)) / (ss_tot / (n - 1))
    else:
        adj_r_squared = r_squared

    coefficients = {col_names[i]: float(beta[i]) for i in range(len(beta))}

    best_idx = int(np.argmax(y_pred))
    best_run = valid_runs[best_idx]
    predicted_optimum = {fname: best_run.factor_values[fname] for fname in factor_names}
    predicted_value = float(y_pred[best_idx])

    # Model diagnostics
    diagnostics = None
    try:
        XtX_inv = np.linalg.pinv(X.T @ X)
        H = X @ XtX_inv @ X.T
        h_diag = np.diag(H)
        resid = y - y_pred

        press_residuals = resid / (1.0 - h_diag + 1e-12)
        press = float(np.sum(press_residuals ** 2))
        predicted_r_squared = 1.0 - press / ss_tot if ss_tot > 0 else 0.0

        diagnostics = ModelDiagnostics(
            residuals=[float(r) for r in resid],
            fitted_values=[float(f) for f in y_pred],
            hat_matrix_diag=[float(h) for h in h_diag],
            press=press,
            predicted_r_squared=predicted_r_squared,
            run_ids=[r.run_id for r in valid_runs],
        )
    except Exception:
        pass

    return RSMModel(
        response_name="",
        coefficients=coefficients,
        r_squared=r_squared,
        adj_r_squared=adj_r_squared,
        predicted_optimum=predicted_optimum,
        predicted_value=predicted_value,
        diagnostics=diagnostics,
    )


def optimize_surface(
    model: RSMModel,
    factor_names: list[str],
    factors: list,
    direction: str = "maximize",
    n_restarts: int = 10,
) -> dict:
    """Find the true optimum of a fitted RSM surface using scipy.optimize.

    Uses L-BFGS-B with multiple random restarts to avoid local optima.
    """
    from scipy.optimize import minimize as scipy_minimize

    coefs = model.coefficients
    n_factors = len(factor_names)

    def predict_coded(x_coded):
        val = coefs.get("intercept", 0.0)
        for i, fname in enumerate(factor_names):
            val += coefs.get(fname, 0.0) * x_coded[i]
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                key = f"{factor_names[i]}*{factor_names[j]}"
                val += coefs.get(key, 0.0) * x_coded[i] * x_coded[j]
            key = f"{factor_names[i]}^2"
            val += coefs.get(key, 0.0) * x_coded[i] ** 2
        return val

    def objective(x_coded):
        val = predict_coded(x_coded)
        return -val if direction == "maximize" else val

    bounds = [(-1.0, 1.0)] * n_factors
    rng = np.random.default_rng(42)

    best_result = None
    best_obj = float('inf')

    for _ in range(n_restarts):
        x0 = rng.uniform(-1, 1, size=n_factors)
        try:
            result = scipy_minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
            if result.fun < best_obj:
                best_obj = result.fun
                best_result = result
        except Exception:
            continue

    if best_result is None:
        return {"optimal_settings": {}, "predicted_value": 0.0, "converged": False}

    factor_map = {f.name: f for f in factors}
    optimal_settings = {}
    for i, fname in enumerate(factor_names):
        factor = factor_map[fname]
        coded_val = best_result.x[i]
        if factor.type in ("continuous", "ordinal"):
            try:
                low = float(factor.levels[0])
                high = float(factor.levels[1])
                center = (low + high) / 2.0
                half_range = (high - low) / 2.0
                optimal_settings[fname] = f"{center + coded_val * half_range:.6g}"
            except ValueError:
                optimal_settings[fname] = f"{coded_val:.4f}"
        else:
            optimal_settings[fname] = factor.levels[1] if coded_val > 0 else factor.levels[0]

    predicted_value = predict_coded(best_result.x)

    return {
        "optimal_settings": optimal_settings,
        "predicted_value": float(predicted_value),
        "converged": bool(best_result.success),
    }


def steepest_ascent(
    model: RSMModel,
    factor_names: list[str],
    factors: list,
    direction: str = "maximize",
    n_steps: int = 10,
) -> list[dict]:
    """Generate a steepest ascent/descent pathway from a linear RSM model."""
    coefs = model.coefficients
    factor_map = {f.name: f for f in factors}

    gradient = np.array([coefs.get(fname, 0.0) for fname in factor_names])
    if direction == "minimize":
        gradient = -gradient

    max_grad = np.max(np.abs(gradient))
    if max_grad == 0:
        return []
    step_vector = gradient / max_grad

    pathway = []
    for step in range(n_steps + 1):
        coded_point = step_vector * step * 0.5
        settings = {}
        predicted = coefs.get("intercept", 0.0)
        for i, fname in enumerate(factor_names):
            factor = factor_map[fname]
            coded_val = coded_point[i]
            predicted += coefs.get(fname, 0.0) * coded_val

            if factor.type in ("continuous", "ordinal"):
                try:
                    low = float(factor.levels[0])
                    high = float(factor.levels[1])
                    center = (low + high) / 2.0
                    half_range = (high - low) / 2.0
                    settings[fname] = f"{center + coded_val * half_range:.6g}"
                except ValueError:
                    settings[fname] = f"{coded_val:.4f}"
            else:
                settings[fname] = factor.levels[1] if coded_val > 0 else factor.levels[0]

        pathway.append({
            "step": step,
            "settings": settings,
            "predicted_value": float(predicted),
        })

    return pathway
```

### `doe/analysis.py`

This file is 989 lines. The complete implementation handles:
- Loading result JSON files (`_load_all_results`)
- Computing main effects with pooled std error and 95% CI via scipy.stats.t (`_compute_main_effects`)
- Computing two-factor interaction effects via concordant/discordant means (`_compute_interaction_effects`)
- Computing per-level summary statistics (`_compute_summary_stats`)
- Computing ANOVA with Type I sequential SS, support for replicated (pure error), pooled, and Lenth PSE error estimation (`_compute_anova`)
- Pareto chart, main effects plot, RSM surface plots, diagnostics (2x2 panel: residuals vs fitted, Q-Q, run order, predicted vs actual), normal probability plot (Filliben approximation), half-normal probability plot
- CSV export of effects and summary statistics

The complete source code is provided in the `doe/analysis.py` section of the `build_prompt.md` file (lowercase). Both files together constitute the full build reference. For the complete verbatim code of `analysis.py`, see the companion file or reconstruct from the algorithm descriptions and function signatures below.

**Key implementation details for `analysis.py`:**

1. **`_compute_main_effects`**: For 2-level factors, effect = high_mean - low_mean. For multi-level, effect = max_mean - min_mean. Uses pooled variance for std_error. CIs use scipy.stats.t with pooled SE and (n_low + n_high - 2) df. Percentage contribution = |effect| / sum(|effects|) * 100. Results sorted by |effect| descending.

2. **`_compute_interaction_effects`**: Only for pairs of 2-level factors. Concordant = both high or both low; discordant = one high, one low. Effect = mean(concordant) - mean(discordant).

3. **`_compute_anova`**: Type I sequential SS. For each factor: SS = sum_over_levels(n_i * (mean_i - grand_mean)^2). Interaction SS = SS_AB_total - SS_A - SS_B. Three error methods:
   - **replicates**: pure error from identical factor settings, lack-of-fit F-test
   - **pooled**: standard residual error when df_error > 0
   - **lenth**: Lenth's PSE = 1.5 * median(|effects|), trimmed at 2.5*s0, df ≈ n_effects/3

4. **`plot_pareto`**: Horizontal bar chart with cumulative % line on twin axis, 80% threshold marker.

5. **`plot_rsm_surface`**: Fits quadratic RSM, creates 40x40 grid for each pair of continuous factors, predicts Z from coefficients in coded space, renders 3D surface with actual data scattered on top.

6. **`plot_normal_effects`**: Filliben quantiles: norm.ppf((i+1-0.375)/(n+0.25)). Reference line through Q1/Q3. Labels points deviating > 1.5× mean residual.

7. **`plot_half_normal_effects`**: Uses halfnorm.ppf. Reference line through origin and median. Labels deviating points.

8. **`plot_diagnostics`**: 2×2 panel using scipy.stats.probplot for Q-Q.

### `doe/optimize.py`

This file is 513 lines containing two main functions:

1. **`recommend()`**: For each response, finds best observed run, fits linear + quadratic RSM models, reports coefficients, curvature analysis (concave/convex from ^2 terms), notable interactions (|coef| > 0.3), predicted optimum, surface optimization via L-BFGS-B, model quality rating (Excellent/Good/Moderate/Weak based on R²), and factor importance ranking.

2. **`multi_objective()`**: Derringer-Suich desirability functions. Individual desirability d = linear ramp [0,1] between bounds (direction-aware). Overall D = weighted geometric mean (exp(sum(w_i * log(d_i)) / sum(w_i))). Grid search over factor space (meshgrid for ≤3 factors, 5000 random samples for more). Reports response table, recommended settings, trade-off summary, model quality, top 3 runs.

The complete source code for `optimize.py` follows the same patterns as the other files. Both `recommend()` and `multi_objective()` import from `analysis._load_all_results`, `analysis._compute_main_effects`, and `rsm.fit_rsm`.

### `doe/report.py`

This file is 771 lines generating self-contained HTML reports. Key components:

1. **`generate_report()`**: Runs analysis, encodes all plot images as base64 data URIs, collects RSM surface plots via glob, runs optimization analysis, builds HTML sections, writes output.

2. **HTML template** (`_HTML_TEMPLATE`): Standard HTML5 with `{title}`, `{css}`, `{header}`, `{design_summary}`, `{results}`, `{optimization}`, `{design_matrix}`, `{footer}` placeholders.

3. **CSS** (`_CSS`): Uses CSS custom properties (--accent: steelblue, --bg, --bg-alt, --text, --border, --mono). Collapsible `<details>` sections with arrow rotation animation. Responsive at 700px breakpoint. Data tables with alternating row colors and hover effects.

4. **Section builders**: `_build_header`, `_build_design_summary` (factor details table), `_build_results` (effects table, ANOVA table with significant terms bolded, interaction effects, summary stats, embedded plots), `_build_optimization` (best run, RSM coefficients, predicted optimum, factor importance), `_build_design_matrix`, `_build_footer`.

The complete CSS and HTML template are critical — see the companion `build_prompt.md` for the full verbatim `_CSS` and `_HTML_TEMPLATE` strings, or use the CSS variables and structure described above to reconstruct.

### `doe/codegen.py`

```python
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
import stat
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, PackageLoader

from .models import DesignMatrix, DOEConfig


def generate_script(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    output_path: str,
    format: str = "sh",
) -> str:
    template_map = {"sh": "runner_sh.j2", "py": "runner_py.j2"}
    if format not in template_map:
        raise ValueError(f"Unknown format '{format}'. Choose 'sh' or 'py'.")

    env = Environment(
        loader=PackageLoader("doe", "templates"),
        keep_trailing_newline=True,
    )
    env.filters["tojson"] = _tojson

    template = env.get_template(template_map[format])
    context = _build_template_context(matrix, cfg)
    rendered = template.render(**context)

    output_dir = Path(output_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(rendered)

    path = Path(output_path)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return rendered


def _build_template_context(matrix: DesignMatrix, cfg: DOEConfig) -> dict:
    runs_data = [
        {
            "run_id": run.run_id,
            "block_id": run.block_id,
            "factor_values": run.factor_values,
        }
        for run in matrix.runs
    ]
    test_script = str(Path(cfg.test_script).resolve()) if cfg.test_script else ""
    out_directory = str(Path(cfg.out_directory or "results").resolve())
    return {
        "runs": runs_data,
        "test_script": test_script,
        "fixed_factors": cfg.fixed_factors,
        "arg_style": cfg.runner.arg_style,
        "out_directory": out_directory,
        "operation": matrix.operation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(matrix.runs),
        "plan_name": cfg.metadata.get("name", ""),
    }


def _tojson(value) -> str:
    import json
    return json.dumps(value)
```

### `doe/cli.py`

This file is 834 lines implementing the CLI with argparse. It defines 12 subcommands:
`generate`, `analyze`, `info`, `optimize`, `report`, `record`, `status`, `power`, `augment`, `init`, `export-worksheet`, and `--version`.

The complete implementation is in the companion `build_prompt.md` file. Key implementation notes:

- **`_dispatch()`** routes to handler functions based on `args.command`
- **`_handle_init()`** discovers templates from `doe/use_cases/` via `importlib.resources.files`, strips numeric prefix for short names, supports fuzzy matching
- **`_handle_record()`** prompts for numeric response values with validation, supports `--run all` for batch entry
- **`_handle_status()`** shows progress bar with `#` and `.` characters
- **`_handle_power()`** uses `scipy.stats.f` and `scipy.stats.ncf` for non-central F distribution power computation
- **`_handle_export_worksheet()`** supports CSV and Markdown formats with pre-filled existing results
- **`_print_matrix()`** formats design matrix as aligned columns
- **`_print_report()`** outputs effects, ANOVA, interactions, and summary stats to console
- Error handling wraps `_dispatch()` catching FileNotFoundError, JSONDecodeError, ValueError, PermissionError, and OSError

---

## Step 3: Jinja2 Templates

### `doe/templates/__init__.py`

(empty file)

### `doe/templates/runner_sh.j2`

```jinja2
#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Generated by doe on {{ timestamp }}
# Operation: {{ operation }}
# Total runs: {{ total_runs }}{% if plan_name %}
# Plan: {{ plan_name }}{% endif %}

set -uo pipefail

mkdir -p "{{ out_directory }}"

FAILED_RUNS=()

echo "Starting {{ total_runs }} experiment runs..."
echo ""

{% for run in runs %}
if [[ -f "{{ out_directory }}/run_{{ run.run_id }}.json" ]]; then
  echo "=== Run {{ run.run_id }} / {{ total_runs }} already complete, skipping ==="
else
  echo "=== Run {{ run.run_id }} / {{ total_runs }} (Block {{ run.block_id }}) ==="
{% for name, value in run.factor_values.items() %}  echo "  {{ name }} = {{ value }}"
{% endfor %}
{% if arg_style == "env" %}
{% for name, value in run.factor_values.items() %}  export {{ name | upper }}="{{ value }}"
{% endfor %}{% for name, value in fixed_factors.items() %}  export {{ name | upper }}="{{ value }}"
{% endfor %}  if ! "{{ test_script }}" \
    --out "{{ out_directory }}/run_{{ run.run_id }}.json"; then
    echo "ERROR: Run {{ run.run_id }} failed"
    FAILED_RUNS+=({{ run.run_id }})
  fi
{% elif arg_style == "positional" %}
  if ! "{{ test_script }}" \
{% for name, value in run.factor_values.items() %}    "{{ value }}" \
{% endfor %}{% for name, value in fixed_factors.items() %}    "{{ value }}" \
{% endfor %}    --out "{{ out_directory }}/run_{{ run.run_id }}.json"; then
    echo "ERROR: Run {{ run.run_id }} failed"
    FAILED_RUNS+=({{ run.run_id }})
  fi
{% else %}
  if ! "{{ test_script }}" \
{% for name, value in run.factor_values.items() %}    --{{ name }} "{{ value }}" \
{% endfor %}{% for name, value in fixed_factors.items() %}    --{{ name }} "{{ value }}" \
{% endfor %}    --out "{{ out_directory }}/run_{{ run.run_id }}.json"; then
    echo "ERROR: Run {{ run.run_id }} failed"
    FAILED_RUNS+=({{ run.run_id }})
  fi
{% endif %}
fi

echo ""
{% endfor %}
{% raw %}if [[ ${#FAILED_RUNS[@]} -gt 0 ]]; then
  echo "WARNING: ${#FAILED_RUNS[@]} run(s) failed: ${FAILED_RUNS[*]}"{% endraw %}
  echo "Results (partial) in: {{ out_directory }}"
  exit 1
fi

echo "All runs complete. Results in: {{ out_directory }}"
```

### `doe/templates/runner_py.j2`

```jinja2
#!/usr/bin/env python3
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Generated by doe on {{ timestamp }}
Operation: {{ operation }}
Total runs: {{ total_runs }}{% if plan_name %}
Plan: {{ plan_name }}{% endif %}
"""

import os
import subprocess
import sys

RUNS = [
{% for run in runs %}    {
        "run_id": {{ run.run_id }},
        "block_id": {{ run.block_id }},
        "factors": {{ run.factor_values | tojson }},
    },
{% endfor %}]

TEST_SCRIPT = "{{ test_script }}"
OUT_DIRECTORY = "{{ out_directory }}"
FIXED_FACTORS = {{ fixed_factors | tojson }}
ARG_STYLE = "{{ arg_style }}"

os.makedirs(OUT_DIRECTORY, exist_ok=True)

failed_runs = []

print(f"Starting {{ total_runs }} experiment runs...")

for run in RUNS:
    run_id = run["run_id"]
    block_id = run["block_id"]
    factors = run["factors"]
    out_path = f"{OUT_DIRECTORY}/run_{run_id}.json"

    if os.path.exists(out_path):
        print(f"\n=== Run {run_id} / {{ total_runs }} already complete, skipping ===")
        continue

    print(f"\n=== Run {run_id} / {{ total_runs }} (Block {block_id}) ===")
    for name, value in factors.items():
        print(f"  {name} = {value}")

    try:
        if ARG_STYLE == "env":
            env = dict(os.environ)
            env.update({k.upper(): v for k, v in factors.items()})
            env.update({k.upper(): v for k, v in FIXED_FACTORS.items()})
            subprocess.run([TEST_SCRIPT, "--out", out_path], check=True, env=env)
        elif ARG_STYLE == "positional":
            cmd = [TEST_SCRIPT]
            cmd += list(factors.values())
            cmd += list(FIXED_FACTORS.values())
            cmd += ["--out", out_path]
            subprocess.run(cmd, check=True)
        else:  # double-dash
            cmd = [TEST_SCRIPT]
            for name, value in factors.items():
                cmd += [f"--{name}", value]
            for name, value in FIXED_FACTORS.items():
                cmd += [f"--{name}", value]
            cmd += ["--out", out_path]
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Run {run_id} failed with exit code {e.returncode}")
        failed_runs.append(run_id)

if failed_runs:
    print(f"\nWARNING: {len(failed_runs)} run(s) failed: {failed_runs}")
    print(f"Results (partial) in: {OUT_DIRECTORY}")
    sys.exit(1)

print(f"\nAll runs complete. Results in: {OUT_DIRECTORY}")
```

---

## Step 4: GitHub Actions Workflows

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest tests/ -v --tb=short --cov --cov-report=xml --cov-report=html

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report-py${{ matrix.python-version }}
          path: |
            htmlcov/
            coverage.xml
```

### `.github/workflows/pages.yml`

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: website

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

---

## Step 5: Use Case Template Pattern

Each use case in `doe/use_cases/` follows this pattern. There are 221 use cases spanning domains including HPC, cloud, networking, food science, agriculture, manufacturing, sports, cosmetics, electronics, and more.

### Example: `doe/use_cases/01_reactor_optimization/config.json`

```json
{
    "metadata": {
        "name": "Chemical Reactor Optimization",
        "description": "Box-Behnken design to optimize yield and purity of a batch reactor process"
    },
    "factors": [
        {
            "name": "temperature",
            "levels": ["150", "200"],
            "type": "continuous",
            "unit": "\u00b0C",
            "description": "Reactor temperature"
        },
        {
            "name": "pressure",
            "levels": ["2", "6"],
            "type": "continuous",
            "unit": "bar",
            "description": "Operating pressure"
        },
        {
            "name": "catalyst",
            "levels": ["0.5", "2.0"],
            "type": "continuous",
            "unit": "g/L",
            "description": "Catalyst concentration"
        }
    ],
    "fixed_factors": {
        "reaction_time": "60",
        "stirring_speed": "300"
    },
    "responses": [
        {
            "name": "yield",
            "optimize": "maximize",
            "unit": "%",
            "description": "Product yield percentage",
            "weight": 1.5
        },
        {
            "name": "purity",
            "optimize": "maximize",
            "unit": "%",
            "description": "Product purity percentage",
            "weight": 2.0
        },
        {
            "name": "cost",
            "optimize": "minimize",
            "unit": "USD",
            "description": "Batch production cost",
            "weight": 1.0
        }
    ],
    "runner": {
        "arg_style": "double-dash"
    },
    "settings": {
        "block_count": 1,
        "test_script": "./sim.sh",
        "operation": "box_behnken",
        "processed_directory": "./results/analysis",
        "out_directory": "./results"
    }
}
```

### Example: `doe/use_cases/01_reactor_optimization/sim.sh`

```bash
#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated chemical reactor — produces yield, purity, and cost responses.
#
# The underlying model (hidden from the experimenter):
#   yield  = 70 + 8*(T-175)/25 + 5*(P-4)/2 + 3*(C-1.25)/0.75 - 4*(T-175)^2/625 - 2*(P-4)^2/4 + noise
#   purity = 90 + 3*(T-175)/25 - 2*(P-4)/2 + 6*(C-1.25)/0.75 - 1.5*(T-175)^2/625 + noise
#   cost   = 50 + 12*(T-175)/25 + 8*(P-4)/2 + 4*(C-1.25)/0.75 + 2*(T-175)*(P-4)/50 + noise

set -euo pipefail

OUTFILE=""
TEMP=""
PRESS=""
CATAL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)             OUTFILE="$2"; shift 2 ;;
        --temperature)     TEMP="$2";    shift 2 ;;
        --pressure)        PRESS="$2";   shift 2 ;;
        --catalyst)        CATAL="$2";   shift 2 ;;
        --reaction_time)   shift 2 ;;
        --stirring_speed)  shift 2 ;;
        *)                 shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$TEMP" || -z "$PRESS" || -z "$CATAL" ]]; then
    echo "Usage: reactor_sim.sh --temperature T --pressure P --catalyst C --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v T="$TEMP" -v P="$PRESS" -v C="$CATAL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise1 = (rand() - 0.5) * 4;
    noise2 = (rand() - 0.5) * 3;
    noise3 = (rand() - 0.5) * 5;

    t = (T - 175) / 25;
    p = (P - 4) / 2;
    c = (C - 1.25) / 0.75;

    yield_val = 70 + 8*t + 5*p + 3*c - 4*t*t - 2*p*p + 1.5*t*p + noise1;
    if (yield_val < 0) yield_val = 0;
    if (yield_val > 100) yield_val = 100;

    purity_val = 90 + 3*t - 2*p + 6*c - 1.5*t*t + noise2;
    if (purity_val < 0) purity_val = 0;
    if (purity_val > 100) purity_val = 100;

    cost_val = 50 + 12*t + 8*p + 4*c + 2*t*p + noise3;
    if (cost_val < 0) cost_val = 0;

    printf "{\"yield\": %.2f, \"purity\": %.2f, \"cost\": %.2f}", yield_val, purity_val, cost_val;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
```

### Sim.sh Pattern for All Use Cases

Every `sim.sh` follows the same structure:
1. Parse `--out` and factor arguments via `case` statement
2. Ignore fixed factors with `shift 2`
3. Compute response values using `awk` with a polynomial model + random noise
4. Output JSON to `$OUTFILE`

Each use case has its own domain-appropriate model (e.g., coffee extraction yield, network latency, crop yield).

### Complete List of 221 Use Case Directories

```
01_reactor_optimization, 02_webapp_ab_testing, 03_ml_hyperparameter_screening,
04_database_performance_tuning, 05_material_formulation, 06_distillation_column,
07_mpi_collective_tuning, 08_gpu_kernel_optimization, 09_parallel_io_tuning,
10_numa_memory_placement, 11_infiniband_network, 12_job_scheduler_packing,
13_compiler_flags, 14_cache_blocking, 15_distributed_training,
17_cpu_cross_numa_bandwidth, 18_interconnect_topology_routing,
22_prefetch_strategy, 24_gpu_comm_overlap,
27_kubernetes_pod_autoscaling, 28_microservice_circuit_breaker,
29_cdn_cache_optimization, 30_serverless_cold_start,
31_database_connection_pooling, 32_load_balancer_algorithm,
33_api_rate_limiter, 34_container_resource_limits,
36_message_queue_consumer, 37_spark_shuffle_optimization,
38_data_lake_partitioning, 39_stream_processing_windowing,
40_etl_batch_size_tuning, 41_columnar_compression,
42_query_engine_join_strategy, 44_data_replication_lag,
45_time_series_downsampling, 46_feature_store_freshness,
47_tcp_congestion_control, 48_tls_handshake_optimization,
49_firewall_rule_ordering, 50_dns_resolver_caching,
51_bgp_route_convergence, 52_vpn_tunnel_mtu,
54_http2_stream_multiplexing, 55_network_buffer_sizing,
56_wifi_channel_power, 57_waf_rule_threshold,
58_encryption_pipeline, 59_siem_alert_correlation,
60_vulnerability_scan_scheduling, 61_zero_trust_policy_eval,
62_certificate_rotation, 63_ids_signature_tuning,
64_secrets_vault_performance, 65_audit_log_pipeline,
67_smart_sensor_sampling, 68_ble_mesh_topology,
69_rtos_task_priority, 70_lorawan_parameters,
71_edge_inference_quantization, 72_mqtt_broker_tuning,
73_pwm_motor_control, 74_zigbee_network_formation,
75_firmware_ota_strategy, 76_battery_management_charging,
77_cicd_pipeline_parallelism, 78_deployment_canary_rollout,
79_terraform_plan_optimization, 80_docker_build_layer_caching,
81_test_suite_sharding, 82_gitops_sync_interval,
83_log_aggregation_pipeline, 84_feature_flag_evaluation,
86_chaos_engineering_blast_radius, 87_bread_baking,
88_coffee_brewing, 89_pizza_dough, 91_yogurt_fermentation,
93_salad_dressing_emulsion, 95_cookie_texture,
96_fermented_hot_sauce, 97_tomato_greenhouse,
98_compost_maturity, 99_seed_germination,
100_hydroponic_nutrient, 101_lawn_grass_mix,
102_fruit_tree_pruning, 104_irrigation_scheduling,
105_greenhouse_climate, 107_sleep_quality,
108_running_performance, 109_strength_training,
110_meditation_routine, 111_ergonomic_workstation,
113_study_habit, 114_meal_timing,
117_tire_pressure_fuel, 118_engine_oil_change,
119_ev_range_optimization, 122_traffic_signal_timing,
126_windshield_defog, 127_solar_panel_tilt,
128_rainwater_harvesting, 129_home_insulation,
132_water_heater_efficiency, 135_aquaponics_balance,
137_paint_finish_quality, 138_concrete_mix,
139_laundry_stain_removal, 140_candle_making,
141_wood_stain_finish, 144_soap_making,
146_3d_print_quality, 147_landscape_exposure,
148_studio_lighting, 149_lens_sharpness,
151_microscope_imaging, 153_telescope_observation,
154_drone_aerial_photo, 155_photo_print_color,
157_guitar_string_tone, 158_room_acoustics,
159_vinyl_playback, 160_podcast_recording,
162_drum_tuning, 164_headphone_eq,
165_concert_hall_design, 167_dog_kibble_formulation,
168_cat_litter_box, 169_chicken_egg_production,
170_fish_tank_health, 171_dog_training_protocol,
173_horse_feed_ration, 174_reptile_habitat,
177_fabric_dyeing, 178_knitting_tension,
179_sewing_stitch_quality, 180_leather_tanning,
184_wool_felting, 186_iron_press_settings,
187_titration_accuracy, 188_crystallization,
190_pcr_amplification, 194_electroplating,
195_enzyme_kinetics, 197_moving_day_logistics,
198_party_planning, 199_wood_glue_joint,
200_table_saw_cut, 201_wood_finish_drying,
202_mortise_tenon_fit, 204_wood_bending,
205_sandpaper_progression, 208_plywood_layup,
209_golf_driver_launch, 210_swimming_stroke,
211_tennis_racket_string, 212_basketball_shooting,
214_archery_bow_tuning, 218_soccer_passing_drill,
219_moisturizer_absorption, 220_shampoo_foam,
221_nail_polish_durability, 222_lip_balm_texture,
224_perfume_longevity, 226_deodorant_efficacy,
229_soil_compaction, 230_well_drilling,
231_rock_thin_section, 232_seismograph_placement,
233_erosion_control, 234_mineral_flotation,
236_concrete_aggregate, 239_kombucha_brewing,
240_cider_making, 241_mead_honey_wine,
242_sauerkraut_ferment, 246_kefir_grains,
249_gift_wrapping, 250_garage_sale_pricing,
251_coral_reef_restoration, 252_seawater_desalination,
253_tidal_energy, 254_fish_farm_stocking,
256_mangrove_restoration, 258_beach_nourishment,
261_model_rocket_flight, 262_paper_airplane,
263_rc_plane_trim, 267_wind_tunnel_setup,
269_parachute_deployment, 270_hot_air_balloon,
271_led_strip_install, 272_pcb_soldering,
274_battery_charger, 275_audio_amplifier,
277_wire_gauge_selection, 278_motor_speed_control,
280_power_supply_design, 281_watercolor_wash,
282_oil_paint_drying, 283_acrylic_pour,
284_canvas_stretching, 288_printmaking_ink,
291_dairy_cow_nutrition, 292_sheep_shearing,
293_poultry_house_ventilation, 294_cattle_grazing,
295_pig_farrowing, 297_hoof_trimming,
301_laser_cutting_parameters, 302_ceramic_glaze_firing,
303_pharmaceutical_tablet, 304_concrete_admixture_blend,
305_essential_oil_blend, 306_injection_molding,
307_wine_tasting_panel, 308_pcb_solder_reflow,
309_wastewater_treatment, 310_battery_cell_design
```

---

## Step 6: Test Suite

The test suite is in `tests/test_doe.py` (1539 lines). It uses pytest and covers:

1. **Config loading**: Valid configs, legacy array format, legacy static_settings, missing file, invalid JSON, unsupported operations, duplicate factor names, wrong level counts for PB/FF/BB/CCD/DSD
2. **Design generation**: All 11 operation types — verifying run counts, factor value correctness, blocking, randomization
3. **Analysis**: Main effects computation, interaction effects, summary stats, ANOVA (pooled and Lenth methods)
4. **Codegen**: Script generation for both sh and py formats, all three arg styles
5. **CLI integration**: Subcommand dispatch, --version, --dry-run, error handling

Key test helpers:
- `_make_config_dict()`: Builds a raw config dict for JSON serialization
- `_write_config(tmp_path, cfg_dict)`: Writes config to tmpdir and returns path
- `_make_doe_config()`: Builds DOEConfig objects directly (no file I/O)

Run with: `pytest tests/test_doe.py -v`

---

## Step 7: Website

The website is a static site served at doehelper.com via GitHub Pages.

### `website/CNAME`

```
doehelper.com
```

### `website/.nojekyll`

(empty file — disables Jekyll processing)

### Website Structure

- `index.html` — Homepage with gradient hero, 12 feature cards, abstract decorations
- `howto.html` — Quick start guide, installation, basic workflow, reference
- `book.html` — Comprehensive book layout with sidebar and chapters
- `quickstart.html` — Redirects to howto.html
- `ai-prompts.html` — AI prompt cards for config and test script generation
- `ai-config-prompt.txt` — System prompt for AI config assistant (158 lines)
- `ai-testscript-prompt.txt` — System prompt for test script generator (119 lines)
- `css/style.css` — Main design system (308 lines): responsive layouts, animations, callouts, accordions, tabs, book layout
- `css/usecase.css` — Use case page styling (126 lines): hero, sections, tables, steps, TOC
- `logo.svg` — Dark gradient logo with response surface visualization (114 lines)
- `logo-light.svg` — Light version (87 lines)
- `use-cases/*.html` — 221 generated HTML pages (one per use case)
- `images/*.png` — ~4,981 analysis plot images

The website HTML pages and images are generated by `generate_website_pages.py`. They are not hand-written.

---

## Step 8: Utility Scripts

### `generate_website_pages.py`

Large script (~1,278 lines) that generates HTML pages for all use cases. For each use case:
1. Loads config.json
2. Generates design matrix
3. Runs analysis (if results exist)
4. Renders a styled HTML page with design matrices, analysis results, ANOVA tables, embedded plots, optimization recommendations

### `add_multi_opt.py` (139 lines)

Runs multi-objective optimization on all use cases and injects results into their HTML pages.

### `generate_new_plots.py` (111 lines)

Regenerates analysis plots (normal, half-normal, diagnostics) for all use cases and copies to `website/images/`.

---

## Step 9: Training Materials

### `training/generate_slides.py` (~1,591 lines)

Generates 8 PowerPoint training modules using `python-pptx`:
1. Introduction to DOE
2. Getting Started
3. Full Factorial
4. Screening Designs
5. Response Surface
6. Analysis
7. Advanced Topics
8. Capstone

Uses indigo/purple color scheme matching the website.

### `training/exercises.md` (620 lines)

8 comprehensive exercises from installation to capstone project.

### `training/teaching_notes.md` (310 lines)

Full-day course curriculum with module-by-module teaching guidance.

---

## Step 10: Documentation

### `docs/doe_fundamentals.md` (1,158 lines)

Comprehensive fundamentals guide covering DOE principles, history, and statistical concepts.

### `docs/book/`

LaTeX source files (`doe_guide.tex`, `user_guide.tex`) and compiled PDFs for the comprehensive guide and user guide.

---

## Reconstruction Notes

### What can be rebuilt exactly from this file:
- All 10 core Python source files (models, config, design, rsm, codegen — verbatim)
- All configuration files (pyproject.toml, MANIFEST.in, requirements.txt, GitHub workflows — verbatim)
- Both Jinja2 templates (verbatim)
- The sample use case (reactor_optimization — verbatim)

### What requires the companion `build_prompt.md` (lowercase) for exact reproduction:
- `doe/analysis.py` — Algorithm details provided above, full code in companion file
- `doe/optimize.py` — Algorithm details provided above, full code in companion file
- `doe/report.py` — HTML/CSS template details provided above, full code in companion file
- `doe/cli.py` — All subcommand logic described above, full code in companion file

### What must be generated (not stored verbatim):
- The 220 remaining use cases — each follows the pattern above with domain-specific config.json, sim.sh, and README.md
- The ~4,981 PNG plot images — generated by running `doe analyze` on each use case
- The 221 website HTML pages — generated by `generate_website_pages.py`
- The 8 PowerPoint files — generated by `training/generate_slides.py`
- The PDF documentation — compiled from LaTeX sources

### Regeneration commands:

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Generate plots for all use cases
python generate_new_plots.py

# Generate website pages
python generate_website_pages.py

# Add multi-objective optimization to pages
python add_multi_opt.py

# Generate training slides
cd training && python generate_slides.py
```
