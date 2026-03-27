# Use Case 137: Interior Paint Finish Quality

## Scenario

You are painting interior drywall with latex eggshell paint and want to maximize coverage score while minimizing drying time by tuning coat thickness (in mils), ambient humidity, and paint dilution ratio. Thick coats in high humidity can cause sagging and dramatically extend dry time, while over-diluted paint requires extra coats. A Box-Behnken design efficiently models these curved trade-offs with three factors, avoiding the impractical extreme of a thick, diluted coat applied in a steam room.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (coverage_score, dry_time_min)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| coat_mils | 3 | 8 | mils | Wet coat thickness in mils |
| humidity_pct | 30 | 70 | % | Room relative humidity |
| dilution_pct | 0 | 15 | % | Water dilution percentage for latex paint |

**Fixed:** paint_type = latex_eggshell, surface = drywall

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| coverage_score | maximize | pts |
| dry_time_min | minimize | min |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template paint_finish_quality
cd paint_finish_quality
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
