# Use Case 2: Web App A/B Testing

## Scenario

You are optimizing a web application's conversion rate by testing combinations of UI design choices. You want to test every combination of font size (3 levels), color scheme, and layout to find the highest-converting variant.

**This use case demonstrates:**
- Full factorial design (all combinations, including 3-level factors)
- Categorical factor types (non-numeric discrete levels)
- `env` argument style (factors passed as environment variables)
- Python-format runner script (`--format py`)
- `--dry-run` to preview the design matrix before generating
- Single response optimization

## Factors

| Factor | Levels | Type | Description |
|--------|--------|------|-------------|
| font_size | small, medium, large | categorical | Body text font size |
| color_scheme | dark, light | categorical | UI color theme |
| layout | grid, list | categorical | Product listing layout |

**Fixed:** page = homepage, traffic_pct = 10%

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| conversion_rate | maximize | % |

## Why Full Factorial?

- We have only 3 factors with 2-3 levels each → 3 × 2 × 2 = 12 runs (very manageable)
- All factors are categorical — no interpolation needed
- We want to detect all main effects AND interactions (e.g., does dark mode perform differently with grid vs. list layout?)
- Full factorial requires zero external dependencies (stdlib only)

## Running the Demo

### Prerequisites

```bash
cd /workspaces/design_of_experiments
pip install -r requirements.txt
```

### Step 1: Preview the design with `--dry-run`

```bash
python doe.py generate --config use_cases/02_webapp_ab_testing/config.json --dry-run
```

This prints the full design matrix (12 runs) without writing any files. Use this to verify the factor combinations look correct before committing to a run.

Output:
```
Plan      : Web App A/B Testing
Operation : full_factorial
Factors   : font_size, color_scheme, layout
Base runs : 12
Blocks    : 1
Total runs: 12
Responses : conversion_rate [maximize] (%)
Fixed     : page=homepage, traffic_pct=10
```

### Step 2: View design info

```bash
python doe.py info --config use_cases/02_webapp_ab_testing/config.json
```

Same summary plus the full design matrix table showing all 12 factor combinations.

### Step 3: Generate a Python-format runner script

```bash
python doe.py generate --config use_cases/02_webapp_ab_testing/config.json \
    --output use_cases/02_webapp_ab_testing/results/run.py --format py --seed 123
```

This generates a **Python** runner script (instead of the default bash). The `--seed 123` ensures reproducible run order. Open `use_cases/02_webapp_ab_testing/results/run.py` to see how the `env` argument style exports factors as uppercase environment variables (`FONT_SIZE`, `COLOR_SCHEME`, `LAYOUT`) before calling the test script.

### Step 4: Execute the experiments

```bash
python use_cases/02_webapp_ab_testing/results/run.py
```

The simulator reads factors from environment variables and writes a JSON result for each of the 12 runs.

### Step 5: Analyze results

```bash
python doe.py analyze --config use_cases/02_webapp_ab_testing/config.json
```

Key findings:
- **font_size** has the largest effect (3 levels → effect = max(means) - min(means))
- **layout** has a strong effect (grid outperforms list)
- **color_scheme** has a mild effect
- Interaction effects reveal whether specific combinations outperform expectations

### Step 6: Get optimization recommendations

```bash
python doe.py optimize --config use_cases/02_webapp_ab_testing/config.json
```

Reports the best observed run and RSM model predictions for conversion rate.

### Step 7: Generate HTML report

```bash
python doe.py report --config use_cases/02_webapp_ab_testing/config.json \
    --output use_cases/02_webapp_ab_testing/results/report.html
```

Open `use_cases/02_webapp_ab_testing/results/report.html` in a browser for the full interactive report.

## Features Exercised

| Feature | Value |
|---------|-------|
| Design type | `full_factorial` |
| Factor type | `categorical` (all 3 factors) |
| Factor levels | 3 levels (font_size), 2 levels (others) |
| Arg style | `env` |
| Script format | `py` (Python) |
| `--dry-run` | Yes |
| `--seed` | 123 |
| Fixed factors | page, traffic_pct |
| Single response | conversion_rate (maximize) |

## Files

- Config: `use_cases/02_webapp_ab_testing/config.json`
- Simulator: `use_cases/02_webapp_ab_testing/sim.sh`
- Results: `use_cases/02_webapp_ab_testing/results/`
- Report: `use_cases/02_webapp_ab_testing/results/report.html`
