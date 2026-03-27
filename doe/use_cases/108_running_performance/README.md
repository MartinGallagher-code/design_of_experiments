# Use Case 108: Running Training Plan

## Scenario

You are an intermediate distance runner designing a training plan that maximizes VO2max gains while keeping injury risk low. Three key training variables -- weekly mileage, long run percentage, and interval intensity as a fraction of max heart rate -- must be balanced carefully because pushing all three to their extremes simultaneously almost guarantees overtraining injury. A Box-Behnken design avoids those dangerous corner combinations while still estimating the curvature needed to find the optimal training load.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (vo2max_gain, injury_risk)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| weekly_km | 20 | 60 | km | Total weekly running distance |
| long_run_pct | 20 | 40 | % | Long run as percentage of weekly volume |
| interval_pct_max | 80 | 100 | %HR_max | Interval training intensity as % of max heart rate |

**Fixed:** rest_days = 2, runner_level = intermediate

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| vo2max_gain | maximize | mL/kg/min |
| injury_risk | minimize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template running_performance
cd running_performance
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
