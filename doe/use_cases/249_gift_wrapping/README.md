# Use Case 249: Gift Wrapping Efficiency

## Scenario

You are wrapping medium gift boxes in glossy paper and want to maximize visual presentation while minimizing paper waste by adjusting paper overhang, number of tape strips, and curled ribbon strands. Presentation quality has diminishing returns -- extra overhang improves fold neatness up to a point but then creates bulky corners, and excessive tape strips actually detract from appearance. A Box-Behnken design captures these nonlinear trade-offs without testing the wasteful extreme of maximum overhang, maximum tape, and maximum ribbon simultaneously.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (presentation, waste_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| overhang_cm | 2 | 8 | cm | Paper overhang beyond box edges |
| tape_strips | 3 | 8 | strips | Number of tape strips used |
| ribbon_curls | 0 | 6 | curls | Number of curled ribbon strands |

**Fixed:** paper_type = glossy, box_size = medium

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| presentation | maximize | pts |
| waste_pct | minimize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template gift_wrapping
cd gift_wrapping
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
