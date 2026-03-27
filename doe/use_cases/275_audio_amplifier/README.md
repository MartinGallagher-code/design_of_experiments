# Use Case 275: Audio Amplifier Biasing

## Scenario

You are biasing a Class AB audio power amplifier driving an 8-ohm load and want to minimize total harmonic distortion plus noise while maximizing dynamic headroom above rated power. Output stage quiescent bias current, per-rail supply voltage, and negative feedback amount create a classic trade-off: higher bias reduces crossover distortion but wastes power as heat, while more feedback lowers THD but can compromise transient headroom and stability. A Box-Behnken design is ideal because it avoids the extreme corner of maximum bias with maximum supply voltage, which would exceed the output transistors' safe operating area.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (thd_pct, headroom_db)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| bias_ma | 10 | 100 | mA | Output stage quiescent bias current |
| supply_v | 15 | 35 | V | Power supply voltage (per rail) |
| feedback_db | 10 | 30 | dB | Negative feedback amount |

**Fixed:** topology = class_AB, load = 8ohm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| thd_pct | minimize | % |
| headroom_db | maximize | dB |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template audio_amplifier
cd audio_amplifier
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
