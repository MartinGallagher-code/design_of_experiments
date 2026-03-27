# Design of Experiments — Fundamentals & Practical Guide

## What is Design of Experiments?

Imagine you're baking a cake and you want to make it taste better. You could try changing the sugar amount, then the oven temperature, then the baking time — one thing at a time. After dozens of attempts, you might find a decent recipe. But you'd never discover that a *specific combination* of less sugar *with* higher temperature produces the best result, because you never tested them together.

Design of Experiments (DOE) is a systematic method that solves this problem. Instead of changing one thing at a time and hoping for the best, DOE changes multiple variables simultaneously according to a mathematically optimal plan. It then uses statistical analysis to untangle each variable's individual contribution *and* how variables work together.

The key insight: **every run in a DOE plan contributes information about every factor.** Nothing is wasted.

### A Brief History

DOE was invented by Ronald Fisher in the 1920s at the Rothamsted agricultural research station in England. He needed to determine which fertilizer combinations produced the best crop yields, but field plots were expensive and took an entire growing season. He couldn't afford to test one fertilizer at a time.

Fisher's solution — testing multiple factors simultaneously in a structured pattern — revolutionized scientific experimentation. His methods were adopted by manufacturing (Taguchi methods in Japanese industry), pharmaceutical research, and eventually software engineering and technology.

Today, DOE is used everywhere: optimizing chemical processes, tuning database configurations, designing clinical trials, improving semiconductor manufacturing, and training machine learning models.

### Why Not Just Change One Thing at a Time?

The one-variable-at-a-time (OVAT) approach is intuitive but deeply flawed. Here's a concrete example showing why.

#### The Problem with OVAT

Suppose you're optimizing a web server. You suspect two things matter: **thread count** (10 or 100) and **cache size** (64MB or 512MB). The true relationship (which you don't know yet) is:

| Thread Count | Cache Size | Throughput (req/sec) |
|:---:|:---:|:---:|
| 10 | 64MB | 500 |
| 100 | 64MB | 600 |
| 10 | 512MB | 700 |
| 100 | 512MB | 1400 |

**OVAT approach** — start at (10 threads, 64MB cache):
1. Change threads to 100, keep cache at 64MB → throughput goes from 500 to 600. *Conclusion: threads help a little (+100).*
2. Reset threads to 10. Change cache to 512MB → throughput goes from 500 to 700. *Conclusion: cache helps more (+200).*
3. Final recommendation: use 512MB cache. Predicted throughput: 700.

**But** the OVAT approach completely missed the interaction. With *both* high threads *and* large cache, throughput is **1400** — more than double what OVAT predicted. The cache is only truly effective when there are enough threads to use it. OVAT testing at the wrong combination made threads look unimportant.

**DOE approach** — test all four combinations (a 2² full factorial):
- Main effect of threads: average(600, 1400)/2 - average(500, 700)/2 = 1000 - 600 = **+400**
- Main effect of cache: average(700, 1400)/2 - average(500, 600)/2 = 1050 - 550 = **+500**
- Interaction effect: **+500** (threads and cache amplify each other)
- Recommendation: use both 100 threads and 512MB cache. Predicted throughput: 1400.

Same number of experiments. Completely different (and correct) conclusion.

#### Three Fundamental Problems with OVAT

1. **It misses interactions.** If two factors work together (or cancel each other out), OVAT will never detect it. In the real world, interactions are common — they're the rule, not the exception.

2. **It's statistically inefficient.** In OVAT, each run only tells you about the one factor you changed. In a factorial DOE, *every run* contributes to estimating *every factor*. You get more information per run.

3. **It confuses noise with signal.** When you change one factor and observe a difference, was it the factor or just random variation? DOE's structured approach and replication let you separate real effects from noise and compute confidence intervals.

---

## Core Concepts

This section explains the vocabulary of DOE. Understanding these terms will make everything else click.

### Factors and Levels

A **factor** is anything you can control in your experiment. A **level** is a specific setting of that factor.

**Think of it this way:** Factors are the knobs you can turn. Levels are the positions you set each knob to.

| Type | What it means | Example |
|------|--------------|---------|
| **Continuous** | Numeric, can take any value in a range | Temperature: 150°C to 200°C |
| **Categorical** | Distinct categories, no inherent order | Catalyst type: A, B, or C |
| **Ordinal** | Ordered categories | Compiler optimization: -O1, -O2, -O3 |

Most DOE designs test each factor at exactly 2 levels (low and high). This is enough to detect whether a factor matters and in which direction. Response surface designs (CCD, Box-Behnken) add a middle level to detect curvature.

> **How many levels do I need?** Start with 2. If you find a factor is important and suspect a curved (non-linear) relationship, you can always add a center point or switch to a response surface design later. Don't over-complicate your first experiment.

### Responses

A **response** is what you measure — the outcome of each experimental run. You can measure multiple responses from the same experiment.

Each response has an optimization direction:
- **Maximize:** you want more of it (throughput, yield, accuracy)
- **Minimize:** you want less of it (latency, cost, defect rate)

| Response | Direction | Unit | Why it matters |
|----------|-----------|------|----------------|
| Throughput | maximize | req/sec | Higher is better for users |
| p99 Latency | minimize | ms | Tail latency affects user experience |
| CPU Usage | minimize | % | Lower means more headroom |
| Cost per Request | minimize | $ | Budget constraint |

> **Tip:** Measure everything you care about, even if you're primarily optimizing one response. A factor that improves throughput might also increase latency. Multi-response analysis helps you find the best trade-off.

### Main Effects

The **main effect** of a factor is the average change in the response when that factor moves from its low level to its high level, *averaged across all levels of every other factor.*

That "averaged across" part is crucial. It means the main effect is a fair, unbiased estimate — not measured at one specific combination (which is what OVAT gives you).

**Visual intuition:**

```
Response
   │
   │       ○ high temperature
   │      /
   │     /   ← this slope IS the main effect
   │    /
   │   ○ low temperature
   │
   └──────────────────
      Low        High
      Temperature
```

