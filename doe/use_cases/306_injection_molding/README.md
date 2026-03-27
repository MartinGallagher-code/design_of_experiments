# Use Case 306: Injection Molding Quality

## Scenario

You are optimizing an injection molding process for a 45g part in a P20 steel mold, balancing four competing quality responses: surface finish, dimensional accuracy, cycle time, and warpage deflection. Melt temperature, injection pressure, and cooling time interact nonlinearly -- higher melt temperature improves flow and surface finish but increases cycle time and warpage risk, while excessive pressure causes flash and residual stress. A central composite design fits the quadratic response surfaces needed to navigate this four-response trade-off space, with axial points that explore conditions beyond the nominal process window.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (surface_finish, dimensional_accuracy, cycle_time, warpage)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| melt_temp | 200 | 280 | C | Melt temperature |
| injection_pressure | 50 | 120 | MPa | Injection pressure |
| cooling_time | 10 | 30 | s | Cooling time in mold |

**Fixed:** mold_material = P20_steel, part_weight = 45g

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| surface_finish | maximize | Ra_um |
| dimensional_accuracy | maximize | % |
| cycle_time | minimize | s |
| warpage | minimize | mm |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template injection_molding
cd injection_molding
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
