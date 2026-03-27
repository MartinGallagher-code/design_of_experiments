# Use Case 253: Tidal Turbine Placement

## Scenario

You are siting tidal stream turbines in a channel with a 4-meter tidal range and need to maximize annual energy production while minimizing disruption to marine ecosystems. Turbine hub depth, rotor diameter, and cut-in current speed all interact nonlinearly with power capture and fish strike risk. A Box-Behnken design avoids the extreme corner combinations -- such as a large rotor at shallow depth -- that would be physically dangerous or infeasible to test in open water.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (annual_mwh, impact_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| depth_m | 5 | 25 | m | Turbine hub depth |
| rotor_m | 5 | 20 | m | Rotor diameter |
| cutin_ms | 0.5 | 2.0 | m/s | Cut-in current speed |

**Fixed:** site = tidal_channel, tidal_range = 4m

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| annual_mwh | maximize | MWh |
| impact_score | minimize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template tidal_energy
cd tidal_energy
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
