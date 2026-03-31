# DOE Helper — Build Prompt & Complete Reference

## Project Overview

**doehelper** is a command-line Design of Experiments (DOE) helper tool. It guides users through the full experimental workflow: designing experiments, generating runner scripts, executing runs, recording results, performing statistical analysis, optimizing factor settings, and generating reports.

- **Package name:** `doehelper`
- **Version:** 0.1.0
- **License:** GPL-3.0-or-later
- **Author:** Martin J. Gallagher
- **Python:** >=3.10
- **Entry point:** `doe` (maps to `doe.cli:main`)
- **Repository:** https://github.com/MartinGallagher-code/design_of_experiments
- **Homepage:** https://doehelper.com

### Dependencies

| Package | Min Version | Purpose |
|---------|-------------|---------|
| pyDOE3 | >=1.0.0 | Design generation (LHS, Plackett-Burman, Box-Behnken, etc.) |
| numpy | >=1.26.0 | Numerical computation |
| pandas | >=2.0.0 | Data manipulation |
| matplotlib | >=3.7.0 | Plot generation |
| scipy | >=1.11.0 | Statistical distributions and optimization (L-BFGS-B, F-distribution) |
| Jinja2 | >=3.1.0 | Script template rendering |

### Installation

```bash
pip install -e .
# or
pip install -e ".[dev]"   # includes pytest, pytest-cov
```

After installation the `doe` command is available globally.

---

## Typical Workflow

```
1. doe init --template <name>         # Bootstrap from a template
2. doe info --config config.json      # Review design matrix
3. doe generate --config config.json  # Create runner script
4. bash results/run.sh                # Execute experiment
5. doe status --config config.json    # Check progress
6. doe record --config config.json --run <N>  # Manual entry (if needed)
7. doe analyze --config config.json   # Statistical analysis
8. doe optimize --config config.json  # Find optimal settings
9. doe report --config config.json    # HTML report
10. doe augment --config config.json --type star_points  # Refine design
11. doe power --config config.json    # Power analysis
12. doe export-worksheet --config config.json  # Printable worksheet
```

---

## Command Reference

### `doe --version`

Print version, copyright, and license information, then exit.

**Output:**
```
doe 0.1.0
Copyright (C) 2026 Martin J. Gallagher
License: GPL-3.0-or-later <https://www.gnu.org/licenses/gpl-3.0.html>
```

---

### `doe generate`

Generate an experiment design matrix and produce a runner script (shell or Python) that executes each run.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--output FILENAME` | No | `run_experiments.sh` | Output script path |
| `--format {sh,py}` | No | `sh` | Script format: bash shell or Python |
| `--seed INT` | No | None | Random seed for randomizing run order |
| `--dry-run` | No | — | Print the design matrix to stdout without writing any files |

**What it does:**

1. Loads and validates the JSON config file.
2. Generates the design matrix based on the configured `operation` (e.g. full factorial, Plackett-Burman, etc.).
3. Randomizes run order (unless the design is Latin Hypercube, which is inherently random).
4. Applies blocking structure if `block_count > 1`.
5. Renders a runner script from Jinja2 templates (`doe/templates/runner_sh.j2` or `runner_py.j2`).
6. The generated script calls the `test_script` for each run, passing factor values using the configured `arg_style`.
7. Each run produces a JSON result file at `{out_directory}/run_{N}.json`.

**Output (normal mode):**
```
Generated 16 runs -> run_experiments.sh
Run with: bash run_experiments.sh
```

**Output (dry-run mode):** Prints the full design matrix table showing run_id, block_id, and all factor values.

---

### `doe analyze`

Perform statistical analysis on completed experiment results.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--results-dir DIR` | No | from config | Override `out_directory` from config |
| `--no-plots` | No | — | Skip generating plot files |
| `--no-report` | No | — | Skip generating the HTML report |
| `--csv DIR` | No | None | Export analysis results to CSV files in specified directory |
| `--partial` | No | — | Analyze only completed runs; skip missing result files |

**What it does:**

