# Use Case 33: API Rate Limiter Tuning

## Scenario

You are configuring a Redis-backed API rate limiter for a service with 20,000 rps backend capacity and need to maximize successful request throughput (goodput) while maintaining fair access across clients as measured by Jain's fairness index. Five parameters -- per-client rate limit, token bucket burst size, window type (sliding vs fixed), penalty duration, and global rate cap -- all potentially affect the trade-off between protection and legitimate traffic throughput. A fractional factorial design screens these five factors efficiently to identify which rate-limiting knobs most influence the goodput-fairness balance before fine-tuning the critical parameters.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (goodput_rps, fairness_index)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| requests_per_sec | 100 | 1000 | rps | Base rate limit per client |
| burst_size | 10 | 100 | requests | Token bucket burst size |
| window_type | sliding | fixed |  | Rate window type |
| penalty_duration | 10 | 300 | s | Penalty period after limit hit |
| global_limit | 5000 | 50000 | rps | Global rate limit across all clients |

**Fixed:** backend_capacity = 20000, cache_backend = redis

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| goodput_rps | maximize | rps |
| fairness_index | maximize | 0-1 |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template api_rate_limiter
cd api_rate_limiter
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