If the line is steep, the factor has a large effect. If the line is flat, the factor doesn't matter much. If the line goes down, the effect is negative (more of the factor gives less of the response).

**Worked example:** Suppose you run an experiment with 2 factors (A and B) at 2 levels each, and get these results:

| A | B | Response |
|:---:|:---:|:---:|
| low | low | 20 |
| high | low | 30 |
| low | high | 40 |
| high | high | 60 |

Main effect of A = average when A is high − average when A is low = (30+60)/2 − (20+40)/2 = 45 − 30 = **+15**

Main effect of B = average when B is high − average when B is low = (40+60)/2 − (20+30)/2 = 50 − 25 = **+25**

B has a larger main effect than A. Both are positive (increasing either factor increases the response).

### Interaction Effects

An **interaction** means the effect of one factor depends on the level of another factor. In other words, the factors don't act independently — they amplify or cancel each other.

**Everyday example:** Exercise and diet both affect weight loss. But the *combination* of exercise and diet produces more weight loss than you'd predict by adding their individual effects. That's an interaction.

**How to spot an interaction:**
- If the effect of A at B-low is *different* from the effect of A at B-high, there's an interaction.
- On an interaction plot, non-parallel lines = interaction. Crossing lines = strong interaction.

```
                 No Interaction          Strong Interaction
Response         ┌───────────────        ┌───────────────
   │             │  B=high               │     ╳
   │             │ ──────── ○            │   ╱   ╲   B=high
   │             │  B=low                │  ╱     ╲
   │             │ ──────── ○            │ ╱       ╲  B=low
   │             │                       │╱
   └─────────────┘──────────             └───────────
        A: Low → High              A: Low → High
  (lines are parallel)         (lines cross — interaction!)
```

**Using the previous example:**

- Effect of A when B is low: 30 − 20 = 10
- Effect of A when B is high: 60 − 40 = 20

The effect of A is *different* depending on B's level (10 vs 20). That difference is the interaction:

Interaction AB = (effect of A at B-high − effect of A at B-low) / 2 = (20 − 10) / 2 = **+5**

This means A and B have a synergistic interaction — they work better together.

> **Why interactions matter:** If you ignore interactions, you might set factor A to its "best" level based on its main effect, but that "best" level might actually be the worst level when factor B is at a certain setting. DOE catches this. OVAT doesn't.

### Blocking

**Blocking** accounts for known nuisance variation — things that affect your results but aren't what you're trying to study.

**Everyday analogy:** Imagine testing different pizza recipes across two ovens. Oven 1 runs 10°F hotter than Oven 2. If you test all "thick crust" recipes in Oven 1 and all "thin crust" recipes in Oven 2, you can't tell whether thick crust is better or whether Oven 1 just cooks hotter.

**Solution:** Make each oven a "block." Within each oven (block), test both thick and thin crust. Now the oven-to-oven difference is accounted for, and your crust comparison is fair.

Common blocking factors:
- Different days or shifts
- Different machines or test environments
- Different batches of raw material
- Different operators or teams

**How it works in this tool:**

```json
{
    "settings": {
        "block_count": 2
    }
}
```

Setting `block_count` to 2 means the entire design is run twice — once in each block. The tool automatically assigns block IDs and randomizes *within* each block (not across blocks).

> **When to use blocking:** Whenever you know that conditions will change between groups of runs. If you run experiments over 3 days, use 3 blocks. If you have 2 test machines, use 2 blocks. When in doubt, block.

### Randomization

**Randomization** means running your experiments in a random order within each block, rather than in a systematic pattern.

**Why it matters:** Suppose you run 8 experiments in order, and your test machine gradually warms up during the day, causing performance to drift upward. If your design happens to test "high thread count" experiments last, you might falsely attribute the drift to thread count.

Randomization scrambles the order so that any time-related drift is equally likely to affect any factor combination. It doesn't eliminate drift — it prevents drift from being confused with your factors.

**How it works in this tool:**

```bash
# Use --seed for reproducible randomization
doe generate --config config.json --seed 42

# Same seed = same randomized order (important for reproducibility)
doe generate --config config.json --seed 42  # identical output
```

The `--seed` flag is important: it ensures that the `generate` and `analyze` commands produce the same design matrix, so analysis correctly maps results back to factor combinations.

> **Always use a seed in practice.** This makes your experiment fully reproducible. Anyone with the same config and seed can recreate your exact design.

### Replication vs. Repetition

These sound similar but mean very different things:

| | Replication | Repetition |
|---|---|---|
| **What** | Re-do the entire experiment setup from scratch | Re-measure the same setup |
| **Captures** | Full experimental error (setup + measurement + environment) | Only measurement error |
| **Example** | Restart the server, re-apply config, re-run benchmark | Run the same benchmark 3 times without changing anything |
| **Use for** | Estimating real-world variability | Estimating measurement noise |

DOE uses replication (via blocking) to estimate the true experimental error. If you only repeat measurements, you'll underestimate the real variability and overstate the significance of your findings.

---

## Design Types

This section explains each design type in plain language, when to use it, what it looks like, and how many runs it costs.

### Quick Reference

| Design | Best for | Factors | Runs (3 factors) | Estimates Interactions? | Finds Optimum? |
|--------|----------|---------|:-:|:-:|:-:|
| Full Factorial | Complete picture | 2–4 | 8 | Yes, all | No |
| Fractional Factorial | Screening with some interaction info | 4–7 | 4–8 | Some (aliased) | No |
| Plackett-Burman | Fast screening of many factors | 5–20+ | 8–12 | No | No |
| Latin Hypercube | Exploration, simulation | Any | You choose | No | No |
| Central Composite (CCD) | Finding the optimum | 2–5 | 20 | Yes | Yes |
| Box-Behnken | Finding the optimum safely | 3–5 | 15 | Yes | Yes |

### Full Factorial

**The idea:** Test *every possible combination* of factor levels.

