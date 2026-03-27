# Use Case 246: Kefir Grain Cultivation

## Scenario

You are culturing milk kefir in glass jars with whole cow's milk and need to screen five fermentation variables -- milk fat content, fermentation time, grain-to-milk ratio, temperature, and agitation frequency -- to maximize probiotic diversity and taste quality. Each fermentation batch takes 12-48 hours and the grains need recovery time between runs, so a full 32-run factorial is impractical. A fractional factorial identifies which parameters most influence the symbiotic culture's microbial balance and flavor in half the runs, assuming higher-order interactions among these fermentation conditions are negligible.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (probiotic_score, taste_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| fat_pct | 0.5 | 4.0 | % | Milk fat content |
| ferm_hrs | 12 | 48 | hrs | Fermentation time |
| grain_ratio_pct | 3 | 15 | % | Grain-to-milk ratio by weight |
| temp_c | 18 | 28 | C | Fermentation temperature |
| agitation | 0 | 3 | per_day | Gentle agitation frequency per day |

**Fixed:** milk_type = whole_cow, vessel = glass_jar

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| probiotic_score | maximize | pts |
| taste_score | maximize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template kefir_grains
cd kefir_grains
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
