# Use Case 109: Strength Training Program

## Scenario

You are programming a barbell squat cycle for an intermediate lifter and want to understand how sets, reps, rest period, and weekly training frequency interact to drive strength gains versus accumulated fatigue. Conventional wisdom offers conflicting advice -- high sets with low reps, or moderate sets with moderate reps -- so you need hard data on all interactions. A full factorial design tests every combination of these four factors, revealing whether, for example, short rest periods only cause excessive fatigue at high training frequencies.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (strength_gain, fatigue_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| sets | 3 | 6 | sets | Number of sets per exercise |
| reps | 3 | 12 | reps | Repetitions per set |
| rest_sec | 60 | 180 | sec | Rest period between sets |
| freq_per_week | 2 | 5 | days/wk | Training frequency per week |

**Fixed:** exercise = barbell_squat, trainee_level = intermediate

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| strength_gain | maximize | % |
| fatigue_score | minimize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template strength_training
cd strength_training
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
