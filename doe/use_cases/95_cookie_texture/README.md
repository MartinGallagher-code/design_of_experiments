# Use Case 95: Cookie Texture Optimization

## Scenario

You are engineering the perfect chewy cookie and need to understand how butter percentage, brown-to-white sugar ratio, egg count, and baking time control the chewiness-versus-spread trade-off. Brown sugar's hygroscopic nature promotes chewiness while more butter increases spread, and these effects interact with egg protein and bake time in nonlinear ways. A central composite design maps the full curvature of the texture response surface with axial points, pinpointing the formulation that maximizes chewiness and spread ratio simultaneously.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (chewiness_score, spread_ratio)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| butter_pct | 30 | 50 | % | Butter as percentage of flour weight |
| brown_sugar_ratio | 0 | 100 | % | Brown sugar as percentage of total sugar |
| eggs | 1 | 3 | count | Number of eggs per batch |
| bake_time | 8 | 14 | min | Baking time at 175C |

**Fixed:** oven_temp = 175, flour_type = all_purpose

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| chewiness_score | maximize | pts |
| spread_ratio | maximize | ratio |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template cookie_texture
cd cookie_texture
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