1. Loads config and regenerates the design matrix (to know expected runs).
2. Reads all `run_{N}.json` result files from the output directory.
3. For each response variable, computes:
   - **Main Effects:** Effect size (high minus low for 2-level; max minus min for multi-level), standard error, 95% confidence interval, and percentage contribution. Effects are sorted by absolute magnitude.
   - **Interaction Effects:** Two-factor interactions for 2-level factors. Computes concordant vs. discordant combination means. Reports interaction effect size and % contribution.
   - **Summary Statistics:** Per factor level — count (N), mean, standard deviation, min, max.
   - **ANOVA Table:** Type I (sequential) sum of squares, degrees of freedom, mean squares, F-values, and p-values. Includes main effects and interaction rows. Error estimation method depends on design:
     - **Pooled:** Standard residual-based error for replicated designs.
     - **Lenth:** Median-based pseudo-standard-error for unreplicated designs.
     - **Replicates:** Pure error from true replicates when available.
   - **Lack-of-Fit Test:** F-test comparing lack-of-fit SS to pure error SS (when replicates exist).
   - **Model Diagnostics:** Residuals, fitted values, hat matrix diagonal (leverage), PRESS statistic, predicted R-squared.
4. Generates plots (unless `--no-plots`).
5. Generates an HTML report in `processed_directory` (unless `--no-report`).
6. Exports CSV files if `--csv` is specified.

**Console output:**
```
=== Main Effects: Yield ===
Factor               Effect    Std Error   % Contribution
--------------------------------------------------------------
Temperature          12.5000      1.2500           62.5%
Pressure              8.3000      1.2500           27.6%
Catalyst              3.1000      1.2500            3.8%

=== ANOVA Table: Yield ===
Source                     DF           SS           MS          F    p-value
-----------------------------------------------------------------------------
Temperature                 1     625.0000     625.0000     40.000     0.0001
Pressure                    1     275.5600     275.5600     17.636     0.0030
Catalyst                    1      38.4400      38.4400      2.460     0.1553
Residual                    4      62.5000      15.6250
Total                       7    1001.5000     143.0714

=== Interaction Effects: Yield ===
Factor A             Factor B             Interaction   % Contribution
------------------------------------------------------------------------
Temperature          Pressure                  4.2000            7.1%
Temperature          Catalyst                  1.8000            1.3%

=== Summary Statistics: Yield ===

Temperature:
  Level              N      Mean       Std       Min       Max
  ------------------------------------------------------------
  Low                4   45.2500    3.1000   41.0000   48.0000
  High               4   57.7500    2.8000   54.0000   61.0000
```

**Plot files generated** (in `processed_directory`):

| File | Description |
|------|-------------|
| `pareto_{response}.png` | Bar chart of absolute effect magnitudes sorted descending, with cumulative percentage line and 80% threshold marker |
| `main_effects_{response}.png` | One subplot per factor showing mean response at each level, with confidence bands |
| `normal_effects_{response}.png` | Normal probability plot — effects vs. normal quantiles; points far from the line are statistically significant |
| `half_normal_effects_{response}.png` | Half-normal plot — absolute effects vs. half-normal quantiles; more conservative for small effect detection |
| `diagnostics_{response}.png` | 4-panel diagnostic plot: residuals vs. fitted, Q-Q plot, scale-location plot, residuals vs. run order |
| `rsm_{response}_*.png` | Response surface contour plots for continuous factor pairs |

---

### `doe info`

Display design information without generating scripts or running analysis.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |

**What it does:**

1. Loads the config in non-strict mode (does not require `test_script` to exist).
2. Generates the design matrix.
3. Prints design metadata: plan name, description, operation type, factors, base runs, blocks, total runs, responses (with optimize direction and units), and fixed factors.
4. Prints the full design matrix table (run_id, block_id, all factor values).
5. Computes and displays design evaluation metrics.

**Output:**
```
Plan      : Reactor Optimization
Desc      : Optimize yield and purity of chemical reactor
Operation : full_factorial
Factors   : Temperature, Pressure, Catalyst
Base runs : 8
Blocks    : 1
Total runs: 8
Responses : Yield [maximize] (%), Purity [maximize] (%)
Fixed     : Solvent=Water

run_id  block_id  Temperature  Pressure  Catalyst
--------------------------------------------------
1       1         Low          Low       A
2       1         Low          Low       B
...

Design Evaluation Metrics:
  D-efficiency: 100.0%
  A-efficiency: 1.0000
  G-efficiency: 100.0%
```

**Design Evaluation Metrics explained:**

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| D-efficiency | `det(X'X)^(1/p) / n * 100` | Higher = more information per run. 100% = orthogonal |
| A-efficiency | `p / trace((X'X)^-1)` | Average variance of parameter estimates |
| G-efficiency | `p / (n * max(h_ii)) * 100` | Worst-case prediction variance |

---

### `doe optimize`

