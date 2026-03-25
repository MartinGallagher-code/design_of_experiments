#!/usr/bin/env bash
# Simulated: Shampoo Foaming & Cleansing
set -euo pipefail

OUTFILE=""
SF=""
PH=""
VS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --surfactant_pct) SF="$2"; shift 2 ;;
        --ph_level) PH="$2"; shift 2 ;;
        --viscosity_cp) VS="$2"; shift 2 ;;
        --fragrance) shift 2 ;;
        --preservative) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SF" ] || [ -z "$PH" ] || [ -z "$VS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SF="$SF" -v PH="$PH" -v VS="$VS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sf = (SF - 13) / 5; ph = (PH - 5.5) / 1; vs = (VS - 5000) / 3000;
    foam = 6.0 + 1.5*sf - 0.3*ph + 0.5*vs - 0.5*sf*sf + 0.2*ph*ph + 0.2*sf*vs;
    dry = 4.0 + 1.0*sf - 0.5*ph - 0.2*vs + 0.3*sf*sf + 0.2*ph*ph + 0.2*sf*ph;
    if (foam < 1) foam = 1; if (foam > 10) foam = 10;
    if (dry < 1) dry = 1; if (dry > 10) dry = 10;
    printf "{\"foam_score\": %.1f, \"scalp_dryness\": %.1f}", foam + n1*0.3, dry + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
