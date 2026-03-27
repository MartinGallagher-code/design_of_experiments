# Use Case 128: Rainwater Harvesting System

## Scenario

You are designing a residential rainwater harvesting system in a region with 900 mm annual rainfall and 50 L/day household usage, and need to size the storage tank, roof gutter catchment area, and first-flush diverter volume to maximize captured water while minimizing wasteful overflow. Oversizing the tank wastes money; undersizing it loses rainwater. A Box-Behnken design efficiently models the nonlinear interactions between these three components -- particularly how first-flush volume trades off against usable capture at different tank sizes.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (capture_pct, overflow_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| tank_liters | 500 | 5000 | L | Storage tank volume |
| gutter_area_m2 | 50 | 200 | m2 | Roof catchment area connected to gutters |
| first_flush_L | 10 | 80 | L | First-flush diverter volume |

**Fixed:** annual_rainfall_mm = 900, usage_L_day = 50

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| capture_pct | maximize | % |
| overflow_pct | minimize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template rainwater_harvesting
cd rainwater_harvesting
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
