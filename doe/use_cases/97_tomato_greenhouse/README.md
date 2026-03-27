# Use Case 97: Tomato Greenhouse Yield

## Scenario

You are growing Roma tomatoes in a controlled greenhouse with 16-hour supplemental lighting and need to maximize fruit yield per plant while minimizing blossom end rot (BER), a calcium-deficiency disorder. Daytime temperature, relative humidity, and irrigation frequency all interact nonlinearly -- high temperatures boost growth but exacerbate BER if humidity or watering is wrong. A central composite design with axial points maps the full response surface, finding the climate and irrigation sweet spot where yield is high and BER stays below acceptable thresholds.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (yield_kg, ber_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| day_temp | 22 | 32 | C | Daytime greenhouse temperature |
| humidity_pct | 50 | 85 | % | Relative humidity |
| irrigation_freq | 2 | 6 | per_day | Irrigation cycles per day |

**Fixed:** variety = roma, light_hours = 16

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| yield_kg | maximize | kg/plant |
| ber_pct | minimize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template tomato_greenhouse
cd tomato_greenhouse
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
