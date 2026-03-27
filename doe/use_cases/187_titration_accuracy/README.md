# Use Case 187: Titration Accuracy Optimization

## Scenario

You are performing an acid-base titration of HCl with NaOH and need to maximize endpoint precision while minimizing reagent overshoot by tuning burette drop size, magnetic stirrer speed, and indicator concentration. The precision-waste trade-off is nonlinear -- very small drops improve accuracy but slow throughput, while fast stirring can splash and cause erratic readings at high indicator concentrations. A Box-Behnken design models these quadratic effects efficiently without testing the extreme corners where the combination of maximum drop size, maximum stir rate, and maximum indicator would produce unreliable data.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (precision_pct, reagent_waste_ml)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| drop_size_ul | 10 | 100 | uL | Burette drop size near endpoint |
| stir_rpm | 100 | 600 | rpm | Magnetic stirrer speed |
| indicator_pct | 0.05 | 0.5 | % | Indicator solution concentration |

**Fixed:** analyte = HCl, titrant = NaOH

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| precision_pct | maximize | % |
| reagent_waste_ml | minimize | mL |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template titration_accuracy
cd titration_accuracy
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
