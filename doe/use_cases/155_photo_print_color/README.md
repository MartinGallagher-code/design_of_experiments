# Use Case 155: Photo Print Color Accuracy

## Scenario

You are calibrating an 8-color inkjet printer at 1440 DPI to produce gallery-quality photo prints and want to minimize Delta E color deviation while keeping ink consumption per square meter low. Three parameters -- ICC profile gamma, ink density percentage, and paper brightness (ISO) -- interact in subtle ways: boosting ink density on bright paper can oversaturate highlights, while low gamma with dim paper muddies shadows. A Box-Behnken design captures these nonlinear interactions efficiently, avoiding the corners where extreme settings waste expensive ink on obviously poor prints.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (delta_e, ink_ml)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| profile_gamma | 1.8 | 2.4 | gamma | ICC profile gamma value |
| ink_density_pct | 80 | 120 | % | Ink density relative to default |
| paper_brightness | 90 | 100 | ISO | Paper brightness ISO value |

**Fixed:** printer = inkjet_8color, resolution_dpi = 1440

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| delta_e | minimize | dE |
| ink_ml | minimize | mL/m2 |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template photo_print_color
cd photo_print_color
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
