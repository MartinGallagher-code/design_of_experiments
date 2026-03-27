# Use Case 107: Sleep Quality Optimization

## Scenario

You are systematically improving your sleep by experimenting with room temperature, screen cutoff time before bed, and caffeine cutoff hour. These factors likely have diminishing-returns effects -- e.g., cooling the room helps up to a point, then provides no further benefit -- so a linear model would miss the optimum. A central composite design captures these curved relationships with three factors, letting you pinpoint the ideal combination that maximizes sleep quality score while minimizing nighttime awakenings.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (sleep_score, wake_count)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| room_temp | 16 | 22 | C | Bedroom temperature |
| screen_cutoff | 30 | 120 | min | Minutes before bed screens are turned off |
| caffeine_cutoff | 6 | 14 | hrs_before | Hours before bed to stop caffeine |

**Fixed:** bedtime = 22:30, wake_time = 06:30

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| sleep_score | maximize | pts |
| wake_count | minimize | count |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template sleep_quality
cd sleep_quality
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
