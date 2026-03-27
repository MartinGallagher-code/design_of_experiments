# Use Case 50: DNS Resolver Caching

## Scenario

You are tuning an Unbound recursive DNS resolver with DNSSEC validation enabled, serving a high-traffic environment where cache hit rate directly determines user-perceived page load time. The trade-off is memory versus freshness: a large cache with aggressive minimum-TTL overrides maximizes hit rate but serves potentially stale records and consumes significant RAM, while prefetching popular records before expiry reduces cold-miss latency at the cost of upstream query volume. A Central Composite design models the quadratic interactions between cache size, minimum TTL override, and prefetch threshold, finding the optimal balance with just 3 factors.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (avg_resolution_ms, cache_hit_rate)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cache_size | 10000 | 500000 | entries | Resolver cache size |
| min_ttl_s | 30 | 3600 | s | Minimum TTL override |
| prefetch_pct | 0 | 90 | % | Prefetch threshold (% of TTL remaining) |

**Fixed:** resolver = unbound, dnssec = on

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| avg_resolution_ms | minimize | ms |
| cache_hit_rate | maximize | % |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template dns_resolver_caching
cd dns_resolver_caching
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
