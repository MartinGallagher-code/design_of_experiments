# Use Case 307: Wine Tasting Panel

## Scenario

You are blending a 2024 Cabernet Sauvignon and need to maximize aroma complexity and overall balance as scored by a tasting panel. Oak barrel aging duration, residual sugar, and free sulfite concentration interact nonlinearly -- extended oak aging builds complexity but can overpower fruit character, while higher sulfites preserve freshness but dull aroma at excessive levels. A Box-Behnken design with three blocks is ideal because each block maps to a different tasting panel session, controlling for palate fatigue and panel-to-panel variation while fitting the curved sensory response surface.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (aroma_score, balance_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| oak_aging | 3 | 18 | months | Oak barrel aging duration |
| sugar_residual | 1 | 8 | g/L | Residual sugar level |
| sulfite_level | 20 | 60 | mg/L | Free sulfite concentration |

**Fixed:** grape_variety = cabernet_sauvignon, vintage = 2024

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| aroma_score | maximize | pts |
| balance_score | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wine_tasting_panel
cd wine_tasting_panel
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
