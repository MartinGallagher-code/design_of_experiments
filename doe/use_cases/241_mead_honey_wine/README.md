# Use Case 241: Mead (Honey Wine) Production

## Scenario

You are making a traditional mead with wildflower honey and Lalvin D-47 yeast and need to maximize honey aroma retention while minimizing fermentation time by adjusting honey-to-water ratio, yeast nutrient additions, and must pH. Honey must is notoriously nutrient-poor, so underpitching nutrients causes stalled fermentations, while excessive nutrients produce fusel alcohols that mask delicate honey character. A Box-Behnken design captures these nonlinear interactions efficiently without testing the extreme combination of maximum honey, minimum nutrients, and lowest pH that would guarantee a stuck ferment.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (honey_character, completion_days)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| honey_ratio_kg_L | 0.3 | 0.5 | kg/L | Honey per liter of water |
| nutrient_g_L | 0.5 | 3.0 | g/L | Yeast nutrient addition |
| ph_target | 3.5 | 4.5 | pH | Must pH target |

**Fixed:** honey_type = wildflower, yeast = d47

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| honey_character | maximize | pts |
| completion_days | minimize | days |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template mead_honey_wine
cd mead_honey_wine
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
