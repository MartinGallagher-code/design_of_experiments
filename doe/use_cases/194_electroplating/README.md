# Use Case 194: Electroplating Thickness Control

## Scenario

You are nickel-plating mild steel parts and need to screen five process variables -- current density, bath temperature, plating time, bath pH, and agitation speed -- to identify which ones most affect coating thickness and tape-test adhesion. Each plating run ties up the electrochemical cell and requires fresh bath chemistry checks, so minimizing the number of runs is essential. A Plackett-Burman design screens all 5 factors in just 8 runs, efficiently separating the critical main effects before committing to a more detailed optimization study.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (thickness_um, adhesion_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| current_density | 1 | 10 | A/dm2 | Cathode current density |
| bath_temp_c | 20 | 55 | C | Plating bath temperature |
| time_min | 5 | 60 | min | Plating duration |
| bath_ph | 2 | 5 | pH | Bath pH |
| agitation_rpm | 0 | 200 | rpm | Bath agitation speed |

**Fixed:** metal = nickel, substrate = mild_steel

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| thickness_um | maximize | um |
| adhesion_score | maximize | pts |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template electroplating
cd electroplating
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
