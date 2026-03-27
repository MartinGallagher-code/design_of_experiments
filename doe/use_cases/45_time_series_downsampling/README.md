# Use Case 45: Time-Series Downsampling

## Scenario

You are configuring a TimescaleDB continuous-aggregate pipeline ingesting 100,000 data points per second from IoT sensors, and need to minimize both query latency and storage footprint. The core trade-off is granularity versus performance: keeping fine-grained raw data enables precise queries but explodes storage and slows scans, while aggressive downsampling saves disk but loses detail needed for anomaly detection. A Central Composite design maps the curved response surface across downsampling interval, raw-data retention period, and number of pre-computed aggregation functions, capturing the diminishing returns where more aggregations stop improving query speed.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (query_p95_ms, storage_gb)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| downsample_interval_m | 1 | 60 | min | Downsampling interval |
| retention_days | 7 | 365 | days | Raw data retention |
| agg_functions | 2 | 8 | count | Number of pre-computed aggregations |

**Fixed:** db_engine = timescaledb, ingestion_rate = 100000

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| query_p95_ms | minimize | ms |
| storage_gb | minimize | GB |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template time_series_downsampling
cd time_series_downsampling
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
