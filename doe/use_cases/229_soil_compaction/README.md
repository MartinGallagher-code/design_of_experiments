# Use Case 229: Soil Compaction Testing

## Scenario

You are running a Proctor compaction test with a 2.5 kg hammer to find the optimal water content, blows per layer, and number of compaction layers that maximize dry density and California Bearing Ratio for a subgrade soil. Dry density follows a classic parabolic curve with moisture content -- too dry leaves voids, too wet reduces effective compaction energy. A Box-Behnken design captures this nonlinear moisture-density relationship efficiently without testing the extreme corners where very high energy meets very dry soil, which would damage the Proctor mold.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (dry_density_kg_m3, cbr_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| water_pct | 8 | 20 | % | Gravimetric water content |
| blows_per_layer | 15 | 56 | blows | Compaction blows per layer |
| layers | 3 | 5 | layers | Number of compaction layers |

**Fixed:** hammer_kg = 2.5, mold = proctor

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| dry_density_kg_m3 | maximize | kg/m3 |
| cbr_pct | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template soil_compaction
cd soil_compaction
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
