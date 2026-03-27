# Use Case 250: Garage Sale Pricing Strategy

## Scenario

You are running a 6-hour garage sale with 200 items and want to maximize total revenue while minimizing the percentage of unsold items by adjusting starting price (as a fraction of retail), hourly discount rate, and number of directional signs posted in the neighborhood. Revenue responds nonlinearly to pricing -- too high deters early buyers, too low leaves money on the table, and aggressive hourly discounts cannibalize late-sale revenue. A central composite design models these curved pricing dynamics and its axial points help you explore pricing strategies slightly beyond your initial planned range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (revenue_usd, unsold_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| price_multiplier | 0.1 | 0.4 | x_retail | Starting price as fraction of retail |
| discount_per_hr_pct | 0 | 15 | %/hr | Hourly price reduction percentage |
| signs | 2 | 10 | count | Number of directional signs placed |

**Fixed:** duration = 6hrs, items = 200

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| revenue_usd | maximize | USD |
| unsold_pct | minimize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template garage_sale_pricing
cd garage_sale_pricing
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
