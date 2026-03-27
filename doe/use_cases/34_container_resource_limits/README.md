# Use Case 34: Container Resource Limits

## Scenario

You are right-sizing Kubernetes container resource requests and limits for a burstable QoS workload, trying to maximize cluster utilization without triggering OOM kills. Setting requests too low lets the scheduler overpack nodes until the kernel OOM-killer starts evicting pods, while over-requesting wastes capacity that other tenants could use. A Central Composite design efficiently models the nonlinear interaction between CPU request, CPU limit, and memory request, revealing the quadratic curvature where utilization plateaus before instability spikes.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (utilization_pct, oom_kills_per_day)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cpu_request_m | 100 | 1000 | millicores | CPU request |
| cpu_limit_m | 500 | 2000 | millicores | CPU limit |
| memory_request_mb | 128 | 1024 | MB | Memory request |

**Fixed:** memory_limit_mb = 2048, qos_class = burstable

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| utilization_pct | maximize | % |
| oom_kills_per_day | minimize | count |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template container_resource_limits
cd container_resource_limits
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
