# Use Case 84: Feature Flag Evaluation

## Scenario

You are integrating LaunchDarkly feature flags into a latency-sensitive server-side application where flag evaluation adds microseconds to every request. You need to tune cache TTL, targeting rule complexity, and SDK polling interval to minimize evaluation latency while maximizing cache hit rate. A Box-Behnken design is appropriate because cache behavior is nonlinear -- very short TTLs cause constant misses while very long TTLs serve stale flags -- and you need a quadratic model to find the optimal balance.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (evaluation_latency_us, cache_hit_rate_pct)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cache_ttl_sec | 5 | 120 | sec | Feature flag cache TTL |
| rule_complexity_score | 1 | 10 | score | Targeting rule complexity score |
| sdk_polling_interval_sec | 10 | 300 | sec | SDK polling interval |

**Fixed:** platform = launchdarkly, sdk = server_side

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| evaluation_latency_us | minimize | us |
| cache_hit_rate_pct | maximize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template feature_flag_evaluation
cd feature_flag_evaluation
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
