#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# ---------------------------------------------------------------------------
# Simulator: GPU Compute-Communication Overlap
#
# Models overlap efficiency (%) and step time (ms) for a distributed stencil
# application as a function of CUDA stream count, GPUDirect RDMA, halo
# chunking, and kernel fusion.
# ---------------------------------------------------------------------------
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────
OUT="result.json"
NUM_STREAMS=1
GDRDMA="off"
CHUNK_COUNT=1
KERNEL_FUSION="off"

# ── Parse arguments ───────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)           OUT="$2";           shift 2 ;;
        --num_streams)   NUM_STREAMS="$2";   shift 2 ;;
        --gdrdma)        GDRDMA="$2";        shift 2 ;;
        --chunk_count)   CHUNK_COUNT="$2";   shift 2 ;;
        --kernel_fusion) KERNEL_FUSION="$2"; shift 2 ;;
        --*) shift 2 ;;  # ignore unknown fixed-factor flags
        *) shift ;;
    esac
done

# ── Encode categorical flags as 0/1 ──────────────────────────────────────
GDR_FLAG=0; [[ "$GDRDMA"        == "on" ]] && GDR_FLAG=1
FUSE_FLAG=0; [[ "$KERNEL_FUSION" == "on" ]] && FUSE_FLAG=1

# ── Compute responses via awk ─────────────────────────────────────────────
read -r OVERLAP STEP_TIME <<< "$(awk -v s="$NUM_STREAMS" \
     -v g="$GDR_FLAG" \
     -v c="$CHUNK_COUNT" \
     -v f="$FUSE_FLAG" \
     -v seed="$RANDOM" '
BEGIN {
    # ── Seed simple PRNG ──────────────────────────────────────────────
    srand(seed)

    # ── Overlap efficiency model (%) ──────────────────────────────────
    #   base                        25 %
    #   streams  (diminishing)      +15 * (1 - 1/s)   [0 for s=1, ~11.25 for s=4]
    #   GDR on                      +12
    #   chunks   (diminishing)      +8  * (1 - 1/c)   [0 for c=1, ~7 for c=8]
    #   kernel fusion               +10
    #   interaction streams*chunks  +5  * (1 - 1/s) * (1 - 1/c)
    #   interaction gdr+streams     +4  * g * (1 - 1/s)
    ov = 25.0
    ov += 15.0 * (1.0 - 1.0 / s)
    ov += 12.0 * g
    ov += 8.0  * (1.0 - 1.0 / c)
    ov += 10.0 * f
    ov += 5.0  * (1.0 - 1.0 / s) * (1.0 - 1.0 / c)
    ov += 4.0  * g * (1.0 - 1.0 / s)

    # noise +/- ~1 %
    ov += (rand() - 0.5) * 2.0
    if (ov > 98.0) ov = 98.0
    if (ov <  0.0) ov =  0.0

    # ── Step time model (ms) ──────────────────────────────────────────
    #   base                        85 ms
    #   streams  (diminishing)      -12 * (1 - 1/s)
    #   GDR on                      -10
    #   chunks   (diminishing)      -8  * (1 - 1/c)
    #   kernel fusion               -7
    #   interaction streams*chunks  -4  * (1 - 1/s) * (1 - 1/c)
    #   interaction gdr+streams     -3  * g * (1 - 1/s)
    st = 85.0
    st -= 12.0 * (1.0 - 1.0 / s)
    st -= 10.0 * g
    st -= 8.0  * (1.0 - 1.0 / c)
    st -= 7.0  * f
    st -= 4.0  * (1.0 - 1.0 / s) * (1.0 - 1.0 / c)
    st -= 3.0  * g * (1.0 - 1.0 / s)

    # noise +/- ~0.5 ms
    st += (rand() - 0.5) * 1.0
    if (st < 20.0) st = 20.0

    printf "%.2f %.2f\n", ov, st
}')"

# ── Write result JSON ─────────────────────────────────────────────────────
mkdir -p "$(dirname "$OUT")"
cat > "$OUT" <<EOF
{
    "num_streams": "$NUM_STREAMS",
    "gdrdma": "$GDRDMA",
    "chunk_count": "$CHUNK_COUNT",
    "kernel_fusion": "$KERNEL_FUSION",
    "overlap_efficiency": $OVERLAP,
    "step_time_ms": $STEP_TIME
}
EOF

echo "Result written to $OUT"
echo "  overlap_efficiency = ${OVERLAP}%"
echo "  step_time_ms       = ${STEP_TIME} ms"
