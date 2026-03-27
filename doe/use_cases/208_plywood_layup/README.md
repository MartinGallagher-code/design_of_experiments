# Use Case 208: Plywood Layup Optimization

## Scenario

You are manufacturing 5-ply birch plywood and need to maximize bending strength (MOR) while minimizing delamination risk by adjusting veneer thickness, glue spread weight, hot press temperature, and press cycle time. Insufficient glue at high press temperatures causes dry bond lines and delamination, while excessive glue with thick veneers wastes adhesive and extends cycle time. A full factorial across 4 factors captures all interactions -- particularly the critical glue-temperature and veneer-time interactions -- in 16 press cycles, which is feasible for a production trial.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (bend_strength_mpa, delam_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| veneer_mm | 1.0 | 3.0 | mm | Individual veneer sheet thickness |
| glue_g_m2 | 120 | 220 | g/m2 | Glue spread weight |
| press_temp_c | 100 | 150 | C | Hot press temperature |
| press_min | 3 | 10 | min | Press cycle time |

**Fixed:** species = birch, layers = 5

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| bend_strength_mpa | maximize | MPa |
| delam_score | minimize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template plywood_layup
cd plywood_layup
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
