# Power Capping & Performance Trade-off

## Scenario

Modern GPU-accelerated HPC clusters consume enormous amounts of power, and
facility operators must balance raw compute throughput against energy budgets
and cooling constraints. Hardware-level power capping (CPU RAPL limits, GPU
board power limits) and memory frequency scaling provide knobs that directly
trade performance for energy savings -- but the relationship is non-linear and
workload-dependent.

This use case applies a **Central Composite Design (CCD)** with three
continuous factors to systematically map the power-performance Pareto frontier
on a four-node cluster of AMD EPYC 9654 CPUs and NVIDIA H100 SXM GPUs running
HPL (High-Performance Linpack).

### Factors

| Factor | Range | Unit | Description |
|---|---|---|---|
| `cpu_power_cap` | 120 -- 240 | W | CPU package power limit set via RAPL |
| `gpu_power_cap` | 200 -- 400 | W | GPU board power limit via `nvidia-smi` |
| `mem_freq` | 2400 -- 3200 | MHz | DDR5 memory frequency setting |

### Fixed conditions

- **CPU**: AMD EPYC 9654 (96 cores, Genoa)
- **GPU**: NVIDIA H100 SXM (80 GB HBM3)
- **Nodes**: 4
- **Workload**: HPL (High-Performance Linpack)

### Responses

| Response | Goal | Unit | Description |
|---|---|---|---|
| `gflops` | Maximize | GFLOPS | Sustained double-precision floating-point throughput |
| `gflops_per_watt` | Maximize | GFLOPS/W | Energy efficiency (performance per watt) |

## Demonstrates

- **Central Composite Design (CCD)**: A second-order response surface design
  that augments a 2^k factorial with axial (star) points and center-point
  replicates, enabling estimation of quadratic effects and curvature without
  running a full three-level factorial.
- **Power-performance Pareto optimization**: Identifying the set of
  non-dominated configurations where improving one objective (throughput)
  necessarily worsens another (efficiency), and selecting the "knee" of the
  Pareto front.
- **Energy efficiency metrics**: Using GFLOPS-per-watt as a first-class
  response alongside raw GFLOPS so that the experimenter can quantify the
  diminishing returns of increasing power caps.

## Running

```bash
# Generate the CCD experiment matrix
doe generate use_cases/20_power_performance_tradeoff/config.json

# Execute all runs (simulated)
doe run use_cases/20_power_performance_tradeoff/config.json

# Analyse results and fit response surfaces
doe analyse use_cases/20_power_performance_tradeoff/config.json
```
