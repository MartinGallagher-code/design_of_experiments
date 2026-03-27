# Use Case 292: Sheep Shearing Technique

## Scenario

You are optimizing machine shearing technique for spring-shorn Merino sheep to maximize preserved wool staple length while minimizing skin nicks per animal. Comb tooth count, cutter RPM, and handpiece blow angle to the skin all interact nonlinearly -- a wide comb at high speed can grab skin folds, while a steep angle with fine teeth leaves excess second cuts that downgrade fleece value. A central composite design maps these curved relationships and uses axial points to explore settings beyond the initial range, helping find the optimal technique for both wool quality and animal welfare.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (staple_length_cm, nick_count)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| comb_teeth | 9 | 17 | teeth | Shearing comb tooth count |
| cutter_rpm | 2000 | 3500 | rpm | Cutter speed |
| blow_angle_deg | 10 | 40 | deg | Handpiece blow angle to skin |

**Fixed:** breed = merino, season = spring

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| staple_length_cm | maximize | cm |
| nick_count | minimize | per_sheep |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template sheep_shearing
cd sheep_shearing
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
