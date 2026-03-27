# Use Case 99: Seed Germination Rate

## Scenario

You are optimizing germination conditions for lettuce seeds in potting mix and want to maximize germination percentage while minimizing days to seedling emergence. Soil temperature, moisture level, planting depth, and daily light hours all interact -- lettuce seeds require light for germination but too-deep planting blocks it, while high temperatures can induce thermo-dormancy. A full factorial design with 4 factors is practical for a seed trial and captures all interactions, such as whether light requirements change with planting depth and soil temperature.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (germination_pct, days_to_emerge)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| soil_temp | 15 | 28 | C | Soil temperature |
| moisture_level | 30 | 70 | % | Soil moisture field capacity percentage |
| seed_depth | 5 | 25 | mm | Planting depth in millimeters |
| light_hrs | 8 | 16 | hrs | Daily light exposure hours |

**Fixed:** seed_variety = lettuce, medium = potting_mix

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| germination_pct | maximize | % |
| days_to_emerge | minimize | days |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template seed_germination
cd seed_germination
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
