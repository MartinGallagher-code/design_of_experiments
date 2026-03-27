# Use Case 129: Home Insulation Optimization

## Scenario

You are retrofitting a 2,000 sq ft home in climate zone 5A and need to decide where to invest in insulation upgrades -- attic R-value, wall R-value, window U-factor, and air sealing -- to minimize annual heating cost while maximizing comfort. Each upgrade has a different cost-per-R-value, and interactions matter: expensive triple-pane windows yield little benefit if the attic is poorly sealed. A full factorial design tests every combination of these four factors, revealing which upgrade pairs deliver the biggest bang for the buck.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (annual_heat_cost, comfort_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| attic_r | 19 | 49 | R-value | Attic insulation R-value |
| wall_r | 11 | 21 | R-value | Wall insulation R-value |
| window_u | 0.25 | 0.65 | U-factor | Window U-factor (lower = better) |
| air_seal_ach | 2 | 8 | ACH50 | Air changes per hour at 50 Pa |

**Fixed:** climate_zone = 5A, house_sqft = 2000

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| annual_heat_cost | minimize | USD |
| comfort_score | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template home_insulation
cd home_insulation
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
