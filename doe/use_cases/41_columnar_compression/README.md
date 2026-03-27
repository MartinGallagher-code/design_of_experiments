# Use Case 41: Columnar Compression

## Scenario

You are configuring Parquet file settings for a mixed-analytics data lake and need to find the best combination of compression codec (Snappy vs Zstd), dictionary encoding, page size, and row group size. The core trade-off is between compression ratio and read throughput -- Zstd compresses better but may slow scans. With only 4 two-level factors, a full factorial design is affordable and captures all interaction effects, such as whether dictionary encoding benefits one codec more than the other.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (compression_ratio, read_speed_mbps)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| codec | snappy | zstd |  | Compression codec |
| dictionary | off | on |  | Dictionary encoding |
| page_size_kb | 64 | 1024 | KB | Column page size |
| row_group_mb | 32 | 256 | MB | Row group size |

**Fixed:** format = parquet, data_type = mixed_analytics

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| compression_ratio | maximize | x |
| read_speed_mbps | maximize | MB/s |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template columnar_compression
cd columnar_compression
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
