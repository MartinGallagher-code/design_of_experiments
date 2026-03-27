# Use Case 234: Mineral Flotation Separation

## Scenario

You are operating a froth flotation circuit to separate chalcopyrite from a 75 um ground ore and need to maximize copper recovery and concentrate grade by adjusting xanthate collector dosage, frother dosage, and pulp pH. Recovery and grade are inherently opposed -- higher collector dosage improves recovery but drags gangue into the froth, reducing grade, while pH shifts the mineral surface chemistry nonlinearly. A central composite design maps these curved metallurgical responses and its axial points let you probe reagent dosages and pH values slightly beyond the initial range to find the optimal selectivity window.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (recovery_pct, grade_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| collector_g_t | 20 | 80 | g/t | Collector reagent dosage |
| frother_g_t | 10 | 40 | g/t | Frother dosage |
| pulp_ph | 7 | 11 | pH | Pulp slurry pH |

**Fixed:** mineral = chalcopyrite, grind_size = 75um

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| recovery_pct | maximize | % |
| grade_pct | maximize | %Cu |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template mineral_flotation
cd mineral_flotation
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
