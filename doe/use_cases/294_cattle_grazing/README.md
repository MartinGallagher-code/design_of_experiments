# Use Case 294: Rotational Grazing Pattern

## Scenario

You are implementing rotational grazing for beef cattle across a 10-paddock system and need to maximize pasture biomass recovery while maintaining strong average daily weight gains per head. Paddock rest period, instantaneous stocking density, and grazing duration per paddock interact nonlinearly -- short rest with high density can overgraze root reserves and crash regrowth, while long rest periods allow pasture to mature past peak palatability. A Box-Behnken design avoids the extreme corner of maximum density with minimum rest that would degrade the pasture, while fitting the curved recovery response needed for sustainable management.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (pasture_recovery_pct, adg_kg)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| rest_days | 21 | 60 | days | Paddock rest period between grazing |
| stock_density_au_ha | 50 | 200 | AU/ha | Instantaneous stocking density |
| graze_days | 1 | 5 | days | Days of grazing per paddock |

**Fixed:** cattle = beef, paddock_count = 10

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| pasture_recovery_pct | maximize | % |
| adg_kg | maximize | kg/day |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template cattle_grazing
cd cattle_grazing
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
