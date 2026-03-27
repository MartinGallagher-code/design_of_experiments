# Use Case 302: Ceramic Glaze Firing Optimization

## Scenario

You are firing ceramic pieces in an electric kiln and need to achieve smooth glaze surfaces with accurate color reproduction across different clay bodies, glaze thicknesses, peak temperatures, soak times, and cooling schedules. These five factors have mixed levels (some at 2, some at 3) and kiln firing results are sensitive to uncontrollable batch-to-batch variation in atmosphere and element aging. A Taguchi orthogonal array is the right approach because it handles the mixed-level structure efficiently and its signal-to-noise analysis identifies settings that produce robust glaze quality despite kiln variability.

**This use case demonstrates:**
- Taguchi design
- Multi-response analysis (surface_smoothness, color_accuracy)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| clay_type | porcelain | earthenware |  | Base clay body material |
| glaze_thickness | thin | thick |  | Applied glaze coat thickness |
| peak_temperature | 1100 | 1250 | °C | Maximum kiln temperature |
| hold_time | 30 | 90 | min | Soak time at peak temperature |
| cooling_rate | slow | fast |  | Kiln cooling schedule |

**Fixed:** kiln_type = electric

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| surface_smoothness | maximize | score |
| color_accuracy | minimize | deltaE |

## Why Taguchi?

- Uses orthogonal arrays to study many factors with minimal experiments
- Focuses on making the process robust to noise (uncontrollable variation)
- Signal-to-noise ratio analysis identifies factor settings that minimize variability
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template ceramic_glaze_firing
cd ceramic_glaze_firing
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
