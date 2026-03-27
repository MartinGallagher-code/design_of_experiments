# Use Case 258: Beach Nourishment Longevity

## Scenario

You are designing a beach nourishment project for a coastline with moderate wave energy and southward longshore drift, and need to determine which of five design parameters -- sand grain size, berm width, dune crest height, groin spacing, and fill volume -- most strongly influence sand retention lifespan and storm resilience. Full characterization of all five factors simultaneously would require prohibitively many field monitoring campaigns. A Plackett-Burman screening design efficiently identifies the dominant factors in just a handful of runs, so you can focus detailed optimization on the parameters that actually matter.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (retention_yrs, storm_resilience)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| grain_mm | 0.3 | 1.0 | mm | Median sand grain size |
| berm_width_m | 20 | 60 | m | Design berm width |
| dune_height_m | 2 | 5 | m | Constructed dune crest height |
| groin_spacing_m | 100 | 400 | m | Groin structure spacing |
| volume_m3_m | 30 | 100 | m3/m | Sand volume per meter of shoreline |

**Fixed:** wave_climate = moderate, longshore_drift = southward

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| retention_yrs | maximize | yrs |
| storm_resilience | maximize | pts |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template beach_nourishment
cd beach_nourishment
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
