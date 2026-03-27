# Use Case 13: Compiler Optimization Flags

## Scenario

You are screening GCC 13 compiler optimization flags to determine which ones most affect execution time and binary size for the NPB BT benchmark. Aggressive flags like LTO, PGO, and fast-math can dramatically reduce runtime but may inflate binary size or introduce numerical inaccuracies, making it critical to identify the dominant effects before committing to a full optimization study. A Plackett-Burman screening design efficiently tests seven flags in a minimal number of runs.

**This use case demonstrates:**
- Plackett-Burman screening design (7 two-level categorical factors)
- Trade-off between execution time and binary size
- Systematic identification of dominant compiler flags before deeper optimization

## Factors

| Factor     | Level -1 | Level +1 |
|------------|----------|----------|
| opt_level  | O2       | O3       |
| vectorize  | off      | avx512   |
| lto        | off      | on       |
| march      | native   | znver3   |
| unroll     | off      | on       |
| fast_math  | off      | on       |
| pgo        | off      | on       |

**Fixed:** compiler=gcc13, benchmark=npb_bt

## Responses

- **exec_time** (minimize, sec) -- base ~120s, reduced by O3, avx512, lto, pgo, fast_math
- **binary_size** (minimize, MB) -- base ~15MB, increased by lto, unroll, pgo

## Running

```bash
doe run config.json
# or manually:
bash sim.sh --opt_level O3 --vectorize avx512 --lto on --march native \
            --unroll on --fast_math off --pgo on --out result.json
```
