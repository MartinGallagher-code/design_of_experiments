# Use Case 126: Windshield Defog Strategy

## Scenario

You are testing windshield defog strategies on a cold, humid morning (2 C, 85% RH) and want to minimize clearing time while keeping energy draw low. Five HVAC settings -- fan speed, temperature, AC compressor on/off, recirculation mode, and rear defrost -- could all matter, but a full 32-run factorial is impractical when each trial requires re-fogging the windshield from a controlled baseline. A fractional factorial design halves the required runs while still resolving the main effects and key two-factor interactions like AC mode combined with recirculation.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (defog_time_sec, energy_watts)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| fan_speed | 1 | 5 | level | HVAC fan speed setting |
| temp_setting | 18 | 30 | C | Temperature dial setting |
| ac_on | 0 | 1 | bool | Air conditioning compressor on/off |
| recirc | 0 | 1 | bool | Recirculation mode on/off |
| rear_defrost | 0 | 1 | bool | Rear defroster on/off |

**Fixed:** ambient_temp = 2C, humidity = 85pct

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| defog_time_sec | minimize | sec |
| energy_watts | minimize | W |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template windshield_defog
cd windshield_defog
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
