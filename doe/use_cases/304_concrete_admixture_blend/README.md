# Use Case 304: Concrete Admixture Blend Optimization

## Scenario

You are formulating a supplementary cementitious material blend of fly ash, silica fume, and ground granulated blast-furnace slag to add to a 350 kg/m3 cement base at 0.45 w/c ratio, and need to maximize 28-day compressive strength while maintaining workable slump. The three admixture proportions must sum to 100%, creating a constrained mixture space where standard factorial designs do not apply. A mixture simplex lattice design places experimental points systematically across this triangular composition space, fitting Scheffe polynomials that respect the sum-to-one constraint and reveal synergy or antagonism between the pozzolanic materials.

**This use case demonstrates:**
- Mixture Simplex Lattice design
- Multi-response analysis (compressive_strength_28d, workability)
- Mixture modeling with Scheffe polynomials
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| fly_ash | 0 | 100 | % | Fly ash proportion of admixture blend |
| silica_fume | 0 | 100 | % | Silica fume proportion of admixture blend |
| slag | 0 | 100 | % | Ground granulated blast-furnace slag proportion |

**Fixed:** cement_base = 350 kg/m3, water_cement_ratio = 0.45

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| compressive_strength_28d | maximize | MPa |
| workability | maximize | mm_slump |

## Why Mixture Simplex Lattice?

- Designed for mixture experiments where factor proportions must sum to a fixed total
- Places points on a lattice across the simplex, providing uniform coverage of the mixture space
- Fits Scheffe polynomial models that respect the mixture constraint
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template concrete_admixture_blend
cd concrete_admixture_blend
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
