# Use Case 297: Hoof Trimming Schedule

## Scenario

You are developing a hoof care protocol for dairy cows housed on concrete-rubber surfaces and need to determine which of five management factors -- trimming interval, target heel height, dorsal toe angle, front-rear weight distribution, and daily exercise hours -- most strongly influence locomotion lameness scores and hoof wall quality. Testing all 32 combinations in a full factorial would require an impractical number of animals and observation periods. A fractional factorial design efficiently screens these five factors to identify the key drivers of hoof health before investing in a detailed optimization study.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (lameness_score, hoof_health)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| trim_weeks | 6 | 16 | weeks | Trimming interval |
| heel_height_mm | 20 | 40 | mm | Target heel height after trim |
| toe_angle_deg | 45 | 55 | deg | Target dorsal toe angle |
| balance_pct | 45 | 55 | % | Weight on front feet percentage |
| exercise_hrs | 2 | 8 | hrs | Daily exercise/movement hours |

**Fixed:** animal = dairy_cow, surface = concrete_rubber

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| lameness_score | minimize | pts |
| hoof_health | maximize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template hoof_trimming
cd hoof_trimming
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
