# Use Case 24: GPU Compute-Communication Overlap

## Scenario

You are maximizing overlap between GPU kernel execution and inter-node halo exchange communication in a distributed stencil application running on 64 H100 SXM GPUs connected via NDR InfiniBand. Increasing CUDA streams and chunked transfers enables finer-grained pipelining but adds scheduling complexity, while GPUDirect RDMA and kernel fusion each reduce latency through different mechanisms whose combined effects are not obvious. A full factorial design with four two-level factors captures all main effects and interaction effects in 16 runs.

**This use case demonstrates:**
- Full factorial design for systematic enumeration of all factor-level combinations
- GPU kernel-communication pipelining via CUDA streams and chunked transfers
- GPUDirect RDMA impact on removing host-staging copies
- Trade-off between overlap efficiency and per-step wall-clock time

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
