# Use Case 77: CI/CD Pipeline Parallelism

## Scenario

You are optimizing a GitHub Actions CI/CD pipeline for a medium-sized repository where build times are hurting developer velocity but compute costs are under scrutiny. You need to tune parallel job count, runner CPU cores, cache strategy, and artifact compression to minimize pipeline duration without blowing the budget. A full factorial design with 4 factors captures all interactions -- such as whether aggressive caching only pays off when combined with enough parallel jobs to exploit the warm cache.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (pipeline_duration_min, resource_cost_usd)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| parallel_jobs | 1 | 8 | jobs | Number of parallel jobs |
| runner_cpu_cores | 2 | 8 | cores | Runner CPU core count |
| cache_strategy | none | aggressive |  | Build cache strategy |
| artifact_compression | off | on |  | Artifact compression enabled |

**Fixed:** ci_platform = github_actions, repo_size = medium

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| pipeline_duration_min | minimize | min |
| resource_cost_usd | minimize | USD |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template cicd_pipeline_parallelism
cd cicd_pipeline_parallelism
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
