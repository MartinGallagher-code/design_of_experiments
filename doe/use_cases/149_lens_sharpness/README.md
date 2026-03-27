# Use Case 149: Lens Sharpness Testing

## Scenario

You are benchmarking a 24-70 mm zoom lens on a full-frame body at ISO 200 and want to characterize how aperture, focal length, focus distance, and image stabilization (on/off) jointly affect center resolution and corner sharpness falloff. Lens performance varies in complex ways -- wide open at 70 mm may show strong corner softness that disappears by f/8, but only at certain focus distances. A full factorial design tests every combination of these four factors, producing a complete sharpness profile across the entire operating envelope of the lens.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (center_lpmm, corner_falloff_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| aperture_f | 2.8 | 11 | f-stop | Aperture f-number |
| focal_length | 24 | 70 | mm | Focal length |
| focus_dist_m | 1 | 10 | m | Focus distance |
| stabilization | off | on |  | Image stabilization |

**Fixed:** body = full_frame, iso = 200

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| center_lpmm | maximize | lp/mm |
| corner_falloff_pct | minimize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template lens_sharpness
cd lens_sharpness
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
