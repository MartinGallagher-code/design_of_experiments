#!/usr/bin/env bash
# Simulated: Stretching Protocol Design
set -euo pipefail

OUTFILE=""
HS=""
SF=""
WM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --hold_sec) HS="$2"; shift 2 ;;
        --sessions_per_week) SF="$2"; shift 2 ;;
        --warmup_min) WM="$2"; shift 2 ;;
        --stretch_type) shift 2 ;;
        --target_area) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HS" ] || [ -z "$SF" ] || [ -z "$WM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HS="$HS" -v SF="$SF" -v WM="$WM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    hs = (HS - 35) / 25;
    sf = (SF - 4.5) / 2.5;
    wm = (WM - 7.5) / 7.5;
    flex = 4.0 + 1.5*hs + 1.2*sf + 0.5*wm - 0.4*hs*hs - 0.3*sf*sf + 0.3*hs*sf + 0.2*sf*wm;
    sore = 3.5 + 1.0*hs + 0.5*sf - 0.8*wm + 0.3*hs*hs + 0.2*hs*sf - 0.3*wm*sf;
    if (flex < 0.5) flex = 0.5;
    if (sore < 1) sore = 1; if (sore > 10) sore = 10;
    printf "{\"flexibility_gain\": %.1f, \"soreness\": %.1f}", flex + n1*0.5, sore + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
