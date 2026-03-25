#!/usr/bin/env bash
# Simulated: Backyard Composting Bin Design
set -euo pipefail

OUTFILE=""
VL=""
VH=""
IM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --volume_L) VL="$2"; shift 2 ;;
        --vent_holes) VH="$2"; shift 2 ;;
        --insulation_mm) IM="$2"; shift 2 ;;
        --material) shift 2 ;;
        --location) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$VL" ] || [ -z "$VH" ] || [ -z "$IM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v VL="$VL" -v VH="$VH" -v IM="$IM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    vl = (VL - 350) / 250;
    vh = (VH - 14) / 10;
    im = (IM - 25) / 25;
    decomp = 2.5 + 0.8*vl + 0.5*vh + 0.4*im - 0.3*vl*vl - 0.2*vh*vh + 0.2*vl*vh;
    odor = 4.5 - 0.3*vl + 1.2*vh - 0.5*im + 0.2*vh*vh + 0.3*vl*vh;
    if (decomp < 0.3) decomp = 0.3;
    if (odor < 1) odor = 1; if (odor > 10) odor = 10;
    printf "{\"decomp_rate\": %.2f, \"odor_score\": %.1f}", decomp + n1*0.2, odor + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
