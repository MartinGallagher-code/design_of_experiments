# Use Case 73: PWM Motor Control

## Scenario

You are tuning a BLDC motor driver (DRV8305) for a robotic actuator where smooth torque delivery and high efficiency are both critical. PWM switching frequency, dead time between high/low side transitions, and PID proportional gain all interact nonlinearly -- higher PWM frequency reduces torque ripple but increases switching losses, while dead time prevents shoot-through but introduces distortion. A Box-Behnken design models these curved response surfaces without testing extreme corners that risk damaging the power stage.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (torque_ripple_pct, efficiency_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| pwm_frequency_khz | 5 | 50 | kHz | PWM switching frequency |
| dead_time_ns | 100 | 2000 | ns | Dead time between high/low side switching |
| pid_gain_kp | 0.5 | 10.0 | gain | PID proportional gain |

**Fixed:** motor_type = bldc, driver = drv8305

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| torque_ripple_pct | minimize | % |
| efficiency_pct | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template pwm_motor_control
cd pwm_motor_control
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
