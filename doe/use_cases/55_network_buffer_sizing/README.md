# Use Case 55: Network Buffer Sizing

## Scenario

You are tuning Linux kernel network stack parameters on a server with a Mellanox ConnectX (mlx5) NIC to push maximum throughput on a 25/100 Gbps link while keeping CPU softirq overhead manageable. The core tension is between buffering and CPU cost: larger NAPI budgets, transmit queues, TCP write buffers, and backlog queues reduce packet drops and improve throughput but consume more memory and pin CPU cores in softirq processing. A Latin Hypercube design efficiently samples the 4-dimensional sysctl parameter space without assuming linear relationships between these kernel tunables.

**This use case demonstrates:**
- Latin Hypercube design
- Multi-response analysis (throughput_gbps, softirq_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| netdev_budget | 128 | 1024 | packets | NAPI polling budget |
| txqueuelen | 500 | 10000 | packets | Transmit queue length |
| tcp_wmem_max_kb | 256 | 16384 | KB | Max TCP write buffer |
| backlog_max | 1000 | 65536 | packets | Netdev backlog max |

**Fixed:** nic = mlx5, ring_buffer = 4096

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_gbps | maximize | Gbps |
| softirq_pct | minimize | % |

## Why Latin Hypercube?

- A space-filling design that ensures each factor level is sampled exactly once per stratum
- Makes no assumptions about the underlying model form, ideal for computer experiments
- Provides good coverage of the entire factor space with a relatively small number of runs
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template network_buffer_sizing
cd network_buffer_sizing
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
