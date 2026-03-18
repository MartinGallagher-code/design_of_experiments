# Design of Experiments (DOE) Helper Tool — Implementation Plan

## Context

The repository had only a README.md describing a DOE helper tool. This plan documents the full implementation that was built from scratch. The tool reads a JSON config, generates a design matrix (full-factorial or Plackett-Burman), produces an executable runner script, and analyzes results with main effects plots.

---

## File Structure

```
/workspaces/design_of_experiments/
├── README.md
├── PLAN.md                          # this file
├── pyproject.toml                   # package metadata and deps
├── requirements.txt                 # numpy, pandas, matplotlib, pyDOE2, Jinja2
├── doe.py                           # CLI entry point
├── doe/
│   ├── __init__.py
│   ├── models.py                    # dataclasses: Factor, DOEConfig, ExperimentRun, DesignMatrix, AnalysisReport
│   ├── config.py                    # JSON loading + validation → DOEConfig
│   ├── design.py                    # design matrix generation (full_factorial, plackett_burman)
│   ├── codegen.py                   # Jinja2 script rendering → runner.sh / runner.py
│   └── analysis.py                  # results loading, main effects, summary stats, plots
├── templates/
│   ├── runner_sh.j2                 # shell script template
│   └── runner_py.j2                 # Python runner template
└── examples/
    ├── example_config.json          # 3 factors × 2 levels, full_factorial
    └── example_test_script.sh       # stub that writes {"response": <float>} to --out path
```

---

## Data Flow

```
Input JSON
    → doe/config.py    load_config()       → DOEConfig
    → doe/design.py    generate_design()   → DesignMatrix
    → doe/codegen.py   generate_script()   → runner.sh
    → doe/analysis.py  analyze()           → AnalysisReport (after experiments run)
```

---

## Key Modules

### `doe/models.py`
Typed dataclasses shared across all modules:
- `Factor(name, levels)`
- `DOEConfig(factors, static_settings, block_count, test_script, operation, processed_directory, out_directory)`
- `ExperimentRun(run_id, block_id, factor_values, static_settings)`
- `DesignMatrix(runs, factor_names, operation, metadata)`
- `EffectResult(factor_name, main_effect, std_error, pct_contribution)`
- `AnalysisReport(effects, summary_stats, pareto_chart_path, effects_plot_path)`

### `doe/config.py`
- `load_config(path, strict=True) -> DOEConfig` — parse JSON, validate, return typed config
- `_validate_config(cfg)` — checks: supported operation, PB requires 2 levels per factor, unique factor names, block_count ≥ 1
- `SUPPORTED_OPERATIONS = {"full_factorial", "plackett_burman"}`

### `doe/design.py`
- `generate_design(cfg, seed=None) -> DesignMatrix` — dispatch by operation
- `_full_factorial(cfg)` — `itertools.product` over all factor levels; zero extra deps
- `_plackett_burman(cfg)` — `pyDOE2.pbdesign(n)`, maps ±1 to factor levels; requires 2 levels per factor
- `_apply_blocks(runs, block_count, static_settings)` — replicate + assign block_id
- `_randomize_run_order(runs, seed)` — shuffle within each block independently

### `doe/codegen.py`
- `generate_script(matrix, cfg, output_path, format="sh") -> str` — render Jinja2 template, write file, chmod +x
- Shell template: loops over runs, calls `test_script --<factor> <value> ... --out run_N.json`

### `doe/analysis.py`
- `analyze(matrix, cfg, results_dir=None) -> AnalysisReport`
- `_load_results(runs, results_dir)` — reads `run_{N}.json`, extracts `response` float
- `_compute_main_effects(runs, responses, factor_names)` — mean(high) − mean(low); % contribution
- `_compute_summary_stats(...)` — per-factor per-level: n, mean, std, min, max
- `plot_pareto(effects, output_path)` — horizontal bar chart sorted by |effect|, 80% cumulative line
- `plot_main_effects(runs, responses, factor_names, output_path)` — grid of subplots, one per factor

### `doe.py` (CLI)
Three subcommands via argparse:
```
python doe.py generate --config FILE [--output FILE] [--format sh|py] [--seed N] [--dry-run]
python doe.py analyze  --config FILE [--results-dir DIR] [--no-plots]
python doe.py info     --config FILE
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pyDOE2>=1.3.0` | Plackett-Burman design matrices |
| `numpy>=1.26.0` | Array operations |
| `pandas>=2.0.0` | Result aggregation |
| `matplotlib>=3.7.0` | Pareto + main effects plots |
| `scipy>=1.11.0` | Optional deeper analysis |
| `Jinja2>=3.1.0` | Script template rendering |

> Full-factorial uses only stdlib (`itertools.product`). pyDOE2 is only imported inside the Plackett-Burman code path, so the tool works without it for full-factorial designs.

---

## Usage

```bash
# Install deps
pip install -r requirements.txt

# Preview the design (dry run — no files written)
python doe.py generate --config examples/example_config.json --dry-run

# Show design summary
python doe.py info --config examples/example_config.json

# Generate runner script
python doe.py generate --config examples/example_config.json --output run.sh --seed 42

# Run experiments (make stub executable first)
chmod +x examples/example_test_script.sh
bash run.sh

# Analyze results
python doe.py analyze --config examples/example_config.json
```

Expected output for the example config: 8 runs (3 factors × 2 levels, full-factorial). After running, a Pareto chart and main effects plot are written to `results/analysis/`.

---

## Design Decisions

1. **Re-derive design at analysis time** — The `DesignMatrix` is reconstructed from the same config rather than serialized. Use `--seed` to ensure reproducible run order between `generate` and `analyze`.

2. **pyDOE2 as optional import** — Full-factorial has zero extra deps. pyDOE2 is only imported inside `_plackett_burman()` with a helpful install message on `ImportError`.

3. **Per-run JSON result files** — Each run writes `run_{N}.json` with `{"response": <float>}`. Partial failures are isolated; partial results can be inspected individually.

4. **Jinja2 templates** — Keeps template logic separate from Python. New script formats (PowerShell, batch) can be added by adding a template file, no Python changes needed.

5. **Block randomization** — Run order is shuffled within blocks, not across blocks. This is the statistically correct approach for blocked DOE.
