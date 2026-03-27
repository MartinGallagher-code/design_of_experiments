# Use Case 157: Guitar String Tone Optimization

## Scenario

You are dialing in the tone of a solid-body electric guitar in standard tuning and want to maximize both brightness and sustain by adjusting string gauge, action height at the 12th fret, and pickup height. These setup parameters interact -- heavier strings increase sustain but raise action requirements, and moving pickups closer to the strings boosts output at the cost of magnetic damping that kills sustain. A Box-Behnken design maps these curved trade-offs without testing extreme setups like heavy gauge strings at minimum action, which would cause unplayable fret buzz.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (brightness, sustain_sec)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| gauge_thou | 9 | 13 | thou | High E string gauge in thousandths of an inch |
| action_mm | 1.5 | 3.0 | mm | String action height at 12th fret |
| pickup_mm | 2 | 5 | mm | Pickup distance from strings |

**Fixed:** guitar_type = solid_body, tuning = standard

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| brightness | maximize | pts |
| sustain_sec | maximize | sec |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template guitar_string_tone
cd guitar_string_tone
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
