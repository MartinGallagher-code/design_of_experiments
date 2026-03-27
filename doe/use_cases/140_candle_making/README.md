# Use Case 140: Candle Making Optimization

## Scenario

You are crafting soy wax candles in 8 oz jars and want to maximize both burn time and hot scent throw by tuning wick diameter, fragrance oil load percentage, and wax pour temperature. These three factors are tightly coupled -- a large wick with high fragrance load can cause mushrooming and soot, while a small wick in a heavily scented wax produces weak scent throw. A Box-Behnken design models these nonlinear interactions efficiently while avoiding the extreme corners where candle performance degrades dangerously (e.g., maximum wick with maximum fragrance).

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (burn_hrs, scent_throw)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| wick_size | 4 | 10 | mm | Wick diameter in millimeters |
| fragrance_pct | 4 | 12 | % | Fragrance oil load percentage |
| pour_temp_c | 55 | 80 | C | Wax pouring temperature |

**Fixed:** wax_type = soy, container = 8oz_jar

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| burn_hrs | maximize | hrs |
| scent_throw | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template candle_making
cd candle_making
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
