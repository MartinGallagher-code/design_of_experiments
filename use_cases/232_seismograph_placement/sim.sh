#!/usr/bin/env bash
# Simulated: Seismograph Network Placement
set -euo pipefail

OUTFILE=""
SP=""
BR=""
SR=""
FH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --spacing_km) SP="$2"; shift 2 ;;
        --burial_m) BR="$2"; shift 2 ;;
        --sample_hz) SR="$2"; shift 2 ;;
        --filter_hz) FH="$2"; shift 2 ;;
        --sensor) shift 2 ;;
        --network_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SP" ] || [ -z "$BR" ] || [ -z "$SR" ] || [ -z "$FH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SP="$SP" -v BR="$BR" -v SR="$SR" -v FH="$FH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sp = (SP - 15) / 10; br = (BR - 1.5) / 1.5; sr = (SR - 120) / 80; fh = (FH - 5.25) / 4.75;
    det = 80 - 8*sp + 5*br + 3*sr - 2*fh + 2*sp*sp + 1*br*sr;
    false_ = 5 - 1*sp - 2*br + 1*sr - 3*fh + 0.5*sp*sp + 1*sr*sr + 0.5*sr*fh;
    if (det < 40) det = 40; if (det > 100) det = 100; if (false_ < 0) false_ = 0;
    printf "{\"detection_pct\": %.0f, \"false_trigger_day\": %.1f}", det + n1*2, false_ + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
