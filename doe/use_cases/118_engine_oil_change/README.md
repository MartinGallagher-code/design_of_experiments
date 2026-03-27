# Use Case 118: Engine Oil Change Interval

## Scenario

You are maintaining a 4-cylinder gasoline engine with mixed city/highway driving and want to find the most cost-effective oil change strategy that preserves engine health. Three parameters -- oil viscosity grade (0W to 10W), change interval (3,000 to 10,000 miles), and oil filter quality tier -- interact nonlinearly because cheap filters degrade faster at extended intervals, accelerating engine wear. A central composite design maps this curved response surface to find the interval and filter combination that minimizes annual cost without sacrificing engine longevity.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (engine_health, annual_cost)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| viscosity_w | 0 | 10 | W | Oil winter viscosity grade (0W, 5W, 10W) |
| change_interval | 3000 | 10000 | miles | Oil change interval in miles |
| filter_quality | 1 | 5 | tier | Oil filter quality tier (1=economy, 5=premium) |

**Fixed:** engine_type = gasoline_4cyl, driving_style = mixed

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| engine_health | maximize | pts |
| annual_cost | minimize | USD |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template engine_oil_change
cd engine_oil_change
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
