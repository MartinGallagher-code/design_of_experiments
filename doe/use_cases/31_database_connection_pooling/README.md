# Use Case 31: Database Connection Pooling

## Scenario

You are tuning a PostgreSQL connection pool (e.g., PgBouncer or HikariCP) with SSL enabled and need to maximize queries per second while minimizing p95 query latency. Pool size, idle connection timeout, and connection max lifetime interact nonlinearly -- too many connections overwhelm the database with context switching, while aggressive timeouts cause frequent reconnection overhead that spikes tail latency. A Box-Behnken design fits the curved response surface across these three parameters without testing the extreme corner of maximum pool size with minimum timeouts, which would flood the database with constant connection churn.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (throughput_qps, p95_latency_ms)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| pool_size | 5 | 50 | conns | Maximum pool connections |
| idle_timeout | 30 | 300 | s | Idle connection timeout |
| max_lifetime | 300 | 3600 | s | Connection max lifetime |

**Fixed:** db_engine = postgresql, ssl = true

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_qps | maximize | qps |
| p95_latency_ms | minimize | ms |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template database_connection_pooling
cd database_connection_pooling
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
