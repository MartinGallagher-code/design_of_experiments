# Use Case 144: Handmade Soap Formulation

## Scenario

You are developing a cold-process soap recipe at 5% superfat and need to screen five formulation variables -- coconut oil ratio, olive oil ratio, lye concentration, essential oil percentage, and cure time -- to determine which most strongly affect lather quality and bar hardness. Running all 32 combinations would consume excessive oils and require months of curing. A fractional factorial design tests a carefully chosen subset of recipes, efficiently identifying the two or three formulation levers that matter most before you commit to a detailed optimization batch.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (lather_score, hardness_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| coconut_pct | 15 | 40 | % | Coconut oil as percentage of total oils |
| olive_pct | 30 | 70 | % | Olive oil as percentage of total oils |
| lye_concentration | 28 | 38 | % | Sodium hydroxide solution concentration |
| essential_oil_pct | 1 | 4 | % | Essential oil fragrance load |
| cure_weeks | 4 | 8 | weeks | Cold process cure time |

**Fixed:** superfat_pct = 5, method = cold_process

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| lather_score | maximize | pts |
| hardness_score | maximize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template soap_making
cd soap_making
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
