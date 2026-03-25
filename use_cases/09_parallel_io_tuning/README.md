# Use Case 9: Parallel I/O Tuning

## Scenario

You are tuning parallel I/O performance for a scientific application writing 100 GB checkpoint files to a Lustre filesystem. Five factors control striping, aggregation, and buffering behavior. A fractional factorial design (2^{5-1} = 16 runs) halves the full factorial cost while still estimating all main effects.

**This use case demonstrates:**
- Fractional factorial design (resolution V, 5 factors in 16 runs)
- Lustre filesystem tuning for HPC workloads
- Both write and read bandwidth as dual responses
- Effect of collective I/O on parallel file access

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| stripe_count | 4 | 32 | continuous | | Lustre stripe count |
| stripe_size | 1 | 16 | continuous | MB | Lustre stripe size |
| aggregators | 4 | 64 | continuous | | I/O aggregator count |
| collective_io | on | off | categorical | | MPI-IO collective buffering |
| alignment | 1 | 4 | continuous | MB | File alignment boundary |

**Fixed:** filesystem = lustre, file_size_gb = 100

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| write_bw | maximize | GB/s |
| read_bw | maximize | GB/s |

## Running the Demo

```bash
cd /workspaces/design_of_experiments
python doe.py info --config use_cases/09_parallel_io_tuning/config.json
python doe.py generate --config use_cases/09_parallel_io_tuning/config.json \
    --output use_cases/09_parallel_io_tuning/results/run.sh --seed 42
bash use_cases/09_parallel_io_tuning/results/run.sh
python doe.py analyze --config use_cases/09_parallel_io_tuning/config.json
python doe.py report --config use_cases/09_parallel_io_tuning/config.json \
    --output use_cases/09_parallel_io_tuning/results/report.html
```

## Files

- Config: `use_cases/09_parallel_io_tuning/config.json`
- Simulator: `use_cases/09_parallel_io_tuning/sim.sh`
- Results: `use_cases/09_parallel_io_tuning/results/`
