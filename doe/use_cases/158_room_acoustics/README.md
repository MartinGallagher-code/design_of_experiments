# Use Case 158: Room Acoustics Treatment

## Scenario

You are treating a 50 m3 mixing studio and need to achieve a target RT60 reverb time while eliminating flutter echo by tuning the area of absorption panels, diffuser coverage, and number of bass traps. Over-treating with absorption creates a dead, lifeless room; under-treating leaves problematic reflections that color your mixes. A central composite design models these nonlinear acoustic interactions, letting you find the precise balance of absorption and diffusion that produces a neutral, accurate monitoring environment.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (rt60_ms, flutter_echo)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| absorption_m2 | 4 | 20 | m2 | Total absorption panel area |
| diffuser_m2 | 2 | 12 | m2 | Diffuser panel area |
| bass_traps | 2 | 8 | count | Number of corner bass traps |

**Fixed:** room_m3 = 50, purpose = mixing_studio

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| rt60_ms | minimize | ms |
| flutter_echo | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template room_acoustics
cd room_acoustics
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
