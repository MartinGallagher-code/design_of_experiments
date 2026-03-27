# Use Case 110: Meditation Routine Effectiveness

## Scenario

You are establishing a daily meditation practice and want to determine the best combination of session duration, time of day, and the balance between guided versus unguided technique to maximize stress reduction and focus improvement. Meditating for 30 minutes of guided practice at the worst time of day could be less effective than 10 minutes of silent practice at the right time, so interactions matter. A Box-Behnken design efficiently maps these nonlinear relationships with three factors while avoiding impractical extremes.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (stress_reduction, focus_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| duration_min | 5 | 30 | min | Session duration in minutes |
| time_of_day | 6 | 22 | hour | Hour of day for practice (24h format) |
| guided_pct | 0 | 100 | % | Percentage of guided vs silent meditation |

**Fixed:** frequency = daily, environment = quiet_room

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| stress_reduction | maximize | pts |
| focus_score | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template meditation_routine
cd meditation_routine
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