Find optimal factor settings from experimental results using Response Surface Methodology (RSM).

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--results-dir DIR` | No | from config | Override output directory |
| `--response NAME` | No | all | Optimize for a specific response variable |
| `--partial` | No | — | Analyze only completed runs |
| `--multi` | No | — | Multi-objective optimization using desirability functions |
| `--steepest` | No | — | Show steepest ascent/descent pathway |

**Three modes of operation:**

#### Default Mode (single-response optimization)

For each response variable (or the one specified by `--response`):

1. Identifies the best observed run.
2. Fits a **linear RSM model** (`Y = intercept + B1*X1 + B2*X2 + ...`). Reports coefficients, R-squared, and Adjusted R-squared.
3. Fits a **quadratic RSM model** (adds interaction terms `Xi*Xj` and squared terms `Xi^2`). Reports:
   - All coefficients
   - Curvature analysis per factor (concave, convex, or negligible)
   - Notable interactions (synergistic or antagonistic)
4. Reports predicted optimum at observed data points.
5. Runs L-BFGS-B surface optimization (10 random restarts) to find the global surface optimum within factor bounds.
6. Rates model quality: Excellent (R-sq >= 0.9), Good (>= 0.7), Moderate (>= 0.5), or Weak (< 0.5).
7. Ranks factors by importance based on absolute coefficient magnitude.

**Output:**
```
=== Optimization: Yield (maximize) ===

Best observed: Run 5, Yield = 95.20
  Temperature = 180, Pressure = 50

--- Linear Model ---
  Intercept:    78.4500
  Temperature:  +12.3500
  Pressure:     +8.2000
  R-squared: 0.8521, Adjusted R-squared: 0.8102

--- Quadratic Model ---
  Intercept:         78.4500
  Temperature:       +12.3500
  Pressure:          +8.2000
  Temperature^2:     -3.1200
  Pressure^2:        -1.8500
  Temperature*Press: +2.4000
  R-squared: 0.9634, Adjusted R-squared: 0.9268

  Curvature:
    Temperature: concave (peak within range)
    Pressure: concave (peak within range)

  Notable interactions:
    Temperature * Pressure: synergistic (+2.4000)

Predicted optimum (observed): Run 5, Yield = 93.80
Surface optimum: Yield = 96.15
  Temperature = 175.3, Pressure = 52.1

Model quality: Excellent (R-sq=0.963)
Factor importance: Temperature > Pressure
```

#### Steepest Ascent/Descent Mode (`--steepest`)

Computes the gradient direction from the linear RSM model and generates a pathway of steps moving along that gradient (ascent for maximize, descent for minimize).

**Output:**
```
=== Steepest Ascent: Yield ===
Step    Temperature      Pressure     Predicted
-------------------------------------------------
0           150.0          40.0       78.4500
1           162.5          44.1       84.2300
2           175.0          48.2       90.0100
3           187.5          52.3       95.7900
```

#### Multi-Objective Mode (`--multi`)

Uses Derringer-Suich desirability functions to simultaneously optimize multiple responses:

1. Computes individual desirability scores (0 to 1) for each response based on configured `bounds` and `optimize` direction.
2. Calculates overall desirability as the weighted geometric mean (using response `weight` values).
3. Finds factor settings that maximize overall desirability.
4. Generates desirability plots.

**Output:** Individual desirability scores, overall desirability, optimal factor settings, and plot paths.

---

### `doe report`

Generate a self-contained interactive HTML report with embedded analysis and plots.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--results-dir DIR` | No | from config | Override output directory |
| `--output FILENAME` | No | `report.html` | Output HTML file path |
| `--partial` | No | — | Include only completed runs |

**What it does:**

1. Runs full analysis (same as `doe analyze`).
2. Generates all plots.
3. Embeds plots as base64 data URIs so the HTML file is fully self-contained (no external dependencies).
4. Renders an HTML report with:
   - Design summary (operation, factors, runs, blocks)
   - Factor details table (names, types, levels, units)
   - Main effects tables and plots
   - ANOVA tables
   - Interaction effects
   - Summary statistics
   - Diagnostic plots
   - Optimization recommendations
   - Complete design matrix table
   - Interactive collapsible sections
   - Responsive CSS styling

**Output:** A single `.html` file that can be opened in any browser.

---

### `doe record`

