# Use Case 212: Basketball Free Throw Form

## Scenario

You are refining free throw mechanics from 4.6 m with a size 7 basketball and want to maximize shooting accuracy while improving arc consistency by adjusting release angle, release height, and backspin rate. The optimal arc is a nonlinear function of all three parameters -- a high release angle with low backspin produces a soft but inconsistent trajectory, while a flat release with heavy spin reduces the effective hoop opening. A central composite design models this curved accuracy surface and its axial points help explore release mechanics slightly beyond the player's initial comfort zone.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (accuracy_pct, arc_consistency)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| release_angle_deg | 45 | 55 | deg | Ball release angle from horizontal |
| release_height_m | 2.0 | 2.5 | m | Ball release height |
| backspin_rpm | 100 | 300 | rpm | Ball backspin rate |

**Fixed:** distance = 4.6m, ball = size_7

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| accuracy_pct | maximize | % |
| arc_consistency | maximize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template basketball_shooting
cd basketball_shooting
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
