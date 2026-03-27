# Use Case 202: Mortise & Tenon Fit

## Scenario

You are cutting through-tenon joints in white oak and need to maximize pull-apart strength while keeping assembly easy by tuning the tenon-to-mortise gap tolerance, shoulder depth, and adhesive viscosity. A tight tolerance with high-viscosity glue makes assembly nearly impossible, while a loose tolerance with thin glue produces a weak, starved joint. A Box-Behnken design models these nonlinear trade-offs with fewer test joints than a central composite, and avoids the impractical extreme corners where the tightest fit meets the thickest glue.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (pull_strength_kn, assembly_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| tolerance_mm | 0.05 | 0.5 | mm | Tenon-to-mortise gap tolerance |
| shoulder_mm | 3 | 10 | mm | Tenon shoulder depth |
| glue_viscosity | 1000 | 8000 | cP | Adhesive viscosity |

**Fixed:** joint_type = through_tenon, wood = white_oak

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| pull_strength_kn | maximize | kN |
| assembly_score | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template mortise_tenon_fit
cd mortise_tenon_fit
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
