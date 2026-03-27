# Use Case 39: Stream Processing Windowing

## Scenario

You are tuning an Apache Flink streaming job that aggregates clickstream events in real time. You need to balance tumbling window size, watermark delay for late-arriving events, and job parallelism to minimize end-to-end latency while maximizing result accuracy. A Box-Behnken design is ideal here because the relationship between windowing parameters and latency is nonlinear, and you want to model curvature without testing risky extreme corner combinations that could crash the RocksDB state backend.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (end_to_end_latency_ms, result_accuracy)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| window_size_s | 5 | 120 | s | Tumbling window size |
| watermark_delay_s | 1 | 30 | s | Allowed event-time lateness |
| parallelism | 4 | 32 | slots | Job parallelism |

**Fixed:** checkpoint_interval_ms = 10000, state_backend = rocksdb

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| end_to_end_latency_ms | minimize | ms |
| result_accuracy | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template stream_processing_windowing
cd stream_processing_windowing
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
