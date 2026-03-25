# Use Case 17: CPU Cross-NUMA Bandwidth

## Scenario

You are optimizing CPU-to-CPU cross-NUMA node memory bandwidth and latency on a 4-socket supercomputer node with 28 cores per socket. On multi-socket systems, data transfers between NUMA domains traverse different interconnect hops depending on the socket topology: local accesses stay within the same socket, near accesses cross one hop to an adjacent socket (NUMA distance 21), and far accesses cross two hops to a diagonal socket (NUMA distance 31). Understanding these penalties is critical for data placement, task mapping, and communication-intensive HPC workloads. A full factorial design (3 x 2 x 2 x 2 = 24 runs) systematically characterizes how NUMA hop distance, transfer mechanism, thread parallelism, and buffer size interact to determine achievable cross-socket bandwidth and latency.

**This use case demonstrates:**
- Full factorial design with mixed categorical and continuous factors (3 x 2 x 2 x 2 = 24 runs)
- Cross-NUMA CPU-to-CPU bandwidth optimization
- NUMA distance and topology effects on memory throughput
- Interaction between transfer mode and CPU affinity

## Factors

| Factor | Levels | Type | Unit | Description |
|--------|--------|------|------|-------------|
| numa_hop | local, near, far | categorical | | NUMA distance: local (same socket), near (adjacent), far (diagonal) |
| transfer_mode | memcpy, streaming_store | categorical | | Data transfer mechanism |
| thread_count | 1, 14 | continuous | threads | Number of threads performing the transfer |
| buffer_size | 1048576, 268435456 | continuous | bytes | Transfer buffer size (1 MB to 256 MB) |

**Fixed:** sockets = 4, cores_per_socket = 28, numa_distance_near = 21, numa_distance_far = 31

## Responses

| Response | Direction | Unit | Description |
|----------|-----------|------|-------------|
| bandwidth_GBs | maximize | GB/s | Cross-NUMA memory bandwidth |
| latency_ns | minimize | ns | Average per-cacheline access latency |

## Running the Demo

```bash
cd /workspaces/design_of_experiments
python doe.py info --config use_cases/17_cpu_cross_numa_bandwidth/config.json
python doe.py generate --config use_cases/17_cpu_cross_numa_bandwidth/config.json \
    --output use_cases/17_cpu_cross_numa_bandwidth/results/run.sh --seed 42
bash use_cases/17_cpu_cross_numa_bandwidth/results/run.sh
python doe.py analyze --config use_cases/17_cpu_cross_numa_bandwidth/config.json
python doe.py report --config use_cases/17_cpu_cross_numa_bandwidth/config.json \
    --output use_cases/17_cpu_cross_numa_bandwidth/results/report.html
```

## Files

- Config: `use_cases/17_cpu_cross_numa_bandwidth/config.json`
- Simulator: `use_cases/17_cpu_cross_numa_bandwidth/sim.sh`
- Results: `use_cases/17_cpu_cross_numa_bandwidth/results/`
