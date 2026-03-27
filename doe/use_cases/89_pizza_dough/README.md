# Use Case 89: Pizza Dough Formulation

## Scenario

You are perfecting a Neapolitan-style pizza dough and want to maximize both chewiness and leopard-spotted bubble structure in the crust. Flour protein content, yeast amount, olive oil, and cold fermentation time (4-72 hours) all interact -- higher protein builds more gluten but needs longer fermentation, while more oil tenderizes the dough at the expense of bubbles. A full factorial design with 4 factors captures all these interactions, which is feasible since each dough batch is inexpensive to prepare.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (chewiness, bubble_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| protein_pct | 10 | 14 | % | Flour protein content percentage |
| yeast_g | 2 | 7 | g | Yeast amount per 500g flour |
| oil_ml | 10 | 30 | mL | Olive oil per 500g flour |
| ferment_hrs | 4 | 72 | hrs | Cold fermentation time |

**Fixed:** salt_pct = 2.5, water_temp = 20

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| chewiness | maximize | pts |
| bubble_score | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template pizza_dough
cd pizza_dough
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
