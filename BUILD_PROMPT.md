# Build Prompt: Design of Experiments (DOE) Helper Tool

Use this prompt with an AI coding assistant (e.g., Claude) to recreate this project from scratch on a new system. The project is a complete Python CLI tool for designing, executing, and analyzing statistical experiments.

---

## Project Overview

**Package name:** `doehelper`
**Version:** 0.1.0
**Author:** Martin J. Gallagher
**License:** GPL-3.0-or-later
**Python:** >=3.10
**Repository:** https://github.com/MartinGallagher-code/design_of_experiments
**Website:** https://doehelper.com

Build a Python CLI tool called `doe` that automates Design of Experiments (DOE). It generates reproducible design matrices, creates executable runner scripts (Bash or Python), and analyzes results using classical DOE techniques including ANOVA, response surface modeling (RSM), and multi-objective optimization.

---

## Directory Structure

```
design_of_experiments/
├── .github/workflows/
│   ├── ci.yml
│   ├── pages.yml
│   └── publish.yml
├── docs/
│   ├── book/
│   │   ├── doe_guide.tex / .pdf
│   │   └── user_guide.tex / .pdf
│   └── doe_fundamentals.md
├── doe/
│   ├── __init__.py
│   ├── cli.py
│   ├── models.py
│   ├── config.py
│   ├── design.py
│   ├── codegen.py
│   ├── analysis.py
│   ├── rsm.py
│   ├── optimize.py
│   ├── report.py
│   ├── templates/
│   │   ├── runner_sh.j2
│   │   └── runner_py.j2
│   └── use_cases/
│       ├── __init__.py
│       ├── 01_reactor_optimization/
│       │   ├── config.json
│       │   ├── README.md
│       │   ├── sim.sh
│       │   └── results/
│       ├── ... (221 use case directories)
│       └── 310_battery_cell_design/
├── tests/
│   ├── __init__.py
│   └── test_doe.py
├── training/
│   ├── exercises.md
│   ├── teaching_notes.md
│   └── generate_slides.py
├── website/
│   ├── css/style.css, usecase.css
│   ├── js/main.js
│   ├── images/
│   ├── use-cases/ (221 HTML pages)
│   ├── index.html
│   ├── quickstart.html
│   ├── howto.html
│   ├── book.html
│   ├── ai-prompts.html
│   ├── ai-config-prompt.txt
│   ├── ai-testscript-prompt.txt
│   ├── CNAME
│   ├── logo.svg
│   └── logo-light.svg
├── doe.py
├── pyproject.toml
├── requirements.txt
├── MANIFEST.in
├── README.md
├── CHANGELOG.md
├── LICENSE
├── generate_website_pages.py
├── add_multi_opt.py
└── generate_new_plots.py
```

---

## Dependencies (pyproject.toml)

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
    "doe", "doehelper", "experiment", "factorial",
    "statistics", "anova", "response-surface",
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

---

## Core Source Files

### doe/__init__.py

```python
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Design of Experiments (DOE) helper tool."""

__version__ = "0.1.0"
```

### doe/models.py

13 dataclasses for type-safe data structures:

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

### doe/config.py

JSON config loader with validation. Key behaviors:
- Loads `factors` (dict format with name/levels/type/unit/description, or legacy array format `["name", "val1", "val2"]`)
- Loads `fixed_factors` (dict) or legacy `static_settings` (list of `"--key=value"` strings)
- Loads `responses` (dict with name/optimize/unit/description/weight/bounds, or plain strings; defaults to `[ResponseVar(name="response")]` if empty)
- Loads `runner` config (arg_style: double-dash|env|positional, result_file: json)
- Loads `settings` (operation, block_count, test_script, out_directory, processed_directory, lhs_samples)
- Loads `metadata` (name, description)
- Validates: operation in SUPPORTED_OPERATIONS set (11 types), factors non-empty, unique names, block_count >= 1
- Special validation for: plackett_burman (2 levels only), fractional_factorial (2 levels only), box_behnken (3+ factors, 2 numeric levels), central_composite (2 numeric levels), definitive_screening (3+ factors, 2 numeric levels)
- Warns (non-fatal) if test_script doesn't exist when strict=True
- `SUPPORTED_OPERATIONS` = {full_factorial, plackett_burman, latin_hypercube, central_composite, fractional_factorial, box_behnken, definitive_screening, taguchi, d_optimal, mixture_simplex_lattice, mixture_simplex_centroid}

