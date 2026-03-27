# Use Case 201: Wood Finish Drying Conditions

## Scenario

You are applying polyurethane finish to cherry wood and need to minimize drying time to tack-free while maximizing cured film hardness by controlling room temperature, relative humidity, fan-assisted air circulation, and wet coat thickness. High humidity slows solvent evaporation, thick coats extend dry time but can build a harder final film, and fan circulation interacts differently at low versus high temperatures. A full factorial design across these 4 factors (including one categorical on/off factor) provides complete interaction information in just 16 runs, which is manageable for a finishing shop.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (dry_time_hrs, hardness_h)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| temp_c | 15 | 30 | C | Drying room temperature |
| humidity_pct | 30 | 70 | % | Relative humidity |
| air_flow | off | on |  | Fan-assisted air circulation |
| coat_mils | 2 | 6 | mils | Wet film coat thickness |

**Fixed:** finish_type = polyurethane, wood = cherry

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| dry_time_hrs | minimize | hrs |
| hardness_h | maximize | H_pencil |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wood_finish_drying
cd wood_finish_drying
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
