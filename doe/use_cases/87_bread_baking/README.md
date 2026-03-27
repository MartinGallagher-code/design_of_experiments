# Use Case 87: Bread Baking Optimization

## Scenario

You are developing a sourdough bread recipe using bread flour and want to maximize both crust quality (color and crispness) and crumb texture (openness and chew). Oven temperature, dough hydration, and proofing time all interact nonlinearly -- high hydration creates an open crumb but can make the dough unworkable, while longer proofing develops flavor but risks over-proofing. A Box-Behnken design models these curved relationships efficiently without baking at all extreme settings simultaneously, which could produce inedible results.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (crust_score, crumb_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| oven_temp | 200 | 260 | C | Oven temperature in Celsius |
| hydration_pct | 60 | 80 | % | Dough hydration percentage |
| proof_time | 30 | 120 | min | Proofing time in minutes |

**Fixed:** flour_type = bread_flour, salt_pct = 2

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| crust_score | maximize | pts |
| crumb_score | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template bread_baking
cd bread_baking
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
