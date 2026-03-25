#!/usr/bin/env bash
# Simulated CPU cross-NUMA bandwidth benchmark — produces bandwidth_GBs and latency_ns.
#
# Hidden model:
#   bandwidth_GBs ~ 45 GB/s base (local); near degrades to ~30 GB/s, far to ~18 GB/s.
#                   streaming_store adds ~8 GB/s (more on remote NUMA).
#                   14 threads scale BW ~6x vs single thread.
#                   Larger buffers slightly reduce BW due to cache eviction.
#   latency_ns    ~ 70ns base (local); near ~120ns, far ~190ns.
#                   streaming_store reduces latency by ~10ns.
#                   More threads increase contention (+15ns at 14 threads).
#                   Large buffers increase latency slightly.
#
# NOTE: run `chmod +x sim.sh` if needed.

set -euo pipefail

OUTFILE=""
NUMA_HOP=""
TRANSFER_MODE=""
THREAD_COUNT=""
BUFFER_SIZE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)                  OUTFILE="$2";        shift 2 ;;
        --numa_hop)             NUMA_HOP="$2";       shift 2 ;;
        --transfer_mode)        TRANSFER_MODE="$2";  shift 2 ;;
        --thread_count)         THREAD_COUNT="$2";   shift 2 ;;
        --buffer_size)          BUFFER_SIZE="$2";    shift 2 ;;
        --sockets)              shift 2 ;;
        --cores_per_socket)     shift 2 ;;
        --numa_distance_near)   shift 2 ;;
        --numa_distance_far)    shift 2 ;;
        *)                      shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$NUMA_HOP" || -z "$TRANSFER_MODE" || -z "$THREAD_COUNT" || -z "$BUFFER_SIZE" ]]; then
    echo "Usage: sim.sh --numa_hop V --transfer_mode V --thread_count V --buffer_size V --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v hop="$NUMA_HOP" -v mode="$TRANSFER_MODE" \
             -v threads="$THREAD_COUNT" -v bufsz="$BUFFER_SIZE" \
             -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise_bw  = (rand() - 0.5) * 4;
    noise_lat = (rand() - 0.5) * 6;

    # --- Bandwidth model (GB/s) ---
    # Base: single-thread local NUMA bandwidth
    bw = 45.0;

    # NUMA hop penalty
    if (hop == "near") bw = 30.0;
    if (hop == "far")  bw = 18.0;

    # Streaming stores bypass cache, improving throughput
    ss_bonus = 8.0;
    # Interaction: streaming_store helps more on remote NUMA
    if (hop == "near") ss_bonus = 11.0;
    if (hop == "far")  ss_bonus = 14.0;
    if (mode == "streaming_store") bw += ss_bonus;

    # Thread scaling: 14 threads give ~6x single-thread BW
    thread_scale = 1.0 + (threads - 1) * 5.0 / 13.0;
    bw = bw * thread_scale;

    # Large buffers exceed LLC, slight BW reduction
    buf_mb = bufsz / 1048576.0;
    if (buf_mb > 128) bw = bw * 0.94;

    bw += noise_bw;
    if (bw < 2) bw = 2;

    # --- Latency model (ns) ---
    lat = 70.0;
    if (hop == "near") lat = 120.0;
    if (hop == "far")  lat = 190.0;

    # Streaming stores reduce latency slightly (write-combine)
    if (mode == "streaming_store") lat -= 10.0;

    # Thread contention increases latency
    lat += (threads - 1) * 15.0 / 13.0;

    # Large buffers cause more TLB / prefetcher misses
    if (buf_mb > 128) lat += 8.0;

    lat += noise_lat;
    if (lat < 30) lat = 30;

    printf "{\"bandwidth_GBs\": %.1f, \"latency_ns\": %.1f}", bw, lat;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
