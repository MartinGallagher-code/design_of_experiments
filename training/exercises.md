# DOE Helper Training Course — Student Exercises

Copyright (C) 2026 Martin J. Gallagher. All rights reserved.
Licensed under the GNU General Public License v3.0 or later.

---

## Exercise 1: Explore doe-helper

**Time:** 15 minutes
**Objective:** Install doe-helper, explore the CLI, and understand the config.json structure.

### Instructions

1. **Install doe-helper:**
   ```bash
   pip install doehelper
   ```

2. **Explore the CLI:**
   ```bash
   doe --help
   ```
   List all available commands. How many are there?

3. **Create your first experiment:**
   ```bash
   doe init coffee_brewing --design full_factorial
   ```

4. **Examine the configuration:**
   ```bash
   cat coffee_brewing/config.json
   ```

5. **Answer these questions:**
   - What factors are defined? How many levels does each have?
   - What is the response variable? What is its target?
   - What design type is specified?

### Bonus Challenge
Think of a problem in your own work where One-Variable-At-a-Time (OVAT) testing has been used. Write down:
- The factors that were varied
- The response(s) that were measured
- How many experiments were run
- What interactions might have been missed

---

## Exercise 2: Build a Configuration from Scratch

**Time:** 20 minutes
**Objective:** Create a config.json file manually, verify it, and generate a design matrix.

### Scenario
You are optimising a web application's performance. You suspect three factors affect response time:

| Factor          | Low  | High | Units | Type        |
|-----------------|------|------|-------|-------------|
| cache_size      | 64   | 512  | MB    | Continuous  |
| thread_count    | 4    | 32   | -     | Continuous  |
| compression     | -    | -    | -     | Categorical: "none", "gzip", "brotli" |

**Responses:**
- `response_time_ms` — target: minimize
- `throughput_rps` — target: maximize

### Instructions

1. Create the experiment directory:
   ```bash
   mkdir webapp_perf
   ```

2. Create `webapp_perf/config.json` with the factors and responses above. Use `full_factorial` as the design type.

3. Verify your configuration:
   ```bash
   doe info webapp_perf/
   ```
   - How many runs does the design require?
   - Why is it more than 8? (Hint: how many levels does the categorical factor have?)

4. Generate the design matrix:
   ```bash
   doe generate webapp_perf/
   ```

5. Examine the design matrix:
   ```bash
   cat webapp_perf/design.csv
   ```
   - How are the factor levels represented?
   - Is the order randomised?

6. Export as a worksheet:
   ```bash
   doe export-worksheet webapp_perf/
   ```

### Expected Answers
- The design should have 2 x 2 x 3 = 12 runs (not 8, because compression has 3 levels).
- The design matrix should show coded values (-1/+1 for continuous, actual values for categorical).
- Run order should be randomised (unless `randomize: false` was set).

---

## Exercise 3: Full Factorial — Seal Strength

**Time:** 20 minutes
**Objective:** Run a complete full factorial experiment, analyse results, and interpret the output.

### Setup

Create `seal_strength/config.json`:

```json
{
  "factors": {
    "temperature": {"low": 225, "high": 285, "units": "F"},
    "pressure":    {"low": 40,  "high": 90,  "units": "psi"},
    "dwell_time":  {"low": 1.0, "high": 3.5, "units": "sec"}
  },
  "responses": {
    "seal_strength": {"units": "g/in", "target": "maximize"}
  },
  "design": {
    "type": "full_factorial",
    "center_points": 3
  }
}
```

### Instructions

1. Generate the design:
   ```bash
   doe generate seal_strength/
   ```
   How many runs? (Expected: 8 factorial + 3 center = 11)

2. View design information:
   ```bash
   doe info seal_strength/
   ```

3. Run the simulation:
   ```bash
   bash seal_strength/run.sh
   ```

4. Analyse the results:
   ```bash
   doe analyze seal_strength/
   ```

5. **Answer these questions using the analysis output:**

   a. Which factor has the largest main effect on seal strength?

   b. Are there any statistically significant interactions (p < 0.05)?

   c. Look at the Pareto chart — which effects exceed the significance threshold?

   d. Is there evidence of curvature from the center points?

   e. What does the normal probability plot show?

6. Generate a report:
   ```bash
   doe report seal_strength/
   ```
   Open the HTML report and explore the interactive plots.

### Discussion Points
- How would you have approached this problem with OVAT? How many runs would you have needed?
- If you could only afford 4 runs, which design would you choose?

---

## Exercise 4: Screening a Microservice

**Time:** 20 minutes
**Objective:** Use screening designs to efficiently identify important factors from a large set.

### Scenario
You're tuning a microservice and have identified 8 candidate factors:

