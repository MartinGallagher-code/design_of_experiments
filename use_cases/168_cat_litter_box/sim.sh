#!/usr/bin/env bash
# Simulated: Cat Litter Box Management
set -euo pipefail

OUTFILE=""
LD=""
CF=""
BA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --litter_depth_cm) LD="$2"; shift 2 ;;
        --clean_per_day) CF="$2"; shift 2 ;;
        --box_area_cm2) BA="$2"; shift 2 ;;
        --litter_type) shift 2 ;;
        --cats) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$LD" ] || [ -z "$CF" ] || [ -z "$BA" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v LD="$LD" -v CF="$CF" -v BA="$BA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ld = (LD - 6.5) / 3.5; cf = (CF - 2) / 1; ba = (BA - 2750) / 1250;
    odor = 5.5 + 0.8*ld + 1.5*cf + 0.5*ba - 0.3*ld*ld - 0.4*cf*cf + 0.2*ld*cf;
    usage = 85 + 3*ld + 5*cf + 4*ba - 1.5*ld*ld - 2*cf*cf - 1*ba*ba + 1*cf*ba;
    if (odor < 1) odor = 1; if (odor > 10) odor = 10;
    if (usage < 50) usage = 50; if (usage > 100) usage = 100;
    printf "{\"odor_control\": %.1f, \"usage_pct\": %.0f}", odor + n1*0.3, usage + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