Interactively record response values for experiment runs via terminal prompts.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--run {N\|all}` | Yes | — | Run number to record, or `all` for all pending runs |
| `--seed INT` | No | 42 | Random seed for run order |

**What it does:**

1. Generates the design matrix with the given seed (to preserve run order).
2. If `--run all`: identifies runs without a `run_{N}.json` file and iterates through them.
3. If `--run N`: targets a specific run by ID.
4. For each run:
   - Displays run number and block.
   - Shows all factor settings with units.
   - Checks for existing results and asks to overwrite if found.
   - Prompts for each response variable (with units displayed).
   - Validates that input is numeric; re-prompts on invalid input.
   - Saves results to `{out_directory}/run_{N}.json`.
5. Supports Ctrl+C to interrupt; progress is saved for completed runs.

**Interactive session:**
```
--- Run 3 (block 1) ---
Factor settings:
  Temperature = 180
  Pressure = 50
  Enter Yield (%): 92.5
  Enter Purity (%): 88.1
Saved -> results/run_3.json
```

**Result file format** (`run_{N}.json`):
```json
{
  "Yield": 92.5,
  "Purity": 88.1
}
```

---

### `doe status`

Display current experiment progress and next steps.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--seed INT` | No | 42 | Random seed for run order |

**What it does:**

1. Loads config, generates design matrix.
2. Checks which `run_{N}.json` files exist in the output directory.
3. Classifies each run as completed or pending.
4. Displays progress information.

**Output (in progress):**
```
Experiment: Reactor Optimization
Design: full_factorial | 8 runs | 3 factors | 2 responses

Progress: 5/8 complete  [############........]  62%

Completed runs:
  Run 1: Temperature=Low, Pressure=Low, Catalyst=A
  Run 2: Temperature=Low, Pressure=Low, Catalyst=B
  ...

Pending runs:
  Run 6: Temperature=High, Pressure=High, Catalyst=A
  Run 7: Temperature=High, Pressure=High, Catalyst=B
  Run 8: Temperature=Low, Pressure=High, Catalyst=A

Next run to complete: Run 6
  Temperature = High
  Pressure = High (psi)
  Catalyst = A

Record results with: doe record --config <config> --run 6
```

**Output (all complete):**
```
Progress: 8/8 complete  [####################]  100%

All runs complete!

Completed runs:
  Run 1: Temperature=Low, Pressure=Low, Catalyst=A
  ...

Analyze results with: doe analyze --config <config>
```

---

### `doe power`

Compute statistical power for each factor in the design.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--sigma FLOAT` | No | estimated | Error standard deviation. If omitted, estimated from results using residuals of a linear RSM model fit to the first response. |
| `--delta FLOAT` | No | `2 * sigma` | Minimum detectable effect size |
| `--alpha FLOAT` | No | 0.05 | Significance level |
| `--results-dir DIR` | No | from config | Override output directory |
| `--partial` | No | — | Use only completed runs |

**What it does:**

1. If `--sigma` is not provided, attempts to estimate it from existing results by fitting a linear RSM model and computing the standard deviation of residuals.
2. Defaults `--delta` to `2 * sigma` if not provided.
3. For each factor:
   - Computes degrees of freedom (`n_levels - 1`).
   - Approximates replicates per level (`n_runs / n_levels`).
   - Computes non-centrality parameter: `lambda = r * delta^2 / sigma^2`.
   - Computes power using the non-central F-distribution: `P(F > F_crit | H1 true)`.
4. Warns if any factor has power below 0.80.

**Output:**
```
Estimated sigma from residuals: 2.3456

Power Analysis
  Runs: 16, Factors: 4
  Sigma (error std): 2.3456
  Delta (min detectable effect): 4.6912
  Alpha (significance level): 0.05

Factor                    Levels   df     Lambda      Power
------------------------------------------------------------
Temperature                    2    1     16.000      0.975
Pressure                       2    1     16.000      0.975
Catalyst                       3    2      8.000      0.891
Flow Rate                      2    1     16.000      0.975
```

---

### `doe augment`

Add additional runs to an existing design for further refinement.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--type {fold_over,star_points,center_points}` | Yes | — | Type of augmentation |
| `--output FILENAME` | No | `run_experiments_augmented.sh` | Output script path |
| `--format {sh,py}` | No | `sh` | Script format |
| `--seed INT` | No | None | Random seed for run order |

**Augmentation types:**

| Type | What it adds | When to use |
|------|-------------|-------------|
| `fold_over` | Mirror of existing runs by swapping high/low for all 2-level factors | Increase resolution of fractional factorial designs (e.g. Resolution III to IV) |
| `star_points` | Axial (star) points at `alpha = sqrt(n_factors)` distance from center, with other factors at center level | Extend a factorial design into a Central Composite Design for finding optima |
| `center_points` | 3 replicate center points (all factors at center level) | Estimate pure error and test for lack-of-fit / curvature |

