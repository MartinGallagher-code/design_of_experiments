# Use Case 179: Sewing Machine Stitch Quality

## Scenario

You are dialing in a mechanical sewing machine for cotton twill and need to balance upper thread tension, stitch length, and presser foot pressure to maximize stitch evenness while minimizing thread breakage. Too much tension with a short stitch length causes frequent thread breaks, while too little tension with low foot pressure produces loose, uneven seams. A Box-Behnken design captures these nonlinear trade-offs with fewer runs than a central composite, while avoiding the extreme corner settings that would jam the machine.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (stitch_quality, break_rate)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| upper_tension | 2 | 7 | dial | Upper thread tension setting |
| stitch_length_mm | 1.5 | 4.0 | mm | Stitch length |
| foot_pressure | 1 | 5 | level | Presser foot pressure level |

**Fixed:** machine = mechanical, fabric = cotton_twill

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| stitch_quality | maximize | pts |
| break_rate | minimize | per_m |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template sewing_stitch_quality
cd sewing_stitch_quality
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
