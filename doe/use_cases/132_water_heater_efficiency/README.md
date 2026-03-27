# Use Case 132: Water Heater Efficiency

## Scenario

You are reducing energy consumption for a 200 L residential water heater serving a family of four and need to identify which of five parameters -- thermostat setpoint, tank insulation R-value, pipe insulation, recirculation timer, and inlet water temperature -- most significantly affect monthly kWh usage and hot water availability. Testing all 32 combinations over multiple billing cycles is impractical. A Plackett-Burman screening design identifies the dominant factors in just a few test configurations, so you can invest in the upgrades that actually move the energy needle.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (monthly_kwh, availability_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| thermostat_c | 48 | 65 | C | Tank thermostat temperature setting |
| tank_r_value | 6 | 18 | R-value | Tank insulation R-value |
| pipe_insulation | 0 | 1 | bool | Hot water pipe insulation installed |
| recirc_timer | 0 | 1 | bool | Recirculation pump timer enabled |
| inlet_temp_c | 5 | 20 | C | Cold water inlet temperature |

**Fixed:** tank_size_L = 200, household_size = 4

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| monthly_kwh | minimize | kWh |
| availability_pct | maximize | % |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template water_heater_efficiency
cd water_heater_efficiency
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
