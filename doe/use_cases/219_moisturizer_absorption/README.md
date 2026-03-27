# Use Case 219: Moisturizer Absorption Rate

## Scenario

You are formulating an oil-in-water facial moisturizer at pH 5.5 and want to maximize 4-hour skin hydration depth while minimizing greasy residue by adjusting hyaluronic acid concentration, emulsifier percentage, and application amount per square centimeter. Hydration and greasiness are inherently coupled -- higher HA concentrations boost moisture retention but require more emulsifier to remain stable, and thicker application layers increase both hydration and residual film. A Box-Behnken design captures these nonlinear formulation trade-offs without testing extreme corners like maximum HA with minimum emulsifier, which would produce an unstable emulsion.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (hydration_depth, greasiness)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| ha_pct | 0.5 | 3.0 | % | Hyaluronic acid concentration |
| emulsifier_pct | 2 | 8 | % | Emulsifier percentage |
| amount_mg_cm2 | 1 | 4 | mg/cm2 | Application amount per area |

**Fixed:** base = oil_in_water, ph = 5.5

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| hydration_depth | maximize | pts |
| greasiness | minimize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template moisturizer_absorption
cd moisturizer_absorption
```

### Step 2: Preview the design
```bash
doe info --config config.json
```

### Step 3: Generate and run
```bash
doe generate --config config.json --output results/run.sh --seed 42
bash results/run.sh
```

### Step 4: Analyze
```bash
doe analyze --config config.json
```

### Step 5: Optimize and report
```bash
doe optimize --config config.json
doe report --config config.json --output results/report.html
```
