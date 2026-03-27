# Use Case 195: Enzyme Kinetics Assay

## Scenario

You are characterizing alkaline phosphatase kinetics in Tris buffer and need to maximize the initial reaction rate while minimizing substrate inhibition by varying substrate concentration, enzyme loading, buffer pH, and temperature. Alkaline phosphatase exhibits substrate inhibition at high concentrations and denatures above its thermal optimum, and pH-temperature interactions shift the enzyme's active-site conformation. A full factorial across 4 factors at 2 levels captures all pairwise interactions in 16 affordable microplate assay runs.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (reaction_rate, inhibition_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| substrate_mm | 0.1 | 10 | mM | Substrate concentration |
| enzyme_ug | 1 | 20 | ug | Enzyme amount |
| ph | 5 | 9 | pH | Buffer pH |
| temp_c | 20 | 45 | C | Reaction temperature |

**Fixed:** enzyme = alkaline_phosphatase, buffer = tris

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| reaction_rate | maximize | umol/min |
| inhibition_pct | minimize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template enzyme_kinetics
cd enzyme_kinetics
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
