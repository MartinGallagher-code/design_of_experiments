# Use Case 231: Rock Thin Section Preparation

## Scenario

You are preparing 30 um petrographic thin sections of granite and need to maximize polarized-light optical clarity while minimizing thickness variation across the section by adjusting grinding wheel speed, epoxy cure time, and final polishing grit. Grinding too fast on under-cured epoxy tears mineral grains from the mount, while grinding too slowly wastes time and can cause uneven wear. A Box-Behnken design captures these nonlinear interactions without the extreme combination of maximum speed on minimum-cured samples, which would destroy the thin section.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (optical_clarity, thickness_variation_um)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| grind_rpm | 100 | 400 | rpm | Grinding wheel speed |
| cure_hrs | 12 | 48 | hrs | Epoxy cure time before grinding |
| polish_grit | 600 | 1200 | grit | Final polishing grit |

**Fixed:** rock_type = granite, target_um = 30

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| optical_clarity | maximize | pts |
| thickness_variation_um | minimize | um |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template rock_thin_section
cd rock_thin_section
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
