# Use Case 164: Headphone EQ Calibration

## Scenario

You are calibrating a parametric EQ profile for open-back headphones fed by a lossless source and want to maximize listening preference while minimizing ear fatigue over long sessions. Five EQ parameters -- bass boost, mid presence, treble roll-off, virtual soundstage width, and crossfeed percentage -- could all contribute, but subjective A/B listening tests are exhausting and time-limited. A fractional factorial design screens all five parameters in a manageable number of listening sessions, identifying which EQ bands actually drive preference versus which are inaudible distractions.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (preference_score, fatigue_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| bass_boost_db | 0 | 8 | dB | Bass shelf boost at 100Hz |
| mid_presence_db | -3 | 3 | dB | Midrange presence boost at 3kHz |
| treble_rolloff_db | -6 | 0 | dB | Treble rolloff at 10kHz |
| soundstage_pct | 0 | 100 | % | Virtual soundstage widening effect |
| crossfeed_pct | 0 | 60 | % | Crossfeed blending percentage |

**Fixed:** headphone = open_back, source = lossless

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| preference_score | maximize | pts |
| fatigue_score | minimize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template headphone_eq
cd headphone_eq
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
