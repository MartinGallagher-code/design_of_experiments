# Design of Experiments — Fundamentals & Practical Guide

## What is Design of Experiments?

Design of Experiments (DOE) is a systematic method for planning experiments to efficiently extract the maximum amount of information from the minimum number of runs. Instead of changing one variable at a time (OVAT), DOE changes multiple factors simultaneously according to a mathematically optimal plan, then uses statistical analysis to untangle each factor's individual and combined effects.

DOE was developed by Ronald Fisher in the 1920s for agricultural research and has since become a cornerstone of quality engineering, manufacturing optimization, software performance tuning, and scientific research.

### Why not just change one thing at a time?

The one-variable-at-a-time approach has three fundamental problems:

1. **It misses interactions.** If temperature and pressure together produce an effect that neither produces alone, OVAT will never detect it. DOE tests combinations and reveals these interactions.

2. **It's inefficient.** To test 3 factors at 2 levels each, OVAT needs at least 6 runs and only tells you about one factor per run. A full factorial does it in 8 runs and tells you about every factor and every 2-way interaction in every run.

3. **It confuses noise with signal.** When you change one factor and observe a difference, was it the factor or just random variation? DOE uses replication and blocking to separate real effects from noise.

---

## Core Concepts

### Factors and Levels

A **factor** is a variable you can control. Each factor has **levels** — the specific values you will test.

| Term | Example |
|------|---------|
| Factor | Reactor temperature |
| Levels | 150°C (low), 200°C (high) |
| Continuous factor | Temperature: any value in a range |
| Categorical factor | Catalyst type: A or B |

### Responses

A **response** is the outcome you measure. You can have multiple responses per experiment.

| Response | Direction | Unit |
|----------|-----------|------|
| Yield | maximize | % |
| Purity | maximize | % |
| Cost | minimize | USD |

### Main Effects

The **main effect** of a factor is the average change in the response when that factor moves from its low level to its high level. If temperature's main effect on yield is +8%, then increasing temperature from low to high increases yield by 8% on average, across all combinations of the other factors.

### Interaction Effects

An **interaction** between two factors means the effect of one factor depends on the level of the other. For example:
- At low pressure, increasing temperature raises yield by 12%
- At high pressure, increasing temperature raises yield by only 4%

The interaction effect is (12% - 4%) / 2 = 4%. This is invisible to one-variable-at-a-time testing.

### Blocking

**Blocking** accounts for known sources of variation that you cannot or do not want to eliminate. If you must run experiments over two days and day-to-day conditions vary, you assign blocks (day 1, day 2) and randomize within each block. This prevents day-to-day variation from being confused with factor effects.

### Randomization

**Randomization** is the deliberate shuffling of run order within each block. It protects against unknown lurking variables (e.g., equipment drift, operator fatigue) by ensuring they affect all factor combinations equally on average.

---

## Design Types

### Full Factorial

**What:** Tests every possible combination of factor levels.

**When to use:** You have 2–4 factors with 2–3 levels each, and you need complete information about all main effects and interactions.

**Runs:** For k factors at 2 levels each: 2^k runs. (2 factors = 4 runs, 3 factors = 8 runs, 4 factors = 16 runs)

**Example:**
```
Temperature:  low   low   high  high
Pressure:     low   high  low   high
─────────────────────────────────────
Run 1:        low   low              → measure response
Run 2:        low   high             → measure response
Run 3:        high  low              → measure response
Run 4:        high  high             → measure response
```

**Strengths:** Complete picture. Estimates all main effects and all interactions with no confounding.

**Weakness:** Run count grows exponentially. 7 factors × 2 levels = 128 runs.

```bash
# Full factorial with this tool:
# config.json: "operation": "full_factorial"
python doe.py generate --config config.json --seed 42
```

### Fractional Factorial

**What:** A carefully chosen subset of the full factorial that still estimates main effects and some interactions, but with fewer runs.

**When to use:** You have 5+ factors and cannot afford a full factorial, but want to screen which factors matter most.

