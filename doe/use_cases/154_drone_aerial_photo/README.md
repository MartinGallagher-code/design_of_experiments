# Use Case 154: Drone Aerial Photography

## Scenario

You are planning a drone aerial survey with a 1-inch sensor camera in light wind and need to optimize flight altitude, gimbal angle, flight speed, and image overlap percentage to minimize ground sample distance (GSD) while keeping motion blur acceptable. Flying low and slow maximizes resolution but drastically increases flight time and battery consumption, while high overlap improves stitching at the cost of storage and processing. A full factorial design tests every combination of these four parameters, producing a complete performance map for mission planning.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (gsd_cm, blur_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| altitude_m | 30 | 120 | m | Flight altitude |
| gimbal_angle | -90 | -45 | deg | Camera gimbal pitch angle |
| flight_speed | 2 | 12 | m/s | Horizontal flight speed |
| overlap_pct | 60 | 85 | % | Image overlap for stitching |

**Fixed:** camera = 1inch_sensor, wind = light

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| gsd_cm | minimize | cm/px |
| blur_score | minimize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template drone_aerial_photo
cd drone_aerial_photo
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
