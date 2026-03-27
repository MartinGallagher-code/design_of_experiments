# Use Case 147: Landscape Photo Exposure

## Scenario

You are shooting landscape photographs with a 24 mm lens in daylight and want to maximize dynamic range while minimizing sensor noise by tuning ISO, aperture, and shutter speed. The classic exposure triangle creates a three-way trade-off: stopping down for depth of field demands either higher ISO (more noise) or slower shutter speed (motion blur risk). A Box-Behnken design efficiently maps these curved interactions without testing the impractical extremes of ISO 3200 at f/16, where noise would overwhelm any sharpness gain.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (dynamic_range_ev, noise_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| iso | 100 | 3200 | ISO | Sensor sensitivity |
| aperture | 2.8 | 16 | f-stop | Lens aperture f-number |
| shutter_speed_ms | 1 | 1000 | ms | Shutter speed in milliseconds |

**Fixed:** lens_mm = 24, white_balance = daylight

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| dynamic_range_ev | maximize | EV |
| noise_score | minimize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template landscape_exposure
cd landscape_exposure
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
