#!/usr/bin/env bash
# =============================================================================
# REAL NUMA Benchmark Harness for AMD EPYC Dual-Socket Systems
# =============================================================================
#
# This is the REAL test script you'd use on actual hardware (replace sim.sh).
# It allocates memory on a source NUMA node, pins threads to a destination
# node, performs the transfer, and reports bandwidth + latency as JSON.
#
# Prerequisites:
#   - numactl, gcc (for the C harness), perf (optional)
#   - Root or CAP_SYS_NICE for hugepage allocation
#   - Build the C harness first:  gcc -O2 -march=native -o numa_xfer numa_xfer.c -lnuma -lpthread
#
# Usage (called by doe-helper generated runner):
#   ./numa_bench.sh --numa_distance local --transfer_mode memcpy \
#                   --thread_count 24 --buffer_size_mb 512 \
#                   --hugepages 2M --numa_balancing off \
#                   --mem_policy local --out results/run_1.json
# =============================================================================

set -euo pipefail

# --- Parse arguments ---
OUTFILE=""
NUMA_DISTANCE="local"
TRANSFER_MODE="memcpy"
THREAD_COUNT="1"
BUFFER_SIZE_MB="1"
HUGEPAGES="off"
NUMA_BALANCING="off"
MEM_POLICY="local"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)              OUTFILE="$2";          shift 2 ;;
        --numa_distance)    NUMA_DISTANCE="$2";    shift 2 ;;
        --transfer_mode)    TRANSFER_MODE="$2";    shift 2 ;;
        --thread_count)     THREAD_COUNT="$2";     shift 2 ;;
        --buffer_size_mb)   BUFFER_SIZE_MB="$2";   shift 2 ;;
        --hugepages)        HUGEPAGES="$2";        shift 2 ;;
        --numa_balancing)   NUMA_BALANCING="$2";   shift 2 ;;
        --mem_policy)       MEM_POLICY="$2";       shift 2 ;;
        # Absorb fixed factors
        --sockets|--cores_per_socket|--cpu_governor|--turbo_boost|--smt|--nps_setting)
                            shift 2 ;;
        *)                  shift ;;
    esac
done

if [[ -z "$OUTFILE" ]]; then
    echo "ERROR: --out <path> is required" >&2
    exit 1
fi

# --- Determine NUMA nodes ---
# Dual-socket NPS1: node 0 = socket 0, node 1 = socket 1
SRC_NODE=0
if [[ "$NUMA_DISTANCE" == "remote" ]]; then
    DST_NODE=1
else
    DST_NODE=0
fi

# --- Configure NUMA balancing ---
if [[ "$NUMA_BALANCING" == "off" ]]; then
    echo 0 | sudo tee /proc/sys/kernel/numa_balancing > /dev/null 2>&1 || true
else
    echo 1 | sudo tee /proc/sys/kernel/numa_balancing > /dev/null 2>&1 || true
fi

# --- Configure hugepages ---
HUGE_FLAG=""
if [[ "$HUGEPAGES" == "2M" ]]; then
    PAGES_NEEDED=$(( (BUFFER_SIZE_MB + 1) ))
    echo "$PAGES_NEEDED" | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages > /dev/null 2>&1 || true
    HUGE_FLAG="--hugepages"
fi

# --- Build numactl command ---
MEMBIND_FLAG=""
if [[ "$MEM_POLICY" == "interleave" ]]; then
    MEMBIND_FLAG="--interleave=all"
else
    MEMBIND_FLAG="--membind=$SRC_NODE"
fi

BUFFER_BYTES=$(( BUFFER_SIZE_MB * 1048576 ))

# --- Warmup: 3 untimed iterations ---
echo "Warmup (3 iterations)..."
for i in 1 2 3; do
    numactl --cpunodebind="$DST_NODE" $MEMBIND_FLAG \
        ./numa_xfer \
            --mode "$TRANSFER_MODE" \
            --threads "$THREAD_COUNT" \
            --bytes "$BUFFER_BYTES" \
            --iterations 1 \
            $HUGE_FLAG \
            --quiet 2>/dev/null || true
done

# --- Timed run: 10 iterations, report median ---
echo "Benchmark (10 iterations)..."
RAW_OUTPUT=$(numactl --cpunodebind="$DST_NODE" $MEMBIND_FLAG \
    ./numa_xfer \
        --mode "$TRANSFER_MODE" \
        --threads "$THREAD_COUNT" \
        --bytes "$BUFFER_BYTES" \
        --iterations 10 \
        $HUGE_FLAG \
        --json)

# numa_xfer outputs: {"bandwidth_GBs": X.X, "latency_ns": Y.Y}
mkdir -p "$(dirname "$OUTFILE")"
echo "$RAW_OUTPUT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
