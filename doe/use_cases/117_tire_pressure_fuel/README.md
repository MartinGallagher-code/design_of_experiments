# Use Case 117: Tire Pressure & Fuel Economy

## Scenario

You are tuning tire pressures on an all-season sedan to maximize fuel economy (MPG) while minimizing tread wear rate. Front pressure, rear pressure, and cargo load interact -- higher pressure improves rolling resistance but accelerates center-tread wear, especially under heavy loads. A Box-Behnken design captures these nonlinear trade-offs with three factors while avoiding the extreme corners where both axles are simultaneously at minimum or maximum pressure, conditions that could compromise handling safety during testing.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (mpg, wear_rate)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| front_psi | 28 | 38 | psi | Front tire pressure |
| rear_psi | 28 | 38 | psi | Rear tire pressure |
| load_kg | 100 | 400 | kg | Cargo load weight |

**Fixed:** vehicle = sedan, tire_model = all_season

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| mpg | maximize | mpg |
| wear_rate | minimize | mm/10k_mi |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template tire_pressure_fuel
cd tire_pressure_fuel
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
