# Use Case 220: Shampoo Foaming & Cleansing

## Scenario

You are developing a daily-use shampoo and want to maximize foam volume and cleansing while minimizing post-wash scalp dryness by adjusting surfactant concentration, product pH, and viscosity. Foam quality responds nonlinearly to surfactant level -- it plateaus above a critical micelle concentration -- and low pH with high surfactant aggressively strips natural oils, causing dryness. A central composite design maps these curved relationships and its axial points help you explore formulations slightly outside the initial pH and viscosity ranges to find the optimal balance.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (foam_score, scalp_dryness)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| surfactant_pct | 8 | 18 | % | Primary surfactant concentration |
| ph_level | 4.5 | 6.5 | pH | Product pH |
| viscosity_cp | 2000 | 8000 | cP | Product viscosity |

**Fixed:** fragrance = floral, preservative = phenoxyethanol

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| foam_score | maximize | pts |
| scalp_dryness | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template shampoo_foam
cd shampoo_foam
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
