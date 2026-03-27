# Use Case 222: Lip Balm Texture Formulation

## Scenario

You are formulating a tube lip balm with vitamin E and need to maximize both moisturizing feel and product firmness by varying beeswax percentage, shea butter percentage, carrier oil type (coconut vs. jojoba), and flavor oil load. High beeswax gives firmness but reduces perceived moisture, while high shea butter softens the stick but can make it too mushy for tube dispensing. A full factorial across these 4 factors -- including one categorical oil type -- captures all interaction effects in just 16 small batches, revealing which ingredient ratios and oil pairings deliver the best texture.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (moisture_score, firmness_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| beeswax_pct | 15 | 30 | % | Beeswax percentage |
| shea_pct | 10 | 30 | % | Shea butter percentage |
| oil_type | coconut | jojoba |  | Carrier oil type |
| flavor_pct | 0.5 | 3.0 | % | Flavor oil percentage |

**Fixed:** vitamin_e = 1pct, container = tube

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| moisture_score | maximize | pts |
| firmness_score | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template lip_balm_texture
cd lip_balm_texture
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
