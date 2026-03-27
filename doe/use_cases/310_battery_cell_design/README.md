# Use Case 310: Lithium-Ion Battery Cell Design

## Scenario

You are designing a lithium-ion pouch cell and need to simultaneously maximize energy density, power density, and cycle life by tuning cathode and anode coating thicknesses, electrolyte salt concentration, separator porosity, charge C-rate, and electrode tab width. Thicker electrodes pack more energy but increase ionic resistance and degrade power output, while aggressive charge rates accelerate lithium plating and shorten cycle life. With 6 continuous factors spanning a vast design space, a Latin Hypercube design with 25 runs provides efficient, model-free coverage without assuming any particular response surface shape.

**This use case demonstrates:**
- Latin Hypercube design
- Multi-response analysis (energy_density, power_density, cycle_life)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cathode_thickness | 50 | 150 | microns | Cathode coating thickness |
| anode_thickness | 60 | 120 | microns | Anode coating thickness |
| electrolyte_conc | 0.8 | 1.4 | M | Electrolyte salt concentration |
| separator_porosity | 30 | 60 | % | Separator membrane porosity |
| charge_rate | 0.5 | 3 | C | Charging C-rate |
| tab_width | 10 | 30 | mm | Electrode tab width |

**Fixed:** cell_format = pouch, temperature = 25C

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| energy_density | maximize | Wh/kg |
| power_density | maximize | W/kg |
| cycle_life | maximize | cycles |

## Why Latin Hypercube?

- A space-filling design that ensures each factor level is sampled exactly once per stratum
- Makes no assumptions about the underlying model form, ideal for computer experiments
- Provides good coverage of the entire factor space with a relatively small number of runs
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template battery_cell_design
cd battery_cell_design
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
