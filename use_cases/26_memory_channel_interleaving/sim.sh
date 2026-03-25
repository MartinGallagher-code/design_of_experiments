#!/usr/bin/env bash
# sim.sh -- Simulator for Memory Channel & Rank Interleaving DOE
# Models STREAM Triad bandwidth (GB/s) and random-access latency (ns)
# as functions of SNC mode, channel/rank interleaving, and DIMM population.

set -euo pipefail

# ── Parse arguments ──────────────────────────────────────────────────────────
OUT=""
SNC_MODE="disabled"
CHANNEL_INTERLEAVE="1way"
RANK_INTERLEAVE="1way"
DIMMS_PER_CHANNEL="1"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)                OUT="$2";                shift 2 ;;
        --snc_mode)           SNC_MODE="$2";           shift 2 ;;
        --channel_interleave) CHANNEL_INTERLEAVE="$2"; shift 2 ;;
        --rank_interleave)    RANK_INTERLEAVE="$2";    shift 2 ;;
        --dimms_per_channel)  DIMMS_PER_CHANNEL="$2";  shift 2 ;;
        --*) shift 2 ;;  # ignore unknown fixed-factor flags
        *) shift ;;
    esac
done

if [[ -z "$OUT" ]]; then
    echo "Error: --out is required" >&2
    exit 1
fi

# ── Deterministic seed from inputs ───────────────────────────────────────────
SEED_STR="${SNC_MODE}_${CHANNEL_INTERLEAVE}_${RANK_INTERLEAVE}_${DIMMS_PER_CHANNEL}"
HASH=$(echo -n "$SEED_STR" | md5sum | cut -c1-8)
SEED=$(( 16#$HASH % 100000 ))

# ── Helper: pseudo-random noise in [-scale, +scale] ─────────────────────────
noise() {
    local scale="$1"
    SEED=$(( (SEED * 1103515245 + 12345) & 0x7fffffff ))
    local raw=$(( SEED % 2001 - 1000 ))   # -1000..1000
    awk "BEGIN {printf \"%.4f\", ${raw}/1000.0 * ${scale}}"
}

# ── STREAM Triad bandwidth model (GB/s) ─────────────────────────────────────
stream_base=300.0

# SNC4: better locality -> +45 GB/s
snc_bw=0.0
[[ "$SNC_MODE" == "snc4" ]] && snc_bw=45.0

# 8-way channel interleave: +35 GB/s
ch_bw=0.0
[[ "$CHANNEL_INTERLEAVE" == "8way" ]] && ch_bw=35.0

# 4-way rank interleave: +20 GB/s
rk_bw=0.0
[[ "$RANK_INTERLEAVE" == "4way" ]] && rk_bw=20.0

# 2 DIMMs per channel: +60 GB/s (double the banks)
dimm_bw=0.0
[[ "$DIMMS_PER_CHANNEL" == "2" ]] && dimm_bw=60.0

# Interaction: snc4 + 8-way channel -> +15 GB/s synergy
interact_bw=0.0
if [[ "$SNC_MODE" == "snc4" && "$CHANNEL_INTERLEAVE" == "8way" ]]; then
    interact_bw=15.0
fi

n1=$(noise 3.0)
stream_triad=$(awk "BEGIN {printf \"%.2f\", \
    ${stream_base} + ${snc_bw} + ${ch_bw} + ${rk_bw} + ${dimm_bw} + ${interact_bw} + ${n1}}")

# ── Random-access latency model (ns) ────────────────────────────────────────
lat_base=85.0

# SNC4: shorter path -> -12 ns
snc_lat=0.0
[[ "$SNC_MODE" == "snc4" ]] && snc_lat=-12.0

# 8-way channel interleave: more hops -> +5 ns
ch_lat=0.0
[[ "$CHANNEL_INTERLEAVE" == "8way" ]] && ch_lat=5.0

# 4-way rank interleave: +3 ns
rk_lat=0.0
[[ "$RANK_INTERLEAVE" == "4way" ]] && rk_lat=3.0

# 2 DIMMs per channel: electrical load -> +8 ns
dimm_lat=0.0
[[ "$DIMMS_PER_CHANNEL" == "2" ]] && dimm_lat=8.0

# Interaction: snc4 offsets interleave penalty -> -4 ns
interact_lat=0.0
if [[ "$SNC_MODE" == "snc4" && "$CHANNEL_INTERLEAVE" == "8way" ]]; then
    interact_lat=-4.0
fi

n2=$(noise 1.5)
random_lat=$(awk "BEGIN {printf \"%.2f\", \
    ${lat_base} + ${snc_lat} + ${ch_lat} + ${rk_lat} + ${dimm_lat} + ${interact_lat} + ${n2}}")

# ── Write results ────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$OUT")"
cat > "$OUT" <<EOF
{
    "stream_triad_GBs": ${stream_triad},
    "random_lat_ns": ${random_lat}
}
EOF

echo "Run complete: stream_triad=${stream_triad} GB/s  random_lat=${random_lat} ns -> ${OUT}"
