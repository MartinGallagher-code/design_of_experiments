# Design of Experiments (DOE) Helper Tool

A Python CLI tool that automates the creation and analysis of experimental designs. It generates reproducible design matrices, creates executable runner scripts, and analyzes results using classical DOE techniques.

## Features

- **Multiple design strategies**: Full-factorial, Plackett-Burman, Latin Hypercube, Central Composite
- **Multi-response analysis**: Analyze multiple response variables per experiment with per-response optimization direction
- **Main effects & interaction effects**: Compute main effects, two-factor interactions, confidence intervals, and summary statistics
- **Visualization**: Pareto charts with cumulative contribution line, main effects plots
- **Runner script generation**: Bash or Python scripts with three argument styles (double-dash, env, positional)
- **Blocking & randomization**: Statistically correct within-block randomization
- **CSV export**: Export analysis results to CSV for further processing
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
| `pyDOE3` | Plackett-Burman, Latin Hypercube, Central Composite designs |
| `numpy` | Array operations for design generation |
| `matplotlib` | Pareto and main effects plots |
| `scipy` | Confidence interval calculations |
| `Jinja2` | Runner script template rendering |

> Full-factorial designs use only the Python standard library. `pyDOE3` is lazily imported only when needed.

## Quick Start

```bash
# Preview the design matrix (no files written)
python doe.py generate --config examples/example_config.json --dry-run

# Generate a runner script
python doe.py generate --config examples/example_config.json --output run.sh --seed 42

# Run the experiments
bash run.sh

# Analyze results
python doe.py analyze --config examples/example_config.json

# Export analysis results to CSV
python doe.py analyze --config examples/example_config.json --csv

# Show design summary
python doe.py info --config examples/example_config.json
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
        {"name": "yield", "optimize": "maximize", "unit": "%", "description": "Product yield"},
        {"name": "cost",  "optimize": "minimize", "unit": "USD", "description": "Production cost"}
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
| `lhs_samples` | `0` (auto) | Number of LHS samples; `0` = `max(10, 2 * n_factors)` |

## Supported Design Operations

| Operation | Description | Requirements |
|-----------|-------------|--------------|
| `full_factorial` | All combinations of factor levels | Any number of levels per factor |
| `plackett_burman` | 2-level screening design | Exactly 2 levels per factor |
| `latin_hypercube` | Space-filling design for continuous factors | Any factor types; continuous factors are interpolated |
| `central_composite` | Response surface methodology (CCD) | Exactly 2 numeric levels per factor |

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
python doe.py analyze --config FILE [--results-dir DIR] [--no-plots] [--csv]
```

| Flag | Description |
|------|-------------|
| `--config` | Path to JSON config file (required) |
| `--results-dir` | Override `out_directory` from config |
| `--no-plots` | Skip generating plot images |
| `--csv` | Export results to CSV files |

### `info` — Display design summary
```
python doe.py info --config FILE
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

- **Main effects**: For 2-level factors, `mean(high) - mean(low)`. For >2 levels, `max(means) - min(means)`.
- **Interaction effects**: Two-factor interactions for all pairs of 2-level factors.
- **Confidence intervals**: 95% CI on main effects using the t-distribution.
- **Summary statistics**: Per-factor, per-level: count, mean, std, min, max.
- **Pareto chart**: Horizontal bar chart of effect magnitudes with cumulative contribution line.
- **Main effects plot**: Grid of line plots showing mean response at each factor level.

## Project Structure

```
design_of_experiments/
├── doe.py                  # CLI entry point
├── doe/
│   ├── models.py           # Dataclasses (Factor, DOEConfig, DesignMatrix, etc.)
│   ├── config.py           # JSON config loading and validation
│   ├── design.py           # Design matrix generation
│   ├── codegen.py          # Runner script generation (Jinja2)
│   └── analysis.py         # Results analysis, plotting, CSV export
├── templates/
│   ├── runner_sh.j2        # Bash runner template
│   └── runner_py.j2        # Python runner template
├── tests/                  # Test suite (pytest)
├── examples/
│   ├── example_config.json
│   └── sysbench_config.json
└── .github/workflows/
    └── ci.yml              # CI pipeline
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

MIT
