# Use Case 151: Microscope Imaging Quality

## Scenario

You are imaging stained tissue sections on a brightfield microscope with a CMOS camera and need to maximize spatial resolution while minimizing chromatic aberration by tuning objective magnification, illumination intensity, and condenser numerical aperture. Higher magnification does not always mean better images -- mismatched condenser NA introduces color fringing, and excessive illumination washes out contrast. A central composite design models these nonlinear optical interactions, letting you find the configuration that produces the sharpest, most color-accurate micrographs.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (resolution_um, aberration_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| magnification | 10 | 100 | x | Objective magnification |
| illumination_pct | 20 | 100 | % | Illumination intensity percentage |
| condenser_na | 0.2 | 0.9 | NA | Condenser numerical aperture |

**Fixed:** specimen = stained_tissue, camera = cmos_sensor

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| resolution_um | minimize | um |
| aberration_score | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template microscope_imaging
cd microscope_imaging
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
