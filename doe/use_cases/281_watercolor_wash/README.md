# Use Case 281: Watercolor Wash Technique

## Scenario

You are laying a flat watercolor wash with ultramarine pigment on 300gsm cold-press paper and want to achieve even color coverage while avoiding unwanted blooms and backruns. Water-to-pigment ratio, paper pre-wetting level, and brush angle to the surface all interact -- wetter paper forgives uneven strokes but invites blooming, while a steep brush angle deposits more pigment but creates streaks. A Box-Behnken design is well-suited because it avoids the extreme corners where simultaneous maximum wetness and steep angles would guarantee runaway blooms.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (evenness, blooming)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| water_ratio | 2 | 8 | ratio | Water-to-pigment volume ratio |
| paper_wetness | 1 | 5 | level | Paper pre-wetting level (1=dry, 5=saturated) |
| brush_angle_deg | 15 | 60 | deg | Brush angle to paper surface |

**Fixed:** paper = 300gsm_cold_press, pigment = ultramarine

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| evenness | maximize | pts |
| blooming | minimize | pts |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template watercolor_wash
cd watercolor_wash
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
