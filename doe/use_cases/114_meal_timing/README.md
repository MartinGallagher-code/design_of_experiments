# Use Case 114: Meal Timing and Energy Levels

## Scenario

You are experimenting with meal timing and macronutrient distribution on a fixed 2,200-calorie moderate-activity diet to maximize sustained energy and afternoon alertness. Five factors -- meal frequency, eating window, protein ratio, morning calorie percentage, and fiber intake -- could all play a role, but testing every combination at two levels would require 32 days of strict dietary control. A fractional factorial design cuts this to a manageable number of runs while still identifying which dietary levers actually move the needle on energy and alertness.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (energy_score, afternoon_alertness)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| meals_per_day | 2 | 6 | meals | Number of meals per day |
| eating_window_hrs | 8 | 16 | hrs | Daily eating window duration |
| protein_pct | 15 | 35 | % | Protein as percentage of total calories |
| morning_cal_pct | 20 | 50 | % | Percentage of calories consumed before noon |
| fiber_g | 15 | 40 | g | Daily fiber intake in grams |

**Fixed:** total_calories = 2200, activity_level = moderate

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| energy_score | maximize | pts |
| afternoon_alertness | maximize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template meal_timing
cd meal_timing
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
