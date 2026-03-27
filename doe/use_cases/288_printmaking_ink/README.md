# Use Case 288: Printmaking Ink Viscosity

## Scenario

You are mixing relief printmaking ink for BFK Rives paper and need to determine which of five formulation and process variables -- tack level, linseed oil percentage, pigment concentration, viscosity modifier amount, and roller pressure -- most strongly influence image clarity and ink transfer efficiency. Adjusting all five simultaneously in a full factorial would require 32 trial prints, consuming expensive paper and ink. A Plackett-Burman screening design identifies the dominant factors in just a handful of pulls, so you can focus detailed formulation work on what actually matters.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (print_quality, transfer_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| tack_level | 2 | 8 | level | Ink tack rating |
| oil_pct | 20 | 50 | % | Linseed oil percentage |
| pigment_pct | 15 | 35 | % | Pigment concentration |
| modifier_pct | 0 | 10 | % | Viscosity modifier |
| roller_pressure | 1 | 5 | level | Roller pressure setting |

**Fixed:** method = relief, paper = BFK_rives

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| print_quality | maximize | pts |
| transfer_pct | maximize | % |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template printmaking_ink
cd printmaking_ink
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