**Runs:** 2^(k-p) where p is the number of factors aliased with interactions. For 7 factors: 2^(7-4) = 8 runs instead of 128.

**Strengths:** Dramatically fewer runs. Still estimates all main effects.

**Weakness:** Some effects are **confounded** (aliased) with each other — you cannot distinguish them. Higher resolution designs reduce this problem but require more runs.

**Resolution:**
- Resolution III: Main effects are confounded with 2-factor interactions
- Resolution IV: Main effects are clear; 2-factor interactions are confounded with each other
- Resolution V: Main effects and 2-factor interactions are both clear

```bash
# Fractional factorial with this tool:
# config.json: "operation": "fractional_factorial"
python doe.py generate --config config.json --seed 42
```

### Plackett-Burman

**What:** A 2-level screening design that efficiently estimates main effects in the fewest possible runs.

**When to use:** You have many factors (5–20+) and want to quickly identify the vital few that matter, before investing in a more detailed design.

**Runs:** Always a multiple of 4. For up to 7 factors: 8 runs. Up to 11 factors: 12 runs.

**Strengths:** Very efficient — screens many factors quickly.

**Weakness:** Cannot estimate interactions. Only tells you which factors have large main effects.

```bash
# Plackett-Burman with this tool:
# config.json: "operation": "plackett_burman"
python doe.py generate --config config.json --seed 42
```

### Latin Hypercube Sampling

**What:** A space-filling design that divides each factor's range into equal-probability intervals and samples exactly once from each interval.

**When to use:** You have continuous factors, want to explore a wide parameter space, and don't need a structured factorial grid. Common in simulation, computer experiments, and sensitivity analysis.

**Runs:** You choose the sample count (default: max(10, 2 × n_factors)).

**Strengths:** Good space coverage with relatively few runs. Works well with any number of factors.

**Weakness:** Not optimal for estimating specific effects or interactions — better suited for building surrogate models.

```bash
# Latin Hypercube with this tool:
# config.json: "operation": "latin_hypercube", "lhs_samples": 20
python doe.py generate --config config.json --seed 42
```

### Central Composite Design (CCD)

**What:** A response surface design that augments a 2-level factorial with center points and star (axial) points. This allows fitting a quadratic model.

**When to use:** You have 2–5 continuous factors and want to find the optimum (peak or valley) of a response surface — not just which factors matter, but the exact settings that maximize or minimize the response.

**Runs:** 2^k (factorial) + 2k (star) + center points. For 3 factors: 8 + 6 + 4 = 18 runs.

**Strengths:** Fits a full quadratic model (linear + interaction + squared terms). Can find the true optimum within the design space.

**Weakness:** Requires numeric factor levels. Star points extend beyond the factorial range, which may be infeasible in some physical systems.

```bash
# Central Composite Design with this tool:
# config.json: "operation": "central_composite"
python doe.py generate --config config.json --seed 42
```

### Box-Behnken

**What:** Another response surface design, but one that avoids extreme corner points. Each run has at most two factors at their extreme levels; the remaining factors are at their center.

**When to use:** Same situations as CCD, but when corner points are infeasible or dangerous (e.g., running a reactor at maximum temperature AND maximum pressure simultaneously).

**Runs:** For 3 factors: 15 runs. For 4 factors: 27 runs.

**Strengths:** Avoids extreme combinations. All points lie within the safe operating region. Fits a quadratic model.

**Weakness:** Requires at least 3 factors. Requires numeric levels. Slightly less information about extreme corners compared to CCD.

```bash
# Box-Behnken with this tool:
# config.json: "operation": "box_behnken"
python doe.py generate --config config.json --seed 42
```

---

## Choosing the Right Design

```
How many factors?
│
├─ 2-4 factors, want complete picture
│  → Full Factorial
│
├─ 5+ factors, want to screen which matter
│  ├─ Need some interaction info → Fractional Factorial
│  └─ Only need main effects    → Plackett-Burman
│
├─ 2-5 continuous factors, want to find the optimum
│  ├─ Extreme corners are OK    → Central Composite Design
│  └─ Avoid extreme corners     → Box-Behnken
│
└─ Many continuous factors, exploratory/simulation
   → Latin Hypercube Sampling
```

