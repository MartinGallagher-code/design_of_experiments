# Use Case 82: GitOps Sync Interval

## Scenario

You are managing Kubernetes deployments across 3 clusters with Argo CD and need to detect configuration drift quickly while maintaining high reconciliation success rates. Shorter sync intervals catch drift faster but increase API server load and can cause reconciliation conflicts, while enabling automatic pruning keeps resources clean but risks deleting resources during transient failures. A full factorial design with 3 factors tests every combination to reveal all interactions between sync interval, health check timeout, and prune behavior.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (drift_detection_delay_sec, reconciliation_success_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| sync_interval_sec | 30 | 300 | sec | GitOps sync interval |
| health_check_timeout | 10 | 60 | sec | Health check timeout |
| prune_enabled | off | on |  | Automatic resource pruning |

**Fixed:** tool = argocd, cluster_count = 3

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| drift_detection_delay_sec | minimize | sec |
| reconciliation_success_pct | maximize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template gitops_sync_interval
cd gitops_sync_interval
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
