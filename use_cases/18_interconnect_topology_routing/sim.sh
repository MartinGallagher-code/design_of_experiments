#!/usr/bin/env bash
# Simulated dragonfly network routing benchmark — produces msg_latency_us and throughput_GBs.
#
# Hidden model:
#   latency ~ 5us base, adaptive routing -1.2us, more VCs -0.8us,
#             alltoall +2.5us, higher link BW -0.6us,
#             scatter +1.8us for alltoall / -0.5us for nearest_neighbor,
#             interaction: adaptive + alltoall -1.5us
#   throughput ~ 800 GB/s base, adaptive +120, more VCs +80,
#               alltoall -200, higher BW +150, compact +60 for nearest_neighbor,
#               interaction: adaptive + more VCs +50

set -euo pipefail

OUTFILE=""
ROUTING_MODE=""
VC_COUNT=""
TRAFFIC_PATTERN=""
LINK_BANDWIDTH=""
JOB_PLACEMENT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)              OUTFILE="$2";          shift 2 ;;
        --routing_mode)     ROUTING_MODE="$2";     shift 2 ;;
        --vc_count)         VC_COUNT="$2";         shift 2 ;;
        --traffic_pattern)  TRAFFIC_PATTERN="$2";  shift 2 ;;
        --link_bandwidth)   LINK_BANDWIDTH="$2";   shift 2 ;;
        --job_placement)    JOB_PLACEMENT="$2";    shift 2 ;;
        --topology)         shift 2 ;;
        --groups)           shift 2 ;;
        --switches_per_group) shift 2 ;;
        --nodes)            shift 2 ;;
        *)                  shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$ROUTING_MODE" || -z "$VC_COUNT" || -z "$TRAFFIC_PATTERN" || -z "$LINK_BANDWIDTH" || -z "$JOB_PLACEMENT" ]]; then
    echo "Usage: sim.sh --routing_mode V --vc_count V --traffic_pattern V --link_bandwidth V --job_placement V --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v route="$ROUTING_MODE" -v vc="$VC_COUNT" -v traffic="$TRAFFIC_PATTERN" \
             -v bw="$LINK_BANDWIDTH" -v place="$JOB_PLACEMENT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise_lat = (rand() - 0.5) * 0.6;
    noise_thr = (rand() - 0.5) * 40;

    # --- Latency model (us) ---
    lat = 5.0;

    # Adaptive routing reduces latency
    if (route == "adaptive") lat -= 1.2;

    # More virtual channels reduce head-of-line blocking
    lat -= (vc - 2) / 6.0 * 0.8;

    # Alltoall generates more congestion
    if (traffic == "alltoall") lat += 2.5;

    # Higher link bandwidth reduces serialization delay
    lat -= (bw - 100) / 100.0 * 0.6;

    # Placement effect depends on traffic pattern
    if (place == "scatter" && traffic == "alltoall")        lat += 1.8;
    if (place == "scatter" && traffic == "nearest_neighbor") lat -= 0.5;

    # Interaction: adaptive routing helps alltoall significantly
    if (route == "adaptive" && traffic == "alltoall") lat -= 1.5;

    lat += noise_lat;
    if (lat < 1.0) lat = 1.0;

    # --- Throughput model (GB/s) ---
    thr = 800.0;

    # Adaptive routing improves load balance
    if (route == "adaptive") thr += 120;

    # More VCs improve throughput
    thr += (vc - 2) / 6.0 * 80;

    # Alltoall saturates links
    if (traffic == "alltoall") thr -= 200;

    # Higher bandwidth directly boosts throughput
    thr += (bw - 100) / 100.0 * 150;

    # Compact placement helps nearest_neighbor locality
    if (place == "compact" && traffic == "nearest_neighbor") thr += 60;

    # Interaction: adaptive + more VCs synergy
    if (route == "adaptive") thr += (vc - 2) / 6.0 * 50;

    thr += noise_thr;
    if (thr < 50) thr = 50;

    printf "{\"msg_latency_us\": %.2f, \"throughput_GBs\": %.2f}", lat, thr;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
