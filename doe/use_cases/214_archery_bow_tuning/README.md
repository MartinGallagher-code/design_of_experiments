# Use Case 214: Archery Bow Tuning

## Scenario

You are tuning a recurve bow for 18 m indoor target shooting and need to tighten group diameter while eliminating vertical point-of-impact drift by adjusting draw weight, arrow spine rating, brace height, and nocking point height. The draw-weight-to-spine match is the most critical interaction -- an overly stiff arrow with low draw weight fishtails, while a weak spine at high draw weight porpoises vertically. A full factorial across these 4 factors captures all two-way interactions in 16 ends of arrows, which is feasible in a single tuning session.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (group_size_cm, vertical_drift_cm)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| draw_weight_lbs | 30 | 50 | lbs | Bow draw weight |
| arrow_spine | 400 | 700 | spine | Arrow spine deflection rating |
| brace_height_in | 6 | 9 | in | Brace height |
| nock_height_mm | 0 | 6 | mm | Nocking point height above square |

**Fixed:** bow_type = recurve, distance = 18m

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| group_size_cm | minimize | cm |
| vertical_drift_cm | minimize | cm |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template archery_bow_tuning
cd archery_bow_tuning
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
