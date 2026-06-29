# Public API Reference

This document defines the stable public API for DOE Helper and backward compatibility guarantees.

## Stability Guarantees

### Stable API (Semver Protected)

Functions and classes documented here are part of the public API. Breaking changes are only introduced in major version releases and are announced in the CHANGELOG.

**Stable modules:**
- `doe.config`: Configuration loading and validation
- `doe.design`: Design matrix generation
- `doe.models`: Data structures and result types
- `doe.analysis`: Design analysis and statistics
- `doe.rsm`: Response surface modeling
- `doe.codegen`: Script generation

**Stable CLI commands:**
- All subcommands and their primary options documented in `docs/commands.md`
- Flag names and meanings are stable across MINOR versions

### Internal API (No Guarantees)

Functions and classes prefixed with `_` (underscore) are private/internal and may change without notice:

```python
from doe.analysis import _load_all_results  # PRIVATE - not stable
from doe.design import _full_factorial       # PRIVATE - not stable
```

**How to identify private APIs:**
- Function/class name starts with `_`
- Located in modules marked as "internal" or not documented
- Imported via `from doe._internal import ...`

### Undocumented Parameters

Parameters not mentioned in docs or examples are implementation details and may change.

## Core Public APIs

### Configuration

```python
from doe.config import load_config
from doe.models import DOEConfig

# Load and validate a configuration
cfg: DOEConfig = load_config("config.json")

# Access configuration properties
print(cfg.factors)           # list[Factor]
print(cfg.responses)         # list[ResponseVar]
print(cfg.operation)         # str (design type)
print(cfg.out_directory)     # str (results path)
```

### Design Generation

```python
from doe.design import generate_design
from doe.models import DesignMatrix

# Generate a design matrix
matrix: DesignMatrix = generate_design(cfg, seed=42)

# Access design properties
print(matrix.runs)           # list[ExperimentRun]
print(matrix.factor_names)   # list[str]
print(matrix.operation)      # str (design type used)
print(matrix.metadata)       # dict (n_runs, n_factors, etc.)
```

### Analysis

```python
from doe.analysis import analyze
from doe.models import AnalysisReport

# Analyze experimental results
report: AnalysisReport = analyze(cfg, results_dir="results/")

# Access results
for response_name, analysis in report.results_by_response.items():
    print(f"{response_name}:")
    for effect in analysis.effects:
        print(f"  {effect.factor_name}: {effect.main_effect}")
    if analysis.anova_table:
        print(f"  R²: {analysis.anova_table}")
```

### Response Surface Modeling

```python
from doe.rsm import fit_rsm, optimize_surface, steepest_ascent

# Fit a response surface model
model = fit_rsm(
    runs=matrix.runs,
    responses={1: 85.3, 2: 87.1, ...},  # run_id → value
    factor_names=matrix.factor_names,
    factors=cfg.factors,
    model_type="quadratic"
)

# Find the surface optimum
optimum = optimize_surface(
    model=model,
    factor_names=matrix.factor_names,
    factors=cfg.factors,
    direction="maximize"
)
print(optimum["optimal_settings"])
print(optimum["predicted_value"])

# Generate steepest ascent path
path = steepest_ascent(
    model=model,
    factor_names=matrix.factor_names,
    factors=cfg.factors,
    direction="maximize",
    n_steps=10
)
for step in path:
    print(f"Step {step['step']}: {step['settings']}")
```

### Report Generation

```python
from doe.report import generate_report

# Generate an interactive HTML report
generate_report(
    cfg=cfg,
    results_dir="results/",
    output_path="report.html",
    partial=False
)
```

## Command-Line Interface

The CLI is part of the stable public API. Commands and options documented in `docs/commands.md` are stable.

All CLI output should be parseable but is not guaranteed to be machine-readable (may change format between minor versions).

```bash
# Stable commands (semver protected)
doe init --factors N --budget K --goal screening
doe generate --config config.json
doe analyze --config config.json
doe optimize --config config.json
doe report --config config.json
doe next-batch --config config.json
```

## Deprecation Policy

When a feature needs to be removed:

1. **Deprecation announcement** (Minor release): Feature is marked `@deprecated`, warnings logged, documented in CHANGELOG
2. **Supported period** (1+ minor releases): Feature still works but warns users
3. **Removal** (Major release): Feature removed, documented in CHANGELOG with migration path

### Example Deprecation

```python
import warnings

@deprecated("Use `doe.design.generate_design()` instead")
def legacy_generate(cfg):
    warnings.warn(
        "legacy_generate is deprecated, use generate_design() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return generate_design(cfg)
```

## Example: Full Workflow Using Public APIs

```python
from doe.config import load_config
from doe.design import generate_design
from doe.analysis import analyze
from doe.rsm import fit_rsm, optimize_surface
from doe.report import generate_report

# 1. Load configuration
cfg = load_config("config.json")

# 2. Generate design
matrix = generate_design(cfg, seed=42)

# 3. Run experiments (external; results in JSON files)
# ... (user runs bash script or Python runner)

# 4. Analyze results
report = analyze(cfg, results_dir="results/")

# 5. Fit model and optimize (if multi-level factors)
responses = {
    1: 85.3,
    2: 87.1,
    # ... etc.
}
model = fit_rsm(
    runs=matrix.runs,
    responses=responses,
    factor_names=matrix.factor_names,
    factors=cfg.factors,
    model_type="quadratic"
)
optimum = optimize_surface(model, matrix.factor_names, cfg.factors)

# 6. Generate report
generate_report(cfg, results_dir="results/", output_path="report.html")
```

## Backward Compatibility

- **Python versions**: Minimum supported version is Python 3.10
- **Dependencies**: Pins are in `pyproject.toml`; transitive versions are semver-compatible
- **Configuration files**: JSON config format is backwards compatible; new keys have defaults

## Questions?

- For feature requests, open an issue on GitHub
- For API questions, see CONTRIBUTING.md
- For security issues, see SECURITY.md
