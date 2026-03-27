# Use Case 178: Knitting Gauge & Tension

## Scenario

You are knitting a garment in merino wool stockinette and need to hit a target stitch gauge while maximizing fabric drape by adjusting needle diameter, yarn weight category, and tension dial setting. Gauge and drape respond nonlinearly to these parameters -- a slightly larger needle can dramatically open up fabric hand, but too large creates holes. A central composite design lets you model these curved relationships and even predict behavior at axial points beyond the initial factor ranges.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (gauge_sts_10cm, drape_score)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| needle_mm | 3.0 | 6.0 | mm | Knitting needle diameter |
| yarn_weight | 1 | 5 | category | Yarn weight category (1=fingering, 5=bulky) |
| tension_setting | 3 | 9 | dial | Machine tension dial (or hand tension 1-10) |

**Fixed:** fiber = merino_wool, stitch_pattern = stockinette

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| gauge_sts_10cm | maximize | sts/10cm |
| drape_score | maximize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template knitting_tension
cd knitting_tension
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
