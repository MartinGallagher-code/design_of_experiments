# Use Case 38: Data Lake Partitioning

## Scenario

You are organizing a 5TB data lake with 90-day retention and need to minimize both median analytical query time and monthly storage cost. Partition column strategy (date, date+hour, or date+hour+region), columnar file format (Parquet vs ORC), target compacted file size, and Z-order optimization all interact -- finer partitioning speeds up filtered queries but creates a small-file problem that inflates storage metadata costs and slows full scans. A full factorial design is the right approach because with four factors at small level counts the run matrix is manageable, and you need complete interaction information to understand how partitioning strategy interacts with file format and compaction choices.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (query_time_s, storage_cost_month)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| partition_cols | date | date_hour_region |  | Partition column strategy |
| file_format | parquet | orc |  | Columnar file format |
| target_file_mb | 64 | 256 | MB | Target file size after compaction |
| z_order | off | on |  | Z-order optimization |

**Fixed:** table_size_tb = 5, retention_days = 90

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| query_time_s | minimize | s |
| storage_cost_month | minimize | USD |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template data_lake_partitioning
cd data_lake_partitioning
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
