# Use Case 67: Smart Sensor Sampling

## Scenario

You are configuring an ESP32 with a BME280 environmental sensor for a battery-powered IoT deployment where the device must last months on a single charge. There are 5 parameters to balance -- ADC sample rate, resolution, averaging window, sleep mode depth, and wakeup interval -- where higher accuracy demands more frequent sampling and higher resolution, directly increasing power draw. A fractional factorial design screens which of these settings most affect the accuracy-versus-battery-life trade-off.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (measurement_accuracy_pct, power_consumption_mw)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| sample_rate_hz | 1 | 100 | Hz | ADC sample rate |
| adc_resolution_bits | 8 | 16 | bits | ADC resolution |
| averaging_window | 1 | 32 | samples | Moving average window size |
| sleep_mode_depth | 1 | 4 | level | Deep sleep mode level |
| wakeup_interval_sec | 1 | 60 | sec | Wakeup interval from sleep |

**Fixed:** mcu = esp32, sensor = bme280

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| measurement_accuracy_pct | maximize | % |
| power_consumption_mw | minimize | mW |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template smart_sensor_sampling
cd smart_sensor_sampling
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
