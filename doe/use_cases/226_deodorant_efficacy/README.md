# Use Case 226: Natural Deodorant Efficacy

## Scenario

You are developing a natural twist-up deodorant and need to screen five ingredients -- baking soda, arrowroot powder, coconut oil, essential oils, and beeswax -- for their effects on odor control duration and skin irritation. The central trade-off is that baking soda is the most effective odor neutralizer but causes sensitivity at high concentrations, and you do not know which other ingredients interact with it. A fractional factorial efficiently identifies the dominant formulation drivers in half the runs, letting you reformulate before committing to panel testing.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (odor_control_hrs, sensitivity_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| baking_soda_pct | 5 | 25 | % | Baking soda percentage |
| arrowroot_pct | 10 | 30 | % | Arrowroot powder percentage |
| coconut_oil_pct | 20 | 50 | % | Coconut oil percentage |
| eo_drops | 5 | 20 | drops/oz | Essential oil drops per ounce |
| beeswax_pct | 2 | 10 | % | Beeswax for firmness |

**Fixed:** container = twist_up, batch_size = 4oz

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| odor_control_hrs | maximize | hrs |
| sensitivity_score | minimize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template deodorant_efficacy
cd deodorant_efficacy
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
