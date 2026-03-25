#!/usr/bin/env bash
# Simulated: Backyard Chicken Egg Production
set -euo pipefail

OUTFILE=""
LH=""
FP=""
CA=""
VT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --light_hrs) LH="$2"; shift 2 ;;
        --feed_protein_pct) FP="$2"; shift 2 ;;
        --calcium_g) CA="$2"; shift 2 ;;
        --ventilation) VT="$2"; shift 2 ;;
        --breed) shift 2 ;;
        --flock_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$LH" ] || [ -z "$FP" ] || [ -z "$CA" ] || [ -z "$VT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v LH="$LH" -v FP="$FP" -v CA="$CA" -v VT="$VT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    lh = (LH - 13) / 3; fp = (FP - 17) / 3; ca = (CA - 4) / 2; vt = (VT == "high") ? 1 : -1;
    eggs = 5.0 + 0.8*lh + 0.5*fp + 0.2*ca + 0.3*vt - 0.3*lh*lh + 0.1*lh*fp;
    shell = 0.35 + 0.01*lh + 0.015*fp + 0.04*ca + 0.01*vt + 0.005*ca*ca;
    if (eggs < 2) eggs = 2; if (eggs > 7) eggs = 7;
    if (shell < 0.2) shell = 0.2; if (shell > 0.5) shell = 0.5;
    printf "{\"eggs_per_week\": %.1f, \"shell_thickness\": %.3f}", eggs + n1*0.3, shell + n2*0.01;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
