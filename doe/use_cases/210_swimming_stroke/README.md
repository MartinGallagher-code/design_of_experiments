# Use Case 210: Swimming Stroke Efficiency

## Scenario

You are optimizing freestyle technique in a 25 m pool and want to maximize swimming speed while minimizing energy cost per 100 m by adjusting stroke rate, distance per stroke, and kick-to-stroke ratio. The speed-efficiency trade-off is sharply nonlinear -- a high stroke rate with a short stroke length churns water without propulsion, while a slow rate with a 6-beat kick wastes energy on excessive kicking. A central composite design maps this curved performance surface and its axial points let you explore stroke parameters slightly beyond the athlete's current comfortable range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (speed_m_s, energy_kj_100m)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| stroke_rate | 40 | 70 | strokes/min | Stroke rate |
| stroke_length_m | 1.5 | 2.5 | m | Distance per stroke |
| kick_ratio | 2 | 6 | kicks/stroke | Kick tempo per stroke cycle |

**Fixed:** stroke = freestyle, pool = 25m

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| speed_m_s | maximize | m/s |
| energy_kj_100m | minimize | kJ/100m |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template swimming_stroke
cd swimming_stroke
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
