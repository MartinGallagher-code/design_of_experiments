# Use Case 21: SIMD Vectorization Tuning

## Scenario

Optimizing the vectorization strategy for stencil computation kernels running
on AVX-512 capable HPC processors (Xeon 8490H). The experiment explores how
SIMD register width, data layout, loop unrolling, and memory alignment interact
to affect sustained throughput and vectorization efficiency of a 7-point stencil
kernel operating on a 512x512x512 double-precision grid.

A **full factorial design** with 4 two-level factors produces **2^4 = 16 runs**,
enabling estimation of all main effects and interactions.

## Factors

| # | Factor | Levels | Type | Description |
|---|--------|--------|------|-------------|
| 1 | `simd_width` | 256, 512 bits | Continuous | AVX2 vs AVX-512 register width |
| 2 | `data_layout` | AoS, SoA | Categorical | Array of Structures vs Structure of Arrays |
| 3 | `unroll_factor` | 1, 8 | Continuous | Loop unrolling factor |
| 4 | `alignment` | none, 64B | Categorical | Data alignment strategy |

## Fixed Factors

- **Processor:** Intel Xeon 8490H (Sapphire Rapids, 60 cores)
- **Kernel:** 7-point stencil
- **Grid size:** 512 x 512 x 512
- **Precision:** double (FP64)

## Responses

| Response | Goal | Unit | Description |
|----------|------|------|-------------|
| `gflops` | Maximize | GFLOPS | Sustained compute throughput |
| `vectorization_pct` | Maximize | % | Percentage of FLOPs executed in SIMD lanes |

## Demonstrates

- **Full factorial design** -- systematic enumeration of all factor-level combinations
- **SIMD width selection** -- quantifying the benefit of AVX-512 over AVX2
- **Compiler hint effectiveness** -- measuring the impact of unrolling and alignment pragmas
- **Data layout impact** -- AoS vs SoA tradeoffs for vectorized stencil computation

## Running

```bash
# Generate the experiment matrix and run scripts
doe generate use_cases/21_vectorization_simd_tuning/config.json

# Execute all 16 runs
doe run use_cases/21_vectorization_simd_tuning/config.json

# Analyse results
doe analyse use_cases/21_vectorization_simd_tuning/config.json
```
