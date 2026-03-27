# Use Case 64: Secrets Vault Performance

## Scenario

You are tuning a HashiCorp Vault cluster backed by Consul with AWS KMS auto-unseal for a microservices platform that fetches secrets at high request rates. You need to balance seal wrap worker threads, secret cache size, and lease TTL to minimize read latency while maximizing operations throughput. A Box-Behnken design is well-suited because cache saturation and lease renewal overhead create nonlinear response surfaces, and running at all extreme settings simultaneously risks KMS throttling.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (read_latency_ms, throughput_ops)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| seal_wrap_threads | 1 | 8 | threads | Seal wrap worker threads |
| cache_size_mb | 64 | 512 | MB | Secret cache size |
| lease_ttl_sec | 30 | 600 | sec | Secret lease time-to-live |

**Fixed:** vault_backend = consul, seal_type = awskms

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| read_latency_ms | minimize | ms |
| throughput_ops | maximize | ops/s |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template secrets_vault_performance
cd secrets_vault_performance
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
