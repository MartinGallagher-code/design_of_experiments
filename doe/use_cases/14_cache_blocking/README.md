# Use Case 14: Cache Blocking Strategy

## Scenario

You are tuning cache blocking tile sizes and prefetch distance for a DGEMM kernel operating on a 4096x4096 matrix. Tile sizes that are too small leave performance on the table, while tiles that are too large overflow the cache and spike miss rates, so the optimal configuration lies in a narrow region of the four-dimensional parameter space. A Latin Hypercube design with 25 samples provides space-filling coverage to efficiently map this landscape.

**This use case demonstrates:**
- Latin Hypercube design for space-filling exploration of continuous factors
- Cache hierarchy optimization for dense linear algebra
- Trade-off between computational throughput (GFLOPS) and cache miss rate

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