**Output:**
```
Augmented design: 8 original + 6 new = 14 total runs
Generated -> run_experiments_augmented.sh
```

---

### `doe init`

Bootstrap a new experiment from a built-in use case template.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--template NAME` | No | — | Template name (e.g. `reactor_optimization`, `coffee_brewing`). If omitted, lists all templates. |
| `--list` | No | — | List all available templates |
| `--output-dir DIR` | No | `.` (current directory) | Directory to extract the template into |

**What it does:**

1. Scans `doe/use_cases/` for available templates (directories containing `config.json`).
2. If `--list` or no template specified: prints a table of all 310+ templates with design type, factor count, and name.
3. If `--template` specified:
   - Finds the template (supports fuzzy matching — partial name match).
   - Creates a directory named after the template.
   - Copies `config.json`, `sim.sh`, and `README.md` from the template.
   - Prints next steps.

**Template listing output:**
```
Available templates (310):

Template                            Design                 Factors   Name
----------------------------------------------------------------------------------------------------
reactor_optimization                full factorial               4   Chemical Reactor Optimization
coffee_brewing                      full factorial               3   Coffee Brewing Experiment
injection_molding                   fractional factorial         6   Injection Molding Process
ml_hyperparameter_tuning            latin hypercube              5   ML Hyperparameter Tuning
...

Usage: doe init --template <name>
Example: doe init --template reactor_optimization
```

**Template extraction output:**
```
Created 'reactor_optimization/' from template 'reactor_optimization'
  Name: Chemical Reactor Optimization
  Design: full factorial
  Factors: 4, Responses: 2

Next steps:
  cd reactor_optimization
  doe info --config config.json
  doe generate --config config.json --output results/run.sh
  bash results/run.sh
  doe analyze --config config.json
```

**Template categories include:** Manufacturing, Software/Systems, Food/Cooking, Biology/Agriculture, Materials Science, Chemistry, Physics/Engineering, Wellness, and many more domains.

Each template contains:
- `config.json` — Full DOE configuration with factors, responses, and settings
- `sim.sh` — A simulation script that generates synthetic results for learning/testing
- `README.md` — Documentation and instructions

---

### `doe export-worksheet`

Export the experiment design as a printable worksheet for manual data collection.

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--config FILE` | Yes | — | Path to JSON configuration file |
| `--format {csv,markdown}` | No | `csv` | Output format |
| `--output FILE` | No | stdout | Output file path. If omitted, prints to stdout. |
| `--seed INT` | No | 42 | Random seed for run order |

**What it does:**

1. Generates the design matrix.
2. Builds columns: Run, Block (if multiple blocks), factor names (with units), response names (with units), Notes.
3. Pre-fills any existing results from `run_{N}.json` files.
4. Formats as CSV or Markdown.

**CSV output:**
```csv
Run,Temperature (C),Pressure (psi),Yield (%),Purity (%),Notes
1,Low,Low,,,
2,Low,High,,,
3,High,Low,,,
4,High,High,,,
```

**Markdown output:**
```markdown
# Experiment Worksheet: Reactor Optimization
Design: Full Factorial | 4 runs | 2 factors | 2 responses
Fixed: Solvent = Water

| Run | Temperature (C) | Pressure (psi) | Yield (%) | Purity (%) | Notes |
|-----|-----------------|-----------------|-----------|------------|-------|
| 1   | Low             | Low             |           |            |       |
| 2   | Low             | High            |           |            |       |
| 3   | High            | Low             |           |            |       |
| 4   | High            | High            |           |            |       |

Instructions:
- Fill in response columns after each run
- Record any anomalies in the Notes column
- Enter results with: doe record --config config.json --run <N>
```

---

## Supported Design Types

### Full Factorial (`full_factorial`)

Creates all possible combinations of all factor levels.

- **Run count:** Product of all factor level counts (e.g. 3 factors with 2 levels each = 2x2x2 = 8 runs)
- **Requirements:** None (works with any factor types and level counts)
- **Best for:** Small number of factors (2-5) with few levels each
- **Strengths:** Estimates all main effects and interactions; no confounding
- **Weakness:** Run count grows exponentially with factors

### Fractional Factorial (`fractional_factorial`)

