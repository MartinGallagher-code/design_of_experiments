# Use Case 262: Paper Airplane Distance

## Scenario

You are engineering a dart-fold paper airplane from A4 80gsm stock and want to maximize straight-line flight distance while maintaining flight stability. Wingspan, paper-clip nose ballast, and wing dihedral angle each affect the center-of-gravity and aerodynamic stability in nonlinear ways -- too much nose weight kills distance, while too little causes pitch-up stalls. A central composite design fits the curved response surface needed to find the sweet spot, including axial points that probe beyond the initial factor ranges.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (distance_m, stability_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| wingspan_cm | 15 | 30 | cm | Wingspan |
| nose_weight_g | 0 | 3 | g | Paper clip nose ballast |
| dihedral_deg | 0 | 15 | deg | Wing dihedral angle |

**Fixed:** paper = A4_80gsm, fold = dart

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| distance_m | maximize | m |
| stability_score | maximize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template paper_airplane
cd paper_airplane
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
