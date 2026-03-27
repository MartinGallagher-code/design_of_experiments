# Use Case 74: Zigbee Network Formation

## Scenario

You are commissioning a Zigbee smart home network using the Z-Stack on channel 15 and need devices to join quickly while maintaining long-term network stability. There are 5 parameters to balance -- scan duration, max children per router, link cost threshold, routing table size, and end device poll rate -- where aggressive scan and poll settings speed up joins but can destabilize an established mesh. A fractional factorial design efficiently screens which of these network formation parameters matter most.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (join_time_sec, network_stability_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| scan_duration_exp | 2 | 7 | exp | Channel scan duration exponent |
| max_children | 4 | 20 | nodes | Maximum children per router |
| link_cost_threshold | 1 | 7 | cost | Link cost threshold for neighbor table |
| route_table_size | 10 | 50 | entries | Routing table size |
| poll_rate_ms | 100 | 2000 | ms | End device poll rate |

**Fixed:** zigbee_stack = z_stack, channel = 15

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| join_time_sec | minimize | sec |
| network_stability_pct | maximize | % |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template zigbee_network_formation
cd zigbee_network_formation
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
