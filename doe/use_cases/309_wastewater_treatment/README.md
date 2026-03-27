# Use Case 309: Wastewater Treatment Optimization

## Scenario

You are optimizing an activated sludge wastewater treatment plant rated at 10,000 m3/day and need to maximize BOD removal efficiency while minimizing settled sludge volume. Seven process parameters -- pH, hydraulic retention time, aeration rate, flocculant dose, temperature, mixing intensity, and filter media grade -- all potentially affect treatment performance, but pilot-scale trials are expensive and time-consuming. A Plackett-Burman design screens all seven factors in just 8 runs to identify which operational knobs have the greatest impact on effluent quality, before committing to detailed optimization of the critical few.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (bod_removal, sludge_volume)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| ph_level | 6 | 9 | pH | Treatment pH level |
| retention_time | 4 | 12 | hours | Hydraulic retention time |
| aeration_rate | 2 | 6 | L/min | Aeration rate |
| flocculant_dose | 10 | 50 | mg/L | Flocculant dosage |
| temperature | 15 | 30 | C | Wastewater temperature |
| mixing_intensity | low | high |  | Mixing intensity setting |
| filter_grade | coarse | fine |  | Filter media grade |

**Fixed:** plant_capacity = 10000 m3/day

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| bod_removal | maximize | % |
| sludge_volume | minimize | mL/L |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 7 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wastewater_treatment
cd wastewater_treatment
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
