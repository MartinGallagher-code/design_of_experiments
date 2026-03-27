#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated InfiniBand network benchmark — produces msg_rate and p99_lat.
#
# Hidden model:
#   msg_rate ~ 100 Mmsg/s base, increased by larger queue_depth (more pipelining),
#              larger MTU (fewer packets), rdma_cm=on (better connection setup)
#   p99_lat  ~ 2.0us base, reduced by rdma_cm=on and larger MTU,
#              slightly increased by very deep queues (head-of-line blocking)

set -euo pipefail

OUTFILE=""
MTU=""
QUEUE_DEPTH=""
RDMA_CM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)          OUTFILE="$2";      shift 2 ;;
        --mtu)          MTU="$2";          shift 2 ;;
        --queue_depth)  QUEUE_DEPTH="$2";  shift 2 ;;
        --rdma_cm)      RDMA_CM="$2";      shift 2 ;;
        --ib_speed)     shift 2 ;;
        --ports)        shift 2 ;;
        *)              shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$MTU" || -z "$QUEUE_DEPTH" || -z "$RDMA_CM" ]]; then
    echo "Usage: sim.sh --mtu V --queue_depth V --rdma_cm V --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v mtu="$MTU" -v qd="$QUEUE_DEPTH" -v rdma="$RDMA_CM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise1 = (rand() - 0.5) * 8;
    noise2 = (rand() - 0.5) * 0.25;

    # Message rate model (Mmsg/s)
    mr = 100.0;
    # Deeper queues allow more pipelining
    mr += (qd - 64) / 448.0 * 40;
    # Larger MTU means fewer messages needed, but also higher per-msg rate
    mr += (mtu - 2048) / 2048.0 * 18;
    # RDMA CM provides optimized connection paths
    if (rdma == "on") mr += 15;
    # Interaction: deep queues + large MTU
    mr += (qd - 64) / 448.0 * (mtu - 2048) / 2048.0 * 10;
    # Quadratic: diminishing returns on queue depth
    mr -= ((qd - 288) / 224.0) * ((qd - 288) / 224.0) * 5;
    mr += noise1;
    if (mr < 20) mr = 20;

    # P99 latency model (us)
    lat = 2.0;
    # RDMA CM reduces connection overhead
    if (rdma == "on") lat -= 0.35;
    # Larger MTU reduces per-byte overhead
    lat -= (mtu - 2048) / 2048.0 * 0.25;
    # Very deep queues can cause head-of-line blocking
    lat += (qd - 64) / 448.0 * 0.4;
    # Quadratic effect on queue depth
    lat += ((qd - 288) / 224.0) * ((qd - 288) / 224.0) * 0.15;
    lat += noise2;
    if (lat < 0.5) lat = 0.5;

    printf "{\"msg_rate\": %.1f, \"p99_lat\": %.3f}", mr, lat;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
