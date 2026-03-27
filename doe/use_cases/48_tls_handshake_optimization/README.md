# Use Case 48: TLS Handshake Optimization

## Scenario

You are optimizing TLS 1.3 handshake performance on a high-traffic nginx reverse proxy serving thousands of new connections per second. You need to tune session cache size, session ticket timeout, and OCSP stapling worker threads to minimize full handshake latency while maximizing session resumption rates. A Box-Behnken design fits this problem because cache saturation and timeout effects are likely nonlinear, and you need a quadratic model without testing extreme corners that could exhaust memory or stall OCSP responses.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (handshake_ms, resumption_rate)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| session_cache_size | 1000 | 100000 | entries | TLS session cache size |
| session_timeout_s | 60 | 86400 | s | Session ticket timeout |
| ocsp_stapling_workers | 1 | 8 | threads | OCSP stapling worker threads |

**Fixed:** tls_version = 1.3, cipher = AES-256-GCM

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| handshake_ms | minimize | ms |
| resumption_rate | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template tls_handshake_optimization
cd tls_handshake_optimization
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
