# Use Case 111: Ergonomic Workstation Setup

## Scenario

You are setting up an ergonomic workstation with a 27-inch monitor and adjustable chair, and need to find the sweet spot across desk height, monitor distance, chair recline angle, and break frequency that maximizes both comfort and productivity over a full workday. Each parameter has a nonlinear effect -- too close to the monitor causes eye strain, too far reduces readability -- so you need curvature estimates. A central composite design fits a full quadratic model for all four factors, letting you locate the optimal configuration precisely.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (comfort_score, productivity_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| desk_height_cm | 65 | 80 | cm | Desk surface height |
| monitor_dist_cm | 50 | 80 | cm | Distance from eyes to monitor |
| chair_recline_deg | 90 | 115 | deg | Chair backrest recline angle |
| break_freq_min | 25 | 90 | min | Minutes between standing breaks |

**Fixed:** monitor_size = 27in, chair_type = ergonomic

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| comfort_score | maximize | pts |
| productivity_pct | maximize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template ergonomic_workstation
cd ergonomic_workstation
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
