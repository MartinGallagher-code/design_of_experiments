#!/usr/bin/env bash
# Simulated: Rain Garden Design
set -euo pipefail

OUTFILE=""
AR=""
SD=""
BH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --area_m2) AR="$2"; shift 2 ;;
        --soil_depth_cm) SD="$2"; shift 2 ;;
        --berm_height_cm) BH="$2"; shift 2 ;;
        --drainage_area_m2) shift 2 ;;
        --soil_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AR" ] || [ -z "$SD" ] || [ -z "$BH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AR="$AR" -v SD="$SD" -v BH="$BH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ar = (AR - 12.5) / 7.5;
    sd = (SD - 60) / 30;
    bh = (BH - 20) / 10;
    infil = 70 + 10*ar + 8*sd + 5*bh - 3*ar*ar - 2*sd*sd + 2*ar*sd + 1.5*ar*bh;
    pond = 18 - 4*ar - 3*sd + 2*bh + 1.5*ar*ar + 1*sd*sd - 0.5*ar*sd;
    if (infil < 20) infil = 20; if (infil > 100) infil = 100;
    if (pond < 1) pond = 1;
    printf "{\"infiltration_pct\": %.0f, \"ponding_hrs\": %.1f}", infil + n1*3, pond + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
