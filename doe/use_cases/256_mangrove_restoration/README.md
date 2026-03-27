# Use Case 256: Mangrove Restoration Planting

## Scenario

You are restoring Rhizophora mangroves in an estuary and need to maximize one-year seedling survival and height growth by varying planting density, tidal zone placement, and sediment nutrient amendment. Planting too densely in low tidal zones with heavy amendment can waterlog roots, while sparse high-zone plantings may desiccate -- the optimum lies somewhere in between. A central composite design lets you fit a quadratic response surface to capture these curved survival relationships and predict performance beyond the original factor ranges.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (survival_1yr_pct, height_gain_cm)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| density_per_m2 | 1 | 6 | plants/m2 | Planting density |
| tidal_zone | 1 | 3 | zone | Tidal zone (1=low,3=high) |
| amendment_kg_m2 | 0 | 3 | kg/m2 | Sediment nutrient amendment |

**Fixed:** species = rhizophora, site = estuary

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| survival_1yr_pct | maximize | % |
| height_gain_cm | maximize | cm |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template mangrove_restoration
cd mangrove_restoration
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
