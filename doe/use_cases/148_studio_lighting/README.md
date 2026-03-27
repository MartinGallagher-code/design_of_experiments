# Use Case 148: Studio Portrait Lighting

## Scenario

You are setting up a studio portrait lighting rig against a grey background and need to maximize skin tone accuracy while minimizing harsh shadows by tuning key light power (in watt-seconds), fill-to-key ratio, and softbox modifier size. The relationship between modifier size and shadow softness is nonlinear -- doubling the softbox does not halve shadow harshness at all fill ratios. A central composite design captures these quadratic effects across three factors, letting you find the precise lighting setup for flattering, accurate portraits.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (skin_accuracy, shadow_harshness)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| key_power_ws | 100 | 500 | Ws | Key light power in watt-seconds |
| fill_ratio | 2 | 8 | ratio | Key-to-fill light ratio |
| modifier_cm | 60 | 150 | cm | Light modifier diameter |

**Fixed:** background = grey, distance_m = 2

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| skin_accuracy | maximize | pts |
| shadow_harshness | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template studio_lighting
cd studio_lighting
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
