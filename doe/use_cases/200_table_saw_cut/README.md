# Use Case 200: Table Saw Cut Quality

## Scenario

You are crosscutting maple on a 10-inch table saw and need to maximize surface smoothness while minimizing bottom-side tearout by adjusting blade RPM, feed rate, and blade tooth count. The chip load per tooth -- determined by the interaction of all three factors -- governs cut quality nonlinearly: too aggressive a feed with a low tooth count causes splintering, while too slow a feed with a high-tooth blade generates excessive heat and burn marks. A central composite design maps this curved response surface and lets you predict optimal settings even at RPMs beyond the initial test range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (smoothness, tearout_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| blade_rpm | 3000 | 5000 | rpm | Blade rotation speed |
| feed_rate | 1 | 5 | m/min | Workpiece feed rate |
| tooth_count | 24 | 80 | teeth | Blade tooth count |

**Fixed:** blade_diam = 10in, material = maple

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| smoothness | maximize | pts |
| tearout_score | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template table_saw_cut
cd table_saw_cut
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
