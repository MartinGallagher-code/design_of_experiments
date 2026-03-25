# Use Case 14: Cache Blocking Strategy

Optimize DGEMM cache blocking tile sizes and prefetch distance using a Latin Hypercube design (25 samples).

## Factors

| Factor        | Low | High | Unit       |
|---------------|-----|------|------------|
| block_i       | 16  | 256  | elements   |
| block_j       | 16  | 256  | elements   |
| block_k       | 16  | 256  | elements   |
| prefetch_dist | 1   | 8    | iterations |

**Fixed:** matrix_size=4096, algorithm=dgemm

## Responses

- **gflops** (maximize, GFLOPS) -- peaks around block sizes 64-128, drops at extremes
- **cache_miss_rate** (minimize, %) -- lowest at mid-range blocks with moderate prefetch

## Running

```bash
doe run config.json
# or manually:
bash sim.sh --block_i 64 --block_j 64 --block_k 64 --prefetch_dist 4 --out result.json
```
