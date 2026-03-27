# DOE Helper Training Course — Teaching Notes

Copyright (C) 2026 Martin J. Gallagher. All rights reserved.
Licensed under the GNU General Public License v3.0 or later.

## Course Overview

**Duration:** 1 full day (8 hours) or 2 half-days (4 hours each)
**Audience:** Engineers, scientists, analysts, and technical leads
**Prerequisites:** Basic statistics (mean, standard deviation, hypothesis testing); command-line familiarity
**Software:** Python 3.10+, doe-helper (`pip install doehelper`)

### Suggested Schedule (Full Day)

| Time        | Module | Topic                                   | Duration |
|-------------|--------|-----------------------------------------|----------|
| 09:00-09:45 | 1      | Introduction to DOE                     | 45 min   |
| 09:45-10:30 | 2      | Getting Started with doe-helper         | 45 min   |
| 10:30-10:45 |        | *Break*                                 | 15 min   |
| 10:45-11:30 | 3      | Full Factorial Designs                  | 45 min   |
| 11:30-12:15 | 4      | Fractional Factorial & Screening        | 45 min   |
| 12:15-13:15 |        | *Lunch*                                 | 60 min   |
| 13:15-14:00 | 5      | Response Surface Designs                | 45 min   |
| 14:00-14:45 | 6      | Analysis & Interpretation               | 45 min   |
| 14:45-15:00 |        | *Break*                                 | 15 min   |
| 15:00-15:45 | 7      | Multi-Response & Advanced Topics        | 45 min   |
| 15:45-17:15 | 8      | Capstone Project & Presentations        | 90 min   |

---

## Module 1: Introduction to DOE (45 min)

### Teaching Approach (20 min lecture, 15 min exercise, 10 min discussion)

**Opening Hook (5 min):**
Ask participants: "How do you currently decide what settings to use when tuning a system?" Collect answers. Most will describe ad-hoc or OVAT approaches. This sets up the motivation for DOE.

**Key Points to Emphasise:**
- The OVAT trap is intuitive but statistically inefficient. Use the web-server example: 3 factors, each at 2 levels. OVAT tests 7 combinations and misses interactions. Full factorial tests 8 and captures everything.
- Effect sparsity is the principle that makes screening designs work. In a system with 10 factors, typically only 2-3 have meaningful effects.
- DOE is not new — it was developed in the 1920s for agriculture and has been proven across every field of engineering and science.

**Common Student Questions:**
- *"When should I NOT use DOE?"* — When there's only one factor, when the system is too expensive to test at multiple settings, or when you already have abundant data (use regression instead).
- *"How many factors can I handle?"* — Screening designs can handle 20+ factors in 20 runs. Emphasise that DOE scales.
- *"Do I need to understand the statistics to use doe-helper?"* — Basic understanding helps interpretation, but doe-helper automates the statistics. Focus on understanding what "significant" means.

**Exercise 1 Notes:**
- Ensure all participants have doe-helper installed before starting.
- Walk around and help with any installation issues.
- The config.json exploration is key — make sure they understand factors, levels, and responses.
- The bonus question prepares them for the rest of the course.

---

## Module 2: Getting Started with doe-helper (45 min)

### Teaching Approach (20 min lecture/demo, 20 min exercise, 5 min wrap-up)

**Live Demo (15 min):**
Walk through a complete example on screen:
1. `doe init coffee_brewing --design full_factorial`
2. Open and explain each field in config.json
3. `doe info coffee_brewing/`
4. `doe generate coffee_brewing/`
5. Show the design matrix in design.csv
6. Show the runner script (run.sh or run.py)

**Key Points to Emphasise:**
- config.json is the single source of truth for an experiment.
- Factor coding: all factors are internally scaled to -1/+1 for analysis. This makes effects directly comparable regardless of original units.
- The "target" field in responses drives the optimisation direction.
- `doe info` is your pre-flight check — always run it before generating.

**Common Pitfalls:**
- JSON syntax errors (missing commas, trailing commas). Recommend a JSON linter.
- Forgetting to set units — not technically required but makes reports much more readable.
- Setting low > high for factors. doe-helper will catch this but explain why coded variables need low < high.
- Categorical factors in designs that require continuous factors (e.g., CCD). doe-helper will warn.

**Exercise 2 Notes:**
- The webapp_perf scenario is intentionally realistic for software engineers.
- Common mistake: trying to use categorical factors with full_factorial (it works, but the run count may surprise them since "none"/"gzip"/"brotli" creates 3 levels, giving 2 x 2 x 3 = 12 runs instead of 8).
- After `doe generate`, have students look at the design.csv and count runs.
- If time permits, have students modify a factor and re-generate to see the impact.

---

## Module 3: Full Factorial Designs (45 min)

### Teaching Approach (20 min lecture, 20 min exercise, 5 min discussion)

**Whiteboard Work (10 min):**
Draw a 2^2 factorial design on the whiteboard:
- Show the four corners of the square
- Calculate effects by hand: main A, main B, interaction AB
- Use the seal strength example from the slides

