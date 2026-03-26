# Design of Experiments (DOE) Helper Tool

Created and developed by **Martin J. Gallagher**.

A Python CLI tool that automates the creation and analysis of experimental designs. It generates reproducible design matrices, creates executable runner scripts, and analyzes results using classical DOE techniques including ANOVA, response surface modeling, and multi-objective optimization.

## Features

- **Multiple design strategies**: Full-factorial, Fractional Factorial, Plackett-Burman, Latin Hypercube, Central Composite, Box-Behnken, Definitive Screening, Taguchi, D-optimal, and Mixture designs
- **ANOVA tables**: Full analysis of variance with F-tests, p-values, and Lenth's pseudo-standard-error for unreplicated designs
- **Multi-response analysis**: Analyze multiple response variables per experiment with per-response optimization direction
- **Main effects & interaction effects**: Compute main effects, two-factor interactions, confidence intervals, and summary statistics
- **Model diagnostics**: Residual plots, normal probability plots, leverage analysis, PRESS statistic, and predicted R²
- **Visualization**: Pareto charts, main effects plots, normal/half-normal probability plots, model diagnostic panels, and 3D response surface plots
- **True surface optimization**: Find the actual optimum of fitted RSM surfaces using scipy.optimize (L-BFGS-B with multi-start)
- **Steepest ascent/descent**: Generate follow-up experiment pathways along the gradient direction
- **Power analysis**: Compute statistical power for each factor to guide sample size decisions
- **Design evaluation**: D-efficiency, A-efficiency, and G-efficiency metrics
- **Design augmentation**: Extend existing designs with fold-over, star points, or center points
- **Alias structure analysis**: Display confounding patterns for fractional factorial designs
- **Runner script generation**: Bash or Python scripts with three argument styles (double-dash, env, positional)
- **Blocking & randomization**: Statistically correct within-block randomization
- **CSV export**: Export analysis results to CSV for further processing
- **HTML reports**: Self-contained interactive reports with embedded plots and ANOVA tables
- **Error recovery**: Generated runner scripts handle per-run failures gracefully

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd design_of_experiments

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .

# For development (includes pytest)
pip install -e ".[dev]"
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `pyDOE3` | Plackett-Burman, Latin Hypercube, Central Composite, Taguchi, fractional factorial designs |
| `numpy` | Array operations for design generation and RSM |
| `matplotlib` | Pareto, main effects, diagnostic, and response surface plots |
| `scipy` | Confidence intervals, ANOVA F-tests, surface optimization, power analysis |
| `Jinja2` | Runner script template rendering |
| `pandas` | Data manipulation |

> Full-factorial designs use only the Python standard library. `pyDOE3` is lazily imported only when needed.

## Quick Start

```bash
# Preview the design matrix (no files written)
python doe.py generate --config examples/example_config.json --dry-run

# Generate a runner script
python doe.py generate --config examples/example_config.json --output run.sh --seed 42

# Run the experiments
bash run.sh

# Analyze results (with ANOVA, plots, and diagnostics)
python doe.py analyze --config examples/example_config.json

# Export analysis results to CSV
python doe.py analyze --config examples/example_config.json --csv results/csv

# Show design summary with evaluation metrics
python doe.py info --config examples/example_config.json

# Get optimization recommendations (with true surface optimization)
python doe.py optimize --config examples/example_config.json

# Multi-objective optimization using desirability functions
python doe.py optimize --config examples/example_config.json --multi

# Show steepest ascent/descent pathway
python doe.py optimize --config examples/example_config.json --steepest

# Compute statistical power for each factor
python doe.py power --config examples/example_config.json --sigma 2.0 --delta 5.0

# Augment an existing design with fold-over runs
python doe.py augment --config examples/example_config.json --type fold_over

# Generate an interactive HTML report
python doe.py report --config examples/example_config.json --output report.html
```

## Configuration

The tool is driven by a JSON configuration file. Here is a full example:

```json
{
    "metadata": {
        "name": "example experiment",
        "description": "3-factor 2-level full factorial example"
    },
    "factors": [
        {"name": "temperature", "levels": ["low", "high"], "type": "categorical"},
        {"name": "pressure",    "levels": ["low", "high"], "type": "categorical"},
        {"name": "catalyst",    "levels": ["A", "B"],      "type": "categorical"}
    ],
    "fixed_factors": {
        "duration": "60"
    },
    "responses": [
        {"name": "yield", "optimize": "maximize", "unit": "%", "description": "Product yield", "weight": 1.5},
        {"name": "cost",  "optimize": "minimize", "unit": "USD", "description": "Production cost", "weight": 1.0}
    ],
    "runner": {
        "arg_style": "double-dash",
        "result_file": "json"
    },
    "settings": {
        "block_count": 1,
        "test_script": "examples/example_test_script.sh",
        "operation": "full_factorial",
        "processed_directory": "results/analysis",
        "out_directory": "results"
    }
}
```

### Configuration Reference

#### `metadata` (optional)
| Field | Description |
|-------|-------------|
| `name` | Experiment plan name |
| `description` | Human-readable description |

#### `factors` (required)
Each factor can be specified as a dict or a legacy array:

**Dict format** (recommended):
```json
{"name": "temperature", "levels": ["100", "200"], "type": "continuous", "unit": "°C", "description": "Reactor temperature"}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique factor name |
| `levels` | Yes | At least 2 levels |
| `type` | No | `categorical` (default), `continuous`, or `ordinal` |
| `unit` | No | Unit of measurement |
| `description` | No | Human-readable description |

**Legacy array format**: `["factor_name", "level1", "level2", ...]`

#### `fixed_factors` (optional)
Key-value pairs passed to every run unchanged:
```json
{"duration": "60", "warmup-time": "3"}
```

#### `responses` (optional)
If omitted, defaults to a single response named `"response"`.

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Response variable name (must match keys in result JSON) |
| `optimize` | No | `maximize` (default) or `minimize` |
| `unit` | No | Unit of measurement |
| `description` | No | Human-readable description |
| `weight` | No | Weight for multi-objective optimization (default: 1.0) |
| `bounds` | No | `[low, high]` bounds for desirability function |

#### `runner` (optional)
| Field | Default | Description |
|-------|---------|-------------|
| `arg_style` | `double-dash` | How factors are passed to the test script: `double-dash` (`--name value`), `env` (environment variables), or `positional` |
| `result_file` | `json` | Result file format |

#### `settings` (required)
| Field | Default | Description |
|-------|---------|-------------|
| `operation` | `full_factorial` | Design type (see below) |
| `test_script` | | Path to the test script to execute per run |
| `block_count` | `1` | Number of blocks (replicates) |
| `out_directory` | `results` | Directory for per-run result JSON files |
| `processed_directory` | | Directory for analysis outputs (plots, CSVs) |
| `lhs_samples` | `0` (auto) | Number of LHS samples; `0` = `max(10, 2 * n_factors)`. Also used as `n_runs` for D-optimal designs. |

## Supported Design Operations

| Operation | Description | Requirements |
|-----------|-------------|--------------|
| `full_factorial` | All combinations of factor levels | Any number of levels per factor |
| `fractional_factorial` | Resolution III fractional factorial | Exactly 2 levels per factor |
| `plackett_burman` | 2-level screening design | Exactly 2 levels per factor |
| `latin_hypercube` | Space-filling design for continuous factors | Any factor types; continuous factors are interpolated |
| `central_composite` | Response surface methodology (CCD) | Exactly 2 numeric levels per factor |
| `box_behnken` | 3-level response surface design | At least 3 factors, exactly 2 numeric levels each |
| `definitive_screening` | Modern 3-level screening design (Jones-Nachtsheim) | At least 3 factors, exactly 2 numeric levels each |
| `taguchi` | Orthogonal array design with S/N ratios | Any factor types |
| `d_optimal` | Algorithmically optimized design (Fedorov exchange) | Any factor types; set `lhs_samples` for desired run count |
| `mixture_simplex_lattice` | Simplex-lattice for mixture/formulation experiments | Components that sum to 1 |
| `mixture_simplex_centroid` | Simplex-centroid for mixture/formulation experiments | Components that sum to 1 |

## CLI Reference

### `generate` — Create design and runner script
```
python doe.py generate --config FILE [--output FILE] [--format sh|py] [--seed N] [--dry-run]
```

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--output` | Output script path (default: `run_experiments.sh`) |
| `--format` | Script format: `sh` or `py` (default: `sh`) |
| `--seed` | Random seed for reproducible run order |
| `--dry-run` | Print design matrix without writing files |