### The Sequential Strategy

In practice, DOE is iterative:

1. **Screen** (Plackett-Burman or Fractional Factorial): Test 10+ factors in 12–16 runs. Identify the 3–5 that matter.
2. **Characterize** (Full Factorial): Run a complete design on the important factors. Estimate interactions.
3. **Optimize** (CCD or Box-Behnken): Fit a response surface model on the key factors. Find the optimal operating point.
4. **Confirm**: Run a few verification experiments at the predicted optimum.

---

## Analysis Techniques

### Main Effects Analysis

For each factor, compute the average response at each level. The main effect is the difference between the high and low averages. Rank factors by the absolute magnitude of their effects to identify which matter most.

The **Pareto chart** displays factors sorted by effect magnitude with a cumulative contribution line. Factors above the 80% line are the "vital few."

### Interaction Effects

For each pair of 2-level factors, compute the interaction effect:
- Group runs where both factors are concordant (both high or both low)
- Group runs where factors are discordant (one high, one low)
- Interaction = mean(concordant) - mean(discordant)

A large interaction means the factors have a synergistic or antagonistic relationship.

### Confidence Intervals

A 95% confidence interval on a main effect tells you: if you repeated the entire experiment many times, 95% of the intervals would contain the true effect. If the interval includes zero, the effect is not statistically significant at the 5% level.

This tool computes CIs using the pooled t-test for 2-level factors.

### Response Surface Modeling (RSM)

RSM fits a polynomial regression model to the experimental data:

- **Linear model:** response = β₀ + β₁x₁ + β₂x₂ + ... + ε
- **Quadratic model:** adds interaction terms (β₁₂x₁x₂) and squared terms (β₁₁x₁²)

The R² statistic tells you how well the model explains the observed variation (0 = useless, 1 = perfect fit). The adjusted R² penalizes for model complexity.

RSM is most useful with CCD and Box-Behnken designs, which provide enough data points to fit quadratic models and find the true optimum.

---

## Using This Tool

### Step-by-Step Workflow

**1. Define the problem**

What are you trying to optimize or understand? What factors can you control? What responses will you measure?

**2. Create a configuration file**

```json
{
    "metadata": {
        "name": "My experiment",
        "description": "What I'm trying to learn"
    },
    "factors": [
        {"name": "factor_a", "levels": ["1", "10"], "type": "continuous", "unit": "units"},
        {"name": "factor_b", "levels": ["low", "high"], "type": "categorical"}
    ],
    "responses": [
        {"name": "throughput", "optimize": "maximize", "unit": "ops/sec"},
        {"name": "latency",   "optimize": "minimize", "unit": "ms"}
    ],
    "settings": {
        "operation": "full_factorial",
        "test_script": "my_test.sh",
        "out_directory": "results"
    }
}
```

**3. Preview and generate**

```bash
# See what the design looks like
python doe.py info --config config.json

# Generate the runner script
python doe.py generate --config config.json --output run.sh --seed 42
```

**4. Write your test script**

Your test script receives factor values and must write a JSON result file:

```bash
#!/bin/bash
# my_test.sh — receives --factor_a VALUE --factor_b VALUE --out PATH
# Run your actual experiment/benchmark here, then write results:
echo "{\"throughput\": 1234.5, \"latency\": 12.3}" > "$OUT_PATH"
```

**5. Execute**

```bash
bash run.sh
```

**6. Analyze**

```bash
# Terminal output with main effects, interactions, stats
python doe.py analyze --config config.json

# Get optimization recommendations with RSM
python doe.py optimize --config config.json

# Generate a shareable HTML report
python doe.py report --config config.json --output report.html

# Export to CSV for further analysis
python doe.py analyze --config config.json --csv results/csv
```

### Application: Software Performance Benchmarking

