# Use Case 47: TCP Congestion Control

## Scenario

You are benchmarking TCP stack settings on a 10 Gbps data center link to maximize sustained throughput while minimizing retransmissions. The key trade-off is between aggressive congestion control (BBR vs CUBIC), initial congestion window size, receive buffer limits, and ECN support. With just 4 factors at two levels, a full factorial design is practical and reveals all interactions -- such as whether BBR benefits more from large initial windows than CUBIC does.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (throughput_gbps, retransmit_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| congestion_algo | cubic | bbr |  | TCP congestion control algorithm |
| init_cwnd | 10 | 40 | segments | Initial congestion window |
| rmem_max_kb | 256 | 4096 | KB | Maximum receive buffer |
| ecn | off | on |  | Explicit Congestion Notification |

**Fixed:** mtu = 1500, link_speed = 10Gbps

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_gbps | maximize | Gbps |
| retransmit_pct | minimize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template tcp_congestion_control
cd tcp_congestion_control
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
