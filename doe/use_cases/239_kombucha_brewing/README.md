# Use Case 239: Kombucha Brewing Balance

## Scenario

You are brewing black tea kombucha with a mature SCOBY and want to maximize carbonation and flavor complexity by adjusting sugar concentration, primary fermentation duration, and tea leaf strength. The SCOBY metabolizes sugar into organic acids and CO2 nonlinearly -- too much sugar with a long ferment produces vinegar, while too little sugar with weak tea yields flat, insipid kombucha. A Box-Behnken design models these curved fermentation dynamics without testing the extreme corners that would produce either undrinkable vinegar or essentially sweet tea.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (fizz_score, flavor_complexity)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| sugar_g_L | 50 | 100 | g/L | Sugar concentration |
| ferm_days | 5 | 21 | days | Primary fermentation duration |
| tea_g_L | 5 | 15 | g/L | Tea leaf concentration |

**Fixed:** tea_type = black, scoby_age = mature

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| fizz_score | maximize | pts |
| flavor_complexity | maximize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template kombucha_brewing
cd kombucha_brewing
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
