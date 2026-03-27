# Use Case 221: Nail Polish Durability

## Scenario

You are testing an air-dry nail polish system and want to maximize days before first chip and 5-day gloss retention by adjusting the number of base coats, color coats, and top coat thickness. Adding more layers improves durability up to a point, but excessive thickness causes peeling and extends drying time, while a thin top coat loses gloss quickly under daily wear. A Box-Behnken design models these diminishing-return curves with fewer test manicures than a central composite, and avoids the impractical extreme of maximum layers on every coat.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (days_no_chip, gloss_retention_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| base_coats | 1 | 2 | coats | Number of base coat layers |
| color_coats | 1 | 3 | coats | Number of color coat layers |
| topcoat_thickness | 1 | 3 | mils | Top coat thickness in mils |

**Fixed:** prep = dehydrator, cure = air_dry

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| days_no_chip | maximize | days |
| gloss_retention_pct | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template nail_polish_durability
cd nail_polish_durability
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