**Key Points to Emphasise:**
- The beauty of full factorial is that it's balanced — every effect estimate uses ALL the data.
- Interactions are the main reason DOE exists. Draw a non-parallel interaction plot and explain what it means practically.
- Center points are cheap insurance. 3-5 center points added to a 2^k design detect curvature without adding many runs.
- ANOVA partitions total variability into components. The F-test asks "is this component large relative to random noise?"

**Teaching the Pareto Chart:**
Show a real Pareto chart output from doe-helper. Walk through:
1. What the bars represent (absolute effect magnitudes)
2. What the reference line means (significance threshold)
3. How to read which factors matter
4. Connection to ANOVA p-values (they tell the same story)

**Exercise 3 Notes:**
- The seal strength experiment is a classic DOE teaching example.
- Students should find that temperature has the largest effect, with a significant temperature x pressure interaction.
- If the simulation includes random noise, results will vary between students — this is a teaching opportunity about replication.
- The `doe report` HTML output is impressive — give students 5 minutes to explore it.

---

## Module 4: Fractional Factorial & Screening (45 min)

### Teaching Approach (20 min lecture, 20 min exercise, 5 min wrap-up)

**Conceptual Foundation (10 min):**
Before diving into resolution and aliasing, establish the intuition:
- "We can't afford to test everything, so we test a clever subset."
- "The trade-off is that some effects become tangled together (aliased)."
- "Resolution tells us how badly tangled things are."

Use this analogy: Resolution III is like sharing a phone line with someone — you can hear them but also hear background noise (2FIs). Resolution V is like having your own dedicated line — crystal clear.

**Key Points to Emphasise:**
- Resolution III: adequate for initial screening but requires follow-up.
- Resolution IV: the sweet spot for most screening situations.
- Resolution V: almost as good as a full factorial.
- Definitive Screening Designs are the modern best practice for screening. If students will only remember one screening design, make it DSD.
- The screening workflow is iterative: screen -> narrow -> characterise -> optimise.

**Fold-Over Demo:**
Show `doe augment --method fold-over` and explain:
- It creates a mirror image of the original design
- Combined with the original, it breaks aliasing
- This is the sequential advantage — you don't need to plan everything upfront

**Exercise 4 Notes:**
- Students design a screening experiment with 8 factors.
- Plackett-Burman for 8 factors needs 12 runs. DSD needs 17 runs.
- Encourage students to compare the two approaches and discuss the trade-off.
- The comparison between PB and DSD is the most important learning outcome: more runs gives cleaner estimates.

---

## Module 5: Response Surface Designs (45 min)

### Teaching Approach (20 min lecture, 20 min exercise, 5 min discussion)

**Visual Approach (15 min):**
RSM is best taught visually. If possible, show:
- A 3D surface plot with a clear optimum (hill)
- A saddle point surface (tricky — the optimum depends on direction)
- Contour plots as the 2D projection

Use the analogy: "A contour map is like a topographic map. You're looking for the peak of the mountain."

**Key Points to Emphasise:**
- CCD = factorial + star points + center points. Show how each component adds information.
- Star points extend the design along each axis to estimate quadratic effects.
- Box-Behnken avoids extreme corners — important when extreme combinations are dangerous, expensive, or physically impossible.
- Alpha (star point distance) controls rotatability. doe-helper sets this automatically.
- LHS is fundamentally different: it's model-free and space-filling. Use it when you don't trust any model assumption.

**doe optimize Demo:**
Run `doe optimize` live and explain:
- It uses scipy.optimize (L-BFGS-B) with 20 random restarts
- Multiple restarts avoid local optima
- The output shows optimal settings and predicted responses
- Desirability score balances multiple responses

**Exercise 5 Notes:**
- The reactor_optimization use case is pre-built — students can use `doe init`.
- CCD for 3 factors produces 20 runs. Box-Behnken produces 15.
- Key comparison: do they give the same optimal settings? Usually very close.
- If time permits, ask students to try LHS with 20 runs and compare.

---

## Module 6: Analysis & Interpretation (45 min)

### Teaching Approach (25 min lecture/demo, 15 min exercise, 5 min discussion)

**Deep Analysis Demo (25 min):**
This module requires more lecture time because interpretation is a skill, not just a procedure. Walk through a complete `doe analyze` output:

1. **ANOVA table:** Read each column, explain degrees of freedom, show how SS partitions total variability. Emphasise p-values: < 0.05 significant, < 0.01 highly significant.

2. **Pareto chart:** Point to the reference line. Ask "which factors matter?" This should be immediate.

3. **Main effects plots:** "Which factor has the steepest slope?" That's the one with the biggest main effect.

4. **Interaction plots:** "Are the lines parallel? No? Then there's an interaction." Show what parallel vs. crossing means practically.

