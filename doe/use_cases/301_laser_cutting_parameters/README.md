# Use Case 301: Laser Cutting Parameter Optimization

## Scenario

You are dialing in a CO2 laser cutter for 2mm sheet material and need to maximize edge quality while minimizing kerf width across five process parameters: laser power, cutting speed, pulse frequency, focal point offset, and assist gas pressure. These factors likely have both linear and quadratic effects on cut quality -- for example, there is an optimal focal offset where the beam waist sits precisely at the material surface. A definitive screening design is ideal because it detects both main effects and quadratic curvature in just 11 runs while keeping main effects completely unconfounded with two-factor interactions.

**This use case demonstrates:**
- Definitive Screening design
- Multi-response analysis (edge_quality, kerf_width)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| power | 40 | 80 | W | Laser power output |
| speed | 100 | 500 | mm/s | Cutting head travel speed |
| frequency | 5000 | 25000 | Hz | Laser pulse frequency |
| focus_offset | -3 | 3 | mm | Focal point offset from surface |
| gas_pressure | 2 | 8 | bar | Assist gas pressure |

**Fixed:** material_thickness = 2

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| edge_quality | maximize | score |
| kerf_width | minimize | mm |

## Why Definitive Screening?

- A modern 3-level design that efficiently screens factors while detecting quadratic effects
- Requires only 2k+1 runs for k factors, making it very efficient for 4--12 factors
- Avoids confounding of main effects with two-factor interactions, unlike traditional screening designs
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template laser_cutting_parameters
cd laser_cutting_parameters
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
