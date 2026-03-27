# Use Case 98: Compost Maturity Optimization

## Scenario

You are managing a 1 cubic meter compost pile of mixed greens and browns and want to reach mature, nutrient-rich compost as quickly as possible. The carbon-to-nitrogen ratio, moisture content, and turning frequency all interact nonlinearly -- too much nitrogen causes ammonia loss, excess moisture creates anaerobic conditions, and over-turning can cool the pile below thermophilic temperatures. A Box-Behnken design models these curved relationships efficiently without testing extreme corners where the pile could go anaerobic or dry out completely.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (maturity_weeks, nutrient_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cn_ratio | 20 | 40 | ratio | Carbon-to-nitrogen ratio |
| moisture_pct | 40 | 65 | % | Moisture content percentage |
| turn_freq | 1 | 7 | per_week | Turning frequency per week |

**Fixed:** pile_volume = 1m3, initial_material = mixed_greens_browns

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| maturity_weeks | minimize | weeks |
| nutrient_score | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template compost_maturity
cd compost_maturity
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