5. **Residual diagnostics:** This is where most students struggle. Spend time on:
   - Residuals vs. fitted: random scatter is good, patterns are bad
   - Normal Q-Q: points should follow the diagonal line
   - Common problem patterns: funnel shape (transform), curve (add quadratic terms)

6. **Model adequacy:** R^2, Adj-R^2, Pred-R^2. The gap between Adj and Pred should be < 0.2. If not, the model may be overfitting.

**Common Interpretation Mistakes:**
- Confusing statistical significance with practical significance. A factor can be statistically significant but have a tiny effect.
- Ignoring interactions and only looking at main effects.
- Overfitting: adding too many terms to the model.
- Not checking residuals before trusting the results.

**Exercise 6 Notes:**
- Students should write their own interpretation — this is the most important skill.
- Walk around and review their summaries. Look for:
  - Correct identification of significant factors
  - Mention of interactions (if present)
  - Reference to residual diagnostics
  - Appropriate confidence in conclusions

---

## Module 7: Multi-Response & Advanced Topics (45 min)

### Teaching Approach (25 min lecture, 15 min exercise, 5 min wrap-up)

**Multi-Response Optimisation (15 min):**
- Start with the conflict: "You can have high yield OR low cost, but not both. How do you choose?"
- Explain desirability functions with a simple visual:
  - For "maximize": d = 0 at worst, d = 1 at best, linear in between
  - For "minimize": inverted
  - For "target": peaks at the target value
  - Overall D = geometric mean — all responses must be acceptable
- Show `doe optimize` with multiple responses and interpret the output.

**Design Augmentation (5 min):**
- Key message: DOE is sequential. You build knowledge iteratively.
- `doe augment` lets you extend without starting over.
- This is a major practical advantage over ad-hoc testing.

**Taguchi and Mixtures (5 min):**
- Brief overview only — these are specialised topics.
- Taguchi: focus on the S/N ratio concept.
- Mixtures: constraints (sum to 1) make them unique.

**Exercise 7 Notes:**
- The multi-response exercise builds on previous work, so students have context.
- Key learning: the desirability score is a compromise. No single response is perfectly optimised.
- Power analysis often surprises students — designs they thought were adequate may lack power for small effects.

---

## Module 8: Capstone Project (90 min)

### Teaching Approach (10 min introduction, 70 min project work, 10 min presentations)

**Project Setup (10 min):**
- Present the three options and let students choose (or form groups).
- Clarify deliverables and time budget.
- Suggest time allocation: 30 min screening, 30 min RSM/optimization, 10 min report.

**Facilitation During Project (70 min):**
- Walk around and offer guidance, but let students drive.
- Common issues:
  - Getting stuck on config.json — point them to `doe init` templates.
  - Not knowing which factors to drop after screening — look at p-values and Pareto.
  - Running out of budget — remind them of the budget constraint and help them choose designs wisely.
  - Interpretation paralysis — encourage them to write a simple sentence: "Factor X matters because..."

**Presentations (10 min or more if time allows):**
- Each student/group presents for 3-5 minutes.
- Encourage questions from the audience.
- Look for: clear problem statement, justified design choices, correct interpretation, practical recommendations.

---

## General Teaching Tips

1. **Use the 221 use cases** as examples throughout. They cover diverse domains, so you can pick examples relevant to your audience.

2. **Encourage hands-on work.** Every module has an exercise. Resist the urge to spend too long on slides.

3. **Install doe-helper beforehand.** Send installation instructions 1 week before the course. Have a backup plan (shared server, Docker container) for installation issues.

4. **Print the exercise sheets.** Students appreciate having a physical reference they can annotate.

5. **Adapt to the audience.** For software engineers, emphasise cloud/DevOps use cases. For scientists, use chemical/biological examples. For manufacturing, use quality/process examples.

6. **Emphasise the workflow, not just the statistics.** The power of DOE is in the systematic approach: define -> design -> run -> analyse -> optimise. The statistics support this, but the workflow is what participants will use daily.

7. **Address "but my problem is different" early.** When participants say their problem can't use DOE, ask: "Do you have controllable factors and a measurable response?" If yes, DOE applies.

8. **Leave time for the capstone.** The capstone is where learning solidifies. Don't sacrifice it for more lecture time.

---

## Assessment Rubric (for Capstone)

| Criterion                  | Excellent (5)               | Good (3-4)                  | Needs Work (1-2)           |
|----------------------------|-----------------------------|-----------------------------|----------------------------|
| Design selection           | Appropriate, justified      | Reasonable choice           | Wrong design type          |
| doe-helper usage           | Full workflow, all commands  | Most commands used          | Limited use                |
| Analysis interpretation    | Correct, nuanced            | Mostly correct              | Significant errors         |
| Factor selection           | Well-reasoned screening      | Adequate                    | Arbitrary                  |
| Optimisation               | Multi-response, desirability | Single response             | Not attempted              |
| Report quality             | Clear, complete, actionable | Adequate                    | Missing key elements       |
| Presentation               | Clear, confident, concise   | Adequate communication      | Unclear or incomplete      |
