# Use Case 167: Dog Kibble Formulation

## Scenario

You are formulating a dry kibble recipe for medium-breed adult dogs and want to maximize both palatability (measured by preference trials) and coat condition score by tuning protein content, fat percentage, and fiber content. These three macronutrients interact -- high protein with low fat produces a dry, less palatable kibble, while high fat with low fiber causes digestive issues that worsen coat quality. A Box-Behnken design efficiently models these nonlinear nutritional trade-offs while avoiding the extreme formulations that would fail AAFCO nutritional adequacy guidelines.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (palatability, coat_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| protein_pct | 20 | 35 | % | Crude protein percentage |
| fat_pct | 8 | 18 | % | Crude fat percentage |
| fiber_pct | 2 | 6 | % | Crude fiber percentage |

**Fixed:** breed_size = medium, life_stage = adult

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| palatability | maximize | pts |
| coat_score | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template dog_kibble_formulation
cd dog_kibble_formulation
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
