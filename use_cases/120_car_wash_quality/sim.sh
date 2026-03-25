#!/usr/bin/env bash
# Simulated: Car Wash Quality Optimization
set -euo pipefail

OUTFILE=""
WP=""
SD=""
RS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --water_pressure) WP="$2"; shift 2 ;;
        --soap_dilution) SD="$2"; shift 2 ;;
        --rinse_sec) RS="$2"; shift 2 ;;
        --wash_type) shift 2 ;;
        --water_temp) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WP" ] || [ -z "$SD" ] || [ -z "$RS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WP="$WP" -v SD="$SD" -v RS="$RS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wp = (WP - 1400) / 600;
    sd = (SD - 5.5) / 4.5;
    rs = (RS - 75) / 45;
    clean = 6.5 + 1.5*wp - 1.0*sd + 0.5*rs - 0.6*wp*wp + 0.3*sd*sd + 0.4*wp*sd;
    water = 80 + 20*wp - 5*sd + 15*rs + 5*wp*rs;
    if (clean < 1) clean = 1; if (clean > 10) clean = 10;
    if (water < 20) water = 20;
    printf "{\"clean_score\": %.1f, \"water_liters\": %.0f}", clean + n1*0.3, water + n2*5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