**When to use:** You have a small number of factors (2–4) and can afford the runs. This is the gold standard — it gives you complete information about every factor and every interaction.

**How many runs?**

| Factors | Levels each | Runs | Example |
|:---:|:---:|:---:|---|
| 2 | 2 | 4 | Temperature × Pressure |
| 3 | 2 | 8 | Temperature × Pressure × Catalyst |
| 4 | 2 | 16 | Starting to get expensive |
| 5 | 2 | 32 | Consider fractional instead |
| 3 | 3 | 27 | Three levels per factor |
| 2 × 3 | mixed | 6 | One 2-level, one 3-level factor |

**What it looks like** (3 factors, 2 levels):

```
Run  Temperature  Pressure  Catalyst  → Response
 1     low         low       A        → 42.3
 2     high        low       A        → 51.7
 3     low         high      A        → 47.2
 4     high        high      A        → 68.9
 5     low         low       B        → 39.8
 6     high        low       B        → 55.1
 7     low         high      B        → 44.6
 8     high        high      B        → 71.3
```

Every combination appears exactly once. Every run contributes to estimating every effect.

**Strengths:**
- Complete picture — no confounding, no aliasing, no approximations
- Estimates all main effects and all interactions (2-way, 3-way, etc.)
- The statistical gold standard

**Weaknesses:**
- Run count grows exponentially: 2^k. At 7 factors, that's 128 runs.
- Overkill when you have many factors and most don't matter

**Tool usage:**
```json
{
    "settings": {
        "operation": "full_factorial"
    }
}
```

### Fractional Factorial

**The idea:** Run a *carefully chosen fraction* of the full factorial. Give up information about high-order interactions (which are usually negligible) to save runs.

**When to use:** You have 4–7 factors and a full factorial is too expensive. You want to screen factors but also get some information about two-factor interactions.

**How does the "fraction" work?**

Think of it this way. In a 2⁵ full factorial (32 runs), you can estimate:
- 5 main effects
- 10 two-factor interactions
- 10 three-factor interactions
- 5 four-factor interactions
- 1 five-factor interaction

That's 31 independent pieces of information. But you probably only care about the 5 main effects and maybe the 10 two-factor interactions (15 total). The three-factor and higher interactions are almost always negligible in practice (the *effect sparsity principle*).

A fractional factorial with 16 runs (a "half fraction," 2⁵⁻¹) can estimate all 5 main effects and all 10 two-factor interactions — but each main effect is *aliased* with a four-factor interaction, and each two-factor interaction is aliased with a three-factor interaction. Since those higher-order effects are negligible, this aliasing doesn't matter.

**Resolution** — how clean are the estimates?

| Resolution | What it means | Good for |
|:---:|---|---|
| III | Main effects aliased with 2-factor interactions | Initial screening only |
| IV | Main effects are clean; 2FIs aliased with other 2FIs | Screening with some interaction info |
| V | Main effects and 2FIs are all clean | Near-full-factorial quality |

**Rule of thumb:** Use Resolution IV or higher if you suspect important interactions. Use Resolution III only for initial screening when you have many factors and need minimal runs.

**Tool usage:**
```json
{
    "settings": {
        "operation": "fractional_factorial"
    }
}
```

### Plackett-Burman

**The idea:** The most efficient possible 2-level screening design. It tells you which factors have large main effects using the absolute minimum number of runs.

**When to use:** You have many factors (5–20+) and your goal is to quickly separate the "vital few" from the "trivial many." You don't care about interactions yet — you just need to know which knobs to focus on.

**How many runs?**

PB designs always use a multiple of 4 runs. You can screen up to N-1 factors in N runs:

| Runs | Max Factors | That's only... |
|:---:|:---:|---|
| 8 | 7 | 8 runs to screen 7 factors! |
| 12 | 11 | 12 runs to screen 11 factors |
| 20 | 19 | 20 runs to screen 19 factors |
| 24 | 23 | You get the idea |

**Real-world example:** A performance engineer suspects 11 database configuration parameters might affect throughput. Testing all combinations (2¹¹ = 2048 runs) is absurd. A PB design screens all 11 in just 12 runs and identifies the 3 that actually matter.

**What you get:** A Pareto chart showing which factors have the largest main effects. The top 3–5 factors typically account for 80% of the variation (the Pareto principle).

**What you don't get:** Interaction estimates. PB designs confound interactions with main effects in a complex way. If you suspect interactions are important, follow up with a factorial on the important factors.

**Tool usage:**
```json
{
    "settings": {
        "operation": "plackett_burman"
    }
}
```

### Latin Hypercube Sampling (LHS)

**The idea:** Spread sample points evenly across the entire factor space, ensuring no large gaps or clusters. Unlike factorial designs, LHS doesn't use a fixed grid — it's a space-filling design.

**Analogy:** Imagine placing 10 dots on a 10×10 grid such that every row and every column has exactly one dot (like a Sudoku constraint). That's the Latin Hypercube property in 2D. In higher dimensions, the same principle applies — every "slice" of each factor's range gets exactly one sample.

**When to use:**
- Computer simulations where the response has no random noise
- Exploring a high-dimensional space with many continuous factors
- Building surrogate models (kriging, Gaussian processes, neural networks)
- Sensitivity analysis and uncertainty quantification
- When you don't have a clear "low/high" for each factor and want to explore

**How many runs?** You choose. The default in this tool is max(10, 2 × number_of_factors). More samples = better coverage, but diminishing returns beyond about 10× the number of factors.

**Strengths:**
- Excellent space coverage — no large unexplored regions
- Works with any number of factors (scales better than factorials)
- No requirement for 2-level factors — works with continuous ranges

**Weaknesses:**
- Not designed for estimating specific effects or interactions
- Less statistically efficient than factorial designs for small k
- No built-in error estimation (since each point is unique)

**Tool usage:**
```json
{
    "settings": {
        "operation": "latin_hypercube",
        "lhs_samples": 30
    }
}
```

### Central Composite Design (CCD)

