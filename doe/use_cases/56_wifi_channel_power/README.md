# Use Case 56: WiFi Channel & Power

## Scenario

You are deploying WiFi 6 access points on the 5 GHz band in a high-density office environment and need to balance throughput against coverage radius. There are 5 parameters to tune -- channel width, transmit power, guard interval, beamforming, and MIMO spatial streams -- but site surveys are time-consuming. A fractional factorial design screens these factors efficiently, revealing whether wider channels or more spatial streams matter most for your specific floor plan.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (throughput_mbps, coverage_m)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| channel_width | 20 | 80 | MHz | Channel bandwidth |
| tx_power | 10 | 23 | dBm | Transmit power level |
| guard_interval | short | long |  | Guard interval |
| beamforming | off | on |  | Explicit beamforming |
| spatial_streams | 1 | 4 | count | MIMO spatial streams |

**Fixed:** standard = wifi6, band = 5GHz

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_mbps | maximize | Mbps |
| coverage_m | maximize | m |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template wifi_channel_power
cd wifi_channel_power
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
