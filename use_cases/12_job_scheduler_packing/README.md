# Use Case 12: Job Scheduler Packing

Optimize HPC job scheduler packing to maximize throughput and resource efficiency using a central composite design.

## Factors

| Factor         | Low | High | Unit  |
|----------------|-----|------|-------|
| nodes          | 4   | 64   | count |
| tasks_per_node | 8   | 48   | count |
| mem_per_task   | 1   | 8    | GB    |

**Fixed:** partition=compute, walltime=4h

## Responses

- **throughput** (maximize, jobs/h) -- peaks at moderate tasks_per_node, decreases with high memory
- **efficiency** (maximize, %) -- decreases with more nodes due to communication overhead

## Running

```bash
doe run config.json
# or manually:
bash sim.sh --nodes 16 --tasks_per_node 24 --mem_per_task 4 --out result.json
```
