# Use Case 305: Essential Oil Therapeutic Blend

## Scenario

You are formulating a therapeutic essential oil blend from four components -- lavender, eucalyptus, peppermint, and tea tree -- diluted at 5% in jojoba carrier oil, and need to maximize both panelist relaxation scores and antimicrobial zone-of-inhibition diameter. The four oil proportions must sum to 100%, and synergy effects between oils (e.g., lavender-eucalyptus for relaxation, tea tree-peppermint for antimicrobial potency) are expected to be significant. A mixture simplex centroid design is ideal because it systematically tests pure components, binary blends, ternary blends, and the overall centroid to efficiently estimate these blending synergies.

**This use case demonstrates:**
- Mixture Simplex Centroid design
- Multi-response analysis (relaxation_score, antimicrobial_zone)
- Mixture modeling with Scheffe polynomials
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| lavender | 0 | 100 | % | Lavender oil proportion |
| eucalyptus | 0 | 100 | % | Eucalyptus oil proportion |
| peppermint | 0 | 100 | % | Peppermint oil proportion |
| tea_tree | 0 | 100 | % | Tea tree oil proportion |

**Fixed:** carrier_oil = jojoba, dilution = 5%

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| relaxation_score | maximize | pts |
| antimicrobial_zone | maximize | mm |

## Why Mixture Simplex Centroid?

- Designed for mixture experiments where factor proportions must sum to a fixed total
- Includes vertices, edge midpoints, face centroids, and the overall centroid of the simplex
- Efficiently estimates blending and synergy effects among mixture components
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template essential_oil_blend
cd essential_oil_blend
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
