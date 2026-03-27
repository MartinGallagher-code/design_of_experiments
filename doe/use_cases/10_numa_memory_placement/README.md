# Use Case 10: NUMA Memory Placement

## Scenario

You are optimizing memory performance on a dual-socket server with 32 cores per socket. Three categorical factors — NUMA memory policy, thread binding strategy, and huge page configuration — control how memory is allocated and accessed. A full factorial design (2^3 = 8 runs) is small enough to run exhaustively and reveals a classic NUMA trade-off: configurations that maximize bandwidth often increase latency, and vice versa.

**This use case demonstrates:**
- Full factorial design with all categorical factors (2^3 = 8 runs)
- NUMA-aware performance tuning
- Trade-off between bandwidth (STREAM Triad) and latency
- Interaction effects between memory policy and thread binding

## Factors

| Factor | Low | High | Type | Description |
|--------|-----|------|------|-------------|
| mem_policy | local | interleave | categorical | NUMA memory policy |
| thread_bind | close | spread | categorical | Thread binding strategy |
| hugepages | off | 2M | categorical | Huge page configuration |

**Fixed:** sockets = 2, cores_per_socket = 32

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| stream_triad | maximize | GB/s |
| latency_ns | minimize | ns |

## Running the Demo

```bash
cd /workspaces/design_of_experiments
doe info --config use_cases/10_numa_memory_placement/config.json
doe generate --config use_cases/10_numa_memory_placement/config.json \
    --output use_cases/10_numa_memory_placement/results/run.sh --seed 42
bash use_cases/10_numa_memory_placement/results/run.sh
doe analyze --config use_cases/10_numa_memory_placement/config.json
doe report --config use_cases/10_numa_memory_placement/config.json \
    --output use_cases/10_numa_memory_placement/results/report.html
```

## Files

- Config: `use_cases/10_numa_memory_placement/config.json`
- Simulator: `use_cases/10_numa_memory_placement/sim.sh`
- Results: `use_cases/10_numa_memory_placement/results/`
