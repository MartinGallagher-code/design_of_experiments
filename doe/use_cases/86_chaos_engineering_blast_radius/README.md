# Use Case 86: Chaos Engineering Blast Radius

## Scenario

You are running LitmusChaos experiments against a microservices architecture and need to calibrate injection parameters that maximize the resilience insights gained while minimizing the blast radius -- the number of downstream services affected by cascading failures. The core trade-off is experiment aggressiveness versus production safety: injecting failures into a larger percentage of pods for longer durations reveals hidden coupling and retry storms, but risks breaching SLOs for real users if the steady-state threshold is set too loosely. A Central Composite design models the quadratic relationship between failure injection percentage, experiment duration, and steady-state success threshold, capturing the nonlinear boundary where controlled chaos tips into uncontrolled outage.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (resilience_score, blast_radius_services)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| failure_injection_pct | 5 | 50 | % | Failure injection percentage |
| experiment_duration_min | 5 | 30 | min | Chaos experiment duration |
| steady_state_threshold | 0.9 | 0.99 | ratio | Steady state success threshold |

**Fixed:** tool = litmus, target = microservices

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| resilience_score | maximize | score |
| blast_radius_services | minimize | count |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template chaos_engineering_blast_radius
cd chaos_engineering_blast_radius
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
