#!/usr/bin/env bash
# Simulated: LED Grow Light Spectrum
set -euo pipefail

OUTFILE=""
RB=""
PP=""
PH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --red_blue_ratio) RB="$2"; shift 2 ;;
        --ppfd) PP="$2"; shift 2 ;;
        --photoperiod_hrs) PH="$2"; shift 2 ;;
        --plant_type) shift 2 ;;
        --distance_cm) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$RB" ] || [ -z "$PP" ] || [ -z "$PH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v RB="$RB" -v PP="$PP" -v PH="$PH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rb = (RB - 4.5) / 3.5;
    pp = (PP - 500) / 300;
    ph = (PH - 16) / 4;
    growth = 5.0 + 0.8*rb + 2.0*pp + 1.0*ph - 0.5*rb*rb - 0.6*pp*pp - 0.3*ph*ph + 0.3*rb*pp;
    heat = 50 + 5*rb + 25*pp + 8*ph + 3*pp*pp + 2*rb*pp;
    if (growth < 0.5) growth = 0.5;
    if (heat < 15) heat = 15;
    printf "{\"growth_rate_g\": %.1f, \"heat_watts\": %.0f}", growth + n1*0.3, heat + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
