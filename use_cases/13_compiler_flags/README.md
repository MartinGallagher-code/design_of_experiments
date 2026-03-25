# Use Case 13: Compiler Optimization Flags

Screen GCC 13 compiler flags using a Plackett-Burman design to identify which flags most affect execution time and binary size on the NPB BT benchmark.

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
