#!/usr/bin/env bash
# Simulated: Dovetail Joint Aesthetics
set -euo pipefail

OUTFILE=""
TA=""
PT=""
BL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tail_angle_deg) TA="$2"; shift 2 ;;
        --pin_tail_ratio) PT="$2"; shift 2 ;;
        --baseline_mm) BL="$2"; shift 2 ;;
        --wood) shift 2 ;;
        --board_thickness) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TA" ] || [ -z "$PT" ] || [ -z "$BL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TA="$TA" -v PT="$PT" -v BL="$BL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ta = (TA - 10.5) / 3.5; pt = (PT - 0.55) / 0.25; bl = (BL - 1.25) / 0.75;
    vis = 6.5 + 0.5*ta + 0.8*pt + 0.3*bl - 0.5*ta*ta - 0.4*pt*pt + 0.2*ta*pt;
    tight = 7.0 - 0.3*ta - 0.2*pt + 0.5*bl - 0.3*ta*ta + 0.2*pt*pt - 0.3*bl*bl + 0.2*ta*bl;
    if (vis < 1) vis = 1; if (vis > 10) vis = 10;
    if (tight < 1) tight = 1; if (tight > 10) tight = 10;
    printf "{\"visual_appeal\": %.1f, \"tightness\": %.1f}", vis + n1*0.3, tight + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
