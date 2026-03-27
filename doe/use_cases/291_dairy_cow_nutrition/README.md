# Use Case 291: Dairy Cow Feed Ration

## Scenario

You are formulating a total mixed ration for mid-lactation Holstein dairy cows and need to maximize daily milk production while minimizing feed cost per cow. Forage-to-concentrate ratio, crude protein percentage, and net energy for lactation all interact -- pushing concentrate too high boosts milk yield but risks ruminal acidosis, while excess protein is expensive and excreted as nitrogen waste. A Box-Behnken design avoids the extreme corner of high concentrate, high protein, and high energy that would be metabolically dangerous, while fitting the curved production response needed to find the economically optimal ration.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (milk_kg_day, feed_cost_day)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| forage_pct | 40 | 70 | % | Forage as percentage of total DMI |
| protein_pct | 14 | 20 | %CP | Crude protein percentage |
| energy_mcal | 1.5 | 1.8 | Mcal/kg | Net energy for lactation |

**Fixed:** breed = holstein, lactation_stage = mid

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| milk_kg_day | maximize | kg/day |
| feed_cost_day | minimize | USD/day |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template dairy_cow_nutrition
cd dairy_cow_nutrition
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
