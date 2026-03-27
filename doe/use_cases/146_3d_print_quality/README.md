# Use Case 146: 3D Print Quality Tuning

## Scenario

You are dialing in print settings for PLA on an FDM 3D printer with a 60 C heated bed and want to maximize surface finish quality while minimizing print time. Four slicer parameters -- layer height, print speed, nozzle temperature, and infill percentage -- interact nonlinearly: high speed at low temperature causes under-extrusion, while fine layers at slow speed produce beautiful prints that take forever. A central composite design fits a full quadratic model over these four factors, locating the precise settings that balance quality against time.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (surface_quality, print_time_min)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| layer_height_mm | 0.1 | 0.3 | mm | Layer height |
| print_speed | 30 | 80 | mm/s | Print head speed |
| nozzle_temp_c | 190 | 220 | C | Nozzle temperature for PLA |
| infill_pct | 10 | 50 | % | Infill percentage |

**Fixed:** material = PLA, bed_temp = 60C

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| surface_quality | maximize | pts |
| print_time_min | minimize | min |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template 3d_print_quality
cd 3d_print_quality
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
