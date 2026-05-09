# When to pick which adaptive strategy

`doe next-batch` reads the existing results and proposes the next batch.
The choice of strategy goes in your config:

```json
"adaptive": {
  "strategy": "bayesian",
  "batch_size": 4,
  "stopping_max_phases": 5
}
```

| Strategy           | Surrogate              | Acquisition          | Multi-objective | Categorical factors | Replicate noise |
|--------------------|------------------------|----------------------|-----------------|---------------------|-----------------|
| `refine`           | none                   | perturb best run     | n/a             | yes (kept fixed)    | n/a             |
| `explore`          | none                   | distance to existing | n/a             | yes (kept fixed)    | n/a             |
| `balanced`         | none                   | half refine / half explore | n/a       | yes                 | n/a             |
| `model_guided`     | quadratic / linear OLS | predicted optimum + max leverage | n/a   | yes (decoded back)  | n/a             |
| `bayesian`         | Gaussian process       | Expected Improvement (q-EI w/ constant-liar) | no | one-hot encoded   | from replicates |
| `multi_objective`  | one GP per response    | random Tchebycheff EI scalarisation          | yes | one-hot encoded   | one GP-fit's σ_n² each |

## Decision tree

```
multiple responses?
├── yes → multi_objective
└── no
    │
    enough data for a GP fit (n ≥ 5–10)?
    ├── yes → bayesian
    └── no
        │
        is this the first batch after a small seed?
        ├── yes → model_guided
        └── no
            │
            do you have a clear current best?
            ├── yes → refine
            └── no  → explore  (or balanced when uncertain)
```

## Practical tips

- **Seed matters.** GP-based strategies need ≥ 5 well-spaced points to
  fit a meaningful length scale. A 2-level full / fractional factorial
  + a few centre points is a good seed.
- **Bayesian on small budgets**: prefer `bayesian` once you have at
  least one well-fit GP; it tends to outperform `refine` on smooth
  surfaces from about phase 2 onwards.
- **Categorical factors**: `bayesian` and `multi_objective` use a
  one-hot encoder under the hood, so categoricals can vary in the
  proposed batch. `refine` / `explore` keep them at the current run's
  level.
- **Replicates help GPs**: when you have replicate runs (same factor
  settings), `bayesian` automatically uses the within-group variance
  as that point's noise term, producing tighter posteriors elsewhere.
