# Use Case 173: Horse Feed Ration Balance

## Scenario

You are formulating the daily ration for a 500 kg moderate-work horse and need to screen five nutritional levers -- hay volume, grain concentrate, mineral supplement, oil supplement, and feeding frequency -- for their effects on body condition score and hoof wall quality. A full factorial across all five factors would require 32 runs of multi-week feeding trials, which is impractical with live animals. A fractional factorial lets you identify the dominant nutritional drivers in half the runs while assuming higher-order interactions between supplements are negligible.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (body_condition, hoof_quality)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| hay_kg | 6 | 12 | kg/day | Daily hay intake |
| grain_kg | 1 | 5 | kg/day | Daily grain concentrate |
| mineral_g | 30 | 90 | g/day | Mineral supplement amount |
| oil_ml | 0 | 120 | mL/day | Vegetable oil supplement |
| feed_freq | 2 | 4 | per_day | Feeding frequency per day |

**Fixed:** horse_weight = 500kg, activity = moderate

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| body_condition | maximize | pts |
| hoof_quality | maximize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template horse_feed_ration
cd horse_feed_ration
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
