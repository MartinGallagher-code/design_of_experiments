#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# --------------------------------------------------------------------------
# sim.sh  --  Prefetch-strategy simulator for Use Case 22
#
# Simulates solver_time_sec and cache_miss_rate for a memory-bound CFD
# workload under various hardware/software prefetch configurations.
# --------------------------------------------------------------------------
set -euo pipefail

# ---- defaults ------------------------------------------------------------
OUT="result.json"
HW_PREFETCHER="off"
SW_PREFETCH_DIST="64"
L2_STREAM_DETECT="off"
DCACHE_POLICY="write_back"
PREFETCH_THREADS="0"
TLB_PREFETCH="off"

# ---- parse arguments (double-dash style) ---------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)               OUT="$2";               shift 2 ;;
        --hw_prefetcher)     HW_PREFETCHER="$2";     shift 2 ;;
        --sw_prefetch_dist)  SW_PREFETCH_DIST="$2";  shift 2 ;;
        --l2_stream_detect)  L2_STREAM_DETECT="$2";  shift 2 ;;
        --dcache_policy)     DCACHE_POLICY="$2";     shift 2 ;;
        --prefetch_threads)  PREFETCH_THREADS="$2";  shift 2 ;;
        --tlb_prefetch)      TLB_PREFETCH="$2";      shift 2 ;;
        # silently skip fixed factors the runner may pass
        --processor|--workload|--grid_points|--iterations)
            shift 2 ;;
        *)
            echo "Warning: unknown argument '$1'" >&2
            shift ;;
    esac
done

# ---- helper: seeded pseudo-random noise via awk --------------------------
noise() {
    # Returns a small Gaussian-ish noise value scaled by $1.
    awk -v scale="$1" -v seed="$RANDOM" '
    BEGIN {
        srand(seed)
        u1 = rand(); u2 = rand()
        if (u1 < 1e-10) u1 = 1e-10
        z = sqrt(-2 * log(u1)) * cos(6.2831853 * u2)
        printf "%.6f", z * scale
    }'
}

# ---- compute solver_time_sec ---------------------------------------------
time_base=120.0

time_hw=0.0
[[ "$HW_PREFETCHER" == "on" ]] && time_hw=-18.0

# sw_prefetch_dist: linear interpolation  64 -> 0,  512 -> -12
time_sw=$(awk -v d="$SW_PREFETCH_DIST" 'BEGIN { printf "%.4f", -12.0 * (d - 64) / (512 - 64) }')

time_stream=0.0
[[ "$L2_STREAM_DETECT" == "on" ]] && time_stream=-10.0

time_dcache=0.0
[[ "$DCACHE_POLICY" == "write_back" ]] && time_dcache=-5.0

# prefetch_threads: -8 per thread (0 or 2)
time_pthreads=$(awk -v t="$PREFETCH_THREADS" 'BEGIN { printf "%.4f", -8.0 * t }')

time_tlb=0.0
[[ "$TLB_PREFETCH" == "on" ]] && time_tlb=-6.0

# interaction: hw_prefetcher ON + l2_stream_detect ON -> extra -7
time_interact=0.0
if [[ "$HW_PREFETCHER" == "on" && "$L2_STREAM_DETECT" == "on" ]]; then
    time_interact=-7.0
fi

time_noise=$(noise 1.8)

solver_time=$(awk -v base="$time_base" \
    -v hw="$time_hw" -v sw="$time_sw" -v st="$time_stream" \
    -v dc="$time_dcache" -v pt="$time_pthreads" -v tlb="$time_tlb" \
    -v ix="$time_interact" -v n="$time_noise" \
    'BEGIN {
        val = base + hw + sw + st + dc + pt + tlb + ix + n
        if (val < 30) val = 30
        printf "%.2f", val
    }')

# ---- compute cache_miss_rate ---------------------------------------------
miss_base=12.0

miss_hw=0.0
[[ "$HW_PREFETCHER" == "on" ]] && miss_hw=-3.0

# sw_prefetch_dist: linear  64 -> 0,  512 -> -2
miss_sw=$(awk -v d="$SW_PREFETCH_DIST" 'BEGIN { printf "%.4f", -2.0 * (d - 64) / (512 - 64) }')

miss_stream=0.0
[[ "$L2_STREAM_DETECT" == "on" ]] && miss_stream=-2.5

miss_tlb=0.0
[[ "$TLB_PREFETCH" == "on" ]] && miss_tlb=-1.0

# interaction: hw + stream -> extra -1.5
miss_interact=0.0
if [[ "$HW_PREFETCHER" == "on" && "$L2_STREAM_DETECT" == "on" ]]; then
    miss_interact=-1.5
fi

miss_noise=$(noise 0.4)

cache_miss=$(awk -v base="$miss_base" \
    -v hw="$miss_hw" -v sw="$miss_sw" -v st="$miss_stream" \
    -v tlb="$miss_tlb" -v ix="$miss_interact" -v n="$miss_noise" \
    'BEGIN {
        val = base + hw + sw + st + tlb + ix + n
        if (val < 0.5) val = 0.5
        printf "%.2f", val
    }')

# ---- write output --------------------------------------------------------
mkdir -p "$(dirname "$OUT")"

cat > "$OUT" <<ENDJSON
{
    "solver_time_sec": ${solver_time},
    "cache_miss_rate": ${cache_miss}
}
ENDJSON

echo "Wrote results to ${OUT}"
echo "  solver_time_sec = ${solver_time} s"
echo "  cache_miss_rate = ${cache_miss} %"