| Factor           | Low    | High   | Units  |
|------------------|--------|--------|--------|
| connection_pool  | 5      | 50     | -      |
| request_timeout  | 1      | 30     | sec    |
| retry_limit      | 0      | 5      | -      |
| batch_size       | 10     | 1000   | -      |
| cache_ttl        | 60     | 3600   | sec    |
| thread_count     | 4      | 64     | -      |
| buffer_size_kb   | 4      | 256    | KB     |
| log_level_detail | 1      | 5      | -      |

**Response:** `latency_p99` (units: ms, target: minimize)

### Instructions

1. Create `microservice/config.json` with the 8 factors above.

2. **Plackett-Burman design:**
   ```bash
   # Set design type to "plackett_burman"
   doe generate microservice/
   doe info microservice/
   ```
   How many runs does the PB design require?

3. **Definitive Screening design:**
   Change the design type to `"definitive_screening"` and regenerate:
   ```bash
   doe generate microservice/
   doe info microservice/
   ```
   How many runs does the DSD require?

4. **Compare the two designs:**

   | Aspect                  | Plackett-Burman | Definitive Screening |
   |-------------------------|-----------------|----------------------|
   | Number of runs          |                 |                      |
   | Levels per factor       |                 |                      |
   | Main effects aliased?   |                 |                      |
   | Detects curvature?      |                 |                      |

5. Choose one design, run the simulation, and analyse:
   ```bash
   bash microservice/run.sh
   doe analyze microservice/
   ```

6. **Identify significant factors.** Which 3-4 factors appear to have the largest effects?

7. **Plan a follow-up:** Create a new config with only the significant factors and a `full_factorial` design.

### Expected Answers
- PB for 8 factors: 12 runs
- DSD for 8 factors: 17 runs (2k+1)
- PB: 2 levels, main effects aliased with 2FIs, no curvature detection
- DSD: 3 levels, main effects not aliased with 2FIs, can detect curvature

---

## Exercise 5: Response Surface Optimisation

**Time:** 20 minutes
**Objective:** Use CCD and Box-Behnken designs to model a response surface and find the optimum.

### Setup

Use the reactor_optimization use case:

```json
{
  "factors": {
    "temperature": {"low": 150, "high": 200, "units": "C"},
    "pressure":    {"low": 1.0, "high": 5.0, "units": "bar"},
    "catalyst":    {"low": 0.5, "high": 1.5, "units": "g"}
  },
  "responses": {
    "yield":  {"units": "%", "target": "maximize"},
    "purity": {"units": "%", "target": "maximize"},
    "cost":   {"units": "USD", "target": "minimize"}
  },
  "design": {
    "type": "ccd",
    "center_points": 6
  }
}
```

### Instructions

1. Generate the CCD design:
   ```bash
   doe generate reactor_rsm/
   doe info reactor_rsm/
   ```
   How many runs? What are the three components (factorial, star, center)?

2. Run the simulation and analyse:
   ```bash
   bash reactor_rsm/run.sh
   doe analyze reactor_rsm/
   ```

3. Examine the response surface:
   - Look at the 3D surface plots. Where is the optimum region?
   - Look at the contour plots. Are there any ridges or saddle points?
   - What is the R-squared for each response?

4. Find optimal settings:
   ```bash
   doe optimize reactor_rsm/
   ```
   Record the optimal settings and predicted responses.

5. **Now try Box-Behnken:** Change the design type to `"box_behnken"` and repeat steps 1-4.

6. **Comparison table:**

   | Aspect               | CCD              | Box-Behnken     |
   |----------------------|------------------|-----------------|
   | Number of runs       |                  |                 |
   | Optimal temperature  |                  |                 |
   | Optimal pressure     |                  |                 |
   | Optimal catalyst     |                  |                 |
   | Predicted yield      |                  |                 |
   | R-squared            |                  |                 |

### Discussion
- When would you prefer CCD over Box-Behnken?
- How confident are you in the predicted optimum?

---

## Exercise 6: Analysis Deep Dive

**Time:** 15 minutes
**Objective:** Practice interpreting analysis output and diagnosing model adequacy.

### Instructions

Use the results from Exercise 5 (reactor_rsm with CCD).

1. **ANOVA interpretation:**
   - List all factors/interactions with p < 0.05.
   - Calculate the % contribution of each significant source.
   - Which factor explains the most variability?

2. **Pareto chart:**
   - Do the significant effects from ANOVA match the Pareto chart?
   - Are there any borderline effects (close to the threshold)?

