# Use Case 303: Pharmaceutical Tablet Compression

## Scenario

You are developing a 500mg oral tablet formulation and need to simultaneously optimize crushing hardness, 30-minute dissolution rate, and friability -- all of which have strict regulatory bounds. Compression force, granule size, binder concentration, and lubricant percentage interact in complex ways: more binder and force increase hardness but can retard dissolution, while lubricant improves ejection but weakens the tablet matrix. A D-optimal design is the right choice because it maximizes statistical efficiency for the specific polynomial model while respecting the constrained response bounds required for pharmaceutical Quality by Design.

**This use case demonstrates:**
- D-Optimal design
- Multi-response analysis (hardness, dissolution_rate, friability)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| compression_force | 5 | 20 | kN | Tablet press compression force |
| granule_size | 50 | 200 | microns | Mean granule particle size |
| binder_pct | 2 | 8 | % | Binder concentration in formulation |
| lubricant_pct | 0.5 | 2 | % | Lubricant concentration in formulation |

**Fixed:** active_ingredient = 500mg

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| hardness | maximize | N |
| dissolution_rate | maximize | % |
| friability | minimize | % |

## Why D-Optimal?

- An algorithmically generated design that maximizes the determinant of the information matrix
- Highly flexible -- can handle irregular design spaces, mixture constraints, or custom models
- Produces the most statistically efficient design for a specified model with a given number of runs
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template pharmaceutical_tablet
cd pharmaceutical_tablet
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
