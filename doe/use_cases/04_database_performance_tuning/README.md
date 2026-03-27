# Use Case 4: Database Performance Tuning

## Scenario

You are tuning a PostgreSQL database for an OLTP workload. There are 6 configuration parameters to investigate, but running benchmarks is time-consuming. You need an efficient screening design that tells you which knobs matter most, with replicate blocks to assess variability.

**This use case demonstrates:**
- Plackett-Burman design (efficient 2-level screening for many factors)
- Blocking with replication (`block_count: 2`)
- Mixed factor types (continuous + categorical)
- `--no-plots` mode for headless/CI environments
- `--csv` export for downstream analysis in R/Excel/pandas
- `double-dash` argument style (default)

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| shared_buffers | 256 | 1024 | continuous | MB | Shared memory buffer pool |
| work_mem | 4 | 64 | continuous | MB | Per-operation working memory |
| max_connections | 50 | 200 | continuous | | Maximum client connections |
| effective_cache | 512 | 4096 | continuous | MB | OS disk cache estimate |
| wal_level | minimal | replica | categorical | | Write-ahead log level |
| checkpoint_timeout | 60 | 900 | continuous | sec | Checkpoint interval |

**Fixed:** pg_version = 16, storage = nvme

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput | maximize | tps |
| p99_latency | minimize | ms |

## Why Plackett-Burman?

- 6 factors at 2 levels: full factorial = 64 runs, way too many
- Plackett-Burman gives us 8 base runs (just N+1 where N is the number of factors, rounded up)
- With 2 blocks: 16 total runs, which is very manageable
- Perfect for screening — identify the "vital few" parameters before fine-tuning
- Blocking lets us estimate run-to-run variability

## Running the Demo

### Prerequisites

```bash
pip install doehelper
```

### Step 1: Preview the design

```bash
doe info --config config.json
```

Output:
```
Plan      : Database Performance Tuning
Operation : plackett_burman
Factors   : shared_buffers, work_mem, max_connections, effective_cache, wal_level, checkpoint_timeout
Base runs : 8
Blocks    : 2
Total runs: 16
Responses : throughput [maximize] (tps), p99_latency [minimize] (ms)
Fixed     : pg_version=16, storage=nvme
```

Notice: 8 base runs × 2 blocks = 16 total runs. Each block is an independent replicate with its own randomized order.

### Step 2: Generate the runner script

```bash
doe generate --config config.json \
    --output results/run.sh --seed 42
```

### Step 3: Execute the experiments

```bash
bash results/run.sh
```

### Step 4: Analyze without plots (headless mode)

```bash
doe analyze --config config.json --no-plots
```

The `--no-plots` flag skips Pareto charts and main effects plots — useful in CI pipelines, SSH sessions, or environments without a display. You still get the full text-based analysis with effects, interactions, and summary statistics.

### Step 5: Export results to CSV

```bash
doe analyze --config config.json \
    --csv results/csv
```

This creates CSV files in `results/csv/`:
- `main_effects_throughput.csv` — Factor, effect, std error, contribution, CI bounds
- `main_effects_p99_latency.csv` — Same for latency
- `summary_stats_throughput.csv` — Per-factor, per-level statistics
- `summary_stats_p99_latency.csv` — Same for latency

Import these into R, pandas, or Excel for custom analysis.

### Step 6: Optimize

```bash
doe optimize --config config.json
```

### Step 7: Generate report

```bash
doe report --config config.json \
    --output results/report.html
```

## Interpreting the Results

### Blocking Effects

With 2 blocks you can compare results across replicates:
- If the same factors dominate in both blocks → robust finding
- If results differ between blocks → environmental noise may be significant

### Screening Outcome

Plackett-Burman reveals the "vital few" parameters. Typical PostgreSQL findings:
- **shared_buffers** and **effective_cache** usually have the largest throughput effects
- **max_connections** often drives latency (more connections = more contention)
- **wal_level** affects write throughput but not reads

### Next Steps

1. Drop unimportant factors (fix them at convenient values)
2. Run a full factorial or CCD on the 2-3 important factors
3. Fine-tune for your specific workload

## Features Exercised

| Feature | Value |
|---------|-------|
| Design type | `plackett_burman` |
| Factor types | `continuous` (5) + `categorical` (1) |
| Blocking | `block_count: 2` (16 total = 8 base × 2) |
| Arg style | `double-dash` (default) |
| `--no-plots` | Yes (headless analysis) |
| `--csv` export | Yes (4 CSV files) |
| Fixed factors | pg_version, storage |
| Multi-response | throughput (maximize), p99_latency (minimize) |

## Files

- Config: `config.json`
- Simulator: `sim.sh`
- Results: `results/`
- CSV exports: `results/csv/`
- Report: `results/report.html`
