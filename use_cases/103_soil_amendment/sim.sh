#!/usr/bin/env bash
# Simulated: Soil Amendment Blend
set -euo pipefail

OUTFILE=""
LM=""
OM=""
GY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --lime_kg_ha) LM="$2"; shift 2 ;;
        --organic_matter_pct) OM="$2"; shift 2 ;;
        --gypsum_kg_ha) GY="$2"; shift 2 ;;
        --soil_type) shift 2 ;;
        --initial_ph) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$LM" ] || [ -z "$OM" ] || [ -z "$GY" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v LM="$LM" -v OM="$OM" -v GY="$GY" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    lm = (LM - 1750) / 1250;
    om = (OM - 5) / 3;
    gy = (GY - 1000) / 1000;
    ph = 6.0 + 0.5*lm + 0.1*om + 0.15*gy - 0.15*lm*lm - 0.05*om*om + 0.08*lm*om;
    wr = 150 + 10*lm + 30*om + 5*gy - 5*lm*lm - 8*om*om + 3*om*gy;
    if (ph < 4.5) ph = 4.5; if (ph > 8) ph = 8;
    if (wr < 80) wr = 80;
    printf "{\"ph_achieved\": %.2f, \"water_retention\": %.0f}", ph + n1*0.1, wr + n2*8;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
