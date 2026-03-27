# Use Case 12: Job Scheduler Packing

## Scenario

You are optimizing job scheduler packing parameters on an HPC cluster to maximize throughput and resource efficiency. Increasing tasks per node improves utilization but risks memory contention, while scaling across more nodes introduces communication overhead that erodes efficiency. A central composite design lets you model these nonlinear trade-offs and find the sweet spot across node count, task density, and memory allocation.

**This use case demonstrates:**
- Central composite design for response surface modeling
- Trade-off between throughput and resource efficiency
- Nonlinear effects of task packing density on memory-bound workloads

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
