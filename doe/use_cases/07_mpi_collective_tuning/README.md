# Use Case 7: MPI Collective Tuning

## Scenario

You are tuning MPI collective communication on a 32-node cluster running OpenMPI. Six factors — message size, algorithm choice, processes per node, eager/rendezvous threshold, process binding, and collective auto-tuning — all potentially affect allreduce latency and bandwidth. A Plackett-Burman screening design efficiently identifies which factors matter most before a deeper optimization study.

**This use case demonstrates:**
- Plackett-Burman screening design (6 factors in 12 runs per block)
- Blocking to account for run-to-run cluster variability
- Trade-off between latency and bandwidth optimization
- Mixing continuous and categorical factors in HPC contexts

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| msg_size | 4096 | 1048576 | continuous | bytes | Message size |
| algorithm | ring | recursive_doubling | categorical | | Allreduce algorithm |
| ppn | 16 | 64 | continuous | | Processes per node |
| eager_limit | 4096 | 262144 | continuous | bytes | Eager protocol threshold |
| binding | core | socket | categorical | | Process binding policy |
| coll_tuning | on | off | categorical | | Auto-tuning |

**Fixed:** nodes = 32, mpi_impl = openmpi

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| allreduce_latency | minimize | us |
| bandwidth | maximize | GB/s |

## Running the Demo

```bash
cd /workspaces/design_of_experiments
doe info --config use_cases/07_mpi_collective_tuning/config.json
doe generate --config use_cases/07_mpi_collective_tuning/config.json \
    --output use_cases/07_mpi_collective_tuning/results/run.sh --seed 42
bash use_cases/07_mpi_collective_tuning/results/run.sh
doe analyze --config use_cases/07_mpi_collective_tuning/config.json
doe report --config use_cases/07_mpi_collective_tuning/config.json \
    --output use_cases/07_mpi_collective_tuning/results/report.html
```

## Files

- Config: `use_cases/07_mpi_collective_tuning/config.json`
- Simulator: `use_cases/07_mpi_collective_tuning/sim.sh`
- Results: `use_cases/07_mpi_collective_tuning/results/`
