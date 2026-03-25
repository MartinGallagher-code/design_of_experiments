#!/usr/bin/env bash
# Simulated: Tie-Dye Pattern Control
set -euo pipefail

OUTFILE=""
SH=""
SA=""
BT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --soak_hrs) SH="$2"; shift 2 ;;
        --soda_ash_g_L) SA="$2"; shift 2 ;;
        --band_tightness) BT="$2"; shift 2 ;;
        --fabric) shift 2 ;;
        --dye_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SH" ] || [ -z "$SA" ] || [ -z "$BT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SH="$SH" -v SA="$SA" -v BT="$BT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sh = (SH - 14) / 10; sa = (SA - 30) / 20; bt = (BT - 3) / 2;
    vib = 6.0 + 1.0*sh + 0.8*sa + 0.3*bt - 0.3*sh*sh - 0.2*sa*sa + 0.2*sh*sa;
    pat = 5.5 + 0.3*sh + 0.2*sa + 1.5*bt - 0.2*sh*sh + 0.1*sa*sa - 0.4*bt*bt + 0.2*sh*bt;
    if (vib < 1) vib = 1; if (vib > 10) vib = 10;
    if (pat < 1) pat = 1; if (pat > 10) pat = 10;
    printf "{\"vibrancy\": %.1f, \"pattern_definition\": %.1f}", vib + n1*0.3, pat + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
