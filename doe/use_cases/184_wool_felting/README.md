# Use Case 184: Wool Felting Process

## Scenario

You are wet-felting a merino wool blend into a medium-weight textile and need to screen five process variables -- water temperature, agitation time, soap concentration, merino percentage, and compression cycles -- to maximize felt density while controlling dimensional shrinkage. Each felting trial consumes material and takes significant hands-on time, so a full 32-run factorial is impractical. A fractional factorial efficiently identifies which parameters dominate shrinkage and firmness while assuming three-way and higher interactions are negligible.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (shrinkage_pct, density_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| water_temp_c | 40 | 80 | C | Water temperature |
| agitation_min | 5 | 30 | min | Agitation time |
| soap_ml_L | 1 | 10 | mL/L | Soap concentration |
| merino_pct | 50 | 100 | % | Merino wool percentage in blend |
| compressions | 10 | 50 | cycles | Manual compression cycles |

**Fixed:** technique = wet_felting, thickness = medium

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| shrinkage_pct | minimize | % |
| density_score | maximize | pts |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wool_felting
cd wool_felting
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
