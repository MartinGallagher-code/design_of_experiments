# Use Case 65: Audit Log Pipeline

## Scenario

You are building a compliance audit log pipeline that streams JSON events to S3 and must handle bursty ingestion without dropping events or violating latency SLAs. There are 5 parameters to tune -- batch size, flush interval, compression level, buffer pool size, and writer threads -- where larger batches improve throughput but increase end-to-end latency. A fractional factorial design screens these factors efficiently, identifying the dominant knobs before committing to a deeper optimization.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (ingest_rate_eps, end_to_end_latency_ms)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| batch_size | 100 | 10000 | events | Events per batch |
| flush_interval_ms | 100 | 5000 | ms | Flush interval |
| compression_level | 1 | 9 | level | Compression level |
| buffer_pool_mb | 32 | 512 | MB | In-memory buffer pool size |
| writer_threads | 1 | 8 | threads | Parallel writer threads |

**Fixed:** storage = s3, format = json_lines

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| ingest_rate_eps | maximize | events/s |
| end_to_end_latency_ms | minimize | ms |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template audit_log_pipeline
cd audit_log_pipeline
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
