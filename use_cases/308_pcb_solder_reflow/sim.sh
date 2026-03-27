#!/usr/bin/env bash
# Simulated: PCB Solder Reflow Profile (Fractional Factorial)
set -euo pipefail

OUTFILE=""
PT=""
ST=""
PK=""
TAL=""
CR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --preheat_temp) PT="$2"; shift 2 ;;
        --soak_time) ST="$2"; shift 2 ;;
        --peak_temp) PK="$2"; shift 2 ;;
        --time_above_liquidus) TAL="$2"; shift 2 ;;
        --cooling_rate) CR="$2"; shift 2 ;;
        --solder_paste) shift 2 ;;
        --board_layers) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PT" ] || [ -z "$ST" ] || [ -z "$PK" ] || [ -z "$TAL" ] || [ -z "$CR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PT="$PT" -v ST="$ST" -v PK="$PK" -v TAL="$TAL" -v CR="$CR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    # Normalize factors to [-1, 1]
    pt = (PT - 175) / 25;
    st = (ST - 90) / 30;
    pk = (PK - 245) / 15;
    tal = (TAL - 60) / 30;
    cr = (CR - 2.5) / 1.5;

    # Joint strength (N): higher peak temp and longer TAL help, but too much degrades
    js = 45 + 5*pk + 3*tal + 2*pt + 1.5*st - 2*cr - 1.5*pk*tal + 0.8*pt*st;
    js = js + n1 * 2.0;
    if (js < 10) js = 10;
    if (js > 80) js = 80;

    # Void percentage: worse with fast heating, better with longer soak and moderate peak
    vp = 8 - 2*st - 1.5*pk + 1.5*cr + 0.8*tal + 0.5*pt + 0.6*cr*pk - 0.4*st*tal;
    vp = vp + n2 * 0.8;
    if (vp < 0.5) vp = 0.5;
    if (vp > 25) vp = 25;

    printf "{\"joint_strength\": %.1f, \"void_percentage\": %.2f}", js, vp;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
