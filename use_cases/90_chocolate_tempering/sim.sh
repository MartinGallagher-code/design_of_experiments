#!/usr/bin/env bash
# Simulated: Chocolate Tempering Process
set -euo pipefail

OUTFILE=""
ST=""
CR=""
AR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --seed_temp) ST="$2"; shift 2 ;;
        --cool_rate) CR="$2"; shift 2 ;;
        --agitation_rpm) AR="$2"; shift 2 ;;
        --cocoa_pct) shift 2 ;;
        --cocoa_butter_pct) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$ST" ] || [ -z "$CR" ] || [ -z "$AR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v ST="$ST" -v CR="$CR" -v AR="$AR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    st = (ST - 29.5) / 2.5;
    cr = (CR - 1.75) / 1.25;
    ar = (AR - 70) / 50;
    snap = 6.5 + 1.8*st - 0.6*cr + 0.4*ar - 2.0*st*st - 0.5*cr*cr + 0.7*st*cr;
    gloss = 7.0 + 1.5*st - 0.8*cr + 0.6*ar - 1.5*st*st - 0.3*cr*cr - 0.2*ar*ar + 0.4*st*ar;
    if (snap < 1) snap = 1; if (snap > 10) snap = 10;
    if (gloss < 1) gloss = 1; if (gloss > 10) gloss = 10;
    printf "{\"snap_score\": %.1f, \"gloss_score\": %.1f}", snap + n1*0.3, gloss + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
