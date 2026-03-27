# Use Case 170: Tropical Fish Tank Health

## Scenario

You are maintaining a 200 L tropical freshwater aquarium with 20 fish and want to maximize fish vitality while minimizing algae growth by tuning weekly water change percentage, daily feeding amount, and photoperiod duration. These parameters are tightly coupled through the nitrogen cycle -- overfeeding raises nitrates that fuel algae, but infrequent water changes compound the problem, and excess light accelerates algae growth on top of that. A Box-Behnken design models these nonlinear biological interactions while avoiding the extreme corners where fish health would be compromised by simultaneous overfeeding and minimal water changes.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (vitality_score, algae_level)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| water_change_pct | 10 | 40 | %/week | Weekly water change percentage |
| feed_g_day | 0.5 | 3.0 | g/day | Daily feeding amount |
| light_hrs | 6 | 12 | hrs | Daily photoperiod |

**Fixed:** tank_L = 200, fish_count = 20

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| vitality_score | maximize | pts |
| algae_level | minimize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template fish_tank_health
cd fish_tank_health
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
