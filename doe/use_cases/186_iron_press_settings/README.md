# Use Case 186: Garment Pressing Settings

## Scenario

You are pressing a wool-blend garment through a press cloth and need to achieve razor-sharp creases without causing fabric shine or glazing. The three controllable parameters -- iron sole plate temperature, steam output rate, and pressing duration -- interact nonlinearly: too much heat with prolonged contact causes irreversible shine, while insufficient steam yields weak creases. A central composite design maps the curved response surface and its axial points help predict behavior at temperatures and steam rates slightly beyond the initial range.

**This use case demonstrates:**
- Central Composite design
- Multi-response analysis (crease_sharpness, shine_risk)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| iron_temp_c | 110 | 200 | C | Iron sole plate temperature |
| steam_g_min | 0 | 40 | g/min | Steam output rate |
| press_sec | 3 | 15 | sec | Pressing duration per area |

**Fixed:** fabric = wool_blend, press_cloth = yes

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| crease_sharpness | maximize | pts |
| shine_risk | minimize | pts |

## Why Central Composite?

- An RSM design that adds axial (star) points to a factorial core for fitting quadratic models
- Provides excellent predictions across the full factor space including beyond the original ranges
- Can be executed in blocks, separating the factorial, axial, and center-point portions
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template iron_press_settings
cd iron_press_settings
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
