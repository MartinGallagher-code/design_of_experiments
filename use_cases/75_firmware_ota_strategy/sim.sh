#!/usr/bin/env bash
# Simulated: Firmware OTA Strategy
set -euo pipefail

OUTFILE=""
CS=""
RC=""
DE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --chunk_size_kb) CS="$2"; shift 2 ;;
        --retry_count) RC="$2"; shift 2 ;;
        --delta_encoding) DE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CS" ] || [ -z "$RC" ] || [ -z "$DE" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CS="$CS" -v RC="$RC" -v DE="$DE" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cs = (CS - 32.5) / 31.5;
    rc = (RC - 3) / 2;
    de = (DE == "on") ? 1 : -1;
    ut = 120 - 40*cs + 10*rc - 35*de + 8*cs*cs + 3*rc*rc + 5*cs*rc - 4*cs*de;
    sr = 92 - 2*cs + 5*rc + 3*de - 1*cs*cs - 0.5*rc*rc + 1*cs*rc + 0.8*rc*de;
    if (ut < 5) ut = 5; if (sr > 100) sr = 100; if (sr < 70) sr = 70;
    printf "{\"update_time_sec\": %.0f, \"success_rate_pct\": %.1f}", ut + n1*8, sr + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
