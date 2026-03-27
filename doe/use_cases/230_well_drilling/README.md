# Use Case 230: Water Well Drilling Parameters

## Scenario

You are completing a 150 mm cased water well in an alluvial sand aquifer and need to maximize sustainable pumping rate while minimizing turbidity by adjusting well depth, screen slot opening size, and gravel pack grain size. The screen-gravel interaction is critical -- slots too wide for the gravel pack pass sand, while too-fine gravel restricts flow at depth. A central composite design models these nonlinear hydraulic relationships and its axial points let you explore depths and slot sizes slightly beyond the initial range to locate the optimal well completion parameters.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (flow_rate_lpm, turbidity_ntu)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| depth_m | 15 | 60 | m | Well depth |
| screen_slot_mm | 0.5 | 2.0 | mm | Well screen slot opening size |
| gravel_mm | 2 | 8 | mm | Gravel pack grain size |

**Fixed:** aquifer = alluvial_sand, casing_diam = 150mm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| flow_rate_lpm | maximize | L/min |
| turbidity_ntu | minimize | NTU |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template well_drilling
cd well_drilling
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
