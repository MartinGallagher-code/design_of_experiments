# Use Case 113: Study Session Optimization

## Scenario

You are preparing for a biology exam and want to optimize your 3-hour study sessions by tuning study block length, break duration, active recall percentage, and ambient noise level. Conventional study advice conflicts -- some suggest Pomodoro-style short blocks, others recommend deep 50-minute sessions -- and the best approach likely depends on interactions between these factors. A full factorial design tests every combination and determines, for example, whether active recall is only effective above a certain block length or noise level.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (retention_pct, attention_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| block_min | 15 | 50 | min | Uninterrupted study block duration |
| break_min | 3 | 15 | min | Break duration between blocks |
| active_recall_pct | 0 | 100 | % | Percentage of time using active recall vs passive reading |
| noise_db | 25 | 65 | dB | Background noise level |

**Fixed:** subject = biology, total_hours = 3

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| retention_pct | maximize | % |
| attention_score | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template study_habit
cd study_habit
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
