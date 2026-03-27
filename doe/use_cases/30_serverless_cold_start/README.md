# Use Case 30: Serverless Cold Start

## Scenario

You are deploying AWS Lambda functions behind API Gateway and need to minimize cold start latency while controlling per-million-invocation costs. Six configuration knobs -- memory allocation, runtime language (Python vs Go), deployment package size, VPC attachment, Lambda layers count, and provisioned concurrency -- all potentially affect initialization time, but each also has cost implications. A Plackett-Burman design efficiently screens all six factors in just 8 benchmark runs to identify which configuration choices dominate cold start performance before investing in provisioned concurrency or architecture changes.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (cold_start_ms, cost_per_million)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| memory_mb | 128 | 1024 | MB | Function memory allocation |
| runtime | python | go |  | Runtime language |
| package_mb | 5 | 50 | MB | Deployment package size |
| vpc_enabled | no | yes |  | VPC attachment |
| layers_count | 0 | 5 | count | Lambda layers attached |
| provisioned | 0 | 10 | count | Provisioned concurrency |

**Fixed:** region = us-east-1, trigger = api-gateway

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| cold_start_ms | minimize | ms |
| cost_per_million | minimize | USD |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template serverless_cold_start
cd serverless_cold_start
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
