# Use Case 81: Test Suite Sharding

## Scenario

You are parallelizing a 4,500-test pytest suite across CI runners and need to minimize total wall-clock time while reducing the flaky failure rate that blocks deployments. The key trade-off is speed versus reliability: more shards reduce per-runner execution time but increase the probability that at least one shard hits a flaky test, while retrying flaky tests improves the green-build rate but extends wall time -- and generous timeout multipliers prevent legitimate slow tests from being killed but mask genuine hangs. A Central Composite design captures the nonlinear sweet spot across shard count, retry count, and timeout multiplier where diminishing parallelism returns meet rising flakiness.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (total_wall_time_min, flaky_failure_rate)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| shard_count | 2 | 16 | shards | Number of test shards |
| retry_flaky_count | 0 | 3 | retries | Flaky test retry count |
| timeout_multiplier | 1.0 | 3.0 | x | Test timeout multiplier |

**Fixed:** framework = pytest, test_count = 4500

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| total_wall_time_min | minimize | min |
| flaky_failure_rate | minimize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template test_suite_sharding
cd test_suite_sharding
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
