# Use Case 277: Wire Gauge & Run Length

## Scenario

You are wiring a 20A/120V copper circuit and need to minimize voltage drop percentage while keeping wire cost per meter reasonable. AWG gauge, one-way run length, and conduit fill percentage interact nonlinearly -- heavier gauge reduces voltage drop but increases material cost and may violate NEC conduit fill limits on longer runs. A Box-Behnken design efficiently fits the curved cost-performance surface across these three factors without testing the impractical corner of heaviest gauge at maximum fill in the longest run.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (voltage_drop_pct, cost_per_m)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| awg | 10 | 18 | AWG | Wire gauge (smaller = thicker) |
| run_m | 5 | 30 | m | Wire run length one-way |
| fill_pct | 20 | 60 | % | Conduit fill percentage |

**Fixed:** circuit = 20A_120V, conductor = copper

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| voltage_drop_pct | minimize | % |
| cost_per_m | minimize | USD/m |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wire_gauge_selection
cd wire_gauge_selection
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
