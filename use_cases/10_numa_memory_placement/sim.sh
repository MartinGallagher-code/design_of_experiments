#!/usr/bin/env bash
# Simulated NUMA memory benchmark — produces stream_triad and latency_ns.
#
# Hidden model:
#   stream_triad ~ 200 GB/s base; interleave+spread maximizes BW across sockets;
#                  hugepages reduce TLB misses, improving throughput.
#   latency_ns   ~ 80ns base; local policy reduces it; close binding reduces it;
#                  hugepages slightly reduce latency via TLB.

set -euo pipefail

OUTFILE=""
MEM_POLICY=""
THREAD_BIND=""
HUGEPAGES=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)              OUTFILE="$2";      shift 2 ;;
        --mem_policy)       MEM_POLICY="$2";   shift 2 ;;
        --thread_bind)      THREAD_BIND="$2";  shift 2 ;;
        --hugepages)        HUGEPAGES="$2";    shift 2 ;;
        --sockets)          shift 2 ;;
        --cores_per_socket) shift 2 ;;
        *)                  shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$MEM_POLICY" || -z "$THREAD_BIND" || -z "$HUGEPAGES" ]]; then
    echo "Usage: sim.sh --mem_policy V --thread_bind V --hugepages V --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v mp="$MEM_POLICY" -v tb="$THREAD_BIND" -v hp="$HUGEPAGES" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise1 = (rand() - 0.5) * 8;
    noise2 = (rand() - 0.5) * 5;

    # STREAM Triad model (GB/s)
    st = 200.0;
    # Interleave distributes bandwidth across both sockets
    if (mp == "interleave") st += 35;
    # Spread binding uses both sockets memory controllers
    if (tb == "spread") st += 28;
    # Hugepages reduce TLB pressure for large working sets
    if (hp == "2M") st += 18;
    # Interaction: interleave + spread is synergistic
    if (mp == "interleave" && tb == "spread") st += 12;
    st += noise1;
    if (st < 50) st = 50;

    # Latency model (ns)
    lat = 80.0;
    # Local policy keeps data on the nearest NUMA node
    if (mp == "local") lat -= 18;
    # Close binding keeps threads near their data
    if (tb == "close") lat -= 14;
    # Hugepages reduce TLB miss penalty
    if (hp == "2M") lat -= 8;
    # Interaction: local + close is best for latency
    if (mp == "local" && tb == "close") lat -= 6;
    lat += noise2;
    if (lat < 20) lat = 20;

    printf "{\"stream_triad\": %.1f, \"latency_ns\": %.1f}", st, lat;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
