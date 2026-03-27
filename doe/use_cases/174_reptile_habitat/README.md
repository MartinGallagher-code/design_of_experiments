# Use Case 174: Reptile Terrarium Setup

## Scenario

You are setting up a 120 cm terrarium for a bearded dragon and need to dial in basking temperature, humidity, UVB output, and substrate depth to maximize natural activity while minimizing stress behaviors like glass surfing and hiding. Because these environmental parameters interact strongly -- high humidity at high basking temperatures can cause respiratory issues, while low UVB with deep substrate reduces thermoregulation opportunities -- a full factorial design is appropriate to capture all interaction effects across just 4 factors.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (activity_score, stress_indicators)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| basking_c | 30 | 40 | C | Basking spot temperature |
| humidity_pct | 30 | 70 | % | Enclosure humidity |
| uvb_pct | 5 | 14 | %UVI | UVB output percentage |
| substrate_cm | 3 | 15 | cm | Substrate depth |

**Fixed:** species = bearded_dragon, enclosure_L = 120cm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| activity_score | maximize | pts |
| stress_indicators | minimize | pts |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template reptile_habitat
cd reptile_habitat
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
