# Use Case 75: Firmware OTA Strategy

## Scenario

You are delivering firmware updates over CoAP to a fleet of constrained IoT devices on unreliable wireless links with LZ4 compression. You need to tune transfer chunk size, retry count, and delta encoding to minimize total update time while maximizing success rate across devices with varying connectivity. A full factorial design with 3 factors is inexpensive and reveals whether delta encoding's bandwidth savings interact with chunk size and retry behavior.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (update_time_sec, success_rate_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| chunk_size_kb | 1 | 64 | KB | OTA transfer chunk size |
| retry_count | 1 | 5 | retries | Chunk retry count on failure |
| delta_encoding | off | on |  | Delta/differential firmware updates |

**Fixed:** transport = coap, compression = lz4

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| update_time_sec | minimize | sec |
| success_rate_pct | maximize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template firmware_ota_strategy
cd firmware_ota_strategy
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
