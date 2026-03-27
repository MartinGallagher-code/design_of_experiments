# Use Case 104: Drip Irrigation Scheduling

## Scenario

You are optimizing a drip irrigation system for summer strawberries, balancing water conservation against crop yield. Three continuous parameters -- drip rate, watering interval, and emitter spacing -- interact nonlinearly because soil moisture dynamics are highly sensitive to application timing and spatial distribution. A central composite design is ideal here, providing enough points to fit a full second-order response surface model and locate the precise sweet spot between water waste and plant stress.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (water_use_L, crop_yield)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| drip_rate | 1 | 4 | L/hr | Emitter drip rate |
| interval_hrs | 6 | 48 | hrs | Irrigation interval |
| emitter_spacing | 20 | 50 | cm | Distance between drip emitters |

**Fixed:** crop = strawberry, season = summer

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| water_use_L | minimize | L/m2/wk |
| crop_yield | maximize | kg/m2 |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template irrigation_scheduling
cd irrigation_scheduling
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
