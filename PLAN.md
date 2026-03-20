# Design of Experiments (DOE) Helper Tool — Implementation Plan

## Context

A Python CLI tool that automates the creation and analysis of experimental designs. It reads a JSON config, generates a design matrix using classical DOE techniques, produces executable runner scripts, and analyzes results with main effects, interaction effects, response surface modeling, and visualization.

---

## File Structure

```
/workspaces/design_of_experiments/
├── README.md
├── PLAN.md                          # this file
├── pyproject.toml                   # package metadata and deps
├── requirements.txt
├── doe.py                           # thin CLI wrapper (calls doe.cli:main)
├── doe/
│   ├── __init__.py
│   ├── cli.py                       # CLI entry point (argparse, subcommands)
│   ├── models.py                    # dataclasses: Factor, DOEConfig, DesignMatrix, etc.
│   ├── config.py                    # JSON loading + validation → DOEConfig
│   ├── design.py                    # design matrix generation (6 design types)
│   ├── codegen.py                   # Jinja2 script rendering → runner.sh / runner.py
│   ├── analysis.py                  # results loading, effects, stats, plots, CSV export
│   ├── rsm.py                       # response surface modeling (linear/quadratic fits)
│   ├── optimize.py                  # optimization recommendations from results
│   └── report.py                    # self-contained HTML report generation
├── templates/
│   ├── runner_sh.j2                 # shell script template (with error recovery)
│   └── runner_py.j2                 # Python runner template (with error recovery)
├── tests/
│   ├── __init__.py
│   └── test_doe.py                  # comprehensive test suite (pytest)
├── examples/
│   ├── example_config.json          # 3 factors × 2 levels, full_factorial
│   ├── example_test_script.sh
│   ├── sysbench_config.json         # multi-response, plackett_burman
│   └── sysbench_test.sh
└── .github/workflows/
    └── ci.yml                       # CI pipeline (Python 3.10/3.11/3.12)
```

---

## Data Flow

```
Input JSON
    → doe/config.py    load_config()       → DOEConfig
    → doe/design.py    generate_design()   → DesignMatrix
    → doe/codegen.py   generate_script()   → runner.sh / runner.py
    → (user runs experiments)
    → doe/analysis.py  analyze()           → AnalysisReport
    → doe/rsm.py       fit_rsm()           → RSMModel
    → doe/optimize.py  recommend()         → stdout recommendations
    → doe/report.py    generate_report()   → report.html
```

---

## Key Modules

### `doe/models.py`
Typed dataclasses shared across all modules:
- `Factor(name, levels, type, description, unit)`
- `ResponseVar(name, optimize, unit, description)`
- `RunnerConfig(arg_style, result_file)`
- `DOEConfig(factors, fixed_factors, responses, block_count, test_script, operation, ...)`
- `ExperimentRun(run_id, block_id, factor_values)`
- `DesignMatrix(runs, factor_names, operation, metadata)`
- `EffectResult(factor_name, main_effect, std_error, pct_contribution, ci_low, ci_high)`
- `InteractionEffect(factor_a, factor_b, interaction_effect, pct_contribution)`
- `ResponseAnalysis(response_name, effects, summary_stats, interactions)`
- `AnalysisReport(results_by_response, pareto_chart_paths, effects_plot_paths)`

### `doe/config.py`
- `load_config(path, strict=True) -> DOEConfig` — parse JSON, validate, return typed config
- Supports modern dict-based and legacy array-based factor formats
- Converts legacy `static_settings` to `fixed_factors`
- `SUPPORTED_OPERATIONS = {"full_factorial", "fractional_factorial", "plackett_burman", "latin_hypercube", "central_composite", "box_behnken"}`

### `doe/design.py`
- `generate_design(cfg, seed=None) -> DesignMatrix` — dispatch by operation
- `_full_factorial(cfg)` — `itertools.product`; zero extra deps
- `_fractional_factorial(cfg)` — `pyDOE3.fracfact()`; Resolution III auto-generation
- `_plackett_burman(cfg)` — `pyDOE3.pbdesign()`; 2-level screening
- `_latin_hypercube(cfg, seed)` — `pyDOE3.lhs()`; maximin criterion
- `_central_composite(cfg)` — `pyDOE3.ccdesign()`; circumscribed CCD
- `_box_behnken(cfg)` — `pyDOE3.bbdesign()`; 3+ factors, numeric levels
- `_apply_blocks()` — replicate + assign block_id
- `_randomize_run_order()` — shuffle within each block independently

### `doe/analysis.py`
- `analyze(matrix, cfg, results_dir, no_plots, pareto_threshold)` → AnalysisReport
- Main effects with 95% confidence intervals (scipy.stats.t)
- Two-factor interaction effects for 2-level factors
- Summary statistics per factor per level
- Pareto charts and main effects plots (matplotlib)
- `export_csv(report, output_dir)` — CSV export of effects and stats

### `doe/rsm.py`
- `fit_rsm(runs, responses, factor_names, factors, model_type)` → RSMModel
- Linear and quadratic polynomial regression via numpy least-squares
- R² and adjusted R² statistics
- Predicted optimum from observed factor combinations

### `doe/optimize.py`
- `recommend(matrix, cfg, results_dir, response_name)` — print optimization recommendations
- Best observed run, RSM model fit, factor importance ranking

### `doe/report.py`
- `generate_report(matrix, cfg, results_dir, output_path)` — self-contained HTML report
- Embedded base64 plot images, collapsible sections, responsive tables

### `doe/codegen.py`
- `generate_script(matrix, cfg, output_path, format)` — render Jinja2 template, chmod +x
- Three arg styles: double-dash, env, positional
- Error recovery: track failed runs, continue on failure, summary at end

### `doe/cli.py`
Six subcommands via argparse:
```
doe generate  --config FILE [--output FILE] [--format sh|py] [--seed N] [--dry-run]
doe analyze   --config FILE [--results-dir DIR] [--no-plots] [--csv DIR]
doe info      --config FILE
doe optimize  --config FILE [--results-dir DIR] [--response NAME]
doe report    --config FILE [--results-dir DIR] [--output FILE]
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pyDOE3>=1.0.0` | PB, LHS, CCD, fractional factorial, Box-Behnken |
| `numpy>=1.26.0` | Array operations, RSM least-squares |
| `matplotlib>=3.7.0` | Pareto + main effects plots |
| `scipy>=1.11.0` | Confidence intervals (t-distribution) |
| `Jinja2>=3.1.0` | Script template rendering |

> Full-factorial uses only stdlib. pyDOE3 is lazily imported only when needed.

---

## Design Decisions

1. **Re-derive design at analysis time** — The `DesignMatrix` is reconstructed from the same config. Use `--seed` for reproducible run order between `generate` and `analyze`.

2. **pyDOE3 as optional import** — Full-factorial has zero extra deps. pyDOE3 is only imported inside design functions with helpful install messages.

3. **Per-run JSON result files** — Each run writes `run_{N}.json`. Partial failures are isolated.

4. **Jinja2 templates** — Script format extensible by adding template files.

5. **Block randomization** — Within-block shuffling (statistically correct).

6. **Multi-response framework** — Each response analyzed independently with per-response plots and optimization direction.

7. **Self-contained HTML reports** — Base64-encoded images, inline CSS, no external dependencies.

8. **Runner error recovery** — Failed runs tracked and reported; partial results preserved.

9. **CLI in package** — `doe/cli.py` holds CLI logic; `doe.py` is a thin wrapper; `pyproject.toml` entry point is `doe.cli:main`.
