# Use Case 272: PCB Soldering Parameters

## Scenario

You are hand-soldering through-hole PCB components with a chisel tip and rosin flux, and need to maximize joint quality scores while minimizing solder bridge defects per 100 joints. Iron tip temperature, contact duration, and solder wire diameter interact in nonlinear ways -- too hot or too long causes pad lift and bridging, while too cool yields cold joints. A central composite design fits the curved response surface that captures these thermal-window effects and identifies the optimal iron settings with axial points extending beyond the initial range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (joint_quality, bridge_rate)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| iron_temp_c | 280 | 380 | C | Soldering iron tip temperature |
| contact_sec | 1 | 5 | sec | Iron contact duration |
| solder_mm | 0.5 | 1.2 | mm | Solder wire diameter |

**Fixed:** flux = rosin, tip = chisel_2mm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| joint_quality | maximize | pts |
| bridge_rate | minimize | per_100 |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template pcb_soldering
cd pcb_soldering
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
