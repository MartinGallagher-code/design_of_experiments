# Use Case 5: Composite Material Formulation

## Scenario

You are developing a new composite material and need to explore a large, continuous design space. With 4 factors (3 continuous + 1 ordinal), you want good coverage without testing every combination. Latin Hypercube Sampling gives you space-filling coverage that captures the full range of each factor.

**This use case demonstrates:**
- Latin Hypercube design (space-filling for continuous factors)
- Continuous and ordinal factor types
- Custom `lhs_samples` count (20 samples instead of the default)
- `--results-dir` override for analysis
- `--seed` for reproducible LHS sampling
- Multi-response optimization

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| polymer_ratio | 0.3 | 0.8 | continuous | | Polymer-to-resin ratio |
| filler_pct | 5 | 30 | continuous | % | Filler loading percentage |
| cure_temp | 120 | 200 | continuous | C | Curing temperature |
| particle_size | fine, medium, coarse | | ordinal | | Filler particle size grade |

**Fixed:** cure_time_min = 45, ambient_humidity = 50%

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| tensile_strength | maximize | MPa |
| flexibility | maximize | mm |

## Why Latin Hypercube?

- Continuous factors need interpolation, not just high/low — LHS samples across the full range
- 4 factors with 20 samples gives good coverage (default would be max(10, 2×4) = 10)
- The ordinal factor (particle_size) is binned into its 3 levels automatically
- Space-filling "maximin" criterion ensures no clustering of sample points
- Great for building surrogate models or identifying promising regions

## Running the Demo

### Prerequisites

```bash
cd /workspaces/design_of_experiments
pip install -r requirements.txt
```

### Step 1: Preview the design

```bash
python doe.py info --config use_cases/05_material_formulation/config.json
```

Output:
```
Plan      : Composite Material Formulation
Operation : latin_hypercube
Factors   : polymer_ratio, filler_pct, cure_temp, particle_size
Base runs : 20
Blocks    : 1
Total runs: 20
Responses : tensile_strength [maximize] (MPa), flexibility [maximize] (mm)
Fixed     : cure_time_min=45, ambient_humidity=50
```

Notice: 20 runs (from `lhs_samples: 20`) instead of the default 10. The continuous factors show interpolated values (e.g., polymer_ratio = 0.4523) rather than just "low" and "high."

### Step 2: Generate with a seed for reproducibility

```bash
python doe.py generate --config use_cases/05_material_formulation/config.json \
    --output use_cases/05_material_formulation/results/run.sh --seed 99
```

The seed controls numpy's random state for LHS generation, ensuring you get the exact same sample points every time.

### Step 3: Execute the experiments

```bash
bash use_cases/05_material_formulation/results/run.sh
```

### Step 4: Analyze with `--results-dir` override

```bash
python doe.py analyze --config use_cases/05_material_formulation/config.json \
    --results-dir use_cases/05_material_formulation/results
```

The `--results-dir` flag overrides the `out_directory` from the config file. This is useful when:
- Results are stored in a different location than configured
- You want to analyze results from a previous run
- Multiple result sets exist in different directories

### Step 5: Optimize

```bash
python doe.py optimize --config use_cases/05_material_formulation/config.json
```

With 20 LHS samples, the optimizer has a richer dataset to find the best observed point and fit an RSM model. Look for:
- **tensile_strength**: Which factor ranges give the strongest material?
- **flexibility**: Is there a trade-off with strength?

### Step 6: Generate report

```bash
python doe.py report --config use_cases/05_material_formulation/config.json \
    --output use_cases/05_material_formulation/results/report.html
```

## Interpreting the Results

### Continuous Factor Coverage

Unlike 2-level designs where each factor takes only "low" or "high," LHS produces unique values across the entire range. This enables:
- Detecting non-linear effects (e.g., cure_temp has a quadratic effect on tensile strength)
- Building regression models with better interpolation
- Identifying narrow optimal regions within the factor space

### Ordinal Factor Handling

The ordinal factor `particle_size` is binned into its 3 levels (fine, medium, coarse). About 1/3 of the 20 runs will use each level, spread across the LHS sample.

### Next Steps

1. Identify the most promising region from LHS results
2. Narrow the factor ranges around that region
3. Run a Box-Behnken or CCD for precise optimization

## Features Exercised

| Feature | Value |
|---------|-------|
| Design type | `latin_hypercube` |
| Factor types | `continuous` (3) + `ordinal` (1, 3 levels) |
| `lhs_samples` | 20 (custom, overrides default of 10) |
| `--results-dir` | Override at analysis time |
| `--seed` | 99 (controls numpy RNG for LHS) |
| Arg style | `double-dash` |
| Fixed factors | cure_time_min, ambient_humidity |
| Multi-response | tensile_strength + flexibility (both maximize) |

## Files

- Config: `use_cases/05_material_formulation/config.json`
- Simulator: `use_cases/05_material_formulation/sim.sh`
- Results: `use_cases/05_material_formulation/results/`
- Report: `use_cases/05_material_formulation/results/report.html`
