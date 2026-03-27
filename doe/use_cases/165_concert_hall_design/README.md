# Use Case 165: Concert Hall Acoustic Design

## Scenario

You are designing an 800-seat concert hall with hardwood flooring and need to determine which architectural parameters -- ceiling height, width-to-length ratio, surface absorption (NRC), diffusion index, and stage riser height -- most strongly influence acoustic clarity (C80) and tonal warmth. Building physical scale models or running full acoustic simulations for every possible combination is prohibitively expensive at this design stage. A Plackett-Burman screening design identifies the two or three dominant geometric factors in minimal simulation runs, guiding the architect toward the most acoustically impactful design decisions.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (clarity_c80, warmth_index)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| ceiling_m | 8 | 18 | m | Ceiling height |
| width_ratio | 0.5 | 0.9 | ratio | Width-to-length ratio |
| absorption_nrc | 0.3 | 0.7 | NRC | Average absorption coefficient |
| diffusion_idx | 0.2 | 0.8 | index | Diffusion index |
| stage_riser_m | 0.3 | 1.2 | m | Stage riser height |

**Fixed:** seats = 800, floor_material = hardwood

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| clarity_c80 | maximize | dB |
| warmth_index | maximize | ratio |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template concert_hall_design
cd concert_hall_design
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
