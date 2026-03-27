# Use Case 267: Wind Tunnel Test Setup

## Scenario

You are commissioning a closed-return wind tunnel with a 1x1m test section and need to determine which setup parameters most influence data accuracy and run-to-run repeatability. Five factors -- freestream velocity, model scale ratio, turbulence grid installation, sting mount angle, and wake rake position -- all potentially affect measurement quality, but tunnel time is expensive. A Plackett-Burman design screens all five factors in minimal runs to identify which setup knobs matter most before committing to detailed aerodynamic testing campaigns.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (data_accuracy, repeatability_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| speed_ms | 10 | 50 | m/s | Tunnel freestream velocity |
| model_scale | 0.1 | 0.3 | ratio | Model-to-full scale ratio |
| turb_grid | 0 | 1 | bool | Turbulence grid installed |
| sting_deg | -5 | 15 | deg | Sting mount angle of attack |
| rake_pct | 50 | 150 | %chord | Wake rake position as % of chord |

**Fixed:** tunnel = closed_return, test_section = 1x1m

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| data_accuracy | maximize | pts |
| repeatability_pct | maximize | % |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wind_tunnel_setup
cd wind_tunnel_setup
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
