# Use Case 171: Dog Training Effectiveness

## Scenario

You are training a Labrador Retriever using positive reinforcement and want to maximize command reliability while minimizing the number of sessions needed to learn new commands by tuning session length, reward ratio, and difficulty progression rate. These training variables interact nonlinearly -- short sessions with rapid progression overwhelm the dog, while long sessions with constant rewards can cause satiation and loss of motivation. A central composite design maps these curved behavioral responses, letting you find the training protocol that produces the fastest, most reliable learning.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (reliability_pct, sessions_to_learn)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| session_min | 5 | 20 | min | Training session duration |
| reward_ratio_pct | 30 | 100 | % | Percentage of correct responses rewarded |
| progression_rate | 1 | 5 | level/wk | Difficulty increase per week |

**Fixed:** method = positive_reinforcement, breed = labrador

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| reliability_pct | maximize | % |
| sessions_to_learn | minimize | sessions |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template dog_training_protocol
cd dog_training_protocol
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
