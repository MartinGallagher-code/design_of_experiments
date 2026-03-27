# Use Case 224: Perfume Longevity & Sillage

## Scenario

You are formulating an oriental eau de parfum and want to maximize both scent longevity (hours of detectable wear) and sillage (projection distance) by adjusting ethanol concentration, fixative percentage, and number of spray applications. Higher alcohol accelerates initial projection but shortens longevity as top notes flash off, while more fixative extends wear but can muffle the scent trail. A central composite design maps these curved fragrance dynamics and its axial points help you explore formulations slightly beyond your initial alcohol and fixative ranges to find the sweet spot.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (longevity_hrs, sillage_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| alcohol_pct | 60 | 85 | % | Ethanol concentration |
| fixative_pct | 1 | 5 | % | Fixative ingredient percentage |
| sprays | 2 | 8 | sprays | Number of spray applications |

**Fixed:** fragrance_type = eau_de_parfum, notes = oriental

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| longevity_hrs | maximize | hrs |
| sillage_score | maximize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template perfume_longevity
cd perfume_longevity
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
