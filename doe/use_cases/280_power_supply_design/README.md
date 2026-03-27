# Use Case 280: Linear Power Supply Regulation

## Scenario

You are designing a linear regulated 12V power supply around an LM317 and need to minimize both load regulation percentage and output ripple voltage. Transformer secondary voltage, filter capacitor value, and regulator dropout voltage interact nonlinearly -- a higher transformer tap improves regulation headroom but increases heat dissipation in the regulator, while larger filter caps reduce ripple but have diminishing returns and take more board space. A central composite design maps these curved relationships with axial points that probe beyond the initial component ranges to find the optimal balance of regulation, ripple, and thermal performance.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (load_reg_pct, ripple_mv)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| transformer_v | 12 | 24 | V | Transformer secondary voltage |
| filter_uf | 1000 | 10000 | uF | Filter capacitor value |
| dropout_v | 1 | 4 | V | Regulator minimum dropout voltage |

**Fixed:** regulator = LM317, output = 12V

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| load_reg_pct | minimize | % |
| ripple_mv | minimize | mV_pp |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template power_supply_design
cd power_supply_design
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
