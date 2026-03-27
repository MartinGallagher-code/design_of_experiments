# Use Case 101: Lawn Grass Seed Mix

## Scenario

You are formulating a lawn seed blend of perennial ryegrass, fescue, and Kentucky bluegrass to maximize both turf density and drought tolerance. The three species interact -- increasing one means decreasing another -- so you need a design that captures curvature in the response surface. A Box-Behnken design efficiently estimates quadratic effects with only three factors while avoiding extreme corner combinations that would leave one grass species entirely absent from the mix.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (density_score, drought_tolerance)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| ryegrass_pct | 20 | 60 | % | Perennial ryegrass percentage of mix |
| fescue_pct | 20 | 60 | % | Tall fescue percentage of mix |
| seed_rate | 30 | 80 | g/m2 | Seeding rate in grams per square meter |

**Fixed:** remaining_bluegrass_pct = balance, mowing_height_mm = 50

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| density_score | maximize | pts |
| drought_tolerance | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template lawn_grass_mix
cd lawn_grass_mix
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
