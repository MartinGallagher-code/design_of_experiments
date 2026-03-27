# Use Case 251: Coral Reef Fragment Restoration

## Scenario

You are outplanting Acropora coral fragments on ceramic disc substrates and need to maximize annual growth rate and 6-month survival by adjusting fragment length, planting depth, and inter-fragment spacing. Light availability decreases nonlinearly with depth while wave stress increases in shallow water, and closely spaced fragments compete for nutrients but benefit from mutual shading during bleaching events. A Box-Behnken design captures these curved ecological responses without testing the impractical extreme of the smallest fragments at maximum depth with minimum spacing, which would almost certainly result in total mortality.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (growth_cm_yr, survival_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| fragment_cm | 3 | 10 | cm | Coral fragment length |
| depth_m | 3 | 15 | m | Planting depth |
| spacing_cm | 10 | 40 | cm | Inter-fragment spacing |

**Fixed:** species = acropora, substrate = ceramic_disc

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| growth_cm_yr | maximize | cm/yr |
| survival_pct | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template coral_reef_restoration
cd coral_reef_restoration
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
