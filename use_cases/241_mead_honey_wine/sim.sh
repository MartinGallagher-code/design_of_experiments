#!/usr/bin/env bash
# Simulated: Mead (Honey Wine) Production
set -euo pipefail

OUTFILE=""
HR=""
NG=""
PH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --honey_ratio_kg_L) HR="$2"; shift 2 ;;
        --nutrient_g_L) NG="$2"; shift 2 ;;
        --ph_target) PH="$2"; shift 2 ;;
        --honey_type) shift 2 ;;
        --yeast) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HR" ] || [ -z "$NG" ] || [ -z "$PH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HR="$HR" -v NG="$NG" -v PH="$PH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    hr = (HR - 0.4) / 0.1; ng = (NG - 1.75) / 1.25; ph = (PH - 4) / 0.5;
    honey = 6.5 + 0.8*hr - 0.3*ng + 0.3*ph - 0.5*hr*hr + 0.2*ng*ng + 0.2*hr*ph;
    days = 30 + 8*hr - 10*ng - 3*ph + 3*hr*hr + 2*ng*ng + 2*hr*ng;
    if (honey < 1) honey = 1; if (honey > 10) honey = 10; if (days < 10) days = 10;
    printf "{\"honey_character\": %.1f, \"completion_days\": %.0f}", honey + n1*0.3, days + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
