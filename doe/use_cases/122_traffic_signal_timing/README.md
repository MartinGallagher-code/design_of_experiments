# Use Case 122: Traffic Signal Timing

## Scenario

You are optimizing a four-way intersection during peak hour and need to determine which of six signal timing parameters -- green phase duration, cycle length, offset, pedestrian phase, left-turn phase, and sensor delay -- most strongly affect vehicle throughput and average wait time. Running real-world trials of all possible combinations would disrupt traffic for weeks. A Plackett-Burman screening design tests all six factors in just 12 signal plans, quickly revealing the two or three parameters worth fine-tuning in a follow-up optimization study.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (throughput_vph, avg_wait_sec)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| green_sec | 15 | 60 | sec | Main road green phase duration |
| cycle_sec | 60 | 150 | sec | Total signal cycle length |
| offset_pct | 0 | 50 | % | Offset percentage for coordination |
| ped_phase_sec | 10 | 30 | sec | Pedestrian crossing phase |
| left_turn_sec | 0 | 20 | sec | Protected left-turn phase |
| sensor_delay | 1 | 5 | sec | Vehicle detection sensor delay |

**Fixed:** intersection_type = 4_way, time_of_day = peak

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_vph | maximize | veh/hr |
| avg_wait_sec | minimize | sec |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template traffic_signal_timing
cd traffic_signal_timing
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
