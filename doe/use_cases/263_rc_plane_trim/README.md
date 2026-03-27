# Use Case 263: RC Plane Trim Settings

## Scenario

You are dialing in the trim settings on a 1200mm trainer-class RC airplane and want to maximize battery flight time and pilot handling score simultaneously. Elevator trim, aileron differential, throttle curve, and CG position as a percentage of mean aerodynamic chord all interact -- moving the CG aft improves efficiency but degrades handling, while aggressive throttle curves drain the battery faster. A full factorial design is feasible with four two-level factors and captures every interaction, which is critical since trim parameters are highly coupled in flight dynamics.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (flight_time_min, handling_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| elevator_pct | -5 | 5 | % | Elevator trim percentage |
| aileron_diff_pct | 0 | 40 | % | Aileron differential percentage |
| throttle_curve | 50 | 100 | % | Mid-stick throttle curve point |
| cg_pct_mac | 25 | 35 | %MAC | CG position as % of mean aerodynamic chord |

**Fixed:** model = trainer, wingspan = 1200mm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| flight_time_min | maximize | min |
| handling_score | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template rc_plane_trim
cd rc_plane_trim
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
