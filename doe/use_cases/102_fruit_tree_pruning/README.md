# Use Case 102: Fruit Tree Pruning Strategy

## Scenario

You are managing a Honeycrisp apple orchard and want to find the best pruning strategy to maximize both individual fruit size and total yield per tree. Four controllable factors -- pruning intensity, pruning month, branch angle, and fruit thinning ratio -- all interact in ways that are not well understood for your specific microclimate. A full factorial design lets you estimate every main effect and interaction, which is critical because aggressive pruning combined with heavy thinning could dramatically shift the size-versus-yield trade-off.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (fruit_size_g, yield_kg)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| prune_intensity | 10 | 40 | % | Percentage of canopy removed |
| prune_month | 1 | 3 | month | Pruning month (1=Jan, 3=Mar) |
| branch_angle | 30 | 60 | deg | Target branch angle from vertical |
| thin_ratio | 0 | 50 | % | Fruit thinning percentage |

**Fixed:** tree_age = 7yr, variety = honeycrisp_apple

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| fruit_size_g | maximize | g |
| yield_kg | maximize | kg/tree |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template fruit_tree_pruning
cd fruit_tree_pruning
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
