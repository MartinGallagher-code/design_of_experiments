# Use Case 278: DC Motor Speed Control

## Scenario

You are tuning a brushed DC motor speed controller with a 100 PPR encoder feedback loop and need to maximize steady-state speed accuracy and electrical-to-mechanical efficiency. Five parameters -- PWM switching frequency, duty cycle, supply voltage, load inertia, and PID proportional gain -- all potentially affect performance, but running a full factorial across all five would require 32 test runs on the bench. A fractional factorial design cuts the run count dramatically while still identifying which of these knobs most influence speed regulation and efficiency.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (speed_accuracy_pct, efficiency_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| pwm_khz | 1 | 25 | kHz | PWM switching frequency |
| duty_pct | 20 | 80 | % | PWM duty cycle |
| voltage_v | 6 | 24 | V | Supply voltage |
| load_kg_cm2 | 1 | 10 | kg*cm2 | Load moment of inertia |
| pid_kp | 0.5 | 5.0 | gain | PID proportional gain |

**Fixed:** motor = brushed_DC, encoder = 100ppr

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| speed_accuracy_pct | maximize | % |
| efficiency_pct | maximize | % |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template motor_speed_control
cd motor_speed_control
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
