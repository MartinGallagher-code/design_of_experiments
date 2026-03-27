# Use Case 138: DIY Concrete Mix Design

## Scenario

You are designing a concrete mix for a DIY patio project using sharp sand and no admixtures, and need to maximize 28-day compressive strength while minimizing material cost per cubic meter. Three mix parameters -- cement percentage, water-to-cement ratio, and aggregate size -- have strongly nonlinear effects: too much water weakens the mix catastrophically, but too little makes it unworkable. A central composite design maps this curved response surface precisely, letting you find the strongest affordable mix without trial-and-error waste.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (strength_mpa, cost_per_m3)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cement_pct | 10 | 20 | % | Cement percentage of total mix by weight |
| water_cement_ratio | 0.35 | 0.65 | ratio | Water-to-cement ratio |
| aggregate_mm | 10 | 25 | mm | Maximum aggregate size |

**Fixed:** sand_type = sharp, admixture = none

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| strength_mpa | maximize | MPa |
| cost_per_m3 | minimize | USD/m3 |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template concrete_mix
cd concrete_mix
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
