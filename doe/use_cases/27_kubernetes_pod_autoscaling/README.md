# Use Case 27: Kubernetes Pod Autoscaling

## Scenario

You are configuring the Kubernetes Horizontal Pod Autoscaler for a latency-sensitive production API, balancing p99 response time against hourly compute spend. The core trade-off is reactivity versus cost: a low CPU target with a short stabilization window keeps latency tight but over-provisions pods during traffic spikes, while conservative settings save money but risk SLA breaches. A Central Composite design maps the curved relationship between target CPU utilization, scale-up window, and max replica count, capturing the quadratic sweet spot that a simple factorial would miss.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (p99_latency_ms, hourly_cost)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| target_cpu_pct | 40 | 80 | % | HPA target CPU utilization |
| scaleup_window | 15 | 120 | s | Stabilization window for scale-up |
| max_replicas | 5 | 30 | pods | Maximum replica count |

**Fixed:** min_replicas = 2, namespace = production

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| p99_latency_ms | minimize | ms |
| hourly_cost | minimize | USD |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template kubernetes_pod_autoscaling
cd kubernetes_pod_autoscaling
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
