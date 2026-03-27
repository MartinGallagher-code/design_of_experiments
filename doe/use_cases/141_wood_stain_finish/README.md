# Use Case 141: Wood Stain & Finish

## Scenario

You are finishing oak furniture with walnut stain and need to find the combination of stain dilution, number of stain coats, drying time between coats, and number of topcoat layers that maximizes color depth and surface durability. The interactions are complex -- additional stain coats with insufficient drying time can lift previous layers, while heavy topcoat over diluted stain may look washed out. A full factorial design tests every combination of these four factors, revealing exactly how drying time interacts with coat count to produce the richest, most durable finish.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (color_depth, durability)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| stain_dilution | 0 | 50 | % | Stain dilution with mineral spirits |
| num_coats | 1 | 3 | coats | Number of stain coats |
| dry_hrs | 2 | 24 | hrs | Drying time between coats |
| topcoat_coats | 1 | 3 | coats | Number of polyurethane topcoats |

**Fixed:** wood_type = oak, stain_color = walnut

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| color_depth | maximize | pts |
| durability | maximize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wood_stain_finish
cd wood_stain_finish
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
