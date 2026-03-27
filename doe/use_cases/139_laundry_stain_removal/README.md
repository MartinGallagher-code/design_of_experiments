# Use Case 139: Laundry Stain Removal

## Scenario

You are optimizing a wash cycle for cotton garments with set-in stains and need to determine which of six laundry parameters -- water temperature, detergent dose, pre-soak time, agitation level, oxygen bleach amount, and spin speed -- most strongly affect stain removal while preserving fabric integrity. Testing all 64 combinations at two levels would burn through an impractical number of identically stained test swatches. A Plackett-Burman screening design identifies the critical wash settings in just 12 loads, separating the factors worth optimizing from those you can leave at default.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (stain_removal_pct, fabric_wear)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| water_temp_c | 20 | 60 | C | Wash water temperature |
| detergent_ml | 15 | 60 | mL | Detergent dose per load |
| soak_min | 0 | 30 | min | Pre-soak duration |
| agitation | 1 | 5 | level | Agitation intensity level |
| bleach_ml | 0 | 30 | mL | Oxygen bleach amount |
| spin_rpm | 600 | 1400 | rpm | Final spin speed |

**Fixed:** load_size = medium, fabric = cotton

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| stain_removal_pct | maximize | % |
| fabric_wear | minimize | pts |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template laundry_stain_removal
cd laundry_stain_removal
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
