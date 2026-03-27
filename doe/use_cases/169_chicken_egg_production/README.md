# Use Case 169: Backyard Chicken Egg Production

## Scenario

You are optimizing egg production from a flock of six Rhode Island Red hens and want to maximize weekly eggs per hen and eggshell thickness by tuning supplemental light hours, feed protein percentage, calcium supplement dose, and coop ventilation level. These factors interact biologically -- extra light stimulates laying but increases calcium demand, and poor ventilation with high protein feed raises ammonia levels that stress the birds. A full factorial design tests every combination, revealing critical interactions like whether calcium supplementation only matters above a certain light-hours threshold.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (eggs_per_week, shell_thickness)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| light_hrs | 10 | 16 | hrs | Daily light exposure hours |
| feed_protein_pct | 14 | 20 | % | Feed crude protein percentage |
| calcium_g | 2 | 6 | g/day | Supplemental calcium per hen per day |
| ventilation | low | high |  | Coop ventilation level |

**Fixed:** breed = rhode_island_red, flock_size = 6

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| eggs_per_week | maximize | eggs/hen |
| shell_thickness | maximize | mm |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template chicken_egg_production
cd chicken_egg_production
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
