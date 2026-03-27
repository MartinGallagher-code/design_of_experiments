# Use Case 242: Sauerkraut Fermentation

## Scenario

You are fermenting green cabbage sauerkraut in a crock and want to maximize both sour tang and crisp crunch by adjusting salt percentage, shred width, fermentation temperature, and pressing weight. The salt-temperature interaction is critical -- high salt at low temperature produces slow, mild ferments, while low salt at warm temperature can promote spoilage organisms over desirable Lactobacillus. A full factorial across these 4 factors reveals all interactions in 16 crock batches, which is feasible for a seasonal production run and ensures no important salt-shred or temperature-weight effects are missed.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (tang_score, crunch_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| salt_pct | 2 | 4 | % | Salt as percentage of cabbage weight |
| shred_mm | 2 | 6 | mm | Cabbage shred width |
| temp_c | 15 | 25 | C | Fermentation temperature |
| weight_kg | 1 | 5 | kg | Pressing weight on top |

**Fixed:** cabbage = green, vessel = crock

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| tang_score | maximize | pts |
| crunch_score | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template sauerkraut_ferment
cd sauerkraut_ferment
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
