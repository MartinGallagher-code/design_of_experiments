#!/usr/bin/env bash
# Simulated: Wastewater Treatment Optimization (Plackett-Burman with ordinal factors)
set -euo pipefail

OUTFILE=""
PH=""
RT=""
AR=""
FD=""
TMP=""
MI=""
FG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --ph_level) PH="$2"; shift 2 ;;
        --retention_time) RT="$2"; shift 2 ;;
        --aeration_rate) AR="$2"; shift 2 ;;
        --flocculant_dose) FD="$2"; shift 2 ;;
        --temperature) TMP="$2"; shift 2 ;;
        --mixing_intensity) MI="$2"; shift 2 ;;
        --filter_grade) FG="$2"; shift 2 ;;
        --plant_capacity) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PH" ] || [ -z "$RT" ] || [ -z "$AR" ] || [ -z "$FD" ] || [ -z "$TMP" ] || [ -z "$MI" ] || [ -z "$FG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PH="$PH" -v RT="$RT" -v AR="$AR" -v FD="$FD" -v TMP="$TMP" -v MI="$MI" -v FG="$FG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    # Normalize continuous factors to [-1, 1]
    ph = (PH - 7.5) / 1.5;
    rt = (RT - 8) / 4;
    ar = (AR - 4) / 2;
    fd = (FD - 30) / 20;
    tmp = (TMP - 22.5) / 7.5;

    # Encode ordinal factors: low/coarse = -1, high/fine = +1
    mi = (MI == "high") ? 1 : -1;
    fg = (FG == "fine") ? 1 : -1;

    # BOD removal (%): higher retention, aeration, temp, fine filter help
    bod = 85 + 3*rt + 2.5*ar + 1.5*tmp + 2*fg + 1*mi + 1.5*fd - 1.5*ph*ph;
    bod = bod + n1 * 1.5;
    if (bod < 50) bod = 50;
    if (bod > 99.5) bod = 99.5;

    # Sludge volume (mL/L): increases with flocculant, retention; fine filter reduces
    sv = 150 + 30*fd + 20*rt + 10*mi - 15*fg + 8*ar + 5*tmp - 3*ph;
    sv = sv + n2 * 8;
    if (sv < 50) sv = 50;
    if (sv > 400) sv = 400;

    printf "{\"bod_removal\": %.1f, \"sludge_volume\": %.0f}", bod, sv;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
