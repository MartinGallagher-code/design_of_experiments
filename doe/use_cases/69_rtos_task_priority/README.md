# Use Case 69: RTOS Task Priority

## Scenario

You are configuring FreeRTOS on a 240 MHz MCU for a real-time control application where missed deadlines cause safety-critical failures. You need to tune priority levels, tick rate, stack size, and preemption threshold to minimize worst-case scheduling latency while maximizing CPU utilization. A full factorial design with 4 factors reveals all interactions -- for example, whether a higher tick rate only helps when combined with more priority levels and lower preemption thresholds.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (worst_case_latency_us, cpu_utilization_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| task_priority_levels | 4 | 16 | levels | Number of priority levels |
| tick_rate_hz | 100 | 1000 | Hz | RTOS tick rate |
| stack_size_bytes | 512 | 4096 | bytes | Task stack size |
| preemption_threshold | 1 | 8 | level | Preemption threshold level |

**Fixed:** rtos = freertos, mcu_clock = 240MHz

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| worst_case_latency_us | minimize | us |
| cpu_utilization_pct | maximize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template rtos_task_priority
cd rtos_task_priority
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
