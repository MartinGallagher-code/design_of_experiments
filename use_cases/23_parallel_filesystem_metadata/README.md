# Parallel Filesystem Metadata Performance

## Scenario

An HPC center runs workloads that create, stat, and remove millions of small
files (e.g., ensemble simulations, checkpoint/restart, bioinformatics
pipelines). The parallel filesystem is **Lustre 2.15** serving 256 compute-node
clients. Metadata operations -- not bulk I/O -- are the bottleneck: a single
metadata server (MDS) saturates long before the data servers do.

This experiment tunes Lustre metadata-server performance using a **fractional
factorial 2^(5-1) design** (resolution V) with five factors:

| # | Factor | Low | High | Description |
|---|--------|-----|------|-------------|
| 1 | `mdt_count` | 1 | 4 | Number of metadata targets (DNE striping) |
| 2 | `dir_stripe` | off | on | Directory-level metadata striping (DNE2) |
| 3 | `client_cache` | off | on | Client-side metadata caching |
| 4 | `commit_on_share` | 0 | 1 | Commit-on-sharing for cross-client consistency |
| 5 | `mds_threads` | 64 | 512 | MDS service thread count |

The responses are measured with **mdtest**, the standard MPI metadata benchmark:

* **creates_per_sec** -- file creation rate (ops/s, maximize)
* **stat_per_sec** -- file stat rate (ops/s, maximize)

### Fixed conditions

* Lustre 2.15 filesystem
* 256 client nodes
* 100 000 files per directory
* 4 KB file size

## Demonstrates

* **Fractional factorial design (resolution V)** -- estimate all main effects
  and two-factor interactions with half the runs of a full factorial.
* **Metadata server tuning** -- quantify the throughput gain from adding
  metadata targets and increasing service threads.
* **Directory striping effects** -- measure how DNE2 directory striping
  distributes metadata load across multiple MDTs.
* **Client-side caching impact** -- evaluate the trade-off between caching
  (higher stat throughput) and consistency (commit-on-sharing overhead).

## Running

```bash
# Generate the fractional factorial design and execute the simulator
doe run --config use_cases/23_parallel_filesystem_metadata/config.json

# Analyse results
doe analyse --config use_cases/23_parallel_filesystem_metadata/config.json
```
