# Use Case 162: Drum Head Tuning

## Scenario

You are tuning a 14x5 coated-head snare drum and want to maximize resonance while controlling unwanted overtones by adjusting batter head tension, resonant head tension, and muffling amount. The relationship between the two head tensions determines the drum's pitch and sensitivity in a nonlinear way -- a tight batter with a loose resonant head produces a completely different timbre than matched tensions. A central composite design maps this curved response surface, letting you find the precise tuning that gives a full, controlled snare sound for recording.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (resonance, overtone_control)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| batter_torque | 20 | 80 | in-lb | Batter head lug torque |
| reso_torque | 20 | 80 | in-lb | Resonant head lug torque |
| muffle_pct | 0 | 50 | % | Muffling ring coverage percentage |

**Fixed:** drum_size = 14x5_snare, head_type = coated

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| resonance | maximize | pts |
| overtone_control | maximize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template drum_tuning
cd drum_tuning
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