3. **Residual diagnostics:**
   Examine the four-panel residual plot:

   a. Residuals vs. Fitted Values:
      - Is the scatter random, or is there a pattern?
      - Any funnel shape (non-constant variance)?

   b. Normal Q-Q Plot:
      - Do the points follow the diagonal line?
      - Any outliers (points far from the line)?

   c. Residuals vs. Run Order:
      - Any time trend?
      - Any clusters?

   d. Residuals Histogram:
      - Roughly bell-shaped?

4. **Model adequacy:**
   Record: R^2, Adjusted R^2, Predicted R^2
   - Is the gap between Adj and Pred R^2 less than 0.2?
   - Is the model adequate?

5. **Generate the HTML report:**
   ```bash
   doe report reactor_rsm/
   ```
   Write a 3-sentence executive summary of the findings.

### Write-Up Template
```
Executive Summary:
The experiment tested [number] factors in [number] runs using a [design type].
The most significant factors were [list], explaining [X]% of the variability.
The optimal settings are [settings], with a predicted [response] of [value].
```

---

## Exercise 7: Multi-Response Optimisation

**Time:** 15 minutes
**Objective:** Balance competing objectives using desirability functions and augmentation.

### Instructions

1. Use the reactor_rsm experiment with 3 responses:
   - yield (maximize)
   - cost (minimize)
   - purity (target: 99.5%)

2. Run optimisation:
   ```bash
   doe optimize reactor_rsm/
   ```

3. **Interpret the desirability score:**
   - What is the overall desirability (0-1)?
   - Which response is closest to its target?
   - Which response is the most compromised?

4. **Power analysis:**
   ```bash
   doe power reactor_rsm/
   ```
   - What effect size can the design detect at 80% power?
   - Is this adequate for your needs?

5. **Augment the design:**
   ```bash
   doe augment reactor_rsm/ --method center-points --count 4
   ```
   - How does augmentation change the power analysis?
   - How many total runs now?

6. **Compare single vs. multi-response optimisation:**

   | Metric              | Yield-only Optimum | Multi-Response Optimum |
   |---------------------|--------------------|-----------------------|
   | Temperature         |                    |                       |
   | Pressure            |                    |                       |
   | Catalyst            |                    |                       |
   | Predicted yield     |                    |                       |
   | Predicted cost      |                    |                       |
   | Predicted purity    |                    |                       |
   | Desirability        | N/A                |                       |

### Discussion
- Is the multi-response optimum a good compromise?
- How would you adjust if cost were more important than yield?

---

## Exercise 8: Capstone Project

**Time:** 90 minutes (70 minutes work + 20 minutes presentations)
**Objective:** Apply the complete DOE workflow to a realistic problem.

### Choose Your Scenario

#### Option A: Cloud Infrastructure Optimisation
**Context:** You're optimising a Kubernetes-deployed microservice for a production API.

**Candidate Factors (10):**

| Factor            | Low    | High   | Units   |
|-------------------|--------|--------|---------|
| cpu_limit         | 250    | 2000   | m       |
| memory_limit      | 256    | 2048   | MB      |
| replicas          | 2      | 10     | -       |
| connection_pool   | 10     | 100    | -       |
| thread_count      | 4      | 64     | -       |
| cache_ttl         | 30     | 600    | sec     |
| batch_size        | 10     | 500    | -       |
| retry_limit       | 0      | 5      | -       |
| timeout           | 1      | 30     | sec     |
| gc_interval       | 10     | 300    | sec     |

**Responses:** p99_latency_ms (minimize), throughput_rps (maximize), cost_per_hour (minimize)
**Total budget:** 40 runs across all phases.

#### Option B: Manufacturing — 3D Printing
**Context:** You're optimising FDM 3D printing for functional parts.

**Candidate Factors (8):**

| Factor              | Low   | High  | Units   |
|---------------------|-------|-------|---------|
| layer_height        | 0.1   | 0.3   | mm      |
| print_speed         | 30    | 80    | mm/s    |
| nozzle_temp         | 190   | 230   | C       |
| bed_temp            | 50    | 80    | C       |
| infill_percent      | 15    | 80    | %       |
| retraction_distance | 1     | 8     | mm      |
| cooling_fan_pct     | 0     | 100   | %       |
| wall_count          | 2     | 5     | -       |

**Responses:** tensile_strength_mpa (maximize), print_time_min (minimize), surface_quality (maximize, 1-10 scale)
**Total budget:** 30 runs across all phases.

#### Option C: Recipe — Bread Baking
**Context:** You're developing the perfect sourdough bread recipe.

**Candidate Factors (7):**

| Factor            | Low   | High  | Units   |
|-------------------|-------|-------|---------|
| flour_protein_pct | 10    | 14    | %       |
| hydration_pct     | 60    | 85    | %       |
| starter_pct       | 15    | 35    | %       |
| salt_pct          | 1.5   | 2.5   | %       |
| bulk_ferment_hr   | 3     | 8     | hours   |
| proof_hr          | 1     | 4     | hours   |
| oven_temp         | 220   | 260   | C       |

