# Use Case 188: Crystal Growth Optimization

## Scenario

You are growing copper sulfate crystals from aqueous solution and want to maximize crystal size and purity by tuning cooling rate, initial supersaturation ratio, and seed crystal size. Crystal growth is highly nonlinear -- rapid cooling promotes nucleation of many small crystals, while high supersaturation with small seeds can cause inclusions that reduce purity. A central composite design captures these curved relationships and its axial star points let you explore cooling rates and supersaturation levels slightly beyond the initial experimental range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (crystal_size_mm, purity_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cool_rate_c_hr | 0.5 | 5.0 | C/hr | Cooling rate |
| supersaturation | 1.1 | 1.5 | ratio | Initial supersaturation ratio |
| seed_mm | 0.1 | 2.0 | mm | Seed crystal size |

**Fixed:** solvent = water, compound = copper_sulfate

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| crystal_size_mm | maximize | mm |
| purity_pct | maximize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template crystallization
cd crystallization
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
