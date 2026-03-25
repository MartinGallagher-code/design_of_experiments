#!/usr/bin/env bash
# Simulated: Machine Embroidery Settings
set -euo pipefail

OUTFILE=""
DS=""
ST=""
HT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --density_sts_cm) DS="$2"; shift 2 ;;
        --stabilizer_gsm) ST="$2"; shift 2 ;;
        --hoop_tension) HT="$2"; shift 2 ;;
        --machine) shift 2 ;;
        --thread) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DS" ] || [ -z "$ST" ] || [ -z "$HT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DS="$DS" -v ST="$ST" -v HT="$HT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ds = (DS - 5.5) / 2.5; st = (ST - 80) / 40; ht = (HT - 3) / 2;
    fid = 6.0 + 1.0*ds + 0.5*st + 0.3*ht - 0.5*ds*ds - 0.2*st*st + 0.2*ds*st;
    puck = 4.0 + 0.8*ds - 0.6*st + 0.3*ht + 0.3*ds*ds - 0.2*st*st + 0.2*ds*ht;
    if (fid < 1) fid = 1; if (fid > 10) fid = 10;
    if (puck < 1) puck = 1; if (puck > 10) puck = 10;
    printf "{\"fidelity_score\": %.1f, \"pucker_score\": %.1f}", fid + n1*0.3, puck + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
