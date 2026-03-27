# Use Case 93: Salad Dressing Emulsion Stability

## Scenario

You are formulating a vinaigrette that must stay emulsified on the shelf for hours without separating, while also scoring well on taste panels. There are 6 ingredients and process variables to investigate -- oil ratio, vinegar acidity, mustard (as emulsifier), egg yolks, blending speed, and mixing temperature -- and each batch takes time to prepare and evaluate. A Plackett-Burman screening design identifies which of these factors most affect emulsion stability and taste in just 8 batches, before you invest in fine-tuning the recipe.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (stability_hrs, taste_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| oil_ratio | 50 | 80 | % | Oil percentage of total liquid |
| vinegar_acidity | 4 | 7 | % | Vinegar acidity percentage |
| mustard_g | 2 | 15 | g | Mustard amount (emulsifier) |
| egg_yolk_count | 0 | 3 | count | Number of egg yolks |
| blend_speed | 5000 | 20000 | rpm | Immersion blender speed |
| mix_temp | 5 | 25 | C | Ingredient temperature at mixing |

**Fixed:** total_volume_ml = 500, salt_g = 3

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| stability_hrs | maximize | hrs |
| taste_score | maximize | pts |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template salad_dressing_emulsion
cd salad_dressing_emulsion
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
