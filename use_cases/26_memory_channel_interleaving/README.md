# Memory Channel & Rank Interleaving

## Scenario

Tuning BIOS-level memory interleaving and sub-NUMA clustering (SNC) on a
2-socket server for memory-bandwidth-sensitive HPC workloads. The experiment
uses a **full factorial design with 4 factors** to systematically explore the
memory subsystem configuration space and identify the combination that
maximizes sustained memory bandwidth while keeping random-access latency
under control.

Modern server platforms expose several firmware-level knobs that control how
physical memory addresses are distributed across channels, ranks, and NUMA
domains. Mis-configuring these settings can leave 20-40 % of available
bandwidth on the table or introduce unnecessary latency penalties. This use
case applies a structured DOE approach to navigate the configuration space
efficiently.

## Factors

| Factor | Levels | Description |
|---|---|---|
| `snc_mode` | disabled, snc4 | Sub-NUMA Clustering mode (disabled or 4 clusters per socket) |
| `channel_interleave` | 1way, 8way | Memory channel interleaving granularity |
| `rank_interleave` | 1way, 4way | Memory rank interleaving |
| `dimms_per_channel` | 1, 2 | DIMMs populated per memory channel |

## Fixed Factors

- **Sockets:** 2 (Intel Xeon 8490H)
- **Channels per socket:** 8
- **DIMM type:** DDR5-4800

## Responses

| Response | Goal | Unit |
|---|---|---|
| `stream_triad_GBs` | Maximize | GB/s |
| `random_lat_ns` | Minimize | ns |

## Demonstrates

- **Full factorial design** -- enumerating every combination of 4 two-level factors (2^4 = 16 runs)
- **Memory subsystem tuning** -- quantifying the bandwidth and latency impact of firmware-level memory settings
- **SNC (Sub-NUMA Clustering) effects** -- measuring how sub-NUMA partitioning trades locality for capacity
- **Channel/rank interleaving optimization** -- finding the interleaving strategy that best balances throughput and latency

## Running

```bash
# Generate the full factorial design matrix
doe generate use_cases/26_memory_channel_interleaving/config.json

# Execute all 16 runs
doe run use_cases/26_memory_channel_interleaving/config.json

# Analyse results
doe analyse use_cases/26_memory_channel_interleaving/config.json
```
