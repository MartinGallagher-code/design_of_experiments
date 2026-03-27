# Use Case 205: Sandpaper Grit Progression

## Scenario

You are hand-sanding walnut to a 220-grit finish and need to screen five variables -- starting grit, number of grit progression steps, sanding pressure, passes per grit, and dust extraction -- to maximize surface quality while minimizing total sanding time. Testing all 32 combinations would consume an impractical amount of walnut stock and labor. A fractional factorial identifies which factors (e.g., starting grit vs. number of passes) dominate finish quality in half the runs, assuming higher-order interactions between sanding parameters are negligible.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (finish_score, time_min)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| start_grit | 60 | 120 | grit | Starting sandpaper grit |
| grit_steps | 2 | 5 | steps | Number of grit progression steps |
| pressure_kg | 0.5 | 3.0 | kg | Hand sanding pressure |
| passes | 3 | 10 | passes | Passes per grit level |
| dust_extract | 0 | 1 | bool | Dust extraction on/off |

**Fixed:** wood = walnut, final_grit = 220

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| finish_score | maximize | pts |
| time_min | minimize | min |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template sandpaper_progression
cd sandpaper_progression
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
