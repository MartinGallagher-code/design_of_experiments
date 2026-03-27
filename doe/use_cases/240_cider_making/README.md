# Use Case 240: Hard Cider Fermentation

## Scenario

You are fermenting a mixed-apple cider with champagne yeast and want to maximize apple flavor clarity and ABV by adjusting yeast pitch rate, fermentation temperature, and supplemental sugar addition. Temperature and pitch rate interact nonlinearly -- low pitch rates at warm temperatures stress yeast into producing off-flavors, while high sugar with cold fermentation risks stuck fermentation. A central composite design maps these curved fermentation surfaces and its axial points help you explore temperatures and pitch rates slightly beyond your initial range to find the best balance of flavor and alcohol.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (flavor_clarity, abv_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| pitch_rate_g_L | 0.5 | 2.0 | g/L | Yeast pitch rate |
| ferm_temp_c | 12 | 22 | C | Fermentation temperature |
| sugar_add_g_L | 0 | 50 | g/L | Supplemental sugar addition |

**Fixed:** apple_variety = mixed_cider, yeast = champagne

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| flavor_clarity | maximize | pts |
| abv_pct | maximize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template cider_making
cd cider_making
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
