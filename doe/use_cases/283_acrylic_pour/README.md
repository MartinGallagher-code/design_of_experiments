# Use Case 283: Acrylic Pour Technique

## Scenario

You are perfecting an acrylic pour painting technique using Floetrol medium over a titanium white base, aiming to maximize cell formations and clean color-layer separation. Silicone oil drops per cup, paint consistency (thick to thin), and canvas tilt angle during the pour all interact -- too much silicone with thin paint produces muddy mixing instead of defined cells, while a steep tilt with thick paint causes uneven coverage. A Box-Behnken design avoids these extreme combinations that would waste materials and captures the nonlinear sweet spot where cells form cleanly.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (cell_count, color_separation)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| silicone_drops | 1 | 8 | drops | Silicone oil drops per cup |
| consistency | 1 | 5 | level | Paint consistency (1=thick, 5=thin) |
| tilt_deg | 5 | 30 | deg | Canvas tilt angle during pour |

**Fixed:** medium = floetrol, base = titanium_white

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| cell_count | maximize | per_100cm2 |
| color_separation | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template acrylic_pour
cd acrylic_pour
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
