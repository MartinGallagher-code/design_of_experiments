# Use Case 32: Load Balancer Algorithm

## Scenario

You are configuring an HTTP/2 load balancer in front of 4 backend servers and need to maximize service availability (measured in nines) while minimizing load imbalance across backends. The balancing algorithm (round-robin, least-connections, or IP-hash), health check interval, and connection draining timeout all interact -- IP-hash provides session affinity but can skew load, while aggressive health checks detect failures faster but add overhead. A full factorial design is feasible with three factors at small level counts and captures the algorithm-by-timing interactions that determine whether failovers are graceful or disruptive.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (availability, imbalance_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| algorithm | round_robin | ip_hash |  | Load balancing algorithm |
| health_interval | 5 | 30 | s | Health check interval |
| drain_timeout | 10 | 60 | s | Connection draining timeout |

**Fixed:** backend_count = 4, protocol = http2

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| availability | maximize | % |
| imbalance_pct | minimize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template load_balancer_algorithm
cd load_balancer_algorithm
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
