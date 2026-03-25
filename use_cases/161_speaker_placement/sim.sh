#!/usr/bin/env bash
# Simulated: Speaker Placement in Room
set -euo pipefail

OUTFILE=""
WD=""
TI=""
LD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --wall_dist_cm) WD="$2"; shift 2 ;;
        --toe_in_deg) TI="$2"; shift 2 ;;
        --listener_m) LD="$2"; shift 2 ;;
        --speaker_type) shift 2 ;;
        --room_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WD" ] || [ -z "$TI" ] || [ -z "$LD" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WD="$WD" -v TI="$TI" -v LD="$LD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wd = (WD - 90) / 60;
    ti = (TI - 15) / 15;
    ld = (LD - 2.75) / 1.25;
    img = 6.0 + 0.8*wd + 1.2*ti + 0.5*ld - 0.4*wd*wd - 0.5*ti*ti - 0.3*ld*ld + 0.3*ti*ld;
    bass = 5.5 + 1.0*wd - 0.3*ti + 0.4*ld - 0.5*wd*wd - 0.2*ld*ld + 0.2*wd*ld;
    if (img < 1) img = 1; if (img > 10) img = 10;
    if (bass < 1) bass = 1; if (bass > 10) bass = 10;
    printf "{\"imaging_score\": %.1f, \"bass_evenness\": %.1f}", img + n1*0.3, bass + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
