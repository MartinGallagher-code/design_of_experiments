#!/usr/bin/env bash
# Simulated: Yoga Sequence Design
set -euo pipefail

OUTFILE=""
HS=""
TP=""
WM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --hold_sec) HS="$2"; shift 2 ;;
        --transition_pace) TP="$2"; shift 2 ;;
        --warmup_min) WM="$2"; shift 2 ;;
        --session_length) shift 2 ;;
        --level) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HS" ] || [ -z "$TP" ] || [ -z "$WM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HS="$HS" -v TP="$TP" -v WM="$WM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    hs = (HS - 37.5) / 22.5; tp = (TP - 3) / 2; wm = (WM - 12.5) / 7.5;
    flex = 6.0 + 1.0*hs + 0.3*tp + 0.5*wm - 0.3*hs*hs - 0.2*tp*tp + 0.2*hs*wm;
    relax = 6.5 + 0.5*hs - 1.0*tp + 0.3*wm - 0.2*hs*hs + 0.3*tp*tp + 0.2*hs*tp;
    if (flex < 1) flex = 1; if (flex > 10) flex = 10;
    if (relax < 1) relax = 1; if (relax > 10) relax = 10;
    printf "{\"flexibility_gain\": %.1f, \"relaxation_score\": %.1f}", flex + n1*0.3, relax + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
