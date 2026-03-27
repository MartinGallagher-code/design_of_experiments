# Use Case 198: Party Planning Optimization

## Scenario

You are planning a 50-person birthday party and want to maximize guest satisfaction while minimizing cost per person by tuning venue space per guest, food budget allocation, and scheduled entertainment hours. Satisfaction exhibits diminishing returns -- doubling the food budget does not double enjoyment, and a cramped venue tanks ratings regardless of entertainment quality. A central composite design models these curved relationships and its axial points help you explore budget allocations slightly beyond your initial planning range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (satisfaction, cost_per_person)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| sqft_per_guest | 15 | 40 | sqft | Venue square feet per guest |
| food_budget_pct | 30 | 60 | % | Food as percentage of total budget |
| entertainment_hrs | 1 | 4 | hrs | Scheduled entertainment duration |

**Fixed:** guests = 50, event_type = birthday

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| satisfaction | maximize | pts |
| cost_per_person | minimize | USD |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template party_planning
cd party_planning
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
