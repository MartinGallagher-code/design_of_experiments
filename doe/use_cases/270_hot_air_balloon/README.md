# Use Case 270: Hot Air Balloon Flight Planning

## Scenario

You are planning commercial hot air balloon flights with a fixed 100kg fuel load at 15C ambient temperature and need to maximize both flight duration and altitude ceiling. Burner BTU output, envelope volume, and passenger count create a fundamental trade-off: more passengers require more lift capacity and burn fuel faster, while a larger envelope gains altitude but increases cooling surface area. A Box-Behnken design avoids the dangerous corner condition of maximum passengers in the smallest envelope with the weakest burner, while still fitting the quadratic model needed for this nonlinear thermodynamic system.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (flight_hrs, ceiling_m)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| burner_btu | 6000000 | 12000000 | BTU/hr | Burner heat output |
| envelope_m3 | 2000 | 4000 | m3 | Envelope volume |
| passengers | 2 | 8 | count | Number of passengers |

**Fixed:** fuel_kg = 100, ambient_temp = 15C

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| flight_hrs | maximize | hrs |
| ceiling_m | maximize | m |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template hot_air_balloon
cd hot_air_balloon
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
