# Use Case 88: Coffee Brewing Extraction

## Scenario

You are dialing in a pour-over coffee recipe with medium-roast beans and want to maximize cupping flavor score while minimizing perceived bitterness. The 4 extraction variables -- grind size (200-800 microns), water temperature, brew time, and coffee-to-water ratio -- have sweet spots where under-extraction (sour) transitions to over-extraction (bitter). A central composite design is ideal because it adds axial points beyond the factorial range, capturing the full curvature of the extraction response surface to pinpoint the optimal brew parameters.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (flavor_score, bitterness)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| grind_size | 200 | 800 | um | Coffee grind particle size in microns |
| water_temp | 85 | 96 | C | Water temperature in Celsius |
| brew_time | 180 | 300 | sec | Total brew time in seconds |
| ratio | 14 | 18 | g/g | Coffee-to-water ratio (grams water per gram coffee) |

**Fixed:** roast_level = medium, water_tds = 120

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| flavor_score | maximize | pts |
| bitterness | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template coffee_brewing
cd coffee_brewing
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
