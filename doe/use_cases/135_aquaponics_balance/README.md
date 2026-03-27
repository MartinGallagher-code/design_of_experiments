# Use Case 135: Aquaponics System Balance

## Scenario

You are balancing a tilapia-and-basil aquaponics system where fish waste feeds the plants and plants filter the water for the fish. Three parameters -- fish stocking density, daily feeding rate, and water flow rate through the grow beds -- are tightly coupled: overfeeding at high density with low flow leads to ammonia spikes that stress both fish and plants. A Box-Behnken design captures these nonlinear interactions while avoiding the extreme corners where system crashes are most likely.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (fish_growth_g, plant_yield_g)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| fish_density | 10 | 40 | fish/m3 | Fish stocking density |
| feed_rate_pct | 1 | 4 | %BW/day | Daily feeding rate as % of body weight |
| flow_rate_lph | 200 | 800 | L/hr | Water circulation flow rate |

**Fixed:** fish_species = tilapia, plant = basil

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| fish_growth_g | maximize | g/week |
| plant_yield_g | maximize | g/m2/wk |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template aquaponics_balance
cd aquaponics_balance
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
