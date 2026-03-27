# Use Case 6: Distillation Column Optimization

## Scenario

You are optimizing a distillation column for maximum separation efficiency at minimum energy cost. You suspect the response surface is curved (quadratic), so you need a design with star points and center points to fit a second-order model. Central Composite Design (CCD) is the classic choice.

**This use case demonstrates:**
- Central Composite Design (CCD with circumscribed star points)
- All continuous factors with numeric levels
- Star points that extend beyond the [low, high] factor range
- `--response` flag to optimize a single response
- Full pipeline: info → generate → run → analyze → optimize → report
- RSM quadratic model potential

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| reflux_ratio | 1.5 | 4.5 | continuous | | Reflux ratio (L/D) |
| feed_rate | 50 | 150 | continuous | L/h | Feed stream flow rate |
| column_pressure | 1.0 | 3.0 | continuous | atm | Column operating pressure |

**Fixed:** feed_temp = 80°C, n_trays = 20

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| separation_efficiency | maximize | % |
| energy_cost | minimize | USD/h |

## Why Central Composite Design?

- 3 continuous factors → CCD gives factorial (2³=8) + star (2×3=6) + center (8) = 22 runs
- Star points at ±α extend beyond the factorial cube, probing curvature
- Center replicates estimate pure error for lack-of-fit testing
- CCD supports fitting full quadratic models (linear + interaction + squared terms)
- Orthogonal alpha ensures balanced estimation of all model terms
- Unlike Box-Behnken, CCD *does* test corner points (factorial portion)

## Running the Demo

### Prerequisites

```bash
pip install doehelper
```

### Step 1: Preview the design

```bash
doe info --config config.json
```

Output:
```
Plan      : Distillation Column Optimization
Operation : central_composite
Factors   : reflux_ratio, feed_rate, column_pressure
...
```

Notice the star points in the design matrix — some runs have factor values *outside* the [low, high] range (e.g., reflux_ratio below 1.5 or above 4.5). This is the CCD's circumscribed design: the factorial cube is inscribed within the star points.

### Step 2: Generate the runner script

```bash
doe generate --config config.json \
    --output results/run.sh --seed 55
```

### Step 3: Execute the experiments

```bash
bash results/run.sh
```

The simulator computes separation efficiency using a quadratic model with interactions, and energy cost using a linear model with interactions — producing realistic trade-offs.

### Step 4: Analyze results

```bash
doe analyze --config config.json
```

Look for:
- **Main effects**: Which factors drive efficiency vs. cost?
- **Interactions**: Does reflux_ratio × column_pressure matter?
- **Summary stats**: Center point replicates should have similar means, confirming reproducibility

### Step 5: Optimize for a single response

```bash
doe optimize --config config.json \
    --response separation_efficiency
```

The `--response` flag focuses optimization on just separation_efficiency, ignoring energy_cost. Compare with optimizing all responses:

```bash
doe optimize --config config.json
```

This reveals the trade-off: settings that maximize separation efficiency often increase energy cost.

### Step 6: Generate the HTML report

```bash
doe report --config config.json \
    --output results/report.html
```

The report includes all responses, Pareto charts, main effects plots, and the full design matrix showing the CCD structure (factorial + star + center points).

### Step 7: Export to CSV for custom modeling

```bash
doe analyze --config config.json \
    --csv results/csv
```

Use the exported CSV data to fit a full quadratic RSM model in R or Python (statsmodels/scikit-learn).

## Interpreting the Results

### CCD Structure

The design matrix reveals three types of runs:
1. **Factorial points** (8 runs): All combinations of [low, high] — the corners of the cube
2. **Star points** (6 runs): One factor at ±α while others at center — probes curvature along each axis
3. **Center points** (8 runs): All factors at midpoint — estimates pure error

### Quadratic Effects

The underlying model has squared terms (e.g., reflux_ratio²), which create a curved response surface. The CCD's star and center points let you detect this curvature, which a 2-level design would miss entirely.

### Trade-offs

- **Higher reflux ratio** → better separation but much higher energy cost
- **Higher feed rate** → moderate effect on both responses
- **Higher pressure** → improves separation with moderate energy increase

### Next Steps

1. Fit a full quadratic RSM model using the CCD data
2. Construct a desirability function weighting efficiency vs. cost
3. Find the Pareto-optimal frontier
4. Run confirmation experiments at the predicted optimum

## Features Exercised

| Feature | Value |
|---------|-------|
| Design type | `central_composite` (circumscribed, orthogonal alpha) |
| Factor types | `continuous` (all 3) |
| Star points | Yes (extends beyond [low, high] range) |
| Center points | Yes (8 center replicates) |
| `--response` | Single-response optimization |
| Arg style | `double-dash` |
| `--seed` | 55 |
| `--csv` | Yes |
| Fixed factors | feed_temp, n_trays |
| Multi-response | separation_efficiency (maximize), energy_cost (minimize) |
| Full pipeline | info → generate → run → analyze → optimize → report → csv |

## Files

- Config: `config.json`
- Simulator: `sim.sh`
- Results: `results/`
- CSV exports: `results/csv/`
- Report: `results/report.html`
