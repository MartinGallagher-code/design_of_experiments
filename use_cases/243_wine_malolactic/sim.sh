#!/usr/bin/env bash
# Simulated: Wine Malolactic Fermentation
set -euo pipefail

OUTFILE=""
IR=""
CT=""
SO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --inoc_rate) IR="$2"; shift 2 ;;
        --cellar_temp_c) CT="$2"; shift 2 ;;
        --free_so2_ppm) SO="$2"; shift 2 ;;
        --wine_type) shift 2 ;;
        --ph) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$IR" ] || [ -z "$CT" ] || [ -z "$SO" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v IR="$IR" -v CT="$CT" -v SO="$SO" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ir = (IR - 1.25) / 0.75; ct = (CT - 18.5) / 3.5; so = (SO - 15) / 10;
    mlf = 80 + 8*ir + 5*ct - 10*so - 3*ir*ir - 2*ct*ct + 2*so*so + 2*ir*ct;
    va = 0.3 + 0.05*ir + 0.08*ct + 0.03*so + 0.02*ir*ir + 0.03*ct*ct - 0.01*so*so + 0.02*ir*ct;
    if (mlf < 20) mlf = 20; if (mlf > 100) mlf = 100;
    if (va < 0.1) va = 0.1; if (va > 1.0) va = 1.0;
    printf "{\"mlf_completion_pct\": %.0f, \"va_g_L\": %.2f}", mlf + n1*3, va + n2*0.02;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
