# Use Case 233: Hillside Erosion Control

## Scenario

You are stabilizing a 30% silt-loam hillside after grading and need to minimize annual soil loss while maximizing 6-month vegetation cover by adjusting mulch depth, seed mix application rate, and terrace spacing. Erosion is a nonlinear function of these factors -- thick mulch suppresses runoff but can smother seedlings, while wide terrace spacing concentrates flow between benches. A Box-Behnken design captures these curved relationships without the extreme corner of maximum mulch, maximum seed, and minimum terrace spacing, which would be prohibitively expensive on a large slope.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (soil_loss_t_ha, vegetation_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| mulch_cm | 2 | 10 | cm | Mulch layer depth |
| seed_g_m2 | 10 | 50 | g/m2 | Seed mix application rate |
| terrace_m | 5 | 20 | m | Terrace spacing interval |

**Fixed:** slope_pct = 30, soil_type = silt_loam

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| soil_loss_t_ha | minimize | t/ha/yr |
| vegetation_pct | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template erosion_control
cd erosion_control
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
