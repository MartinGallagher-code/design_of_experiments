# Use Case 54: HTTP/2 Stream Multiplexing

## Scenario

You are tuning HTTP/2 settings on an nginx server with TLS 1.3 to minimize page load time and time-to-first-byte for a content-heavy web application. The parameters -- max concurrent streams, flow control window size, HPACK header table size, and stream priority scheduling -- all interact: larger windows improve throughput but can starve low-priority streams, while aggressive multiplexing may cause head-of-line blocking. A full factorial design with 4 factors is affordable and captures these interactions completely.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (page_load_ms, ttfb_ms)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| max_concurrent_streams | 50 | 250 | streams | Max concurrent HTTP/2 streams |
| window_size_kb | 64 | 1024 | KB | Flow control window size |
| header_table_kb | 4 | 64 | KB | HPACK header table size |
| priority_enabled | off | on |  | Stream priority scheduling |

**Fixed:** tls = 1.3, server = nginx

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| page_load_ms | minimize | ms |
| ttfb_ms | minimize | ms |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template http2_stream_multiplexing
cd http2_stream_multiplexing
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
