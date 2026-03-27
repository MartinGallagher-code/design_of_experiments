# Use Case 83: Log Aggregation Pipeline

## Scenario

You are tuning an ELK (Elasticsearch-Logstash-Kibana) log pipeline with 30-day retention, aiming to maximize ingestion throughput while keeping Kibana query latency fast enough for live incident investigation. The fundamental tension is batching versus responsiveness: large batch sizes and high compression levels improve write throughput and reduce storage but increase indexing latency and slow down queries on recently ingested data, while more parser threads speed up structured extraction but compete with Elasticsearch for CPU. A Latin Hypercube design explores the 4-dimensional space of batch size, flush interval, parser threads, and compression level without assuming any particular interaction model.

**This use case demonstrates:**
- Latin Hypercube design
- Multi-response analysis (ingestion_rate_gbps, query_latency_ms)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| batch_size_kb | 64 | 2048 | KB | Log batch size |
| flush_interval_sec | 1 | 30 | sec | Flush interval to storage |
| parser_threads | 1 | 16 | threads | Log parser threads |
| compression_ratio | 1 | 9 | level | Log compression level |

**Fixed:** stack = elk, retention_days = 30

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| ingestion_rate_gbps | maximize | Gbps |
| query_latency_ms | minimize | ms |

## Why Latin Hypercube?

- A space-filling design that ensures each factor level is sampled exactly once per stratum
- Makes no assumptions about the underlying model form, ideal for computer experiments
- Provides good coverage of the entire factor space with a relatively small number of runs
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template log_aggregation_pipeline
cd log_aggregation_pipeline
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
