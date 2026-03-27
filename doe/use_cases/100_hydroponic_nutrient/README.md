# Use Case 100: Hydroponic Nutrient Solution

## Scenario

You are growing butterhead lettuce in a nutrient film technique (NFT) hydroponic system and need to determine which of six nutrient solution parameters -- nitrogen, phosphorus, potassium, pH, EC, and calcium -- have the greatest impact on growth rate and leaf color. Each batch of nutrient solution takes a full grow cycle to evaluate, so you need an efficient screening design. A Plackett-Burman design lets you test all six factors in just 12 runs, quickly identifying the dominant nutrients before investing in a detailed optimization study.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (growth_rate, color_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| nitrogen_ppm | 100 | 250 | ppm | Nitrogen concentration |
| phosphorus_ppm | 30 | 80 | ppm | Phosphorus concentration |
| potassium_ppm | 150 | 350 | ppm | Potassium concentration |
| ph_level | 5.5 | 6.5 | pH | Solution pH level |
| ec_level | 1.0 | 2.5 | mS/cm | Electrical conductivity |
| calcium_ppm | 100 | 250 | ppm | Calcium concentration |

**Fixed:** crop = butterhead_lettuce, system = NFT

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| growth_rate | maximize | g/day |
| color_score | maximize | pts |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template hydroponic_nutrient
cd hydroponic_nutrient
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
