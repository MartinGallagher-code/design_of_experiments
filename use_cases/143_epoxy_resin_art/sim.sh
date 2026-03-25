#!/usr/bin/env bash
# Simulated: Epoxy Resin Art Curing
set -euo pipefail

OUTFILE=""
RR=""
AT=""
DG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --resin_ratio) RR="$2"; shift 2 ;;
        --ambient_temp_c) AT="$2"; shift 2 ;;
        --degas_min) DG="$2"; shift 2 ;;
        --resin_type) shift 2 ;;
        --mold) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$RR" ] || [ -z "$AT" ] || [ -z "$DG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v RR="$RR" -v AT="$AT" -v DG="$DG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rr = (RR - 2.0) / 0.2;
    at = (AT - 23) / 5;
    dg = (DG - 7.5) / 7.5;
    clar = 7.0 + 0.3*rr + 0.5*at + 1.5*dg - 1.5*rr*rr - 0.3*at*at - 0.4*dg*dg + 0.2*at*dg;
    bub = 8 - 0.5*rr - 1.0*at - 3.0*dg + 1.0*rr*rr + 0.5*at*at + 0.5*dg*dg - 0.3*at*dg;
    if (clar < 1) clar = 1; if (clar > 10) clar = 10;
    if (bub < 0) bub = 0;
    printf "{\"clarity_score\": %.1f, \"bubble_count\": %.1f}", clar + n1*0.3, bub + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
