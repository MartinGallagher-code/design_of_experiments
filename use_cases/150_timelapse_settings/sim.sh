#!/usr/bin/env bash
# Simulated: Timelapse Interval Settings
set -euo pipefail

OUTFILE=""
IV=""
RR=""
DF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --interval_sec) IV="$2"; shift 2 ;;
        --ramp_rate) RR="$2"; shift 2 ;;
        --deflicker_pct) DF="$2"; shift 2 ;;
        --resolution) shift 2 ;;
        --codec) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$IV" ] || [ -z "$RR" ] || [ -z "$DF" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v IV="$IV" -v RR="$RR" -v DF="$DF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    iv = (IV - 16) / 14;
    rr = (RR - 1.05) / 0.95;
    df = (DF - 50) / 50;
    smooth = 6.5 - 1.5*iv + 0.3*rr + 0.5*df - 0.4*iv*iv + 0.2*iv*df;
    flick = 4.0 + 0.5*iv + 1.2*rr - 2.0*df + 0.3*rr*rr + 0.4*df*df + 0.5*rr*df;
    if (smooth < 1) smooth = 1; if (smooth > 10) smooth = 10;
    if (flick < 1) flick = 1; if (flick > 10) flick = 10;
    printf "{\"smoothness\": %.1f, \"flicker_score\": %.1f}", smooth + n1*0.3, flick + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