**The idea:** Start with a 2-level factorial (the corners of a cube), then add "star points" along each axis and some center points. This gives you enough data points to fit a curved (quadratic) model and find the true optimum — not just "is high better than low?" but "exactly how high is best?"

**When to use:** You've already screened your factors (with PB or fractional factorial) and narrowed down to the 2–5 most important continuous factors. Now you want to find the sweet spot.

**What it looks like** (2 factors):

```
                    ★ star point (above)
                    │
         ●──────────┼──────────●
         │          │          │
         │    factorial       │
★ ───────┼──── ◆ center ─────┼───── ★  star points
         │          │          │
         │   (corners of     │
         ●──── the square) ──●
                    │
                    ★ star point (below)

● = factorial points (corners)
★ = star/axial points (along axes, beyond corners)
◆ = center point (middle)
```

The star points extend beyond the factorial range by a distance α (alpha). This is what allows the design to fit squared terms and detect curvature.

**Run counts:**

| Factors | Factorial | Star | Center | Total |
|:---:|:---:|:---:|:---:|:---:|
| 2 | 4 | 4 | 5 | 13 |
| 3 | 8 | 6 | 6 | 20 |
| 4 | 16 | 8 | 7 | 31 |
| 5 | 32 | 10 | 8 | 50 |

**Strengths:**
- Fits a full quadratic model (linear + interaction + curvature)
- Can find the true optimum within (or beyond) the design space
- Can be built sequentially — if you already ran a 2^k factorial, you just add star and center points