### `analyze` — Analyze experiment results
```
python doe.py analyze --config FILE [--results-dir DIR] [--no-plots] [--csv DIR] [--partial]
```

Computes main effects, interaction effects, ANOVA table, and generates plots including Pareto charts, main effects plots, normal/half-normal probability plots, model diagnostic panels, and 3D response surface plots.

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--results-dir` | Override `out_directory` from config |
| `--no-plots` | Skip generating plot images |
| `--csv` | Export results to CSV files in the specified directory |
| `--partial` | Analyze only completed runs, skip missing results |

### `info` — Display design summary
```
python doe.py info --config FILE
```

Shows design matrix, factor details, alias structure (for fractional factorials), and design evaluation metrics (D-efficiency, A-efficiency, G-efficiency).

### `optimize` — Recommend optimal factor settings
```
python doe.py optimize --config FILE [--results-dir DIR] [--response NAME] [--multi] [--steepest] [--partial]
```

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--results-dir` | Override `out_directory` from config |
| `--response` | Optimize for a specific response (default: all) |
| `--multi` | Multi-objective optimization using Derringer-Suich desirability functions |
| `--steepest` | Show steepest ascent/descent pathway for sequential experimentation |
| `--partial` | Analyze only completed runs |

### `power` — Compute statistical power
```
python doe.py power --config FILE [--sigma FLOAT] [--delta FLOAT] [--alpha FLOAT] [--results-dir DIR] [--partial]
```

Computes statistical power for detecting effects of a given size. If `--sigma` is omitted and results are available, sigma is estimated from residuals.

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--sigma` | Error standard deviation (estimated from results if omitted) |
| `--delta` | Minimum detectable effect size (default: 2 * sigma) |
| `--alpha` | Significance level (default: 0.05) |

### `augment` — Extend an existing design
```
python doe.py augment --config FILE --type TYPE [--output FILE] [--format sh|py] [--seed N]
```

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--type` | Augmentation type: `fold_over`, `star_points`, or `center_points` |
| `--output` | Output script path (default: `run_experiments_augmented.sh`) |
| `--format` | Script format: `sh` or `py` (default: `sh`) |

### `report` — Generate interactive HTML report
```
python doe.py report --config FILE [--results-dir DIR] [--output FILE] [--partial]
```

