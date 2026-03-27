# Use Case 293: Poultry House Ventilation

## Scenario

You are managing a 1,200 m2 broiler house with 20,000 birds and need to maximize average daily weight gain while minimizing heat stress mortality during summer months. Fan ventilation rate, inlet baffle opening, fogging system cycle interval, and daily lighting hours all interact -- aggressive fogging with closed inlets raises humidity dangerously, while long light periods increase feed intake but also metabolic heat production. A full factorial design is warranted because all four factors have known two-way interactions in poultry production, and the 16 runs are feasible across house sections.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (weight_gain_g_day, mortality_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| fan_rate_m3_s | 2 | 8 | m3/s | Ventilation fan rate |
| inlet_pct | 20 | 80 | % | Inlet baffle opening percentage |
| fog_interval_min | 5 | 30 | min | Fogging system cycle interval |
| light_hrs | 16 | 23 | hrs | Daily lighting hours |

**Fixed:** birds = 20000, house_m2 = 1200

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| weight_gain_g_day | maximize | g/day |
| mortality_pct | minimize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template poultry_house_ventilation
cd poultry_house_ventilation
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
