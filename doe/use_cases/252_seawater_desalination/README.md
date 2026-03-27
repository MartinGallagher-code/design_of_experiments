# Use Case 252: Seawater Desalination Efficiency

## Scenario

You are optimizing a reverse-osmosis desalination plant using polyamide membranes treating seawater at 35,000 ppm salinity. You need to balance permeate flux against specific energy consumption by tuning feed pressure, water temperature, and recovery ratio, where pushing recovery too high risks membrane fouling and scaling. A central composite design is ideal here because the relationship between pressure, temperature, and flux is nonlinear, requiring a quadratic model to find the true optimum operating window.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (permeate_lmh, sec_kwh_m3)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| pressure_bar | 50 | 70 | bar | Feed pressure |
| feed_temp_c | 15 | 30 | C | Feed water temperature |
| recovery_pct | 35 | 55 | % | Target water recovery percentage |

**Fixed:** membrane = RO_polyamide, salinity = 35000ppm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| permeate_lmh | maximize | L/m2/hr |
| sec_kwh_m3 | minimize | kWh/m3 |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template seawater_desalination
cd seawater_desalination
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
