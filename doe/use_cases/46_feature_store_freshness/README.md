# Use Case 46: Feature Store Freshness

## Scenario

You are operating a feature store backed by S3 Parquet (offline) and Redis (online), serving real-time ML inference that requires both low-latency feature retrieval and minimal staleness for fraud-detection models. The key tension is freshness versus serving cost: frequent materialization and short cache TTLs keep features current but hammer Redis with writes and increase compute spend, while large batch sizes improve throughput but delay feature availability. A Latin Hypercube design explores the 4-parameter space of materialization interval, cache TTL, batch size, and replica count without assuming a specific response model.

**This use case demonstrates:**
- Latin Hypercube design
- Multi-response analysis (serving_latency_ms, freshness_lag_min)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| materialization_interval_m | 1 | 60 | min | Feature materialization interval |
| cache_ttl_s | 10 | 300 | s | Online store cache TTL |
| batch_size | 100 | 10000 | rows | Materialization batch size |
| online_replicas | 1 | 6 | count | Online store replica count |

**Fixed:** offline_store = s3_parquet, online_store = redis

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| serving_latency_ms | minimize | ms |
| freshness_lag_min | minimize | min |

## Why Latin Hypercube?

- A space-filling design that ensures each factor level is sampled exactly once per stratum
- Makes no assumptions about the underlying model form, ideal for computer experiments
- Provides good coverage of the entire factor space with a relatively small number of runs
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template feature_store_freshness
cd feature_store_freshness
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
