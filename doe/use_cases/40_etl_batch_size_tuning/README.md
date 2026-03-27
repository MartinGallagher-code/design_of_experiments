# Use Case 40: ETL Batch Size Tuning

## Scenario

You are optimizing an ETL pipeline that extracts from PostgreSQL and writes Parquet files to S3. There are 5 parameters to tune -- batch size, writer threads, commit interval, transform mode, and buffer size -- but each benchmark run takes significant cluster time. A fractional factorial design lets you efficiently screen which of these knobs most affect throughput and peak memory, without running all 32 combinations.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (rows_per_sec, peak_memory_gb)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| batch_size | 1000 | 100000 | rows | Rows per batch |
| writer_threads | 1 | 16 | threads | Parallel writer threads |
| commit_interval | 1000 | 50000 | rows | Commit frequency |
| transform_mode | row | vectorized |  | Transform execution mode |
| buffer_mb | 64 | 512 | MB | In-memory buffer size |

**Fixed:** source = postgresql, sink = s3_parquet

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| rows_per_sec | maximize | rows/s |
| peak_memory_gb | minimize | GB |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template etl_batch_size_tuning
cd etl_batch_size_tuning
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
