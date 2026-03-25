# GPU Compute-Communication Overlap

## Scenario

Maximizing overlap between GPU kernel execution and NCCL/MPI communication in
a multi-node distributed stencil application running on 64 H100 SXM GPUs
connected via NDR InfiniBand. The goal is to hide as much inter-node halo
exchange latency as possible behind useful computation, reducing the wall-clock
time per simulation step.

A **full factorial design with 4 factors** (each at 2 levels) is used, yielding
2^4 = 16 experimental runs. This captures all main effects and all interaction
effects among the factors.

## Factors

| Factor | Levels | Description |
|---|---|---|
| `num_streams` | 1, 4 | Number of CUDA streams for pipelining compute and communication |
| `gdrdma` | off, on | GPUDirect RDMA — allows the NIC to read/write GPU memory directly |
| `chunk_count` | 1, 8 | Number of halo-exchange chunks enabling finer-grained pipelining |
| `kernel_fusion` | off, on | Fuse interior-compute kernel with boundary-pack kernels |

## Fixed Conditions

- **GPUs:** 64 H100 SXM
- **Interconnect:** NDR InfiniBand (400 Gb/s per port)
- **Problem size:** 2048^3 grid

## Responses

| Response | Goal | Unit | Description |
|---|---|---|---|
| `overlap_efficiency` | Maximize | % | Percentage of communication time hidden behind computation |
| `step_time_ms` | Minimize | ms | Wall-clock time per simulation step |

## Demonstrates

- **Full factorial design** — systematic enumeration of all factor-level combinations
- **GPU kernel-communication pipelining** — using multiple CUDA streams and chunked transfers to overlap work
- **CUDA stream management** — effect of stream count on scheduling flexibility
- **GPUDirect RDMA impact** — quantifying the benefit of removing host-staging copies

## Running

```bash
doe run config.json
```