**Weaknesses:**
- Requires numeric factor levels (can't use categorical factors)
- Star points go outside the factorial range — may be physically infeasible (e.g., temperature below freezing or pressure above equipment limits)
- More runs than Box-Behnken for 3–4 factors

**Tool usage:**
```json
{
    "factors": [
        {"name": "temperature", "levels": ["150", "200"], "type": "continuous"},
        {"name": "pressure",    "levels": ["2", "6"],     "type": "continuous"}
    ],
    "settings": {
        "operation": "central_composite"
    }
}
```

### Box-Behnken

**The idea:** A response surface design that avoids extreme corners. In every run, at most two factors are at their extreme levels; the others are at center. This means you never test the most extreme combination of all factors simultaneously.

**When to use:** Same situations as CCD, but when:
- Testing at all extremes simultaneously is dangerous (reactor explosion, system crash)
- Your equipment can't physically reach all corners
- You have at least 3 continuous factors

**What it looks like** (3 factors):

```
The Box-Behnken for 3 factors tests the EDGES of a cube, not the corners:

        ● ─ ─ ─ ─ ─ ─ ─ ─ ─ ●
       ╱|                   ╱|     ← corners are NOT tested
      ╱ |      ○  edge    ╱  |
    ○╱─ ─ ─ ─ ─ ─ ─ ─ ○╱   ○     ○ = edge midpoints (tested)
    |   |              |    |      ● = corners (avoided!)
    |   ● ─ ─ ─ ─ ─ ─ |─ ─ ●     ◆ = center (tested, replicated)
    ○  ╱               ○  ╱
    | ╱       ◆        | ╱
    |╱                 |╱
    ● ─ ─ ─ ─ ─ ─ ─ ─ ●
```

Each "edge midpoint" run has two factors at extreme levels and the third at center. Plus 3 center-point replicates.

**Run counts:**

| Factors | Edge Runs | Center | Total | vs CCD |
|:---:|:---:|:---:|:---:|:---:|
| 3 | 12 | 3 | 15 | 20 for CCD |
| 4 | 24 | 3 | 27 | 31 for CCD |
| 5 | 40 | 6 | 46 | 50 for CCD |

**Strengths:**
- Avoids extreme corners — all points are within the "safe" region
- Fewer runs than CCD (for 3–4 factors)
- Still fits a full quadratic model

**Weaknesses:**
- Requires at least 3 factors (no Box-Behnken for 2 factors — use CCD instead)
- Requires numeric factor levels
- Less information about behavior at extreme corners (since you don't test them)

**CCD vs Box-Behnken — how to choose:**

| Situation | Choose |
|---|---|
| All extremes are safe to test | CCD (more information at corners) |
| Some extreme combinations are dangerous | Box-Behnken (avoids corners) |
| You already have 2^k factorial data | CCD (augment with star + center points) |
| Starting fresh, want fewer runs | Box-Behnken |
| Only 2 factors | CCD (Box-Behnken requires 3+) |

**Tool usage:**
```json
{
    "factors": [
        {"name": "temperature", "levels": ["150", "200"], "type": "continuous"},
        {"name": "pressure",    "levels": ["2", "6"],     "type": "continuous"},
        {"name": "catalyst",    "levels": ["0.5", "2.0"], "type": "continuous"}
    ],
    "settings": {
        "operation": "box_behnken"
    }
}
```

---

## Choosing the Right Design

### Decision Tree

```
START: How many factors are you testing?
│
├─ 2–4 factors
│  ├─ Want complete information (all interactions)?
│  │  └─ YES → Full Factorial
│  │
│  └─ Want to find the optimal value (not just high vs. low)?
│     ├─ All extremes are safe → Central Composite Design (CCD)
│     └─ Avoid extreme corners → Box-Behnken (needs 3+ factors)
│
├─ 5–7 factors
│  ├─ Just screening (which factors matter?) → Plackett-Burman
│  └─ Need some interaction info too → Fractional Factorial (Res. IV+)
│
├─ 8+ factors
│  └─ Screening → Plackett-Burman
│
└─ Computer simulation / exploring continuous space
   └─ Latin Hypercube Sampling
```

### The Sequential Strategy (The Right Way to Do DOE)

The most powerful approach isn't a single experiment — it's a **sequence** of increasingly focused experiments. Each phase informs the next.

#### Phase 1: Screen (Cheap, Broad)

**Goal:** Which of my many factors actually matter?

**Design:** Plackett-Burman or Resolution III fractional factorial

**Runs:** 8–20 (regardless of how many factors)

**What you learn:** A ranked list of factors by importance. Typically, 3–5 factors account for 80% of the effect.

**Example:** You suspect 12 configuration parameters affect your app's latency. A PB design with 16 runs reveals that only `connection_pool_size`, `gc_heap_size`, and `worker_threads` have meaningful effects. The other 9 parameters are noise.

**What to do next:** Fix the unimportant factors at their cheapest/easiest values. Take the top 3–5 to Phase 2.

#### Phase 2: Characterize (Moderate cost, Focused)

**Goal:** Understand the important factors in detail, including their interactions.

**Design:** Full factorial (2^k) on the screened factors, possibly with center points

**Runs:** 8–32

**What you learn:** The exact main effect and interaction effects. Whether curvature exists (via center points).

**Example:** A 2³ full factorial on the 3 important parameters (8 runs) reveals a strong interaction between `connection_pool_size` and `worker_threads` — increasing both together reduces latency more than expected from either alone.

**What to do next:** If the best result is at a corner of the design space and you suspect the optimum is somewhere in the middle (curvature), proceed to Phase 3.

#### Phase 3: Optimize (Precise, Targeted)

**Goal:** Find the exact optimal settings.

**Design:** CCD or Box-Behnken on the 2–4 most important factors

**Runs:** 15–50

**What you learn:** A quadratic model of the response surface. The predicted optimal factor values. R² tells you how well the model fits.

**Example:** A Box-Behnken on `connection_pool_size` (50–200), `gc_heap_size` (256MB–2GB), and `worker_threads` (4–32) reveals that the optimal settings are pool_size=140, heap=1.4GB, threads=20 — values that aren't at any extreme.

#### Phase 4: Confirm (Cheap, Essential)

**Goal:** Verify that the predicted optimum actually works.

**Design:** 3–5 replicate runs at the predicted optimal settings.

**What you learn:** Whether the model's prediction matches reality. If the observed response falls within the prediction interval, you're done.

**Total cost of the entire sequence:** 8 + 8 + 15 + 5 = **36 runs** to go from 12 unknown factors to a validated optimum. A grid search over 12 parameters at 3 levels each would require 3¹² = 531,441 runs.

---

## Analysis Techniques

Once your experiments are complete, you need to make sense of the data. This section explains what each analysis technique tells you and how to interpret it.

### Main Effects Analysis

The simplest and most important analysis. For each factor, compute the average response at each level.

**Example output from this tool:**
```
=== Main Effects: throughput ===
Factor               Effect    Std Error   % Contribution
--------------------------------------------------------------
buffer_pool_size     +850.3       45.2            62.1%
worker_threads       +312.7       45.2            22.8%
gc_heap_size         +142.1       45.2            10.4%
log_level             -64.5       45.2             4.7%
```

**How to read this:**
- **Effect:** How much the response changes when the factor goes from low to high. Positive = high level produces more. Negative = high level produces less.
- **Std Error:** The uncertainty in the effect estimate. Smaller is better (means more precise).
- **% Contribution:** How much of the total effect is attributable to this factor. Factors above ~80% cumulative are the "vital few."

### The Pareto Chart

A visual representation of main effects, sorted by magnitude, with a cumulative percentage line.

```
% Contribution
100% ─────────────────────────────── ● cumulative
 80% ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ● ─ ─ ─ ─ ─ ─ ← 80% line
                             ╱
                           ●
                         ╱
                       ●
                     ╱

Factor:    buffer_pool  threads   gc_heap   log_level
Effect:    ████████████ ██████    ████      ██
           62%          23%       10%       5%
           ←── vital few ──→     ← trivial many →
```

**The 80% rule:** Factors whose cumulative contribution reaches 80% are the "vital few" — focus your attention on these. The rest can usually be fixed at convenient values.

> **The Pareto threshold is configurable** in this tool. If 80% is too aggressive for your application, adjust it.

### Interaction Effects

For 2-level designs, the tool computes all two-factor interactions automatically.

**Example output:**
```
=== Interaction Effects: throughput ===
Factor A             Factor B              Interaction   % Contribution
------------------------------------------------------------------------
buffer_pool_size     worker_threads            +225.4           78.3%
gc_heap_size         worker_threads             +52.1           18.1%
buffer_pool_size     gc_heap_size               +10.3            3.6%
```

**How to read this:**
- A large positive interaction means the factors *amplify* each other (synergistic).
- A large negative interaction means the factors *cancel* each other (antagonistic).
- A near-zero interaction means the factors act independently.

**When the interaction is large relative to the main effects,** you cannot interpret main effects in isolation. For example, if `buffer_pool × threads` interaction is 225 and `threads` main effect is 312, a significant portion of the "threads" benefit only shows up when `buffer_pool` is also high.

### Confidence Intervals

A 95% confidence interval tells you: "We are 95% confident the true effect falls within this range."

**Example:**
```
temperature:  effect = +8.5,  95% CI = [+3.2, +13.8]
pressure:     effect = +1.2,  95% CI = [-4.1, +6.5]
```

- **Temperature:** The CI is entirely positive [+3.2, +13.8], so the effect is statistically significant. Temperature definitely matters.
- **Pressure:** The CI includes zero [-4.1, +6.5], so the effect is NOT statistically significant. We can't be sure pressure matters at all — the observed effect of +1.2 could be noise.

> **Practical vs. statistical significance:** An effect can be statistically significant but practically tiny (e.g., +0.001% throughput with CI [+0.0005, +0.0015]). Conversely, an effect can look practically important but not be statistically significant (not enough replication). Always consider both.

### Summary Statistics

Per-factor, per-level breakdown of the raw data:

```
buffer_pool_size:
  Level           N       Mean        Std        Min        Max
  ------------------------------------------------------------
  1G              8     1250.3       45.2     1180.0     1320.0
  4G              8     2100.6       62.1     2010.0     2200.0
```

**What to look for:**
- **N:** Number of observations at each level. Should be equal (balanced design).
- **Mean:** Average response. The difference between level means = the main effect.
- **Std:** Standard deviation *within* each level. High std means lots of variability — you may need more replication.
- **Min/Max:** Extreme values. Check for outliers.

### Response Surface Modeling (RSM)

RSM fits a mathematical model to your data. Think of it as drawing the best-fit curve through your experimental points.

**Linear model:** response = a + b₁·factor₁ + b₂·factor₂ + ...
- This is a flat surface (plane). It can't detect curvature.
- Use with factorial and screening designs.

**Quadratic model:** response = a + b₁·factor₁ + b₂·factor₂ + b₁₂·factor₁·factor₂ + b₁₁·factor₁² + b₂₂·factor₂² + ...
- This is a curved surface. It can find peaks, valleys, and saddle points.
- Use with CCD and Box-Behnken designs.

**R² — how good is the model?**

| R² | Meaning |
|:---:|---|
| 0.95–1.00 | Excellent. Model explains almost all variation. |
| 0.80–0.95 | Good. Useful for predictions and optimization. |
| 0.60–0.80 | Fair. Missing factors or non-linear terms may be needed. |
| < 0.60 | Poor. The model doesn't capture the real behavior. Consider adding factors or using a different model. |

**Example optimize output:**
```
=== Optimization: throughput ===
Direction: maximize

Best observed run: #7
  buffer_pool = 4G, threads = 16, gc_heap = 1.5G
  Value: 2200

RSM Model (linear, R² = 0.91):
  Coefficients:
    intercept:   +1675.5
    buffer_pool:  +425.1
    threads:      +156.3
    gc_heap:       +71.0
  Predicted optimum:
    buffer_pool = 4G, threads = 16, gc_heap = 2G
    Predicted value: 2327.9
```

**How to read this:**
- **Best observed run:** The actual run with the highest (or lowest) response. This is a fact, not a prediction.
- **R² = 0.91:** The linear model explains 91% of the variation. Good fit.
- **Coefficients:** How much each factor contributes per coded unit. buffer_pool has the largest coefficient.
- **Predicted optimum:** Where the model predicts the best response. This may be at a combination you didn't actually test — the model is extrapolating.

> **Always verify the predicted optimum** with confirmation runs. Models can be wrong, especially when extrapolating.

---

## Using This Tool

### Installation

```bash
pip install doehelper
```

### Step-by-Step Workflow

#### Step 1: Define Your Problem

Before touching the tool, answer these questions on paper:

1. **What am I trying to optimize or understand?** (e.g., "maximize throughput while keeping latency under 50ms")
2. **What factors can I control?** List all candidates, even ones you're unsure about.
3. **What are reasonable low and high levels for each factor?** Don't pick levels that are too close together (small effects are hard to detect) or unrealistically far apart.
4. **What will I measure?** Define your response(s) precisely, including units.
5. **How much variability is there?** If your system is noisy, you'll need more replication.
6. **How many runs can I afford?** This determines which design to use.

#### Step 2: Create a Configuration File

```json
{
    "metadata": {
        "name": "Web Server Tuning Experiment",
        "description": "Identify which config parameters most affect request throughput"
    },
    "factors": [
        {"name": "worker_threads",  "levels": ["4", "32"],     "type": "continuous", "unit": "threads",  "description": "Number of worker threads"},
        {"name": "connection_pool", "levels": ["50", "200"],   "type": "continuous", "unit": "conns",    "description": "Max database connections"},
        {"name": "cache_size",      "levels": ["64", "512"],   "type": "continuous", "unit": "MB",       "description": "In-memory cache size"},
        {"name": "log_level",       "levels": ["warn", "debug"], "type": "categorical", "description": "Application log verbosity"}
    ],
    "fixed_factors": {
        "jvm_heap": "4G",
        "os": "linux"
    },
    "responses": [
        {"name": "throughput",   "optimize": "maximize", "unit": "req/sec", "description": "Sustained request throughput"},
        {"name": "p99_latency",  "optimize": "minimize", "unit": "ms",      "description": "99th percentile latency"}
    ],
    "runner": {
        "arg_style": "double-dash"
    },
    "settings": {
        "block_count": 2,
        "test_script": "benchmark.sh",
        "operation": "full_factorial",
        "processed_directory": "results/analysis",
        "out_directory": "results"
    }
}
```

**Tips for good configs:**
- Use descriptive names and include units — your future self will thank you.
- Set `block_count` > 1 if your test environment might change between runs (different days, different load, etc.)
- Use `fixed_factors` for things you want held constant — they'll be passed to every run but won't be varied.
- The `metadata` section appears in reports and helps you remember what each experiment was about.

#### Step 3: Preview and Generate

```bash
# See the design before committing to it
doe info --config config.json

# Generate the runner script (always use --seed for reproducibility)
doe generate --config config.json --output run.sh --seed 42

# Or generate a Python runner instead of bash
doe generate --config config.json --output run.py --format py --seed 42
```

#### Step 4: Write Your Test Script

Your test script is called once per experimental run. It receives factor values and must write a JSON result file.

**Bash example:**
```bash
#!/bin/bash
# benchmark.sh — called by the generated runner script

# Parse arguments (double-dash style)
while [[ $# -gt 0 ]]; do
    case "$1" in
        --worker_threads)  THREADS="$2";  shift 2 ;;
        --connection_pool) POOL="$2";     shift 2 ;;
        --cache_size)      CACHE="$2";    shift 2 ;;
        --log_level)       LOG="$2";      shift 2 ;;
        --jvm_heap)        HEAP="$2";     shift 2 ;;
        --out)             OUTFILE="$2";  shift 2 ;;
        *)                 shift ;;
    esac
done

# Apply the configuration
configure_server --threads "$THREADS" --pool "$POOL" --cache "${CACHE}M"

# Run the benchmark
RESULT=$(run_benchmark --duration 60)

# Parse and write results
THROUGHPUT=$(echo "$RESULT" | grep throughput | awk '{print $2}')
LATENCY=$(echo "$RESULT" | grep p99 | awk '{print $2}')

mkdir -p "$(dirname "$OUTFILE")"
echo "{\"throughput\": $THROUGHPUT, \"p99_latency\": $LATENCY}" > "$OUTFILE"
```

**Three argument styles** (configured in `runner.arg_style`):

| Style | How factors are passed | Best for |
|---|---|---|
| `double-dash` | `--factor_name value` | Most scripts/tools |
| `env` | `export FACTOR_NAME=value` | Tools that read env vars |
| `positional` | `value1 value2 value3` | Simple scripts |

#### Step 5: Execute

```bash
# Run all experiments
bash run.sh

# The script will:
# - Skip already-completed runs (safe to re-run after interruption)
# - Track failures and continue (error recovery)
# - Print a summary at the end
```

**If a run fails,** the script records it and continues with the next run. At the end, it prints which runs failed so you can investigate and re-run them.

#### Step 6: Analyze

```bash
# Full analysis with plots
doe analyze --config config.json

# Skip plot generation (faster, for CI/scripts)
doe analyze --config config.json --no-plots

# Get optimization recommendations (best run + RSM model)
doe optimize --config config.json

# Generate a self-contained HTML report (shareable, includes embedded plots)
doe report --config config.json --output report.html

# Export to CSV for further analysis in R, Excel, pandas, etc.
doe analyze --config config.json --csv results/csv
```

---

## Practical Applications

### Software Performance Benchmarking

DOE is arguably the single most underused technique in performance engineering. Most teams tune systems by intuition, tribal knowledge, or changing one thing at a time. DOE does it systematically.

**Database tuning example:**

You suspect 6 MySQL parameters affect OLTP throughput. Instead of manually tuning each one:

```json
{
    "factors": [
        {"name": "innodb_buffer_pool_size", "levels": ["1G", "8G"],    "type": "categorical"},
        {"name": "innodb_io_capacity",      "levels": ["200", "4000"], "type": "continuous"},
        {"name": "max_connections",          "levels": ["100", "500"], "type": "continuous"},
        {"name": "innodb_flush_method",      "levels": ["fsync", "O_DIRECT"], "type": "categorical"},
        {"name": "innodb_log_file_size",     "levels": ["256M", "2G"], "type": "categorical"},
        {"name": "thread_pool_size",         "levels": ["4", "32"],    "type": "continuous"}
    ],
    "responses": [
        {"name": "tps",     "optimize": "maximize", "unit": "tx/sec"},
        {"name": "p99_lat", "optimize": "minimize", "unit": "ms"}
    ],
    "settings": {
        "operation": "plackett_burman",
        "block_count": 2
    }
}
```

8 runs × 2 blocks = 16 runs. The Pareto chart shows that `buffer_pool_size` and `innodb_io_capacity` account for 73% of the throughput variation. The other 4 parameters are noise. You just saved yourself days of manual tuning.

Follow up with a CCD on the 2 important parameters (13 runs) to find the exact optimum.

**Microservice configuration:**

```json
{
    "factors": [
        {"name": "replicas",       "levels": ["2", "8"],     "type": "continuous"},
        {"name": "cpu_limit",      "levels": ["500m", "2"],  "type": "categorical"},
        {"name": "memory_limit",   "levels": ["512Mi", "2Gi"], "type": "categorical"},
        {"name": "hpa_target_cpu", "levels": ["50", "80"],   "type": "continuous"}
    ],
    "responses": [
        {"name": "p95_latency", "optimize": "minimize", "unit": "ms"},
        {"name": "cost_per_hour", "optimize": "minimize", "unit": "$"}
    ],
    "settings": {
        "operation": "full_factorial"
    }
}
```

2⁴ = 16 runs gives you the complete picture of how Kubernetes resource settings interact to affect latency and cost. You'll likely discover that more replicas only help up to a point (interaction with CPU limit), and that doubling memory has no effect if CPU is the bottleneck.

### Scientific Experiments

**Chemical process optimization:**

See the [reactor optimization use case](../use_cases/01_reactor_optimization.md) for a complete worked example using Box-Behnken design.

**Agricultural field trials** (Fisher's original use case):

```json
{
    "factors": [
        {"name": "fertilizer_type", "levels": ["A", "B", "C"], "type": "categorical"},
        {"name": "irrigation_freq", "levels": ["daily", "weekly"], "type": "categorical"},
        {"name": "seed_variety",    "levels": ["hybrid", "heritage"], "type": "categorical"}
    ],
    "responses": [
        {"name": "yield_kg_per_hectare", "optimize": "maximize", "unit": "kg/ha"}
    ],
    "settings": {
        "operation": "full_factorial",
        "block_count": 4
    }
}
```

3 × 2 × 2 = 12 combinations × 4 blocks (field plots) = 48 runs. The blocking accounts for soil variation across different parts of the field.

### Machine Learning Hyperparameter Tuning

Grid search and random search are the default in ML, but DOE is more efficient:

| Approach | 8 hyperparameters, 3 values each | What you learn |
|---|:---:|---|
| Grid search | 6,561 runs | Everything, wastefully |
| Random search | ~100 runs | Noisy estimates, no structure |
| PB screening | 12 runs | Which 3 hyperparameters matter |
| + Full factorial | 8 more runs | Interactions between the top 3 |
| **Total DOE** | **20 runs** | **Focused, actionable knowledge** |

**Example:**
```json
{
    "factors": [
        {"name": "learning_rate",  "levels": ["0.001", "0.1"],  "type": "continuous"},
        {"name": "batch_size",     "levels": ["32", "256"],     "type": "continuous"},
        {"name": "dropout",        "levels": ["0.1", "0.5"],    "type": "continuous"},
        {"name": "hidden_layers",  "levels": ["2", "6"],        "type": "continuous"},
        {"name": "hidden_units",   "levels": ["64", "512"],     "type": "continuous"},
        {"name": "optimizer",      "levels": ["adam", "sgd"],   "type": "categorical"},
        {"name": "weight_decay",   "levels": ["0", "0.01"],     "type": "continuous"},
        {"name": "activation",     "levels": ["relu", "gelu"],  "type": "categorical"}
    ],
    "responses": [
        {"name": "val_accuracy",   "optimize": "maximize"},
        {"name": "train_time_min", "optimize": "minimize", "unit": "min"}
    ],
    "settings": {
        "operation": "plackett_burman"
    }
}
```

12 runs to screen 8 hyperparameters. The Pareto chart immediately tells you that learning_rate, batch_size, and hidden_units matter — the rest can be fixed at defaults.

---

## Common Mistakes and How to Avoid Them

### 1. Choosing factor levels too close together

**Problem:** If you test temperature at 198°C and 202°C, the effect will be tiny and lost in noise.

**Fix:** Make the difference between levels large enough to produce a detectable effect. A good rule of thumb: make the difference at least 2–3x the expected noise level.

### 2. Not randomizing run order

**Problem:** Systematic drift (equipment warm-up, environmental changes) gets confounded with your factors.

**Fix:** Always use `--seed` to randomize. Never run experiments in the order they appear in the design matrix.

### 3. Changing other things between runs

**Problem:** You update the OS halfway through the experiment, or a colleague restarts the server. Now some runs were under different conditions.

**Fix:** Keep everything constant except the factors you're studying. If something does change, use blocking to account for it.

### 4. Testing too many factors at once without screening

**Problem:** Running a full factorial on 8 factors (256 runs) when only 3 of them matter.

**Fix:** Start with a Plackett-Burman screening design (12 runs). Then focus on the important factors.

### 5. Ignoring interactions

**Problem:** You find that "thread count = 32" is "best" based on its main effect, but in reality it's only best when combined with a large connection pool.

**Fix:** Use a design that estimates interactions (full factorial or fractional factorial), and check the interaction effects table.

### 6. Not running confirmation experiments

**Problem:** You trust the RSM model's predicted optimum without verifying it.

**Fix:** Always run 3–5 experiments at the predicted optimal settings. If the result matches the prediction (within the confidence interval), you're done. If not, the model needs work.

### 7. Confusing replication with repetition

**Problem:** You run the benchmark 5 times without restarting the server and compute a standard deviation. This underestimates the true variability.

**Fix:** True replication means resetting the entire experimental setup between runs. Use `block_count > 1` to get true replicates.

---

## Glossary

| Term | Definition |
|------|-----------|
| **ANOVA** | Analysis of Variance — statistical method that partitions total variation into components |
| **Blocking** | Grouping runs to account for known nuisance variation |
| **CCD** | Central Composite Design — response surface design with factorial + star + center points |
| **Coded variable** | Factor rescaled so that low = -1, high = +1, center = 0 |
| **Confounding** | When two effects produce identical patterns and can't be distinguished |
| **DOE** | Design of Experiments |
| **Effect** | Change in the mean response when a factor changes level |
| **Factor** | A controllable input variable |
| **Fractional factorial** | Subset of full factorial that trades higher-order info for fewer runs |
| **Interaction** | When the effect of one factor depends on the level of another |
| **Level** | A specific setting of a factor |
| **LHS** | Latin Hypercube Sampling — space-filling design |
| **Main effect** | Average effect of a factor across all levels of other factors |
| **OVAT** | One Variable At a Time — the inefficient approach DOE replaces |
| **Pareto chart** | Bar chart ranking effects by magnitude with cumulative line |
| **Plackett-Burman** | Efficient screening design for identifying important main effects |
| **R²** | Coefficient of determination — proportion of variance explained by the model (0–1) |
| **Randomization** | Random ordering of runs to protect against lurking variables |
| **Replication** | Independently repeating the entire experimental setup |
| **Resolution** | Severity of confounding in a fractional factorial (III, IV, V) |
| **Response** | Measurable outcome of an experiment |
| **RSM** | Response Surface Methodology — polynomial models for finding optimal settings |

---

## Key Takeaways

1. **DOE beats guessing.** A structured experiment with 15 runs will teach you more than 100 unplanned runs. The math guarantees it.

2. **Start by screening.** Use Plackett-Burman or fractional factorial to find the vital few factors. Don't waste runs on factors that don't matter.

3. **Interactions are real and common.** If you only test one factor at a time, you will miss them and draw wrong conclusions. The web server example at the top proves this.

4. **Randomize and block.** These two practices protect you from hidden variables that can silently invalidate your results. Always use a seed for reproducibility.

5. **Use the sequential strategy.** Screen → Characterize → Optimize → Confirm. Each phase costs 8–20 runs. The total is far less than brute-force exploration.

6. **Use response surface designs to optimize.** CCD or Box-Behnken can find the true optimum — not just "high is better than low" but "exactly this value is best."

7. **Always verify.** Never trust a model prediction without confirmation runs. Models are approximations — reality is the ground truth.

8. **Automate the workflow.** This tool handles the math, generates executable scripts, analyzes results, and produces reports. You focus on defining the problem and interpreting the results.

---

## Further Reading

**Books:**
- Box, G.E.P., Hunter, J.S., & Hunter, W.G. (2005). *Statistics for Experimenters: Design, Innovation, and Discovery*, 2nd ed. Wiley. — The classic. Rigorous but readable.
- Montgomery, D.C. (2017). *Design and Analysis of Experiments*, 9th ed. Wiley. — The standard textbook. Comprehensive.
- Myers, R.H., Montgomery, D.C., & Anderson-Cook, C.M. (2016). *Response Surface Methodology*, 4th ed. Wiley. — Deep dive into RSM.

**Online:**
- NIST/SEMATECH e-Handbook of Statistical Methods: https://www.itl.nist.gov/div898/handbook/ — Free, excellent reference for practitioners.

**This tool's resources:**
- [Use Case 1: Reactor Optimization (Box-Behnken)](../use_cases/01_reactor_optimization.md)
- [LaTeX Book: Design of Experiments — A Practical Guide](book/doe_guide.pdf)
