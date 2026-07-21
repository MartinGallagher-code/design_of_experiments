# Design of Experiments (DOE) Helper Tool

[![CI](https://github.com/MartinGallagher-code/design_of_experiments/actions/workflows/ci.yml/badge.svg)](https://github.com/MartinGallagher-code/design_of_experiments/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/doehelper?logo=pypi&logoColor=white)](https://pypi.org/project/doehelper/)
[![Python versions](https://img.shields.io/pypi/pyversions/doehelper?logo=python&logoColor=white)](https://pypi.org/project/doehelper/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![REUSE status](https://api.reuse.software/badge/github.com/MartinGallagher-code/design_of_experiments)](https://api.reuse.software/info/github.com/MartinGallagher-code/design_of_experiments)

A Python CLI tool that automates the creation and analysis of experimental designs. It generates reproducible design matrices, creates executable runner scripts, and analyzes results using classical DOE techniques including ANOVA, response surface modeling, and multi-objective optimization.

The project includes **221 worked use cases** spanning HPC, cloud infrastructure, networking, food science, agriculture, manufacturing, sports, and many more domains — each with a full configuration, simulated results, and analysis walkthrough. Browse them in [`doe/use_cases/`](https://github.com/MartinGallagher-code/design_of_experiments/tree/main/doe/use_cases).

## Installation

The package is published on PyPI at [pypi.org/project/doehelper](https://pypi.org/project/doehelper/) — install the latest release with:

```bash
pip install doehelper
```

The source lives on GitHub at [github.com/MartinGallagher-code/design_of_experiments](https://github.com/MartinGallagher-code/design_of_experiments). You can [download a release archive](https://github.com/MartinGallagher-code/design_of_experiments/releases) (`.zip`/`.tar.gz`) from the releases page, or clone the repository for development:

```bash
git clone https://github.com/MartinGallagher-code/design_of_experiments.git
cd design_of_experiments
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

The five-step workflow:

```bash
# 1. Bootstrap a config + a starter test.py from your situation.
doe init --factors 3 --budget 30 --goal response_surface --with-test

# 2. Edit the placeholder factor / response names and the TODO block in test.py.

# 3. Generate the runner script (with optional sessions + parallelism).
doe generate --config config.json --session baseline --parallel 4

# 4. Run the experiments.
bash run_experiments.sh

# 5. Analyse — produces a console report plus self-contained HTML.
doe analyze --config config.json
```

Other things you can do once you have results:

```bash
# Recommend a design without committing to it
doe suggest --factors 7 --budget 12 --goal screening

# Iterate with Bayesian optimisation on a GP surrogate
doe next-batch --config config.json     # uses cfg.adaptive.strategy
bash run_next_batch.sh

# Browse sessions on localhost
doe serve --root results/

# Variance-based sensitivity over the fitted surrogate
doe sensitivity --config config.json --n-samples 1024 --csv sobol.csv

# Bundle a session for sharing or filing with a regulator
doe archive --session results/baseline --output baseline.tar.gz \
            --config config.json --extra results/report.html

# Compare two sessions, or trend-fit across N sessions
doe compare --config config.json --baseline results/v1 --candidate results/latest --html compare.html
doe trend   --config config.json --sessions results/v1 results/v2 results/v3 --html trend.html

# Calibrate a parametric simulator against observed data
doe calibrate --config config.json --func sim.py:simulate \
              --params slope:-5:5 intercept:-2:2 --observed results/baseline
```

Or extract one of the built-in use-case templates:

```bash
doe init --list
doe init --template reactor_optimization
```

For the full step-by-step tour see **[docs/user_guide.md](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/docs/user_guide.md)**.

## Documentation

**Getting Started**:
- **[User guide](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/docs/user_guide.md)** — five-step workflow tour from first config to a finished report.
- **[Quick start](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/README.md#quick-start)** — first experiment in 5 minutes.

**Reference**:
- **[Command reference](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/docs/commands.md)** — one-line-per-subcommand cheat sheet.
- **[Config reference](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/docs/config.md)** — every recognised JSON key, default, and constraint.
- **[Public API](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/docs/api.md)** — stable APIs, backward compatibility guarantees, deprecation policy.

**Advanced**:
- **[Adaptive strategies](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/docs/strategies.md)** — when to pick `refine` / `bayesian` / `multi_objective` etc.
- **[Release process](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/docs/RELEASE.md)** — how to cut a release.
- **[Project roadmap](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/ROADMAP.md)** — planned features and vision.

## Features

### Bootstrap & scaffolding
- **`doe init --factors N --budget K --goal screening|response_surface|optimization`** writes a working starter `config.json` (with `--with-test` it also scaffolds `test.py`).
- **`doe suggest`** explains the design choice for any factor count + budget.
- **`doe scaffold-config`** drops an annotated `config.json` with `_<key>_options` showing the alternatives; **`doe scaffold-test`** writes a test-script stub matching the configured `arg_style`.
- **`doe init --template <name>`** extracts one of the built-in use-case templates.

### Design generation
- 14 design strategies: full-factorial, fractional factorial (with `--resolution N` to bump run count until the requested resolution is achievable), Plackett-Burman, Latin Hypercube, central composite, Box-Behnken, definitive screening, Taguchi, D-optimal (with interior-point candidate set), mixture simplex-lattice / centroid, linear / log sweep, **split-plot** with role-based whole-plot / subplot factors.
- **Constraints**: filter generated runs through Python expressions like `"x + y <= 1"` parsed with an AST allow-list.
- **Blocking & centre-point replication**: `block_count`, `replicate_center N` per block.
- **Integer factors**: `Factor.dtype: "int"` rounds and clamps recommended setpoints from every optimiser.
- **Runner backends**: bash (`--format sh`), Python (`--format py`), parallel thread-pool (`--parallel N`), Slurm sbatch array (`--executor slurm` with full `--slurm-{partition,time,cpus-per-task,mem,max-concurrent}` plumbing).
- **Sessions**: `--session [PREFIX]` writes each runner invocation to `<out>/<PREFIX>-<TIMESTAMP>/` and updates `<out>/latest`.

### Running
- **`doe simulate --func module:fn`** drives the design directly from a Python function — no shell.
- **`doe record --run N`** enters results interactively.
- **`doe status`** shows progress.

### Analysis
- **ANOVA**: five error paths chosen automatically (pooled / replicates / Lenth's PSE for unreplicated / split-plot two-error / blocked).
- **Main effects**, two-factor interactions, ordinal trend decomposition (linear + quadratic for >2-level factors).
- **Model adequacy**: PRESS / predicted R², Shapiro-Wilk normality, Durbin-Watson, run-order drift, leverage and Cook's distance with the `F(0.5, p, n-p)` cutoff.
- **Stationary point** classification from Hessian eigenvalues — maximum / minimum / saddle / ridge / rising_ridge with the indeterminate axis surfaced.
- **Achieved power** from the actual residual MS — per-factor power and minimum detectable effect.
- **Cross-validation**: k-fold predicted-vs-actual with RMSE / MAE / R²<sub>cv</sub>.
- **Alias structure** for fractional-factorial / Plackett-Burman.
- **Scheffé canonical form** for mixture designs.
- **Knee-point detection** for saturating curves.
- **Sobol sensitivity** (`doe sensitivity`) — first-order and total-order indices on the fitted RSM via Saltelli sampling.

### Optimisation & iteration
- **`doe optimize`** — true surface optimum (L-BFGS-B with multi-start), multi-objective desirability, steepest ascent / descent.
- **`doe next-batch`** — six adaptive strategies: `refine`, `explore`, `balanced`, `model_guided` (RSM optimum + max-leverage), `bayesian` (numpy-only Gaussian process + Expected Improvement, q-EI via constant-liar fantasising, mixed numeric + one-hot categorical encoder, heteroscedastic noise from replicate scatter), `multi_objective` (per-response GPs + random Tchebycheff scalarisation).
- **`doe calibrate`** fits free parameters in a parametric simulator to observed data.

### Comparing & reporting
- **`doe compare --baseline DIR --candidate DIR`** — paired-run delta + Cohen's d, per-factor effect delta with sign-flip flag, intercept-shift vs slope-shift decomposition, embedded delta dotplot.
- **`doe trend --sessions DIR1 DIR2 …`** — multi-session regression with per-session means and per-step intercept / slope drift; embedded line plot.
- **`doe report`** — self-contained interactive HTML with sticky table-of-contents and embedded plots.
- **`doe archive`** — bundles a session into a tarball with a SHA-256 manifest.
- **`doe serve --root results/`** — stdlib HTTP localhost browser for sessions.

### Power & quality
- **`doe power`** — prospective power analysis (`--sigma`, `--delta`) plus the post-hoc achieved-power block in every `doe analyze`.
- **D-efficiency / A-efficiency / G-efficiency** metrics in `doe info`.

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
        "test_script": "my_test_script.sh",
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

### `init` — Create a new experiment from a built-in template
```
doe init [--template NAME] [--list]
```

| Flag | Description |
|------|-------------|
| `--list` | List all available built-in templates |
| `--template` | Template name (e.g. `reactor_optimization`, `coffee_brewing`) |

### `generate` — Create design and runner script
```
doe generate --config FILE [--output FILE] [--format sh|py] [--seed N] [--dry-run]
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
doe analyze --config FILE [--results-dir DIR] [--no-plots] [--csv DIR] [--partial]
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
doe info --config FILE
```

Shows design matrix, factor details, alias structure (for fractional factorials), and design evaluation metrics (D-efficiency, A-efficiency, G-efficiency).

### `optimize` — Recommend optimal factor settings
```
doe optimize --config FILE [--results-dir DIR] [--response NAME] [--multi] [--steepest] [--partial]
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
doe power --config FILE [--sigma FLOAT] [--delta FLOAT] [--alpha FLOAT] [--results-dir DIR] [--partial]
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
doe augment --config FILE --type TYPE [--output FILE] [--format sh|py] [--seed N]
```

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--type` | Augmentation type: `fold_over`, `star_points`, or `center_points` |
| `--output` | Output script path (default: `run_experiments_augmented.sh`) |
| `--format` | Script format: `sh` or `py` (default: `sh`) |

### `report` — Generate interactive HTML report
```
doe report --config FILE [--results-dir DIR] [--output FILE] [--partial]
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
doe record --config FILE --run N|all [--seed N]
```

### `status` — Show experiment progress
```
doe status --config FILE [--seed N]
```

### `export-worksheet` — Export design as printable worksheet
```
doe export-worksheet --config FILE [--format csv|markdown] [--output FILE] [--seed N]
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
doe power --config config.json --sigma 2.0 --delta 5.0

# Estimate sigma from existing results
doe power --config config.json --delta 5.0 --results-dir results/
```

Power < 0.80 indicates you may need more runs or blocks to reliably detect the specified effect size.

## Project Structure

```
design_of_experiments/
├── doe/
│   ├── __init__.py         # Package version
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
├── tests/                  # Test suite (pytest)
├── website/                # Project website with 221 use case walkthroughs
├── pyproject.toml          # Package metadata and build config
└── .github/workflows/
    ├── ci.yml              # CI pipeline (Python 3.10/3.11/3.12)
    └── publish.yml         # PyPI publish on release
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

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/CONTRIBUTING.md) for development setup and PR guidelines. Please report security vulnerabilities privately per [SECURITY.md](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/SECURITY.md), and note that this project follows the [Contributor Covenant](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/CODE_OF_CONDUCT.md).

## License

This project is licensed under the GNU General Public License v3.0 — see [LICENSE](https://github.com/MartinGallagher-code/design_of_experiments/blob/main/LICENSE) for details.
