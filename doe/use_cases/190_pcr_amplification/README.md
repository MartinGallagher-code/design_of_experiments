# Use Case 190: PCR Amplification Efficiency

## Scenario

You are optimizing a Taq polymerase PCR reaction and need to maximize target band yield while eliminating non-specific amplification by adjusting annealing temperature, primer concentration, MgCl2 concentration, and cycle count. The interaction between MgCl2 and annealing temperature is critical -- excess magnesium at low annealing temperatures promotes mispriming, while too few cycles with low primer concentration yields faint bands. A full factorial design across these 4 factors ensures you capture every two-way interaction, which is essential given that PCR reagent interactions are well-known but template-dependent.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (yield_score, specificity)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| anneal_temp_c | 52 | 65 | C | Annealing step temperature |
| primer_nm | 200 | 600 | nM | Primer concentration |
| mgcl2_mm | 1.0 | 3.0 | mM | MgCl2 concentration |
| cycles | 25 | 40 | cycles | Number of PCR cycles |

**Fixed:** polymerase = taq, template_ng = 50

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| yield_score | maximize | pts |
| specificity | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template pcr_amplification
cd pcr_amplification
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
