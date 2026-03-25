#!/usr/bin/env bash
# Simulated: Screen Printing Quality
set -euo pipefail

OUTFILE=""
MC=""
SP=""
IV=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --mesh_count) MC="$2"; shift 2 ;;
        --squeegee_pressure) SP="$2"; shift 2 ;;
        --ink_viscosity) IV="$2"; shift 2 ;;
        --substrate) shift 2 ;;
        --ink_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MC" ] || [ -z "$SP" ] || [ -z "$IV" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MC="$MC" -v SP="$SP" -v IV="$IV" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mc = (MC - 205) / 95; sp = (SP - 5) / 3; iv = (IV - 5000) / 3000;
    sharp = 6.5 + 1.0*mc + 0.5*sp - 0.8*iv - 0.3*mc*mc - 0.2*sp*sp + 0.2*mc*sp;
    adh = 6.0 - 0.3*mc + 0.8*sp + 0.3*iv - 0.2*mc*mc - 0.3*sp*sp + 0.2*sp*iv;
    if (sharp < 1) sharp = 1; if (sharp > 10) sharp = 10;
    if (adh < 1) adh = 1; if (adh > 10) adh = 10;
    printf "{\"sharpness\": %.1f, \"adhesion_score\": %.1f}", sharp + n1*0.3, adh + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
