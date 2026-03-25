#!/usr/bin/env bash
# Simulated: Router Bit Speed & Feed
set -euo pipefail

OUTFILE=""
RR=""
FR=""
DP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --router_rpm) RR="$2"; shift 2 ;;
        --feed_m_min) FR="$2"; shift 2 ;;
        --depth_mm) DP="$2"; shift 2 ;;
        --bit_type) shift 2 ;;
        --bit_diam) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$RR" ] || [ -z "$FR" ] || [ -z "$DP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v RR="$RR" -v FR="$FR" -v DP="$DP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rr = (RR - 17000) / 7000; fr = (FR - 3.5) / 2.5; dp = (DP - 7.5) / 4.5;
    edge = 6.5 + 0.5*rr + 0.8*fr - 0.3*dp - 0.5*rr*rr - 0.3*fr*fr + 0.2*rr*fr;
    burn = 4.0 + 1.2*rr - 0.8*fr + 0.3*dp + 0.5*rr*rr + 0.2*dp*dp + 0.3*rr*dp;
    if (edge < 1) edge = 1; if (edge > 10) edge = 10;
    if (burn < 1) burn = 1; if (burn > 10) burn = 10;
    printf "{\"edge_quality\": %.1f, \"burn_score\": %.1f}", edge + n1*0.3, burn + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
