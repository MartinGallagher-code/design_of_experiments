# Use Case 209: Golf Driver Launch Conditions

## Scenario

You are fitting a golf driver for a 95 mph swing speed using a three-piece ball and need to maximize carry distance while minimizing side spin by adjusting loft angle, shaft flex, and tee height. Launch angle and spin rate interact nonlinearly -- too much loft with a flexible shaft balloons the ball, while too little loft with a stiff shaft produces a low, spinny slice. A Box-Behnken design captures these curved launch dynamics without testing the extreme corners that would produce obviously unusable ball flights.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (carry_yards, side_spin_rpm)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| loft_deg | 8 | 12 | deg | Driver loft angle |
| shaft_flex | 1 | 5 | rating | Shaft flex (1=stiff to 5=senior) |
| tee_height_mm | 40 | 70 | mm | Tee height above ground |

**Fixed:** swing_speed = 95mph, ball = three_piece

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| carry_yards | maximize | yds |
| side_spin_rpm | minimize | rpm |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template golf_driver_launch
cd golf_driver_launch
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
