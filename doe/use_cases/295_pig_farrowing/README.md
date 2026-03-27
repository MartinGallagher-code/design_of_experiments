# Use Case 295: Pig Farrowing Pen Design

## Scenario

You are designing farrowing pens for Large White sows with average litters of 12 piglets, aiming to maximize pre-weaning piglet survival while ensuring sow comfort and natural behavior. Creep area temperature, heated floor mat coverage, and total pen space per sow interact nonlinearly -- too-warm creep areas reduce piglet huddling mortality but can overheat the sow, while more space improves sow comfort but increases crushing risk if piglets spread out. A central composite design captures these curved welfare responses and explores conditions beyond the initial factor ranges to find settings that satisfy both piglet and sow needs.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (piglet_survival_pct, sow_comfort)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| creep_temp_c | 28 | 35 | C | Creep area temperature |
| heat_mat_pct | 0 | 100 | % | Heated floor mat coverage |
| space_m2 | 4 | 7 | m2 | Total pen space per sow |

**Fixed:** breed = large_white, litter_size = 12

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| piglet_survival_pct | maximize | % |
| sow_comfort | maximize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template pig_farrowing
cd pig_farrowing
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
