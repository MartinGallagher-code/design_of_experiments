# Use Case 29: CDN Cache Hit Optimization

## Scenario

You are optimizing a CDN edge cache configuration serving content from a us-east-1 origin with Brotli compression, and need to maximize cache hit ratio while minimizing bandwidth pulled from the origin servers. TTL duration, eviction policy (LRU vs LFU), edge cache size, and predictive prefetch toggling all interact -- long TTLs boost hit rates but serve stale content, while prefetch can waste cache space on unpopular objects. A full factorial design is ideal because with four factors at two levels the 16 runs are cheap to simulate, and you need to understand every interaction between caching strategy choices.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (hit_ratio, origin_bandwidth)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| ttl_hours | 1 | 24 | h | Cache time-to-live |
| cache_policy | lru | lfu |  | Eviction policy |
| cache_size_gb | 50 | 200 | GB | Edge cache size |
| prefetch | off | on |  | Predictive prefetch |

**Fixed:** origin_region = us-east-1, compression = brotli

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| hit_ratio | maximize | % |
| origin_bandwidth | minimize | Gbps |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template cdn_cache_optimization
cd cdn_cache_optimization
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
