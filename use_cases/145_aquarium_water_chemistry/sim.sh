#!/usr/bin/env bash
# Simulated: Aquarium Water Chemistry
set -euo pipefail

OUTFILE=""
PH=""
CO=""
FE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --target_ph) PH="$2"; shift 2 ;;
        --co2_bps) CO="$2"; shift 2 ;;
        --fert_ml_wk) FE="$2"; shift 2 ;;
        --tank_size_L) shift 2 ;;
        --lighting) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PH" ] || [ -z "$CO" ] || [ -z "$FE" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PH="$PH" -v CO="$CO" -v FE="$FE" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ph = (PH - 6.7) / 0.5;
    co = (CO - 3) / 2;
    fe = (FE - 15) / 10;
    fish = 7.0 + 0.3*ph - 0.5*co + 0.2*fe - 0.8*ph*ph - 0.3*co*co - 0.2*fe*fe + 0.2*ph*co;
    plant = 3.0 - 0.5*ph + 1.2*co + 0.8*fe - 0.3*ph*ph - 0.4*co*co - 0.2*fe*fe + 0.3*co*fe;
    if (fish < 1) fish = 1; if (fish > 10) fish = 10;
    if (plant < 0.5) plant = 0.5;
    printf "{\"fish_health\": %.1f, \"plant_growth\": %.1f}", fish + n1*0.3, plant + n2*0.2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
