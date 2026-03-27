# Use Case 91: Yogurt Fermentation Optimization

## Scenario

You are developing a probiotic yogurt using 3.5% milk fat and want to maximize live culture count (CFU/mL) while keeping sourness mild enough for consumer preference. Fermentation temperature, starter culture percentage, and incubation time all affect acid production nonlinearly -- higher temperatures accelerate fermentation but can kill thermophilic cultures, while longer times increase probiotics but also sourness. A central composite design maps this curved response surface with axial points, finding the precise conditions where probiotic count peaks before over-acidification.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (probiotic_cfu, sourness)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| ferm_temp | 37 | 46 | C | Fermentation temperature |
| starter_pct | 1 | 5 | % | Starter culture percentage |
| ferm_time | 4 | 12 | hrs | Fermentation duration in hours |

**Fixed:** milk_fat_pct = 3.5, pasteurization = 72C_15s

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| probiotic_cfu | maximize | log_CFU/mL |
| sourness | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template yogurt_fermentation
cd yogurt_fermentation
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
