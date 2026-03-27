# Use Case 42: Query Engine Join Strategy

## Scenario

You are tuning Spark SQL join performance on a 100 GB analytical workload. There are 6 parameters to investigate -- join algorithm, hash table budget, sort buffer, broadcast threshold, adaptive execution, and shuffle partitions -- and each benchmark is expensive to run on the cluster. A Plackett-Burman screening design lets you identify which knobs most affect query time and peak executor memory in just 8 runs, before committing to a deeper optimization study.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (query_time_s, peak_memory_gb)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| join_algorithm | hash | sort_merge |  | Join algorithm preference |
| hash_table_mb | 256 | 4096 | MB | Hash table memory budget |
| sort_buffer_mb | 64 | 512 | MB | Sort buffer size |
| broadcast_threshold_mb | 10 | 256 | MB | Broadcast join threshold |
| adaptive_execution | off | on |  | Adaptive query execution |
| partitions | 50 | 400 | count | Shuffle partition count |

**Fixed:** engine = spark_sql, data_size_gb = 100

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| query_time_s | minimize | s |
| peak_memory_gb | minimize | GB |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template query_engine_join_strategy
cd query_engine_join_strategy
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
