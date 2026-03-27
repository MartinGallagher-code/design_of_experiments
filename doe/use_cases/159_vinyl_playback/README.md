# Use Case 159: Vinyl Playback Optimization

## Scenario

You are setting up a belt-drive turntable with a moving-magnet cartridge and want to maximize audio fidelity while minimizing surface noise by adjusting tracking force, anti-skate compensation, and stylus overhang alignment. These parameters are interdependent -- incorrect anti-skate at a given tracking force causes channel imbalance and accelerated groove wear, while misaligned overhang introduces distortion at the inner grooves. A Box-Behnken design efficiently maps these curved relationships without testing the extreme corners where stylus mistracking could damage your records.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (fidelity_score, surface_noise)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| tracking_force_g | 1.2 | 2.2 | g | Stylus tracking force |
| anti_skate_g | 0.5 | 2.0 | g | Anti-skate force |
| overhang_mm | 14 | 18 | mm | Cartridge overhang distance |

**Fixed:** turntable = belt_drive, cartridge_type = moving_magnet

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| fidelity_score | maximize | pts |
| surface_noise | minimize | dB |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template vinyl_playback
cd vinyl_playback
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