A carefully selected fraction of the full factorial design.

- **Run count:** 2^(n-p) where p is chosen to maintain at least Resolution III
- **Requirements:** Exactly 2 levels per factor
- **Best for:** Screening many factors (5-15) when full factorial is too expensive
- **Strengths:** Much fewer runs than full factorial while estimating main effects
- **Weakness:** Some effects are aliased (confounded) with each other
- **Output includes:** Alias structure showing which effects are confounded

### Plackett-Burman (`plackett_burman`)

Two-level screening design based on Hadamard matrices.

- **Run count:** Nearest multiple of 4 that is >= n_factors + 1
- **Requirements:** Exactly 2 levels per factor
- **Best for:** Screening large numbers of factors (up to ~47) with very few runs
- **Strengths:** Extremely efficient for identifying active factors
- **Weakness:** Cannot estimate interactions; main effects may be partially confounded with 2-factor interactions

### Central Composite Design (`central_composite`)

Response surface design combining factorial, star (axial), and center points.

- **Run count:** 2^n (factorial) + 2n (star) + center points
- **Requirements:** Exactly 2 numeric levels per factor (low and high)
- **Best for:** Fitting quadratic response surface models to find optima
- **Strengths:** Can estimate all linear, interaction, and quadratic effects
- **Configuration:** Alpha = "orthogonal", Face = "circumscribed"

### Box-Behnken (`box_behnken`)

Response surface design that avoids corner points.

- **Run count:** 2 * n * (n-1) + 3 center points
- **Requirements:** At least 3 factors, exactly 2 numeric levels each
- **Best for:** Response surface modeling when extreme combinations (corners) are unsafe or impractical
- **Strengths:** No runs at extreme corners; fewer runs than CCD for 3-4 factors
- **Weakness:** Cannot be used to build up from a factorial design

### Definitive Screening Design (`definitive_screening`)

Modern 3-level screening design that can also estimate quadratic effects.

- **Run count:** 2k+1 (odd k) or 2k+3 (even k), where k = number of factors
- **Requirements:** At least 3 factors, exactly 2 numeric levels (tool generates 3 levels internally: low, center, high)
- **Best for:** When you need both screening and some RSM capability in one design
- **Strengths:** Can estimate main effects, some interactions, and quadratic effects; very few runs
- **Weakness:** Limited ability to estimate all interactions

### Latin Hypercube (`latin_hypercube`)

Space-filling design for exploring continuous factor spaces.

- **Run count:** Configurable via `lhs_samples` setting (default: max(10, 2 * n_factors))
- **Requirements:** None (works best with continuous factors)
- **Best for:** Computer experiments, simulation studies, exploring unknown response surfaces
- **Strengths:** Even coverage of the factor space; configurable run count
- **Configuration:** Criterion = "maximin" (maximizes minimum distance between points)
- **Note:** Run order is inherently random; not re-randomized

### Taguchi (`taguchi`)

Orthogonal array design for robust parameter design.

- **Run count:** Determined by the smallest orthogonal array that accommodates all factor/level combinations
- **Requirements:** None (flexible factor/level combinations)
- **Best for:** Robust design where you want to minimize sensitivity to noise factors
- **Strengths:** Balanced, orthogonal designs; well-established methodology

### D-Optimal (`d_optimal`)

