# Design of Experiments (DOE) Helper Tool — Implementation Plan

## Context

A Python CLI tool that automates the creation and analysis of experimental designs. It reads a JSON config, generates a design matrix using classical DOE techniques, produces executable runner scripts, and analyzes results with ANOVA, main effects, interaction effects, response surface modeling, surface optimization, and visualization.

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
│   ├── models.py                    # dataclasses: Factor, DOEConfig, DesignMatrix, AnovaTable, etc.
│   ├── config.py                    # JSON loading + validation → DOEConfig
│   ├── design.py                    # design matrix generation (11 design types + augmentation + evaluation)
│   ├── codegen.py                   # Jinja2 script rendering → runner.sh / runner.py
│   ├── analysis.py                  # results loading, ANOVA, effects, stats, plots, CSV export
│   ├── rsm.py                       # response surface modeling, diagnostics, surface optimization, steepest ascent
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
    → doe/design.py    evaluate_design()   → D/A/G-efficiency metrics
    → doe/codegen.py   generate_script()   → runner.sh / runner.py
    → (user runs experiments)
    → doe/analysis.py  analyze()           → AnalysisReport (with ANOVA, diagnostics, plots)
    → doe/rsm.py       fit_rsm()           → RSMModel (with ModelDiagnostics)
    → doe/rsm.py       optimize_surface()  → true surface optimum
    → doe/rsm.py       steepest_ascent()   → follow-up experiment pathway
    → doe/optimize.py  recommend()         → stdout recommendations
    → doe/optimize.py  multi_objective()   → desirability-based optimization
    → doe/report.py    generate_report()   → report.html