Generates a self-contained HTML report with embedded plots, ANOVA tables, optimization results, and design matrix.

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--results-dir` | Override `out_directory` from config |
| `--output` | Output HTML file path (default: `report.html`) |
| `--partial` | Analyze only completed runs |

### `record` — Interactively record results
```
python doe.py record --config FILE --run N|all [--seed N]
```

### `status` — Show experiment progress
```
python doe.py status --config FILE [--seed N]
```

### `export-worksheet` — Export design as printable worksheet
```
python doe.py export-worksheet --config FILE [--format csv|markdown] [--output FILE] [--seed N]
```

## Test Script Protocol

Your test script must:
1. Accept factor values via the configured `arg_style`
2. Accept `--out <path>` to specify the output file path
3. Write a JSON file to `--out` with keys matching your `responses` names

Example output (`run_1.json`):
```json
{"yield": 85.3, "cost": 12.50}
```

## Analysis Output

The `analyze` command computes:

- **ANOVA table**: Sum of squares decomposition, F-tests, and p-values for each factor and interaction. Uses Lenth's pseudo-standard-error for unreplicated designs (same approach as R's FrF2 package). Includes lack-of-fit test when replicates are available.
- **Main effects**: For 2-level factors, `mean(high) - mean(low)`. For >2 levels, `max(means) - min(means)`.
- **Interaction effects**: Two-factor interactions for all pairs of 2-level factors.
- **Confidence intervals**: 95% CI on main effects using the t-distribution.
- **Summary statistics**: Per-factor, per-level: count, mean, std, min, max.
- **Model diagnostics**: Residuals vs fitted, normal probability plot of residuals, residuals vs run order, predicted vs actual. Includes PRESS statistic and predicted R².
- **Pareto chart**: Horizontal bar chart of effect magnitudes with cumulative contribution line.
- **Main effects plot**: Grid of line plots showing mean response at each factor level.
- **Normal probability plot**: Effects plotted against normal quantiles; significant effects deviate from the reference line and are labeled.
- **Half-normal probability plot**: Absolute effects against half-normal quantiles for screening.
- **Response surface plots**: 3D surface plots for continuous factor pairs from quadratic RSM models.

## Optimization

The `optimize` command provides:

- **Best observed run**: The run with the best response value.
- **RSM models**: Linear and quadratic polynomial regression with R² and adjusted R².
- **True surface optimization**: Uses `scipy.optimize.minimize` (L-BFGS-B) with 10 random restarts to find the actual optimum of the fitted surface, not just the best observed point.
- **Steepest ascent/descent**: Generates a table of follow-up experiment points along the gradient direction (standard RSM Phase 1 methodology, Myers & Montgomery).
- **Multi-objective optimization**: Derringer-Suich desirability functions with weighted geometric mean for optimizing multiple responses simultaneously.
- **Factor importance ranking**: Factors sorted by absolute effect contribution.
- **Curvature and interaction analysis**: For quadratic models, identifies concave/convex shapes and synergistic/antagonistic interactions.

## Design Evaluation

The `info` command displays design evaluation metrics:

- **D-efficiency**: Measures information content; higher is better. Based on `det(X'X)`.
- **A-efficiency**: Measures average prediction variance; higher is better. Based on `trace((X'X)^-1)`.
- **G-efficiency**: Measures worst-case prediction variance; higher is better. Based on maximum leverage.

## Power Analysis

The `power` command helps determine if your design has enough runs to detect effects of a given size:

```bash
# With known error standard deviation
python doe.py power --config config.json --sigma 2.0 --delta 5.0

# Estimate sigma from existing results
python doe.py power --config config.json --delta 5.0 --results-dir results/
```

Power < 0.80 indicates you may need more runs or blocks to reliably detect the specified effect size.

## Project Structure

```
design_of_experiments/
├── doe.py                  # Thin CLI wrapper
├── doe/
│   ├── cli.py              # CLI entry point (argparse, subcommands)
│   ├── models.py           # Dataclasses (Factor, DOEConfig, DesignMatrix, AnovaTable, etc.)
│   ├── config.py           # JSON config loading and validation
│   ├── design.py           # Design matrix generation (11 design types + augmentation)
│   ├── codegen.py          # Runner script generation (Jinja2)
│   ├── analysis.py         # Results analysis, ANOVA, plotting, CSV export
│   ├── rsm.py              # Response surface modeling, surface optimization, steepest ascent
│   ├── optimize.py         # Optimization recommendations
│   └── report.py           # Self-contained HTML report generation
├── templates/
│   ├── runner_sh.j2        # Bash runner template (with error recovery)
│   └── runner_py.j2        # Python runner template (with error recovery)
├── tests/                  # Test suite (93 tests, pytest)
├── examples/
│   ├── example_config.json
│   └── sysbench_config.json
└── .github/workflows/
    └── ci.yml              # CI pipeline (Python 3.10/3.11/3.12)
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=doe --cov-report=term-missing
```

## License

This project is licensed under the GNU General Public License v3.0 — see [LICENSE](LICENSE) for details.
