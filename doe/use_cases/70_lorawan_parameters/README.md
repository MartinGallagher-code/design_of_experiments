# Use Case 70: LoRaWAN Parameters

## Scenario

You are deploying LoRaWAN sensor nodes on the 915 MHz ISM band with 125 kHz bandwidth and need to maximize communication range while preserving battery life measured in years. The fundamental trade-off is link budget versus energy consumption: higher spreading factors (SF7-SF12) and transmit power increase range but exponentially increase time-on-air and drain the coin-cell battery, while stronger forward error correction (coding rate 4/5 to 4/8) improves reliability in noisy environments at the cost of additional airtime. A Central Composite design captures the curved interactions between these 3 parameters, essential because range gains from higher SF plateau due to duty-cycle limits.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (range_km, battery_life_days)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| spreading_factor | 7 | 12 | SF | LoRa spreading factor |
| tx_power_dbm | 2 | 20 | dBm | Transmit power level |
| coding_rate | 5 | 8 | CR | Forward error correction coding rate (4/x) |

**Fixed:** frequency = 915MHz, bandwidth = 125kHz

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| range_km | maximize | km |
| battery_life_days | maximize | days |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template lorawan_parameters
cd lorawan_parameters
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