### doe/design.py

Design matrix generation for 11 design types. Key functions:

- `generate_design(cfg, seed=None) -> DesignMatrix` — dispatcher for all design types; applies blocking, randomization within blocks, builds metadata
- `_full_factorial(cfg)` — uses `itertools.product` over factor levels
- `_plackett_burman(cfg)` — uses `pyDOE3.pbdesign(n_factors)`, maps -1/+1 to factor levels
- `_latin_hypercube(cfg, seed)` — uses `pyDOE3.lhs(n_factors, samples, criterion="maximin")`, decodes continuous factors with linear interpolation, categorical by binning
- `_central_composite(cfg)` — uses `pyDOE3.ccdesign(n_factors, center=(4,4), alpha="orthogonal", face="circumscribed")`, decodes coded values to natural units
- `_fractional_factorial(cfg)` — builds generator string for 2^(n-p) Resolution III design, uses `pyDOE3.fracfact()`, attempts alias structure analysis
- `_box_behnken(cfg)` — uses `pyDOE3.bbdesign(n_factors, center=3)`, decodes coded values
- `_definitive_screening(cfg)` — Jones-Nachtsheim 2011 conference matrix construction: 2k+1 runs for odd k, 2k+3 for even k, three levels (-1,0,+1)
- `_taguchi(cfg)` — uses pyDOE3 orthogonal arrays, finds smallest OA accommodating all factors
- `_d_optimal(cfg)` — Fedorov row exchange algorithm maximizing det(X'X), 100 max iterations, uses RSM module for design matrix building
- `_mixture_simplex_lattice(cfg)` — degree-2 quadratic lattice, all compositions of m=2 into q parts
- `_mixture_simplex_centroid(cfg)` — vertices, edge midpoints, face centroids, overall centroid
- `augment_design(matrix, cfg, type)` — fold_over (mirror levels), star_points (axial with rotatable alpha), center_points (3 replicates)
- `evaluate_design(matrix, cfg) -> dict` — D-efficiency, A-efficiency, G-efficiency metrics
- `_apply_blocks(base_runs, block_count)` — replicates base runs across blocks
- `_randomize_run_order(runs, seed)` — shuffles within blocks, renumbers sequentially
- `_decode_coded_value(code, factor)` — maps coded ±1/±alpha/0 to natural units
- `_decode_lhs_value(x, factor)` — maps [0,1] to factor level

### doe/codegen.py

Script generation using Jinja2 templates:

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

### doe/templates/runner_sh.j2

Bash runner script template with:
- `set -uo pipefail`
- Creates output directory
- Loops through runs, skipping already-completed ones (checks for existing JSON file)
- Three argument styles: double-dash (`--name "value"`), env (`export NAME="value"`), positional
- Error recovery: tracks FAILED_RUNS array, reports failures at end
- Prints run progress (run N / total)
- Uses `{% raw %}` for bash array syntax

### doe/templates/runner_py.j2

Python runner script template with:
- RUNS list with run_id, block_id, factors dict
- Uses subprocess.run() to call test_script
- Three arg styles: double-dash, env (sets os.environ), positional
- Skips completed runs, tracks failed_runs list
- CalledProcessError handling per run

### doe/analysis.py (~988 lines)

Analysis functions:

- `analyze(matrix, cfg, results_dir, no_plots, pareto_threshold, partial) -> AnalysisReport` — main entry point; loads results, computes effects/interactions/ANOVA/summary stats per response; generates plots (Pareto, main effects, normal/half-normal probability, RSM surface, diagnostics)
- `_load_all_results(runs, results_dir, partial) -> dict[int, dict]` — loads run_N.json files; partial mode skips missing with warning; raises FileNotFoundError if none exist
- `_compute_main_effects(runs, responses, factor_names)` — for 2-level factors: high_mean - low_mean; for >2 levels: max_mean - min_mean; includes 95% CI using pooled t-test for 2-level factors
- `_compute_interaction_effects(runs, responses, factor_names)` — two-factor interactions for 2-level factor pairs; concordant vs discordant mean difference
- `_compute_summary_stats(runs, responses, factor_names)` — per-factor per-level: count, mean, std, min, max
- `_compute_anova(runs, responses, factor_names, factors)` — Type I sequential SS; detects replicates for pure error; uses Lenth's PSE for unreplicated designs (s0 = 1.5 * median(|effects|), trim at 2.5*s0); includes interaction SS for 2-level factor pairs; lack-of-fit F-test when replicates exist
- `plot_pareto(effects, output_path, title, threshold)` — horizontal bar chart with cumulative % line, threshold reference line
- `plot_main_effects(runs, responses, factor_names, output_path, ylabel)` — grid of line plots showing mean response per level
- `plot_rsm_surface(runs, responses, factors, factor_names, response_name, output_dir)` — 3D surface plots for each pair of continuous factors; fits quadratic RSM model; 40x40 grid; actual data points as red scatter
- `plot_diagnostics(diagnostics, output_path)` — 2x2 panel: residuals vs fitted, normal probability (scipy probplot), residuals vs run order, predicted vs actual
- `plot_normal_effects(effects, output_path)` — effects vs normal quantiles using Filliben approximation; labels significant deviating points
- `plot_half_normal_effects(effects, output_path)` — absolute effects vs half-normal quantiles; reference line through origin and median; labels outliers
- `export_csv(report, output_dir)` — exports main_effects and summary_stats CSV files per response

### doe/rsm.py (~342 lines)

Response Surface Modeling:

Two dataclasses:
- `ModelDiagnostics`: residuals, fitted_values, hat_matrix_diag (leverage), press, predicted_r_squared, run_ids
- `RSMModel`: response_name, coefficients dict, r_squared, adj_r_squared, predicted_optimum, predicted_value, diagnostics

Key functions:
- `_encode_factor_value(value, factor) -> float` — continuous/ordinal: normalize to [-1,1] using (val - center)/half_range; categorical 2-level: -1/+1 sorted; multi-level: index-based centered
- `_build_design_matrix(runs, factor_names, factors, model_type) -> (X, col_names)` — linear: [1, x1, x2, ...]; quadratic: adds interaction terms (x1*x2) and squared terms (x1^2)
- `fit_rsm(runs, responses, factor_names, factors, model_type) -> RSMModel` — OLS via numpy.linalg.lstsq; computes R^2, adj R^2; finds best observed run; computes hat matrix, leverage, PRESS (leave-one-out shortcut), predicted R^2
- `optimize_surface(model, factor_names, factors, direction, n_restarts=10) -> dict` — L-BFGS-B in coded space [-1,1] with 10 random restarts; returns optimal_settings (decoded to natural units), predicted_value, converged
- `steepest_ascent(model, factor_names, factors, direction, n_steps=10) -> list[dict]` — gradient = linear coefficients; normalized so max step = 1 coded unit; 0.5 coded units per step

### doe/optimize.py (~512 lines)

Optimization recommendations:

- `recommend(matrix, cfg, results_dir, response_name, partial)` — per response: best observed run, linear RSM coefficients/R^2, quadratic RSM if enough data, curvature analysis (concave/convex), interaction analysis (synergistic/antagonistic), surface optimization via scipy L-BFGS-B, model quality assessment, factor importance ranking
- `multi_objective(matrix, cfg, results_dir, partial)` — Derringer-Suich desirability functions; individual desirability d_i in [0,1]; weighted geometric mean for overall D; auto-computes bounds from observed data +5% margin; evaluates all observed runs + grid search (meshgrid for <=3 factors, random 5000-sample Latin hypercube for >3); prints response table, recommended settings, trade-off summary, model quality, top 3 runs

### doe/report.py (~770 lines)

Self-contained HTML report generation:
- `generate_report(matrix, cfg, results_dir, output_path, partial) -> str` — runs full analysis, embeds all plot images as base64 data URIs, collects RSM surface plots, runs optimization analysis, builds HTML sections (header, design summary, results per response, optimization, design matrix, footer)
- Internal helpers: `_encode_image`, `_build_header`, `_build_design_summary`, `_run_optimization`, `_build_optimization`, `_build_results`, `_build_design_matrix`, `_build_footer`
- `_CSS` — complete inline stylesheet with CSS variables (--accent: steelblue), responsive design, data tables with alternating rows, collapsible `<details>` sections
- `_HTML_TEMPLATE` — HTML5 template with `{title}`, `{css}`, `{header}`, `{design_summary}`, `{results}`, `{optimization}`, `{design_matrix}`, `{footer}` placeholders
- HTML escaping for all user-provided strings to prevent XSS
- ANOVA rows with p < 0.05 highlighted bold
- Plot images embedded as `data:image/png;base64,...`

### doe/cli.py (~833 lines)

CLI entry point with 12 subcommands using argparse:

1. **generate** — `--config FILE --output FILE --format sh|py --seed N --dry-run`
2. **analyze** — `--config FILE --results-dir DIR --no-plots --no-report --csv DIR --partial`
3. **info** — `--config FILE` (shows design matrix + D/A/G efficiency metrics)
4. **optimize** — `--config FILE --results-dir DIR --response NAME --partial --multi --steepest`
5. **report** — `--config FILE --results-dir DIR --output FILE --partial`
6. **record** — `--config FILE --run N|all --seed N` (interactive result entry)
7. **status** — `--config FILE --seed N` (progress bar, completed/pending runs)
8. **power** — `--config FILE --sigma FLOAT --delta FLOAT --alpha FLOAT --results-dir DIR --partial` (estimates sigma from residuals if omitted; non-centrality parameter; non-central F distribution power)
9. **augment** — `--config FILE --type fold_over|star_points|center_points --output FILE --format sh|py --seed N`
10. **init** — `--template NAME --list --output-dir DIR` (discovers use_cases via importlib.resources, fuzzy match, copies config.json/sim.sh/README.md)
11. **export-worksheet** — `--config FILE --format csv|markdown --output FILE --seed N`
12. **--version** — prints version, copyright, license

Helper functions: `_dispatch`, `_no_results_message`, `_run_optimize` (steepest/multi/single), `_handle_init`, `_handle_record`, `_record_single_run`, `_handle_status`, `_handle_export_worksheet` (CSV and markdown table), `_handle_power`, `_print_matrix`, `_print_report`

### doe.py (thin wrapper)

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

## Test Suite (tests/test_doe.py, ~1539 lines)

Comprehensive pytest suite with these test classes:

### TestConfigLoading
- `test_valid_dict_factors` — loads factors with type/unit, responses with optimize/unit
- `test_legacy_array_factors` — `["name", "val1", "val2"]` format
- `test_legacy_static_settings_to_fixed_factors` — converts `--key=value` strings
- `test_fixed_factors_dict` — dict with int/bool values converted to strings
- `test_missing_operation_uses_default` — defaults to full_factorial
- `test_invalid_operation` — raises ValueError
- `test_plackett_burman_requires_2_levels` — validation error for 3-level factor
- `test_central_composite_requires_2_numeric_levels` — rejects non-numeric
- `test_central_composite_requires_exactly_2_levels` — rejects 3-level
- `test_duplicate_factor_names` — raises ValueError
- `test_duplicate_response_names` — raises ValueError
- `test_invalid_optimize_value` — rejects "average"
- `test_invalid_arg_style` — rejects "xml"
- `test_empty_factors_list` — requires at least one factor
- `test_block_count_less_than_1` — requires >= 1
- `test_default_response_when_none` — creates default ResponseVar(name="response")
- `test_response_parsing_dict`, `test_response_parsing_string`, `test_response_parsing_invalid`
- `test_factor_missing_name`, `test_factor_fewer_than_2_levels`

### TestDesignGeneration
- `test_full_factorial_run_count` — 2^3 = 8 runs
- `test_full_factorial_all_combinations_present` — all 4 combos for 2 factors
- `test_full_factorial_mixed_level_counts` — 2 x 3 = 6 runs
- `test_full_factorial_deterministic` — same seed = same output
- `test_plackett_burman_structure` — >=4 runs, all values in {lo, hi}
- `test_latin_hypercube_sample_count` — 15 specified samples
- `test_latin_hypercube_default_samples` — max(10, 2*n_factors)
- `test_latin_hypercube_seed_produces_valid_range` — values within [0, 100]
- `test_central_composite_structure` — >=8 runs, all numeric
- `test_blocking_multiplies_runs` — 4 base x 3 blocks = 12
- `test_randomization_with_seed_reproducible`
- `test_randomization_within_blocks_preserves_block_integrity`
- `test_metadata_populated`

### TestFractionalFactorial
- `test_fewer_runs_than_full_factorial` — 5 factors: fractional < full
- `test_all_factor_names_present`
- `test_validation_requires_2_levels`

### TestBoxBehnken
- `test_center_points_present` — center at midpoints
- `test_requires_at_least_3_factors`
- `test_requires_2_numeric_levels`
- `test_requires_exactly_2_levels`

### TestAnalysis
- `test_main_effects_known_case` — A effect = -20.0, B effect = -10.0 (known 2^2 design)
- `test_main_effects_more_than_2_levels` — range = max - min of level means
- `test_summary_stats_correctness` — mean, min, max per level
- `test_multi_response` — two responses analyzed separately
- `test_missing_response_key_warning`
- `test_missing_result_files` — FileNotFoundError
- `test_percentage_contribution_sums_to_100`
- `test_effects_sorted_by_magnitude`
- `test_plot_generation` — creates pareto and effects plot files
- `test_no_plots_skips_generation`

### TestCodegen
- `test_shell_script_created_and_executable`
- `test_python_script_created_and_executable`
- `test_template_contains_run_data` — all run_ids present
- `test_double_dash_arg_style`, `test_env_arg_style`, `test_positional_arg_style` (both sh and py)
- `test_fixed_factors_in_shell_output`, `test_fixed_factors_in_python_output`
- `test_invalid_format_raises`

### TestCLI
- Uses subprocess to run `doe.py` with args
- `test_generate_dry_run_prints_matrix`
- `test_generate_creates_output_file_sh`, `test_generate_creates_output_file_py`
- `test_info_prints_design_info`
- `test_analyze_with_result_files`
- `test_missing_config_raises_error`, `test_no_command_raises_error`
- `test_generate_with_seed`

### TestModels
- Default value tests for Factor, ResponseVar, RunnerConfig, DesignMatrix, AnalysisReport

### TestReportGeneration
- `test_generate_report_produces_html_file` — HTML5 doctype, non-trivial size
- `test_report_contains_key_sections` — Design Summary, Main Effects, Design Matrix
- `test_report_is_self_contained` — no external CSS/JS links
- `test_report_embeds_plots_as_base64`
- `test_report_html_escapes_user_strings` — XSS prevention

### TestRSM
- `test_linear_fit_perfect` — R^2 = 1.0, exact coefficients recovered
- `test_linear_fit_noisy` — R^2 > 0.9
- `test_quadratic_fit` — interaction and squared terms present, exact coefficients
- `test_categorical_encoding` — -1/+1 for sorted 2-level categorical
- `test_empty_runs` — returns zero model

### TestOptimize
- `test_recommend_runs_without_error`
- `test_recommend_specific_response`
- `test_recommend_missing_response`
- `test_best_observed_run` — A=high, B=high with value 75.0
- `test_best_observed_run_minimize` — finds lowest value
- `test_factor_importance_order` — A ranked above B

---

## Configuration Format (config.json)

```json
{
    "metadata": {
        "name": "Chemical Reactor Optimization",
        "description": "Box-Behnken design to optimize yield and purity"
    },
    "factors": [
        {
            "name": "temperature",
            "levels": ["150", "200"],
            "type": "continuous",
            "unit": "°C",
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

---

## GitHub Actions Workflows

### .github/workflows/ci.yml
- Triggers on push to main and PRs
- Matrix: Python 3.10, 3.11, 3.12
- Steps: checkout, setup-python, `pip install -e ".[dev]"`, `pytest tests/ -v --tb=short --cov --cov-report=xml --cov-report=html`, upload coverage artifact

### .github/workflows/pages.yml
- Triggers on push to main and workflow_dispatch
- Deploys `website/` directory to GitHub Pages using actions/deploy-pages@v4

### .github/workflows/publish.yml
- Triggers on release published
- Builds with `python -m build`, publishes to PyPI via pypa/gh-action-pypi-publish@release/v1

---

## Other Files

### MANIFEST.in
```
include LICENSE
include README.md
recursive-include doe/templates *.j2
recursive-include doe/use_cases *.json *.sh *.md
recursive-include tests *
```

### requirements.txt
```
pyDOE3>=1.0.0
numpy>=1.26.0
pandas>=2.0.0
matplotlib>=3.7.0
scipy>=1.11.0
Jinja2>=3.1.0
```

### CHANGELOG.md
```markdown
# Changelog

## 0.1.0 — 2026-03-27

Initial public release.

- 11 design types: full-factorial, fractional-factorial, Plackett-Burman, Latin hypercube, central composite, Box-Behnken, definitive screening, Taguchi, D-optimal, mixture simplex-lattice, mixture simplex-centroid
- ANOVA analysis with F-tests and p-values
- Main effects and two-factor interaction estimation
- Response surface modeling and optimization
- Multi-objective optimization with desirability functions
- Runner script generation (Bash and Python)
- Interactive HTML report generation
- Design evaluation metrics (D/A/G-efficiency)
- Power analysis
- Design augmentation (fold-over, star points, center points)
```

---

## Use Cases (221 total)

Each use case directory contains:
- `config.json` — complete experiment configuration
- `README.md` — description and context
- `sim.sh` — simulation script that generates synthetic results
- `results/` — pre-populated results for analysis examples

### Complete list of use case directories:

01_reactor_optimization, 02_webapp_ab_testing, 03_ml_hyperparameter_screening, 04_database_performance_tuning, 05_material_formulation, 06_distillation_column, 07_mpi_collective_tuning, 08_gpu_kernel_optimization, 09_parallel_io_tuning, 10_numa_memory_placement, 11_infiniband_network, 12_job_scheduler_packing, 13_compiler_flags, 14_cache_blocking, 15_distributed_training, 17_cpu_cross_numa_bandwidth, 18_interconnect_topology_routing, 22_prefetch_strategy, 24_gpu_comm_overlap, 27_kubernetes_pod_autoscaling, 28_microservice_circuit_breaker, 29_cdn_cache_optimization, 30_serverless_cold_start, 31_database_connection_pooling, 32_load_balancer_algorithm, 33_api_rate_limiter, 34_container_resource_limits, 36_message_queue_consumer, 37_spark_shuffle_optimization, 38_data_lake_partitioning, 39_stream_processing_windowing, 40_etl_batch_size_tuning, 41_columnar_compression, 42_query_engine_join_strategy, 44_data_replication_lag, 45_time_series_downsampling, 46_feature_store_freshness, 47_tcp_congestion_control, 48_tls_handshake_optimization, 49_firewall_rule_ordering, 50_dns_resolver_caching, 51_bgp_route_convergence, 52_vpn_tunnel_mtu, 54_http2_stream_multiplexing, 55_network_buffer_sizing, 56_wifi_channel_power, 57_waf_rule_threshold, 58_encryption_pipeline, 59_siem_alert_correlation, 60_vulnerability_scan_scheduling, 61_zero_trust_policy_eval, 62_certificate_rotation, 63_ids_signature_tuning, 64_secrets_vault_performance, 65_audit_log_pipeline, 67_smart_sensor_sampling, 68_ble_mesh_topology, 69_rtos_task_priority, 70_lorawan_parameters, 71_edge_inference_quantization, 72_mqtt_broker_tuning, 73_pwm_motor_control, 74_zigbee_network_formation, 75_firmware_ota_strategy, 76_battery_management_charging, 77_cicd_pipeline_parallelism, 78_deployment_canary_rollout, 79_terraform_plan_optimization, 80_docker_build_layer_caching, 81_test_suite_sharding, 82_gitops_sync_interval, 83_log_aggregation_pipeline, 84_feature_flag_evaluation, 86_chaos_engineering_blast_radius, 87_bread_baking, 88_coffee_brewing, 89_pizza_dough, 91_yogurt_fermentation, 93_salad_dressing_emulsion, 95_cookie_texture, 96_fermented_hot_sauce, 97_tomato_greenhouse, 98_compost_maturity, 99_seed_germination, 100_hydroponic_nutrient, 101_lawn_grass_mix, 102_fruit_tree_pruning, 104_irrigation_scheduling, 105_greenhouse_climate, 107_sleep_quality, 108_running_performance, 109_strength_training, 110_meditation_routine, 111_ergonomic_workstation, 113_study_habit, 114_meal_timing, 117_tire_pressure_fuel, 118_engine_oil_change, 119_ev_range_optimization, 122_traffic_signal_timing, 126_windshield_defog, 127_solar_panel_tilt, 128_rainwater_harvesting, 129_home_insulation, 132_water_heater_efficiency, 135_aquaponics_balance, 137_paint_finish_quality, 138_concrete_mix, 139_laundry_stain_removal, 140_candle_making, 141_wood_stain_finish, 144_soap_making, 146_3d_print_quality, 147_landscape_exposure, 148_studio_lighting, 149_lens_sharpness, 151_microscope_imaging, 153_telescope_observation, 154_drone_aerial_photo, 155_photo_print_color, 157_guitar_string_tone, 158_room_acoustics, 159_vinyl_playback, 160_podcast_recording, 162_drum_tuning, 164_headphone_eq, 165_concert_hall_design, 167_dog_kibble_formulation, 168_cat_litter_box, 169_chicken_egg_production, 170_fish_tank_health, 171_dog_training_protocol, 173_horse_feed_ration, 174_reptile_habitat, 177_fabric_dyeing, 178_knitting_tension, 179_sewing_stitch_quality, 180_leather_tanning, 184_wool_felting, 186_iron_press_settings, 187_titration_accuracy, 188_crystallization, 190_pcr_amplification, 194_electroplating, 195_enzyme_kinetics, 197_moving_day_logistics, 198_party_planning, 199_wood_glue_joint, 200_table_saw_cut, 201_wood_finish_drying, 202_mortise_tenon_fit, 204_wood_bending, 205_sandpaper_progression, 208_plywood_layup, 209_golf_driver_launch, 210_swimming_stroke, 211_tennis_racket_string, 212_basketball_shooting, 214_archery_bow_tuning, 218_soccer_passing_drill, 219_moisturizer_absorption, 220_shampoo_foam, 221_nail_polish_durability, 222_lip_balm_texture, 224_perfume_longevity, 226_deodorant_efficacy, 229_soil_compaction, 230_well_drilling, 231_rock_thin_section, 232_seismograph_placement, 233_erosion_control, 234_mineral_flotation, 236_concrete_aggregate, 239_kombucha_brewing, 240_cider_making, 241_mead_honey_wine, 242_sauerkraut_ferment, 246_kefir_grains, 249_gift_wrapping, 250_garage_sale_pricing, 251_coral_reef_restoration, 252_seawater_desalination, 253_tidal_energy, 254_fish_farm_stocking, 256_mangrove_restoration, 258_beach_nourishment, 261_model_rocket_flight, 262_paper_airplane, 263_rc_plane_trim, 267_wind_tunnel_setup, 269_parachute_deployment, 270_hot_air_balloon, 271_led_strip_install, 272_pcb_soldering, 274_battery_charger, 275_audio_amplifier, 277_wire_gauge_selection, 278_motor_speed_control, 280_power_supply_design, 281_watercolor_wash, 282_oil_paint_drying, 283_acrylic_pour, 284_canvas_stretching, 288_printmaking_ink, 291_dairy_cow_nutrition, 292_sheep_shearing, 293_poultry_house_ventilation, 294_cattle_grazing, 295_pig_farrowing, 297_hoof_trimming, 301_laser_cutting_parameters, 302_ceramic_glaze_firing, 303_pharmaceutical_tablet, 304_concrete_admixture_blend, 305_essential_oil_blend, 306_injection_molding, 307_wine_tasting_panel, 308_pcb_solder_reflow, 309_wastewater_treatment, 310_battery_cell_design

Each use case uses one of the 11 design types with domain-appropriate factors, responses, and a simulation script. The sim.sh scripts generate realistic synthetic data based on the factor values passed as arguments, outputting JSON result files.

---

## Website

The website is a static site deployed to GitHub Pages at doehelper.com. Key pages:

- **index.html** — Homepage with gradient hero, feature cards, navigation to all sections
- **howto.html** — Quick start guide covering installation, configuration, design selection, execution, analysis
- **book.html** — Complete interactive textbook (~79KB) with sidebar navigation covering all DOE concepts in depth
- **ai-prompts.html** — AI system prompts for config.json generation and test script generation
- **use-cases/*.html** — 221 individual use case pages with design details, plots, analysis results, multi-objective optimization

The site uses:
- **css/style.css** — Main design system with CSS custom properties, responsive layout, gradient hero, feature cards, navigation
- **css/usecase.css** — Use case page styling with step numbers, tables, TOC
- **js/main.js** — Interactive features: mobile nav, tabs, accordion, code copy buttons, book TOC, run calculator
- **logo.svg / logo-light.svg** — SVG logos with response surface visualization
- **CNAME** — `doehelper.com`

---

## Training Materials

- **training/teaching_notes.md** — 8-module instructor curriculum with teaching approaches and assessment rubric
- **training/exercises.md** — 8 student exercises from exploration to capstone project
- **training/generate_slides.py** — PowerPoint slide generation script using python-pptx

---

## Documentation

- **docs/doe_fundamentals.md** — Introduction to DOE concepts, history, OVAT problems, worked examples
- **docs/book/doe_guide.tex** — LaTeX guide document (compiles to PDF)
- **docs/book/user_guide.tex** — LaTeX user guide (compiles to PDF)
- **README.md** — Comprehensive project documentation with features, installation, quick start, configuration reference, CLI reference, test script protocol

---

## Key Design Decisions

1. **All levels stored as strings** — factor values are always strings, even numeric; conversion happens at encoding time
2. **Seed-based reproducibility** — design generation uses seeds for deterministic randomization within blocks
3. **Lazy imports** — pyDOE3, matplotlib, scipy imported only when needed (not at module level)
4. **Graceful degradation** — analysis continues if some plots fail; RSM falls back from quadratic to linear
5. **Self-contained reports** — HTML reports embed all CSS and images (base64) with zero external dependencies
6. **Lenth's PSE** — unreplicated designs use Lenth's pseudo-standard-error (median of absolute effects, trimmed at 2.5*s0) instead of requiring replicates for error estimation
7. **Template-based code generation** — Jinja2 templates for Bash and Python runner scripts with three argument style options
8. **Use case templates** — 221 built-in examples accessible via `doe init --template`

---

## How to Build

```bash
# 1. Create project structure
mkdir -p design_of_experiments/{doe/templates,doe/use_cases,tests,.github/workflows,docs/book,training,website/{css,js,images,use-cases}}

# 2. Create all source files as described above

# 3. Install and test
cd design_of_experiments
pip install -e ".[dev]"
pytest tests/ -v

# 4. Verify CLI
doe --version
doe init --list
doe init --template reactor_optimization
cd reactor_optimization
doe info --config config.json
doe generate --config config.json --dry-run
```
