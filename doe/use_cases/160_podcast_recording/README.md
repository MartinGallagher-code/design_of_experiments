# Use Case 160: Podcast Recording Quality

## Scenario

You are setting up a podcast recording chain with a large-diaphragm condenser microphone at 48 kHz and want to maximize voice clarity while pushing the noise floor as low as possible. Four parameters -- mic distance, preamp gain, room acoustic treatment percentage, and noise gate threshold -- all interact: close-miking with high gain captures detail but also every room reflection, while aggressive gating clips natural speech dynamics. A full factorial design tests every combination of these four settings, revealing the exact setup that produces broadcast-quality voice recordings in your specific room.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (clarity_score, noise_floor_db)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| mic_dist_cm | 5 | 30 | cm | Microphone distance from mouth |
| gain_db | 20 | 50 | dB | Preamp gain |
| treatment_pct | 0 | 80 | % | Room acoustic treatment coverage |
| gate_db | -60 | -30 | dB | Noise gate threshold |

**Fixed:** mic_type = large_diaphragm_condenser, sample_rate = 48000

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| clarity_score | maximize | pts |
| noise_floor_db | minimize | dB |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template podcast_recording
cd podcast_recording
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
