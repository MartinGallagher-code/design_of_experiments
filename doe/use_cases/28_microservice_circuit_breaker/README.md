# Use Case 28: Microservice Circuit Breaker

## Scenario

You are configuring a circuit breaker pattern (e.g., Hystrix or Resilience4j) in a microservice architecture and need to minimize both end-user error rate and cascade recovery time. The failure threshold count, request timeout, and half-open retry interval interact nonlinearly -- a low threshold trips the breaker too eagerly causing unnecessary errors, while a long retry interval delays recovery after genuine outages. A Box-Behnken design avoids the risky extreme of maximum timeout with minimum threshold that could mask real failures, while fitting the quadratic model needed to find the resilient sweet spot.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (error_rate, recovery_time)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| failure_threshold | 3 | 15 | count | Failures before circuit opens |
| timeout_ms | 500 | 5000 | ms | Request timeout |
| reset_interval | 5 | 60 | s | Half-open retry interval |

**Fixed:** backend_pool_size = 10, health_check_interval = 5

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| error_rate | minimize | % |
| recovery_time | minimize | s |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template microservice_circuit_breaker
cd microservice_circuit_breaker
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
