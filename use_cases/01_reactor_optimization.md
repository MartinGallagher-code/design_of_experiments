# Use Case 1: Chemical Reactor Optimization

## Scenario

You are optimizing a batch chemical reactor. You can control three continuous process parameters and want to maximize product yield and purity while minimizing production cost. Running the reactor at all extreme settings simultaneously is risky, so you need a design that avoids corner points.

**This use case demonstrates:**
- Box-Behnken design (avoids extreme corners, fits quadratic models)
- Multi-response analysis (yield, purity, cost — each with different optimization directions)
- Response Surface Methodology (RSM) for finding the predicted optimum
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| temperature | 150 | 200 | °C | Reactor temperature |
| pressure | 2 | 6 | bar | Operating pressure |
| catalyst | 0.5 | 2.0 | g/L | Catalyst concentration |

**Fixed:** reaction_time = 60 min, stirring_speed = 300 rpm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| yield | maximize | % |
| purity | maximize | % |
| cost | minimize | USD |

## Why Box-Behnken?

- We have 3 continuous factors — the minimum for Box-Behnken
- We want to avoid testing extreme corners (e.g., max temperature + max pressure + max catalyst simultaneously) for safety reasons
- We want to fit a quadratic model to find the true optimum, not just compare high vs. low
- Box-Behnken gives us 15 runs (vs. 18 for CCD), all within the safe operating region

## Running the Demo

### Prerequisites

```bash
cd /workspaces/design_of_experiments
pip install -r requirements.txt
```

### Step 1: Preview the design

```bash
python doe.py info --config examples/reactor_config.json
```

Output:
```
Plan      : Chemical Reactor Optimization
Operation : box_behnken
Factors   : temperature, pressure, catalyst
Base runs : 15
Blocks    : 1
Total runs: 15
Responses : yield [maximize] (%), purity [maximize] (%), cost [minimize] (USD)
Fixed     : reaction_time=60, stirring_speed=300
```

Notice the Box-Behnken structure: each run has at most two factors at their extremes, while the third stays at center (175°C, 4 bar, 1.25 g/L). Three center-point replicates provide an estimate of pure error.

### Step 2: Generate the runner script

```bash
python doe.py generate --config examples/reactor_config.json \
    --output results/reactor/run.sh --seed 42
```

### Step 3: Execute the experiments

```bash
bash results/reactor/run.sh
```

The simulated reactor produces realistic data: yield follows a quadratic model with temperature as the dominant factor, purity is driven by catalyst concentration, and cost increases with all factors.

### Step 4: Analyze results

```bash
python doe.py analyze --config examples/reactor_config.json
```

Key findings from the analysis:

**Yield:** Temperature and catalyst are the dominant factors (~42% and ~32% contribution). Pressure has a moderate effect (~27%).

**Purity:** Catalyst concentration is the key driver (~44%), followed by pressure (~47%). Temperature has minimal impact (~9%).

**Cost:** All three factors contribute roughly equally, with pressure and catalyst slightly ahead of temperature.

### Step 5: Get optimization recommendations

```bash
python doe.py optimize --config examples/reactor_config.json
```

The optimizer reports:
- **Best observed yield:** Found at a specific temperature/pressure/catalyst combination
- **RSM model fit:** Linear R² values indicate how well a simple model explains each response
- **Factor importance ranking:** Which factors to focus on for each response

### Step 6: Generate the HTML report

```bash
python doe.py report --config examples/reactor_config.json \
    --output results/reactor/report.html
```

Open `results/reactor/report.html` in a browser. The report includes:
- Design summary with factor details
- Main effects and interaction tables for each response
- Pareto charts showing which factors matter most
- Main effects plots showing the response trend at each factor level
- Full design matrix with all run data

### Step 7: Export to CSV (optional)

```bash
python doe.py analyze --config examples/reactor_config.json \
    --csv results/reactor/csv
```

Produces CSV files for further analysis in R, Excel, or pandas.

## Interpreting the Results

### Trade-offs

This experiment reveals a classic multi-objective trade-off:
- **Higher temperature** increases yield but also increases cost
- **Higher catalyst** improves purity but adds cost
- **Higher pressure** has moderate effects on all three responses

There is no single setting that maximizes yield AND purity while minimizing cost. The experimenter must decide which response matters most, or find a compromise.

### Next Steps

In a real investigation, you would:

1. **Fit a quadratic RSM model** to each response (the linear model shown by `optimize` is a starting point)
2. **Construct a desirability function** that weights the three responses
3. **Run confirmation experiments** at the predicted optimum
4. **Narrow the factor ranges** and run another Box-Behnken for fine-tuning

## Files

- Config: `examples/reactor_config.json`
- Simulator: `examples/reactor_sim.sh`
- Results: `results/reactor/`
- Report: `results/reactor/report.html`
