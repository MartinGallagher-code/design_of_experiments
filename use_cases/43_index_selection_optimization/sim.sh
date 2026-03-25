#!/usr/bin/env bash
# Simulated: Index Selection Optimization
set -euo pipefail

OUTFILE=""
FF=""
MW=""
PW=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --fill_factor) FF="$2"; shift 2 ;;
        --maintenance_work_mem_mb) MW="$2"; shift 2 ;;
        --parallel_workers) PW="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$FF" ] || [ -z "$MW" ] || [ -z "$PW" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v FF="$FF" -v MW="$MW" -v PW="$PW" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ff = (FF - 75) / 25;
    mw = (MW - 1056) / 992;
    pw = (PW - 4) / 4;
    bt = 180 - 20*ff - 60*mw - 40*pw + 15*ff*ff + 10*mw*mw + 5*pw*pw + 8*ff*mw;
    qs = 25 + 8*ff + 3*mw + 5*pw - 2*ff*ff - 1*mw*mw + 1.5*ff*pw;
    if (bt < 10) bt = 10; if (qs < 1) qs = 1;
    printf "{\"build_time_s\": %.0f, \"query_speedup\": %.1f}", bt + n1*12, qs + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