DOE is particularly powerful for performance engineering. Instead of guessing which configuration knobs matter, you can systematically test them.

**Example: Database tuning**
```json
{
    "factors": [
        {"name": "innodb_buffer_pool_size", "levels": ["1G", "4G"], "type": "categorical"},
        {"name": "innodb_io_capacity",      "levels": ["200", "2000"], "type": "continuous"},
        {"name": "max_connections",          "levels": ["100", "500"], "type": "continuous"},
        {"name": "query_cache_size",         "levels": ["0", "256M"], "type": "categorical"},
        {"name": "thread_pool_size",         "levels": ["4", "16"], "type": "continuous"}
    ],
    "responses": [
        {"name": "tps",     "optimize": "maximize", "unit": "tx/sec"},
        {"name": "p99_lat", "optimize": "minimize", "unit": "ms"}
    ],
    "settings": {
        "operation": "plackett_burman",
        "test_script": "bench.sh",
        "block_count": 2,
        "out_directory": "results/db_bench"
    }
}
```

With Plackett-Burman, this tests 5 factors in only 8 runs (× 2 blocks = 16 total). The analysis immediately tells you which knobs actually affect performance and which are noise.

**Example: Compiler optimization**
```json
{
    "factors": [
        {"name": "opt_level",    "levels": ["-O1", "-O2", "-O3"], "type": "ordinal"},
        {"name": "lto",          "levels": ["off", "thin", "full"], "type": "categorical"},
        {"name": "march",        "levels": ["native", "x86-64-v3"], "type": "categorical"}
    ],
    "responses": [
        {"name": "runtime_sec",  "optimize": "minimize", "unit": "sec"},
        {"name": "binary_size",  "optimize": "minimize", "unit": "MB"}
    ],
    "settings": {
        "operation": "full_factorial",
        "test_script": "compile_and_bench.sh",
        "out_directory": "results/compiler"
    }
}
```

3 factors × 3 levels × 2 levels = 18 runs, giving a complete picture of how compiler flags interact to affect runtime and binary size.

### Application: Scientific Experiments

**Example: Chemical process optimization (Box-Behnken)**
```json
{
    "factors": [
        {"name": "temperature", "levels": ["150", "200"], "type": "continuous", "unit": "°C"},
        {"name": "pressure",    "levels": ["2", "6"],     "type": "continuous", "unit": "bar"},
        {"name": "catalyst",    "levels": ["0.5", "2.0"], "type": "continuous", "unit": "g/L"}
    ],
    "responses": [
        {"name": "yield",  "optimize": "maximize", "unit": "%"},
        {"name": "purity", "optimize": "maximize", "unit": "%"}
    ],
    "settings": {
        "operation": "box_behnken",
        "test_script": "run_reactor.sh",
        "out_directory": "results/reactor"
    }
}
```

Box-Behnken avoids running the reactor at all extreme corners simultaneously (safest for physical experiments), while still providing enough data to fit a quadratic model and find the optimal temperature/pressure/catalyst combination.

---

## Key Takeaways

1. **DOE beats guessing.** A structured experiment with 15 runs will teach you more than 100 unplanned runs.

2. **Start by screening.** Use Plackett-Burman or fractional factorial to find the vital few factors, then invest runs in understanding those deeply.

3. **Interactions are real and common.** If you only test one factor at a time, you will miss them and draw wrong conclusions.

4. **Randomize and block.** These two practices protect you from hidden variables that can invalidate your results.

5. **Use response surface designs to optimize.** Once you know which factors matter, CCD or Box-Behnken will find the sweet spot.

6. **Automate the workflow.** This tool handles the math and generates executable scripts — you focus on defining the problem and interpreting the results.

---

## Further Reading

- Box, G.E.P., Hunter, J.S., & Hunter, W.G. (2005). *Statistics for Experimenters*. Wiley.
- Montgomery, D.C. (2017). *Design and Analysis of Experiments*. Wiley.
- NIST/SEMATECH e-Handbook of Statistical Methods: https://www.itl.nist.gov/div898/handbook/
