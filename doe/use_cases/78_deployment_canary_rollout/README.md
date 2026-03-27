# Use Case 78: Deployment Canary Rollout

## Scenario

You are configuring Kubernetes canary deployments and need to find the right balance between rollout safety and deployment speed. A larger canary traffic percentage detects issues faster but exposes more users to potential bugs, while longer evaluation windows improve confidence but slow releases. A Box-Behnken design models the nonlinear relationship between canary percentage, evaluation window, and error threshold -- finding the sweet spot where safety scores are high without making deployments painfully slow.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (rollout_safety_score, deployment_time_min)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| canary_pct | 5 | 25 | % | Percentage of traffic to canary |
| evaluation_window_min | 5 | 30 | min | Canary evaluation window |
| error_threshold_pct | 0.5 | 5.0 | % | Error rate threshold for rollback |

**Fixed:** orchestrator = kubernetes, strategy = canary

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| rollout_safety_score | maximize | score |
| deployment_time_min | minimize | min |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template deployment_canary_rollout
cd deployment_canary_rollout
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
