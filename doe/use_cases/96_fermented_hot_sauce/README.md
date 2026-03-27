# Use Case 96: Fermented Hot Sauce Formulation

## Scenario

You are developing a lacto-fermented hot sauce and want to maximize both heat balance and umami depth. There are 5 formulation variables -- pepper Scoville level (5K-100K SHU), salt concentration, garlic ratio, fermentation duration (7-90 days), and post-fermentation vinegar addition -- where longer fermentation builds umami but increases sourness, and higher salt preserves safely but can suppress fermentation. A fractional factorial design screens these factors efficiently, identifying which ingredients and process steps drive flavor complexity.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (heat_balance, umami_depth)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| pepper_shu | 5000 | 100000 | SHU | Pepper Scoville heat units |
| salt_pct | 2 | 6 | % | Salt concentration by weight |
| garlic_pct | 2 | 10 | % | Garlic percentage of total mash |
| ferm_days | 7 | 90 | days | Fermentation duration |
| vinegar_pct | 5 | 25 | % | Vinegar added post-fermentation |

**Fixed:** ferm_temp = 22, jar_size = 1L

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| heat_balance | maximize | pts |
| umami_depth | maximize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template fermented_hot_sauce
cd fermented_hot_sauce
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
