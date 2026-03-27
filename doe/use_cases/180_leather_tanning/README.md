# Use Case 180: Leather Tanning Process

## Scenario

You are vegetable-tanning cowhide and need to optimize tannin concentration, soak duration, bath pH, and fat liquor percentage for maximum softness and color uniformity. Tannin-pH interactions strongly affect penetration depth, while fat liquoring at the wrong pH can cause greasy spots or uneven coloring. With only 4 factors at 2 levels, a full factorial design is affordable and ensures you capture every interaction -- critical when the chemistry between tanning agent and fat liquor is not well characterized for your specific hide lot.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (softness_score, color_uniformity)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| tannin_pct | 3 | 10 | % | Tanning agent concentration |
| soak_hrs | 4 | 24 | hrs | Tanning soak duration |
| ph | 3 | 5 | pH | Bath pH level |
| fat_liquor_pct | 3 | 10 | % | Fat liquor percentage |

**Fixed:** hide_type = cowhide, method = vegetable

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| softness_score | maximize | pts |
| color_uniformity | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template leather_tanning
cd leather_tanning
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
