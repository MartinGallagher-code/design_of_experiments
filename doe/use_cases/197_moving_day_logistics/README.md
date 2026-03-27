# Use Case 197: Moving Day Logistics

## Scenario

You are planning a 20 km apartment move from a 3rd-floor walkup and need to minimize total move duration and item breakage by adjusting box volume, crew size, and bubble-wrap padding layers. Larger boxes speed up truck loading but are harder to carry down stairs and risk more breakage, while extra padding protects fragile items but increases packing time. A Box-Behnken design captures these nonlinear trade-offs without testing the impractical extreme corners like a 2-person crew using maximum-size boxes with minimal padding.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (total_hours, breakage_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| box_volume_L | 30 | 80 | L | Average moving box volume |
| crew_size | 2 | 6 | people | Moving crew size |
| padding_layers | 1 | 4 | layers | Bubble wrap padding layers on fragile items |

**Fixed:** distance_km = 20, apartment_floor = 3

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| total_hours | minimize | hrs |
| breakage_pct | minimize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template moving_day_logistics
cd moving_day_logistics
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
