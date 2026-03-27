# Use Case 105: Greenhouse Climate Control

## Scenario

You are running a 200 m2 greenhouse for cucumber production and need to understand which climate control settings -- ventilation rate, shade cloth coverage, CO2 enrichment, heating setpoint, and misting frequency -- drive plant growth versus energy cost. Adjusting all five parameters simultaneously across a full growing season is impractical and expensive. A Plackett-Burman screening design identifies the two or three most impactful controls in just a handful of runs, so you can focus your energy budget where it matters most.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (growth_index, energy_cost)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| vent_rate | 5 | 30 | ach | Air changes per hour |
| shade_pct | 0 | 60 | % | Shade cloth coverage percentage |
| co2_ppm | 400 | 1200 | ppm | CO2 enrichment level |
| heat_setpoint | 15 | 25 | C | Heating thermostat setpoint |
| mist_freq | 0 | 12 | per_day | Misting cycles per day |

**Fixed:** greenhouse_area = 200m2, crop = cucumber

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| growth_index | maximize | pts |
| energy_cost | minimize | USD/day |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template greenhouse_climate
cd greenhouse_climate
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
