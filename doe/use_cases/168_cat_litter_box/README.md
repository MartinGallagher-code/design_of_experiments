# Use Case 168: Cat Litter Box Management

## Scenario

You are managing litter boxes for a two-cat household using clumping clay litter and want to maximize odor control and box usage rate by tuning litter depth, daily cleaning frequency, and box surface area. Cats are notoriously finicky -- a box that is too small or too shallow gets avoided, leading to house-soiling problems, while excessive cleaning frequency wastes time without proportional odor benefit. A central composite design captures these nonlinear behavioral responses, letting you find the minimum-effort setup that keeps both cats consistently using the box.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (odor_control, usage_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| litter_depth_cm | 3 | 10 | cm | Litter fill depth |
| clean_per_day | 1 | 3 | per_day | Scooping frequency per day |
| box_area_cm2 | 1500 | 4000 | cm2 | Litter box floor area |

**Fixed:** litter_type = clumping_clay, cats = 2

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| odor_control | maximize | pts |
| usage_pct | maximize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template cat_litter_box
cd cat_litter_box
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
