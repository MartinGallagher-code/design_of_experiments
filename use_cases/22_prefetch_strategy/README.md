# Use Case 22: Hardware & Software Prefetch Tuning

## Scenario

A memory-bound Computational Fluid Dynamics (CFD) solver running on Intel Xeon 8490H
processors spends a significant fraction of execution time waiting on data from main
memory. The structured-grid solver iterates over a 256M-point domain, and performance
profiling reveals that last-level cache (LLC) misses dominate the stall cycles.

Modern processors expose several knobs that control how data is brought into the cache
hierarchy ahead of demand: hardware prefetchers built into the CPU, software prefetch
instructions inserted by the compiler or programmer, TLB prefetching, and dedicated
helper threads whose sole job is to run ahead and warm the caches. Tuning these knobs
individually is common, but their interactions are poorly understood -- enabling two
prefetch mechanisms simultaneously can cause cache pollution or bandwidth contention
that negates the benefit of either one alone.

This use case applies a **Plackett-Burman screening design** with **6 factors** to
efficiently identify which prefetch parameters have the largest main effects on solver
time and cache miss rate, and to flag important two-factor interactions before
committing to a full factorial or response-surface study.

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
