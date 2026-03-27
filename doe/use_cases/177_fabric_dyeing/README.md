# Use Case 177: Natural Fabric Dyeing

## Scenario

You are dyeing alum-mordanted cotton muslin with a natural dye and want to maximize color depth (K/S value) and wash fastness by tuning dye concentration, bath temperature, and immersion time. The relationship between these process parameters and dye uptake is known to be nonlinear -- color saturates at high concentrations and fastness can degrade at extreme temperatures. A Box-Behnken design fits a full quadratic response surface while avoiding the extreme corner conditions that would scorch fabric or waste expensive natural dye extract.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (color_depth, wash_fastness)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| dye_concentration_pct | 5 | 30 | %WOF | Dye weight as % of fabric weight |
| bath_temp_c | 40 | 95 | C | Dye bath temperature |
| immersion_min | 30 | 120 | min | Immersion time |

**Fixed:** fabric = cotton_muslin, mordant = alum

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| color_depth | maximize | K/S |
| wash_fastness | maximize | grade |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template fabric_dyeing
cd fabric_dyeing
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
