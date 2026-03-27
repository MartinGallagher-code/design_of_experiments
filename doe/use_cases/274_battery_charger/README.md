# Use Case 274: Battery Charger Settings

## Scenario

You are configuring a charger for 3S LiPo battery packs and need to maximize both achieved capacity and long-term cycle life to 80% retention. Charge C-rate, per-cell voltage cutoff, trickle charge percentage, and temperature cutoff limit all interact -- fast charging at high voltage maximizes capacity per cycle but accelerates lithium plating and capacity fade. A full factorial design is appropriate with four factors because every interaction matters for battery longevity, and the cost of running charge-discharge cycles is manageable compared to the value of getting the profile right.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (capacity_pct, cycle_life)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| charge_c | 0.5 | 2.0 | C | Charge current rate (C-rate) |
| cutoff_v | 4.15 | 4.25 | V | Charge voltage cutoff per cell |
| trickle_pct | 3 | 10 | % | Trickle charge current as % of rated |
| temp_limit_c | 35 | 50 | C | Charge temperature cutoff |

**Fixed:** chemistry = LiPo, cells = 3S

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| capacity_pct | maximize | % |
| cycle_life | maximize | cycles |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template battery_charger
cd battery_charger
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
