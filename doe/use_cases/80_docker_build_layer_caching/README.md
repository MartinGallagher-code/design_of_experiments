# Use Case 80: Docker Build Layer Caching

## Scenario

You are optimizing Docker image builds using BuildKit with ECR as the registry, where slow builds and bloated images are slowing down your deployment pipeline. There are 5 parameters to tune -- cache mode (inline vs registry), max layers, layer squash, build arguments, and multistage build stages -- and each build iteration takes significant time. A fractional factorial design screens which of these Dockerfile and BuildKit settings most affect build time and final image size.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (build_time_sec, image_size_mb)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| build_cache_mode | inline | registry |  | Build cache mode |
| max_layers | 5 | 30 | layers | Maximum Dockerfile layers |
| squash_enabled | off | on |  | Layer squash enabled |
| build_arg_count | 0 | 10 | args | Number of build arguments |
| multistage_stages | 1 | 5 | stages | Multistage build stage count |

**Fixed:** builder = buildkit, registry = ecr

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| build_time_sec | minimize | sec |
| image_size_mb | minimize | MB |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template docker_build_layer_caching
cd docker_build_layer_caching
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
