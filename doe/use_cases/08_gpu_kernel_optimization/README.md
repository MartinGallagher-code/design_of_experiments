# Use Case 8: GPU Kernel Optimization

## Scenario

You are tuning a compute-intensive CUDA kernel on an NVIDIA A100 GPU. Four factors control the kernel launch configuration and code generation: block size, shared memory allocation, loop unroll factor, and floating-point precision. With only 4 two-level factors (16 runs), a full factorial design is affordable and gives complete information about all main effects and interactions.

**This use case demonstrates:**
- Full factorial design (2^4 = 16 runs, all interactions estimable)
- Trade-off between throughput (GFLOPS) and occupancy
- Mixing continuous and categorical factors (precision)
- GPU-specific performance modeling

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| block_size | 128 | 512 | continuous | threads | CUDA block size |
| shared_mem | 16 | 48 | continuous | KB | Shared memory per block |
| unroll_factor | 2 | 8 | continuous | | Loop unroll factor |
| precision | fp32 | fp64 | categorical | | Floating-point precision |

**Fixed:** gpu_model = A100, problem_size = 8192

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| gflops | maximize | GFLOPS |
| occupancy | maximize | % |

## Running the Demo

```bash
cd /workspaces/design_of_experiments
doe info --config use_cases/08_gpu_kernel_optimization/config.json
doe generate --config use_cases/08_gpu_kernel_optimization/config.json \
    --output use_cases/08_gpu_kernel_optimization/results/run.sh --seed 42
bash use_cases/08_gpu_kernel_optimization/results/run.sh
doe analyze --config use_cases/08_gpu_kernel_optimization/config.json
doe report --config use_cases/08_gpu_kernel_optimization/config.json \
    --output use_cases/08_gpu_kernel_optimization/results/report.html
```

## Files

- Config: `use_cases/08_gpu_kernel_optimization/config.json`
- Simulator: `use_cases/08_gpu_kernel_optimization/sim.sh`
- Results: `use_cases/08_gpu_kernel_optimization/results/`
