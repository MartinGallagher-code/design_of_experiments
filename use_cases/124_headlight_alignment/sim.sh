#!/usr/bin/env bash
# Simulated: Headlight Beam Alignment
set -euo pipefail

OUTFILE=""
VD=""
HD=""
BW=""
LC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --vertical_deg) VD="$2"; shift 2 ;;
        --horizontal_deg) HD="$2"; shift 2 ;;
        --bulb_watts) BW="$2"; shift 2 ;;
        --lens_clarity) LC="$2"; shift 2 ;;
        --headlight_type) shift 2 ;;
        --beam) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$VD" ] || [ -z "$HD" ] || [ -z "$BW" ] || [ -z "$LC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v VD="$VD" -v HD="$HD" -v BW="$BW" -v LC="$LC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    vd = (VD - 0) / 2;
    hd = (HD - 0) / 1;
    bw = (BW - 50) / 15;
    lc = (LC - 75) / 25;
    illum = 120 - 20*vd + 5*hd + 30*bw + 25*lc + 5*bw*lc;
    glare = 5 + 2.5*vd + 0.5*hd + 1.2*bw + 0.8*lc + 0.5*vd*bw;
    if (illum < 20) illum = 20;
    if (glare < 1) glare = 1; if (glare > 10) glare = 10;
    printf "{\"illumination_lux\": %.0f, \"glare_score\": %.1f}", illum + n1*8, glare + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
