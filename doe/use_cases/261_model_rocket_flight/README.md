# Use Case 261: Model Rocket Flight Optimization

## Scenario

You are optimizing a 25mm-diameter model rocket with parachute recovery to reach maximum apogee while keeping landing drift small enough to recover in the field. Motor impulse, fin planform area, and nose cone fineness ratio all interact -- a high-impulse motor with small fins may spin unstable, while a blunt nose cone increases drag disproportionately at higher speeds. A Box-Behnken design is well-suited here because it avoids testing extreme corner combinations like maximum impulse with minimum fins, which could produce unsafe flights.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (apogee_m, drift_m)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| impulse_ns | 5 | 40 | Ns | Motor total impulse |
| fin_area_cm2 | 20 | 80 | cm2 | Total fin planform area |
| nose_fineness | 3 | 7 | ratio | Nose cone fineness ratio (L/D) |

**Fixed:** body_diam = 25mm, recovery = parachute

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| apogee_m | maximize | m |
| drift_m | minimize | m |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template model_rocket_flight
cd model_rocket_flight
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