**Responses:** loaf_volume_ml (maximize), crumb_score (maximize, 1-10), crust_color (target: 4, on 1-7 scale)
**Total budget:** 25 runs across all phases.

### Workflow

#### Phase 1: Screening (~30 minutes)

1. Create `capstone_screen/config.json` with ALL candidate factors.
2. Choose a screening design (Plackett-Burman or Definitive Screening).
3. Verify the run count is within your budget for Phase 1 (roughly half your total budget).
   ```bash
   doe info capstone_screen/
   ```
4. Generate and run:
   ```bash
   doe generate capstone_screen/
   bash capstone_screen/run.sh
   ```
5. Analyse:
   ```bash
   doe analyze capstone_screen/
   ```
6. **Decision:** Which 3-4 factors will you keep for Phase 2? Document your reasoning.

#### Phase 2: Response Surface & Optimisation (~30 minutes)

7. Create `capstone_rsm/config.json` with only the significant factors.
8. Choose CCD or Box-Behnken. Verify the run count fits remaining budget.
   ```bash
   doe info capstone_rsm/
   ```
9. Generate, run, and analyse:
   ```bash
   doe generate capstone_rsm/
   bash capstone_rsm/run.sh
   doe analyze capstone_rsm/
   ```
10. Optimise:
    ```bash
    doe optimize capstone_rsm/
    ```
11. Generate the final report:
    ```bash
    doe report capstone_rsm/
    ```

#### Phase 3: Documentation (~10 minutes)

12. Write a brief summary document answering:
    - What was the problem and what factors did you consider?
    - What screening design did you use and what did you learn?
    - Which factors survived screening and why?
    - What RSM design did you use?
    - What are the optimal settings and predicted performance?
    - What would you do next with more budget?

### Deliverables Checklist

- [ ] `capstone_screen/config.json` — screening configuration
- [ ] `capstone_rsm/config.json` — RSM configuration
- [ ] Screening analysis output (saved or screenshot)
- [ ] RSM analysis output (saved or screenshot)
- [ ] `capstone_rsm/report.html` — final HTML report
- [ ] Summary document (can be handwritten notes)
- [ ] 5-minute presentation to the class

### Presentation Guidelines
Your 5-minute presentation should cover:
1. **Problem statement** (30 sec): What were you optimising?
2. **Screening results** (1 min): How many factors did you start with? Which ones survived?
3. **RSM analysis** (1.5 min): What does the response surface look like? Any interactions?
4. **Optimal settings** (1 min): What does doe optimize recommend? How confident are you?
5. **Next steps** (1 min): What would you do with 20 more runs?

---

## Quick Reference Card

### Essential doe-helper Commands

```bash
# Setup
doe init <name> --design <type>    # Create from template
doe info <dir>/                     # Verify design before running

# Execution
doe generate <dir>/                 # Create design matrix + runner
doe record <dir>/                   # Interactively enter results
doe status <dir>/                   # Check experiment progress

# Analysis
doe analyze <dir>/                  # Full statistical analysis
doe optimize <dir>/                 # Find optimal settings
doe power <dir>/                    # Check statistical power
doe report <dir>/                   # Generate HTML report

# Extensions
doe augment <dir>/ --method <m>     # Extend design (fold-over, star, center)
doe export-worksheet <dir>/         # Export as CSV or markdown
```

### Design Type Selection

| Situation                        | Design Type          | doe-helper type       |
|----------------------------------|----------------------|-----------------------|
| Few factors (2-5), need all info | Full Factorial       | full_factorial        |
| Many factors (6+), screening     | Plackett-Burman      | plackett_burman       |
| Modern screening, 3+ factors     | Definitive Screening | definitive_screening  |
| Specific resolution needed       | Fractional Factorial | fractional_factorial  |
| Finding the optimum (2-4 factors)| Central Composite    | ccd                   |
| Optimum, avoid extremes          | Box-Behnken          | box_behnken           |
| Unknown model, simulation        | Latin Hypercube      | latin_hypercube       |
| Robust design                    | Taguchi              | taguchi               |
| Constrained space                | D-Optimal            | d_optimal             |
| Proportions sum to 1             | Mixture              | simplex_lattice       |

### Interpreting Results

| Metric                | Good         | Warning        |
|-----------------------|--------------|----------------|
| p-value               | < 0.05       | > 0.10         |
| R-squared             | > 0.90       | < 0.70         |
| Adj R^2 - Pred R^2    | < 0.20       | > 0.30         |
| Desirability          | > 0.80       | < 0.50         |
| Residual pattern      | Random       | Funnel/Curve   |
