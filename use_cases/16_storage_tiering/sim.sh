#!/bin/bash
# Burst Buffer / Storage Tiering Simulator
# Simulates I/O throughput and stage-in time for various storage tiering configurations.
# Usage: bash sim.sh --burst_buffer on --stage_in async --cache_size 256 \
#                    --write_policy write_back --prefetch on --out results.json

# Defaults
burst_buffer="off"
stage_in="sync"
cache_size=128
write_policy="write_through"
prefetch="off"
out="result.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --burst_buffer) burst_buffer="$2"; shift 2 ;;
    --stage_in) stage_in="$2"; shift 2 ;;
    --cache_size) cache_size="$2"; shift 2 ;;
    --write_policy) write_policy="$2"; shift 2 ;;
    --prefetch) prefetch="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Compute io_throughput and stage_time
read io_throughput stage_time <<< $(awk \
  -v bb="$burst_buffer" -v si="$stage_in" -v cs="$cache_size" \
  -v wp="$write_policy" -v pf="$prefetch" '
BEGIN {
  srand(systime());
  noise_io = (rand() - 0.5) * 2.0;
  noise_st = (rand() - 0.5) * 8.0;

  # Base I/O throughput: ~20 GB/s (GPFS baseline)
  io = 20.0;

  # Burst buffer doubles throughput (NVMe tier)
  if (bb == "on") io = io * 2.0;

  # Async stage-in boosts throughput by ~30% (overlap)
  if (si == "async") io = io * 1.30;

  # Write-back boosts throughput by ~25% (deferred writes)
  if (wp == "write_back") io = io * 1.25;

  # Larger cache helps throughput (log scaling)
  cache_factor = 1 + 0.15 * log(cs / 64) / log(8);
  io = io * cache_factor;

  # Prefetch adds ~10% throughput
  if (pf == "on") io = io * 1.10;

  io = io + noise_io;
  if (io < 10) io = 10;

  # Base stage time: ~120 seconds
  st = 120.0;

  # Async halves stage time
  if (si == "async") st = st * 0.50;

  # Prefetch reduces stage time by ~30%
  if (pf == "on") st = st * 0.70;

  # Burst buffer reduces stage time by ~25%
  if (bb == "on") st = st * 0.75;

  # Larger cache reduces stage time slightly
  cache_st = 1 - 0.08 * log(cs / 64) / log(8);
  st = st * cache_st;

  # Write-back has small effect on stage-in (~5% faster)
  if (wp == "write_back") st = st * 0.95;

  st = st + noise_st;
  if (st < 10) st = 10;

  printf "%.2f %.1f\n", io, st;
}')

# Write JSON output
cat > "$out" <<EOF
{
  "io_throughput": ${io_throughput},
  "stage_time": ${stage_time},
  "parameters": {
    "burst_buffer": "${burst_buffer}",
    "stage_in": "${stage_in}",
    "cache_size": ${cache_size},
    "write_policy": "${write_policy}",
    "prefetch": "${prefetch}",
    "pfs": "gpfs",
    "job_count": 100
  }
}
EOF

echo "Results written to $out"
