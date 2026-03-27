# Use Case 308: PCB Solder Reflow Profile

## Scenario

You are developing a SAC305 lead-free solder reflow profile for a 4-layer PCB and need to maximize joint shear strength while minimizing X-ray void percentage. Five thermal profile parameters -- preheat temperature, soak duration, peak temperature, time above liquidus, and post-peak cooling rate -- all potentially affect joint metallurgy, but a full 32-run factorial would consume too many prototype boards. A fractional factorial screening design identifies which profile zones most influence joint quality in half the runs, providing a foundation for later augmentation with star points to build a full response surface model.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (joint_strength, void_percentage)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| preheat_temp | 150 | 200 | C | Preheat zone temperature |
| soak_time | 60 | 120 | s | Soak zone duration |
| peak_temp | 230 | 260 | C | Peak reflow temperature |
| time_above_liquidus | 30 | 90 | s | Time above solder liquidus temperature |
| cooling_rate | 1 | 4 | C/s | Cooling rate after peak |

**Fixed:** solder_paste = SAC305, board_layers = 4

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| joint_strength | maximize | N |
| void_percentage | minimize | % |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template pcb_solder_reflow
cd pcb_solder_reflow
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
