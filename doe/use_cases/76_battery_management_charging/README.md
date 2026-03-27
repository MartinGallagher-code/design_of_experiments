# Use Case 76: Battery Management Charging

## Scenario

You are programming the CC-CV charging profile for a 4S LiFePO4 battery pack in a BMS, balancing fast charge time against long-term cycle life degradation. The core trade-off is charge speed versus longevity: higher constant-current rates fill the cell faster but accelerate SEI layer growth and lithium plating, while the constant-voltage threshold and trickle cutoff voltage determine how fully the cell charges and how gently it transitions -- overshoot accelerates capacity fade, but stopping too early leaves usable capacity on the table. A Central Composite design models the quadratic curvature in these 3 electrochemical parameters, critical because cycle life degrades nonlinearly near voltage extremes.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (charge_time_min, cycle_life_count)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| charge_current_ma | 500 | 3000 | mA | Constant current charging rate |
| cv_threshold_mv | 3400 | 3650 | mV | Constant voltage threshold |
| trickle_cutoff_mv | 2800 | 3000 | mV | Trickle charge cutoff voltage |

**Fixed:** chemistry = lifepo4, cell_count = 4s

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| charge_time_min | minimize | min |
| cycle_life_count | maximize | cycles |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template battery_management_charging
cd battery_management_charging
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
