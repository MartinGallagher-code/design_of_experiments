# Use Case 232: Seismograph Network Placement

## Scenario

You are deploying an 8-station broadband seismograph network and need to maximize earthquake event detection while minimizing false triggers by adjusting station spacing, sensor burial depth, sampling rate, and highpass filter cutoff. Wider spacing misses small local events but reduces cross-station noise correlation that causes false triggers, while a low-frequency filter cutoff captures deep events but admits more cultural noise. A full factorial across these 4 factors captures all interactions in 16 simulation runs, which is essential because spacing-filter and burial-sampling interactions are poorly documented for this site geology.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (detection_pct, false_trigger_day)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| spacing_km | 5 | 25 | km | Station spacing |
| burial_m | 0 | 3 | m | Sensor burial depth |
| sample_hz | 40 | 200 | Hz | Sampling rate |
| filter_hz | 0.5 | 10 | Hz | Highpass filter cutoff |

**Fixed:** sensor = broadband, network_size = 8_stations

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| detection_pct | maximize | % |
| false_trigger_day | minimize | per_day |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template seismograph_placement
cd seismograph_placement
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
