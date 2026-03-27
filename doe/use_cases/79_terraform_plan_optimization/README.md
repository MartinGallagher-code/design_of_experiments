# Use Case 79: Terraform Plan Optimization

## Scenario

You are speeding up Terraform plan execution for a large AWS infrastructure managed with S3 backend state, where plans currently take minutes and slow down the CI pipeline. There are 6 settings to investigate -- parallelism, state refresh, lock timeout, provider caching, output format, and detailed exit codes -- and each plan run ties up CI resources. A Plackett-Burman screening design identifies which of these parameters most affect plan time and drift detection capability in just 8 runs.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (plan_time_sec, state_drift_detected)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| parallelism | 1 | 20 | threads | Terraform operation parallelism |
| refresh_enabled | off | on |  | State refresh before plan |
| state_lock_timeout | 5 | 120 | sec | State lock acquisition timeout |
| provider_cache | off | on |  | Provider plugin caching |
| plan_out_format | text | json |  | Plan output format |
| detailed_exitcode | off | on |  | Detailed exit code enabled |

**Fixed:** backend = s3, provider = aws

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| plan_time_sec | minimize | sec |
| state_drift_detected | maximize | count |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template terraform_plan_optimization
cd terraform_plan_optimization
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
