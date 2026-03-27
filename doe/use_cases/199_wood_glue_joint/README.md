# Use Case 199: Wood Glue Joint Strength

## Scenario

You are gluing red oak panels with PVA adhesive and need to maximize shear strength while minimizing cure time by adjusting glue spread rate, clamping pressure, and open assembly time. Too much glue starves the joint during squeeze-out under high clamp pressure, while too little open time prevents adequate tack, and excessive open time lets the glue skin over. A Box-Behnken design efficiently models these nonlinear interactions without running the impractical corner combination of maximum spread, maximum pressure, and maximum open time simultaneously.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (shear_strength_mpa, cure_hrs)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| spread_g_m2 | 100 | 250 | g/m2 | Glue spread rate |
| clamp_psi | 50 | 250 | psi | Clamping pressure |
| open_time_min | 1 | 10 | min | Open assembly time before clamping |

**Fixed:** glue_type = PVA, wood = red_oak

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| shear_strength_mpa | maximize | MPa |
| cure_hrs | minimize | hrs |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wood_glue_joint
cd wood_glue_joint
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
