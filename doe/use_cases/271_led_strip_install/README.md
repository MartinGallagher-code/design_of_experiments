# Use Case 271: LED Strip Installation

## Scenario

You are installing 12V warm-white LED strips for architectural under-cabinet lighting and need to achieve uniform brightness across the full run while preventing thermal hot spots that shorten LED life. LED density per meter, power supply headroom percentage, and diffuser-to-LED spacing all interact -- packing more LEDs improves uniformity but increases heat, while moving the diffuser farther away smooths the light but reduces efficiency. A Box-Behnken design efficiently explores these three continuous factors without testing the extreme corner of maximum density at minimum diffuser distance, which would guarantee overheating.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (uniformity_pct, hotspot_temp_c)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| leds_per_m | 30 | 120 | LEDs/m | LED density per meter |
| psu_headroom_pct | 10 | 40 | % | Power supply overhead above rated load |
| diffuser_mm | 5 | 30 | mm | Diffuser distance from LEDs |

**Fixed:** voltage = 12V, color = warm_white

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| uniformity_pct | maximize | % |
| hotspot_temp_c | minimize | C |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template led_strip_install
cd led_strip_install
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
