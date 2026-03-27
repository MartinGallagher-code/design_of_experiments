# Use Case 127: Solar Panel Tilt & Orientation

## Scenario

You are installing a rooftop solar array at 40 degrees N latitude with 400 W panels and need to optimize tilt angle, azimuth orientation, and inter-row spacing to maximize annual kWh yield while keeping panel peak temperature manageable. The relationship between tilt and yield is curved -- too steep sacrifices summer production, too flat sacrifices winter -- and row spacing introduces shading interactions. A central composite design fits a second-order model for all three factors, letting you find the precise geometric configuration for your site.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (annual_kwh, peak_temp_c)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| tilt_deg | 10 | 50 | deg | Panel tilt angle from horizontal |
| azimuth_deg | 150 | 210 | deg | Panel azimuth (180 = due south) |
| row_spacing_m | 1.5 | 4.0 | m | Row-to-row spacing |

**Fixed:** latitude = 40N, panel_watt = 400W

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| annual_kwh | maximize | kWh/panel |
| peak_temp_c | minimize | C |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template solar_panel_tilt
cd solar_panel_tilt
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
