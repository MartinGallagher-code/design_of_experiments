# Use Case 284: Canvas Stretching Tension

## Scenario

You are stretching 60x80cm cotton duck canvases for gallery use and need to maximize surface flatness while minimizing stretcher bar warping over time. Staple spacing, bar profile thickness, canvas weight in GSM, and whether to apply gesso pre-priming all interact -- tight staple spacing on thin bars with heavy canvas can bow the frame, while pre-priming changes the tension characteristics of the fabric. A full factorial design is the right choice because with four factors at two levels the 16-run matrix is affordable, and you need complete interaction information since bar thickness and canvas weight are strongly coupled.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (flatness, warp_mm)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| staple_spacing_cm | 3 | 8 | cm | Staple spacing along edge |
| bar_mm | 18 | 40 | mm | Stretcher bar profile thickness |
| canvas_gsm | 200 | 400 | g/m2 | Canvas weight |
| pre_prime | none | gesso |  | Pre-priming treatment |

**Fixed:** size = 60x80cm, canvas = cotton_duck

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| flatness | maximize | pts |
| warp_mm | minimize | mm |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template canvas_stretching
cd canvas_stretching
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
