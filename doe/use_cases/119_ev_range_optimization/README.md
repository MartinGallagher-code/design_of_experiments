# Use Case 119: EV Range Optimization

## Scenario

You are maximizing the real-world range of a 75 kWh electric SUV by tuning driving speed, cabin temperature setpoint, regenerative braking level, and tire type (standard vs. low-rolling-resistance). These factors interact strongly -- high speed with cabin heating in winter can halve the EPA-rated range -- and you need to understand every interaction to give drivers accurate range estimates. A full factorial design tests all 16 combinations, capturing how tire choice modulates the speed-versus-range penalty and whether regen braking savings depend on driving speed.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (range_km, kwh_per_100km)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| speed_kph | 60 | 120 | kph | Cruising speed |
| cabin_temp | 18 | 26 | C | Cabin climate set temperature |
| regen_level | 1 | 3 | level | Regenerative braking level |
| tire_type | standard | low_rolling |  | Tire rolling resistance type |

**Fixed:** battery_kwh = 75, vehicle_type = suv

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| range_km | maximize | km |
| kwh_per_100km | minimize | kWh/100km |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template ev_range_optimization
cd ev_range_optimization
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
