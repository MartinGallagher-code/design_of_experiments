# Use Case 18: Interconnect Topology & Adaptive Routing

## Scenario

You are optimizing dragonfly network routing on a 3072-node HPC cluster with 16 groups of 48 switches each. Five factors — routing mode, virtual channel count, traffic pattern, link bandwidth, and job placement strategy — all potentially affect message latency and bisection throughput. A Plackett-Burman screening design efficiently identifies which factors dominate performance before committing to a full response-surface study.

**This use case demonstrates:**
- Plackett-Burman screening design (5 factors in 12 runs per block)
- Adaptive routing optimization on dragonfly interconnects
- Congestion-aware traffic management and placement strategies
- Interaction effects between routing algorithm and communication pattern

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| routing_mode | minimal | adaptive | categorical | | Routing algorithm — shortest path vs congestion-aware |
| vc_count | 2 | 8 | continuous | | Virtual channels per physical link |
| traffic_pattern | nearest_neighbor | alltoall | categorical | | Application communication pattern |
| link_bandwidth | 100 | 200 | continuous | Gbps | Per-link injection bandwidth |
| job_placement | compact | scatter | categorical | | Job placement strategy across groups |

**Fixed:** topology = dragonfly, groups = 16, switches_per_group = 48, nodes = 3072

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| msg_latency_us | minimize | us |
| throughput_GBs | maximize | GB/s |

## Running the Demo

```bash
cd /workspaces/design_of_experiments
python doe.py info --config use_cases/18_interconnect_topology_routing/config.json
python doe.py generate --config use_cases/18_interconnect_topology_routing/config.json \
    --output use_cases/18_interconnect_topology_routing/results/run.sh --seed 42
bash use_cases/18_interconnect_topology_routing/results/run.sh
python doe.py analyze --config use_cases/18_interconnect_topology_routing/config.json
python doe.py report --config use_cases/18_interconnect_topology_routing/config.json \
    --output use_cases/18_interconnect_topology_routing/results/report.html
```

## Files

- Config: `use_cases/18_interconnect_topology_routing/config.json`
- Simulator: `use_cases/18_interconnect_topology_routing/sim.sh`
- Results: `use_cases/18_interconnect_topology_routing/results/`
