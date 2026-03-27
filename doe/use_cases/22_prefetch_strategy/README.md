# Use Case 22: Hardware & Software Prefetch Tuning

## Scenario

You are tuning hardware and software prefetch parameters for a memory-bound CFD solver running on Intel Xeon 8490H processors, where LLC misses dominate stall cycles across a 256M-point structured grid. Enabling multiple prefetch mechanisms simultaneously can cause cache pollution or bandwidth contention that negates the benefit of either one alone, so understanding their interactions is critical. A Plackett-Burman screening design with six factors efficiently identifies the dominant prefetch knobs and flags important two-factor interactions before committing to a full optimization study.

**This use case demonstrates:**
- Plackett-Burman screening design (6 factors in 12 runs per block)
- Hardware/software prefetch interaction effects
- Cache hierarchy optimization for memory-bound HPC workloads
- Trade-off between solver time and cache miss rate

## Factors

| # | Factor              | Low               | High              | Description                              |
|---|---------------------|-------------------|-------------------|------------------------------------------|
| 1 | hw_prefetcher       | off               | on                | L2 adjacent-line hardware prefetcher     |
| 2 | sw_prefetch_dist    | 64 bytes          | 512 bytes         | Software prefetch distance ahead of use  |
| 3 | l2_stream_detect    | off               | on                | L2 hardware stream detector              |
| 4 | dcache_policy       | write_back        | write_through     | L1 data cache write policy               |
| 5 | prefetch_threads    | 0                 | 2                 | Dedicated software prefetch helper threads |
| 6 | tlb_prefetch        | off               | on                | TLB entry prefetching                    |

## Responses

- **solver_time_sec** -- Total wall-clock time for 100 solver iterations (minimize).
- **cache_miss_rate** -- LLC miss rate as a percentage (minimize).

## Design

Plackett-Burman screening in 12 runs (the nearest multiple of 4 above k+1 = 7),
replicated in 2 blocks for a total of 24 experimental runs. This design is
Resolution III, meaning main effects are aliased with two-factor interactions.
Follow-up experiments (e.g., a Resolution V fractional factorial) would be needed
to cleanly separate interactions.

## What This Demonstrates

- **Plackett-Burman screening** -- a saturated two-level design that estimates all
  main effects in the minimum number of runs.
- **Prefetch distance optimization** -- quantifying the benefit of tuning the
  software prefetch distance for a specific access pattern.
- **HW / SW prefetch interaction** -- the synergy (or interference) between
  hardware and software prefetch mechanisms.
- **Cache hierarchy effects** -- how write policy, TLB prefetching, and stream
  detection combine to affect overall memory-subsystem performance.

## Running

```bash
doe run use_cases/22_prefetch_strategy/config.json
doe analyze use_cases/22_prefetch_strategy/config.json
```
