# Use Case 282: Oil Paint Drying Medium

## Scenario

You are formulating a drying medium for oil painting with titanium white on linen canvas, aiming to maximize surface gloss after curing while minimizing yellowing (Delta-E color shift) over six months. Linseed oil percentage, alkyd medium concentration, and paint layer thickness interact nonlinearly -- more linseed oil boosts gloss but accelerates yellowing, while thicker layers take longer to cure and may wrinkle. A central composite design captures these curved trade-offs with axial points to explore conditions beyond the initial formulation range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (gloss_score, yellowing_de)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| linseed_pct | 10 | 50 | % | Linseed oil as % of medium |
| medium_pct | 5 | 25 | % | Alkyd medium percentage |
| thickness_mm | 0.5 | 3.0 | mm | Paint layer thickness |

**Fixed:** pigment = titanium_white, support = linen_canvas

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| gloss_score | maximize | pts |
| yellowing_de | minimize | dE |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template oil_paint_drying
cd oil_paint_drying
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
