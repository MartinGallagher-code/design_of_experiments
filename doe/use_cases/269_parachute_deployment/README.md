# Use Case 269: Parachute Deployment Dynamics

## Scenario

You are tuning the deployment sequence of a ram-air parachute canopy for a 90kg load, balancing reliable opening against peak opening shock force measured in g. Deployment altitude, reefing line restriction, and slider opening percentage interact nonlinearly -- aggressive slider settings reduce shock but risk delayed inflation at low altitudes. A central composite design maps the curved relationship between these parameters, including axial points that explore conditions slightly beyond the nominal range to find a robust operating envelope.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (reliability_pct, opening_shock_g)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| deploy_alt_m | 300 | 1500 | m | Deployment altitude AGL |
| reefing_pct | 0 | 50 | % | Reefing line restriction percentage |
| slider_pct | 60 | 100 | % | Slider opening percentage |

**Fixed:** canopy = ram_air, load = 90kg

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| reliability_pct | maximize | % |
| opening_shock_g | minimize | g |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template parachute_deployment
cd parachute_deployment
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
