# Use Case 211: Tennis Racket String Setup

## Scenario

You are stringing a 100 sq-in midplus racket with polyester and need to maximize both power and placement control by adjusting main string tension, cross string tension, and string gauge. Power and control are inherently opposed -- lower tension increases the trampoline effect for power but reduces directional precision, while thicker gauges improve durability but deaden the response. A Box-Behnken design captures these nonlinear trade-offs without the extreme corners like maximum tension on both mains and crosses with the thinnest gauge, which would likely snap strings during play.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (power_score, control_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| main_tension_kg | 20 | 28 | kg | Main string tension |
| cross_tension_kg | 18 | 26 | kg | Cross string tension |
| gauge_mm | 1.15 | 1.35 | mm | String gauge diameter |

**Fixed:** racket = midplus_100, string_material = polyester

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| power_score | maximize | pts |
| control_score | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template tennis_racket_string
cd tennis_racket_string
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
