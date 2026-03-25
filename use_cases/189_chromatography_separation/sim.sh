#!/usr/bin/env bash
# Simulated: Chromatography Separation
set -euo pipefail

OUTFILE=""
FL=""
OP=""
CT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --flow_ml_min) FL="$2"; shift 2 ;;
        --organic_pct) OP="$2"; shift 2 ;;
        --column_temp_c) CT="$2"; shift 2 ;;
        --column) shift 2 ;;
        --detector) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FL" ] || [ -z "$OP" ] || [ -z "$CT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FL="$FL" -v OP="$OP" -v CT="$CT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fl = (FL - 1.25) / 0.75; op = (OP - 55) / 25; ct = (CT - 40) / 15;
    res = 2.5 - 0.5*fl + 0.3*op + 0.2*ct + 0.3*fl*fl - 0.5*op*op - 0.2*ct*ct + 0.2*fl*op;
    run = 15 - 4*fl - 3*op - 1.5*ct + 1*fl*fl + 0.5*op*op;
    if (res < 0.5) res = 0.5;
    if (run < 3) run = 3;
    printf "{\"resolution\": %.2f, \"run_time_min\": %.1f}", res + n1*0.1, run + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