Algorithmically generated design that maximizes the D-criterion (determinant of X'X).

- **Run count:** Configurable via `lhs_samples` setting
- **Requirements:** None
- **Best for:** Irregular designs, constrained factor spaces, mixture of factor types
- **Strengths:** Maximizes information per run; flexible with constraints
- **Algorithm:** Row exchange algorithm, up to 100 iterations
- **Weakness:** Result depends on random starting point

### Mixture Simplex Lattice (`mixture_simplex_lattice`)

For mixture experiments where component proportions must sum to 1.

- **Run count:** Determined by number of components and lattice degree
- **Requirements:** Factor levels represent proportions that sum to 1
- **Best for:** Formulation experiments (blending, alloys, recipes)
- **Configuration:** Quadratic lattice (degree 2)
- **Strengths:** Systematic coverage of the mixture simplex

### Mixture Simplex Centroid (`mixture_simplex_centroid`)

For mixture experiments; includes vertices, edge midpoints, face centroids, and overall centroid.

- **Run count:** 2^q - 1 (where q = number of components)
- **Requirements:** Factor levels represent proportions that sum to 1
- **Best for:** Mixture experiments requiring good coverage of binary and higher-order blends
- **Strengths:** Minimal run count while covering all mixture subspaces

---

## Configuration File Format

The JSON configuration file controls all aspects of the experiment.

### Complete Schema

```json
{
  "metadata": {
    "name": "Experiment Name",
    "description": "What this experiment is investigating"
  },
  "factors": [
    {
      "name": "Temperature",
      "type": "continuous",
      "levels": [150, 200],
      "unit": "C",
      "description": "Reactor temperature"
    },
    {
      "name": "Catalyst",
      "type": "categorical",
      "levels": ["TypeA", "TypeB"],
      "unit": "",
      "description": "Catalyst type used"
    }
  ],
  "fixed_factors": {
    "Solvent": "Water",
    "Pressure_Unit": "psi"
  },
  "responses": [
    {
      "name": "Yield",
      "optimize": "maximize",
      "unit": "%",
      "description": "Product yield percentage",
      "weight": 1.0,
      "bounds": [60, 100]
    },
    {
      "name": "Cost",
      "optimize": "minimize",
      "unit": "USD",
      "description": "Per-batch production cost",
      "weight": 0.5,
      "bounds": [10, 50]
    }
  ],
  "settings": {
    "operation": "full_factorial",
    "block_count": 1,
    "out_directory": "results",
    "processed_directory": "results/plots",
    "test_script": "sim.sh",
    "lhs_samples": 20
  },
  "runner": {
    "arg_style": "double-dash",
    "result_file": "json"
  }
}
```

### Section Details

#### `metadata` (optional)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Experiment name (displayed in reports and status) |
| `description` | string | Description of the experiment |

#### `factors` (required, at least 1)

Each factor must have a name and at least 2 levels. Can be specified as objects or legacy arrays.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Factor name (must be unique) |
| `levels` | array | required | At least 2 values. For continuous factors, provide [low, high] as numbers. |
| `type` | string | `"categorical"` | One of: `categorical`, `continuous`, `ordinal` |
| `unit` | string | `""` | Unit of measurement (displayed in prompts, worksheets, reports) |
| `description` | string | `""` | Description of the factor |

**Legacy array format:** `["FactorName", "Level1", "Level2", ...]`

#### `fixed_factors` (optional)

Key-value pairs of factors that remain constant across all runs. These are passed to the test script but are not varied in the design.

**Legacy format:** `"static_settings": ["--key=value", ...]`

#### `responses` (optional)

If omitted, defaults to a single response named `"response"` with `optimize="maximize"`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Response name (must be unique) |
| `optimize` | string | `"maximize"` | Direction: `maximize` or `minimize` |
| `unit` | string | `""` | Unit of measurement |
| `description` | string | `""` | Description |
| `weight` | float | `1.0` | Weight for multi-objective optimization (higher = more important) |
| `bounds` | array | `null` | `[low, high]` bounds for desirability functions in multi-objective optimization |

**Legacy string format:** `"responses": ["ResponseName"]`

#### `settings` (required for most operations)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `operation` | string | `"full_factorial"` | Design type. One of: `full_factorial`, `plackett_burman`, `latin_hypercube`, `central_composite`, `fractional_factorial`, `box_behnken`, `definitive_screening`, `taguchi`, `d_optimal`, `mixture_simplex_lattice`, `mixture_simplex_centroid` |
| `block_count` | int | `1` | Number of blocks to divide runs into |
| `out_directory` | string | `""` | Directory for result JSON files |
| `processed_directory` | string | `""` | Directory for plots and HTML reports |
| `test_script` | string | `""` | Path to the executable that runs each experiment |
| `lhs_samples` | int | `0` | Number of samples for LHS and D-optimal designs. `0` = auto (`max(10, 2 * n_factors)`) |

#### `runner` (optional)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `arg_style` | string | `"double-dash"` | How factors are passed to test_script |
| `result_file` | string | `"json"` | Result file format |

**Argument styles:**

| Style | Example command |
|-------|----------------|
| `double-dash` | `./sim.sh --Temperature 180 --Pressure 50 --Catalyst TypeA` |
| `env` | `Temperature=180 Pressure=50 Catalyst=TypeA ./sim.sh` |
| `positional` | `./sim.sh 180 50 TypeA` |

---

## Validation Rules

The config loader enforces these validation rules:

| Rule | Applies to |
|------|-----------|
| Operation must be one of the 11 supported types | All |
| At least one factor required | All |
| Factor names must be unique | All |
| `block_count` must be >= 1 | All |
| Exactly 2 levels per factor | `plackett_burman`, `fractional_factorial` |
| Exactly 2 numeric levels per factor | `central_composite`, `box_behnken`, `definitive_screening` |
| At least 3 factors | `box_behnken`, `definitive_screening` |
| Response names must be unique | All |
| `optimize` must be `maximize` or `minimize` | All |
| `arg_style` must be `double-dash`, `env`, or `positional` | All |
| Warning if `test_script` file does not exist | All (strict mode only) |

---

## Result File Format

Each experiment run produces a JSON file at `{out_directory}/run_{N}.json`:

```json
{
  "Yield": 92.5,
  "Purity": 88.1
}
```

- Keys are response variable names (must match `responses[].name` in config)
- Values are numeric (float)
- Created automatically by the test script, or manually via `doe record`

---

## Data Model Classes

Defined in `doe/models.py`:

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `DOEConfig` | Full experiment configuration | `factors`, `fixed_factors`, `responses`, `block_count`, `operation`, `test_script`, `out_directory`, `processed_directory`, `lhs_samples`, `metadata`, `runner` |
| `Factor` | Input variable | `name`, `levels`, `type`, `description`, `unit` |
| `ResponseVar` | Output metric | `name`, `optimize`, `unit`, `description`, `weight`, `bounds` |
| `RunnerConfig` | Script generation settings | `arg_style`, `result_file` |
| `ExperimentRun` | Single experiment run | `run_id`, `block_id`, `factor_values` |
| `DesignMatrix` | Generated design | `runs`, `factor_names`, `operation`, `metadata` |
| `EffectResult` | Per-factor effect | `factor_name`, `main_effect`, `std_error`, `pct_contribution`, `ci_low`, `ci_high` |
| `InteractionEffect` | Two-factor interaction | `factor_a`, `factor_b`, `interaction_effect`, `pct_contribution` |
| `AnovaRow` | One ANOVA table row | `source`, `df`, `ss`, `ms`, `f_value`, `p_value` |
| `AnovaTable` | Full ANOVA table | `rows`, `error_row`, `total_row`, `lack_of_fit_row`, `pure_error_row`, `error_method` |
| `ResponseAnalysis` | Per-response analysis | `response_name`, `effects`, `summary_stats`, `interactions`, `anova_table` |
| `AnalysisReport` | Full analysis results | `results_by_response`, `pareto_chart_paths`, `effects_plot_paths`, `normal_plot_paths`, `half_normal_plot_paths`, `diagnostics_plot_paths` |

---

## Key Source Files

| File | Purpose |
|------|---------|
| `doe/cli.py` | Command-line interface — argument parsing, dispatch, and output formatting |
| `doe/config.py` | Configuration loading, parsing, and validation |
| `doe/models.py` | All data classes (Factor, DOEConfig, DesignMatrix, etc.) |
| `doe/design.py` | Design matrix generation for all 11 design types, augmentation, and design evaluation |
| `doe/analysis.py` | Statistical analysis — effects, interactions, ANOVA, summary stats, diagnostics |
| `doe/rsm.py` | Response Surface Methodology — model fitting, optimization, steepest ascent, encoding |
| `doe/optimize.py` | Optimization recommendations — single-response and multi-objective (desirability) |
| `doe/report.py` | HTML report generation with Jinja2 templates and embedded plots |
| `doe/codegen.py` | Runner script generation from Jinja2 templates |
| `doe/templates/runner_sh.j2` | Bash runner script template |
| `doe/templates/runner_py.j2` | Python runner script template |
| `doe/use_cases/` | 310+ pre-built experiment templates |

---

## Error Handling

The CLI catches and displays friendly messages for:

| Exception | Displayed as |
|-----------|-------------|
| `FileNotFoundError` | `Error: <message>` — config or result files not found |
| `json.JSONDecodeError` | `Error: invalid JSON in config file: <details>` |
| `ValueError` | `Error: <message>` — invalid config (unsupported operation, wrong factor levels, etc.) |
| `PermissionError` | `Error: <message>` — file access denied |
| `OSError` (file not found) | `Error: <message>` |

When results are missing, a helpful message is shown:
```
No results found in 'results/'.

This experiment has 8 runs that need to be completed first.
To run the experiment:
  1. doe generate --config config.json --output results/run.sh
  2. bash results/run.sh

Or record results manually:
  doe record --config config.json --run 1

To analyze partial results (completed runs only):
  doe analyze --config config.json --partial
```
