# Use Case 204: Steam Bending Parameters

## Scenario

You are steam-bending 20 mm white ash for chair backs and need to achieve the tightest possible bend radius while minimizing cracking by adjusting steaming duration, initial wood moisture content, and bending speed. The plasticization of lignin is highly nonlinear -- too short a steam with dry wood causes brittle fracture, while over-steaming wastes time and can weaken fibers. A Box-Behnken design models these curved relationships efficiently while avoiding the extreme corner combination of minimum steam time, minimum moisture, and maximum bending speed that would guarantee failure.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (min_radius_cm, crack_rate_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| steam_min | 30 | 120 | min | Steaming duration |
| moisture_pct | 15 | 30 | % | Wood moisture content |
| bend_speed | 1 | 5 | deg/sec | Bending rate in degrees per second |

**Fixed:** wood_species = white_ash, thickness_mm = 20

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| min_radius_cm | minimize | cm |
| crack_rate_pct | minimize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wood_bending
cd wood_bending
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
