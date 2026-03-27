# Use Case 37: Spark Shuffle Optimization

## Scenario

You are optimizing the shuffle phase of an Apache Spark SQL job running on 8g/4-core executors, where wide transformations like joins and aggregations dominate runtime. Too few shuffle partitions create large tasks that spill to disk, while too many generate excessive scheduler overhead and small-file I/O; meanwhile, the choice between LZ4 and Zstandard compression trades CPU time for network transfer savings. A Full Factorial design tests every combination of partition count, buffer size, and compression codec, ensuring all interaction effects are captured across just 3 factors.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (job_time_min, shuffle_spill_gb)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| shuffle_partitions | 50 | 500 | count | spark.sql.shuffle.partitions |
| shuffle_buffer_kb | 32 | 256 | KB | Shuffle write buffer size |
| compress_codec | lz4 | zstd |  | Shuffle compression codec |

**Fixed:** executor_memory = 8g, executor_cores = 4

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| job_time_min | minimize | min |
| shuffle_spill_gb | minimize | GB |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template spark_shuffle_optimization
cd spark_shuffle_optimization
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
