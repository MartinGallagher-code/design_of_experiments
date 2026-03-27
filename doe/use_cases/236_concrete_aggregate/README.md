# Use Case 236: Aggregate Gradation Optimization

## Scenario

You are designing a Type I cement concrete mix targeting 100 mm slump and need to screen five aggregate properties -- coarse aggregate ratio, sand fineness modulus, maximum aggregate size, fines content, and angularity -- to identify which most affect fresh workability and 28-day compressive strength. Each trial batch requires mixing, slump testing, cylinder casting, and 28 days of curing, making a full factorial impractical. A Plackett-Burman design screens all 5 aggregate parameters in just 8 batches, quickly revealing which gradation variables dominate before committing to a detailed mix optimization.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (workability_score, strength_28d_mpa)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| coarse_pct | 50 | 75 | % | Coarse aggregate percentage |
| fineness_mod | 2.3 | 3.1 | FM | Sand fineness modulus |
| max_size_mm | 10 | 25 | mm | Maximum nominal aggregate size |
| fines_pct | 0 | 5 | % | Material passing 75um sieve |
| angularity | 1 | 5 | level | Coarse aggregate angularity (1=round, 5=crushed) |

**Fixed:** cement = type_I, target_slump = 100mm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| workability_score | maximize | pts |
| strength_28d_mpa | maximize | MPa |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template concrete_aggregate
cd concrete_aggregate
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
