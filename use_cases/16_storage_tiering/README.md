# Use Case 16: Burst Buffer / Storage Tiering

Optimize HPC storage tiering and burst buffer configuration using a fractional factorial design.

## Factors

| Factor        | Level -1      | Level +1      | Unit |
|---------------|---------------|---------------|------|
| burst_buffer  | off           | on            | --   |
| stage_in      | sync          | async         | --   |
| cache_size    | 64            | 512           | GB   |
| write_policy  | write_back    | write_through | --   |
| prefetch      | off           | on            | --   |

**Fixed:** pfs=gpfs, job_count=100

## Responses

- **io_throughput** (maximize, GB/s) -- base ~20 GB/s, doubled by burst_buffer, boosted by async and write_back
- **stage_time** (minimize, sec) -- base ~120s, halved by async+prefetch

## Running

```bash
doe run config.json
# or manually:
bash sim.sh --burst_buffer on --stage_in async --cache_size 256 \
            --write_policy write_back --prefetch on --out result.json
```