```

---

## Key Modules

### `doe/models.py`
Typed dataclasses shared across all modules:
- `Factor(name, levels, type, description, unit)`
- `ResponseVar(name, optimize, unit, description, weight, bounds)`
- `RunnerConfig(arg_style, result_file)`
- `DOEConfig(factors, fixed_factors, responses, block_count, test_script, operation, ...)`
- `ExperimentRun(run_id, block_id, factor_values)`
- `DesignMatrix(runs, factor_names, operation, metadata)`
- `EffectResult(factor_name, main_effect, std_error, pct_contribution, ci_low, ci_high)`
- `InteractionEffect(factor_a, factor_b, interaction_effect, pct_contribution)`
- `AnovaRow(source, df, ss, ms, f_value, p_value)`
- `AnovaTable(rows, error_row, total_row, lack_of_fit_row, pure_error_row, error_method)`
- `ResponseAnalysis(response_name, effects, summary_stats, interactions, anova_table)`
- `AnalysisReport(results_by_response, pareto_chart_paths, effects_plot_paths, normal_plot_paths, half_normal_plot_paths, diagnostics_plot_paths)`

### `doe/config.py`
- `load_config(path, strict=True) -> DOEConfig` — parse JSON, validate, return typed config
- Supports modern dict-based and legacy array-based factor formats
- Converts legacy `static_settings` to `fixed_factors`
- `SUPPORTED_OPERATIONS = {"full_factorial", "fractional_factorial", "plackett_burman", "latin_hypercube", "central_composite", "box_behnken", "definitive_screening", "taguchi", "d_optimal", "mixture_simplex_lattice", "mixture_simplex_centroid"}`

### `doe/design.py`
- `generate_design(cfg, seed=None) -> DesignMatrix` — dispatch by operation
- `_full_factorial(cfg)` — `itertools.product`; zero extra deps
- `_fractional_factorial(cfg)` — `pyDOE3.fracfact()`; Resolution III auto-generation; alias structure via `pyDOE3.fracfact_aliasing()`
- `_plackett_burman(cfg)` — `pyDOE3.pbdesign()`; 2-level screening
- `_latin_hypercube(cfg, seed)` — `pyDOE3.lhs()`; maximin criterion
- `_central_composite(cfg)` — `pyDOE3.ccdesign()`; circumscribed CCD
- `_box_behnken(cfg)` — `pyDOE3.bbdesign()`; 3+ factors, numeric levels
- `_definitive_screening(cfg)` — Conference-matrix construction; 2k+1 runs, 3 levels
- `_taguchi(cfg)` — `pyDOE3.taguchi_design()`; orthogonal array auto-selection
- `_d_optimal(cfg)` — Fedorov row-exchange algorithm; maximizes det(X'X)
- `_mixture_simplex_lattice(cfg)` — Simplex-lattice for formulation experiments
- `_mixture_simplex_centroid(cfg)` — Simplex-centroid for formulation experiments
- `augment_design(matrix, cfg, augment_type)` — fold-over, star points, or center points
- `evaluate_design(matrix, cfg)` — D-efficiency, A-efficiency, G-efficiency
- `_apply_blocks()` — replicate + assign block_id
- `_randomize_run_order()` — shuffle within each block independently

### `doe/analysis.py`
- `analyze(matrix, cfg, results_dir, no_plots, pareto_threshold)` → AnalysisReport
- `_compute_anova(runs, responses, factor_names, factors)` → AnovaTable
  - Type I SS decomposition with F-tests and p-values
  - Lenth's pseudo-standard-error for unreplicated designs
  - Lack-of-fit test when replicates exist
- Main effects with 95% confidence intervals (scipy.stats.t)
- Two-factor interaction effects for 2-level factors
- Summary statistics per factor per level
- `plot_pareto()` — Pareto charts with cumulative contribution line
- `plot_main_effects()` — Grid of line plots per factor
- `plot_normal_effects()` — Normal probability plot of effects with significant effects labeled
- `plot_half_normal_effects()` — Half-normal plot for screening
- `plot_diagnostics()` — 2×2 panel: residuals vs fitted, normal probability, residuals vs run order, predicted vs actual
- `plot_rsm_surface()` — 3D response surface for continuous factor pairs
- `export_csv(report, output_dir)` — CSV export of effects and stats

### `doe/rsm.py`
- `RSMModel(response_name, coefficients, r_squared, adj_r_squared, predicted_optimum, predicted_value, diagnostics)`
- `ModelDiagnostics(residuals, fitted_values, hat_matrix_diag, press, predicted_r_squared, run_ids)`
- `fit_rsm(runs, responses, factor_names, factors, model_type)` → RSMModel
  - Linear and quadratic polynomial regression via numpy least-squares
  - R², adjusted R², PRESS, predicted R²
  - Hat matrix and leverage computation
- `optimize_surface(model, factor_names, factors, direction, n_restarts)` → dict
  - True surface optimization via `scipy.optimize.minimize` (L-BFGS-B)
  - 10 random restarts to avoid local optima
  - Operates in coded space [-1, 1], decodes to natural units
- `steepest_ascent(model, factor_names, factors, direction, n_steps)` → list[dict]
  - Gradient-based follow-up experiment pathway
  - Standard RSM Phase 1 methodology (Myers & Montgomery)

### `doe/optimize.py`
- `recommend(matrix, cfg, results_dir, response_name)` — print optimization recommendations
  - Best observed run, RSM model fit (linear + quadratic), curvature analysis
  - True surface optimization via `optimize_surface()`
  - Factor importance ranking
- `multi_objective(matrix, cfg, results_dir)` — Derringer-Suich desirability functions
  - Weighted geometric mean of individual desirabilities
  - Grid search + response predictions

### `doe/report.py`
- `generate_report(matrix, cfg, results_dir, output_path)` — self-contained HTML report
- Embedded base64 plot images, collapsible sections, responsive tables
- Includes: ANOVA tables, main effects, interactions, summary stats, all plot types, optimization results

### `doe/codegen.py`
- `generate_script(matrix, cfg, output_path, format)` — render Jinja2 template, chmod +x
- Three arg styles: double-dash, env, positional
- Error recovery: track failed runs, continue on failure, summary at end

### `doe/cli.py`
Subcommands via argparse:
```
doe generate    --config FILE [--output FILE] [--format sh|py] [--seed N] [--dry-run]
doe analyze     --config FILE [--results-dir DIR] [--no-plots] [--csv DIR] [--partial]
doe info        --config FILE
doe optimize    --config FILE [--results-dir DIR] [--response NAME] [--multi] [--steepest] [--partial]
doe power       --config FILE [--sigma FLOAT] [--delta FLOAT] [--alpha FLOAT] [--results-dir DIR] [--partial]
doe augment     --config FILE --type fold_over|star_points|center_points [--output FILE] [--format sh|py]
doe report      --config FILE [--results-dir DIR] [--output FILE] [--partial]
doe record      --config FILE --run N|all [--seed N]
doe status      --config FILE [--seed N]
doe export-worksheet --config FILE [--format csv|markdown] [--output FILE] [--seed N]
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pyDOE3>=1.0.0` | PB, LHS, CCD, fractional factorial, Box-Behnken, Taguchi |
| `numpy>=1.26.0` | Array operations, RSM least-squares, hat matrix |
| `pandas>=2.0.0` | Data manipulation |
| `matplotlib>=3.7.0` | Pareto, main effects, diagnostic, normal/half-normal, RSM surface plots |
| `scipy>=1.11.0` | ANOVA F-tests, confidence intervals, surface optimization, power analysis |
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

10. **ANOVA for unreplicated designs** — Uses Lenth's pseudo-standard-error (same approach as R's FrF2), allowing ANOVA even without replicates.

11. **True surface optimization** — Uses `scipy.optimize.minimize` (L-BFGS-B) with 10 random restarts in coded space, replacing the previous approach of only checking observed points.

12. **Backward compatibility** — All new dataclass fields use defaults. New design types are additive to `SUPPORTED_OPERATIONS`. Existing configs remain valid.

13. **No new dependencies** — All features use existing numpy, scipy, matplotlib, and pyDOE3.
