# Use Case 254: Fish Farm Stocking Density

## Scenario

You are managing a 10-meter Atlantic salmon net pen and need to find the best combination of stocking density, daily feeding rate, water exchange, and aeration level to maximize daily weight gain while keeping monthly mortality below acceptable thresholds. Higher stocking densities increase revenue potential but stress fish and degrade water quality, creating strong interactions between factors. A full factorial design is appropriate because you have only four factors and need to capture all possible interactions -- especially the density-by-aeration interaction that drives dissolved oxygen availability.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (growth_g_day, mortality_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| density_kg_m3 | 10 | 40 | kg/m3 | Stocking density |
| feed_pct_bw | 1 | 4 | %BW | Daily feeding rate |
| exchange_pct | 10 | 50 | %/day | Daily water exchange |
| aeration | low | high |  | Aeration level |

**Fixed:** species = atlantic_salmon, cage = 10m_pen

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| growth_g_day | maximize | g/day |
| mortality_pct | minimize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template fish_farm_stocking
cd fish_farm_stocking
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
