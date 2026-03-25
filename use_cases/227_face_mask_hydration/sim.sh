#!/usr/bin/env bash
# Simulated: Face Mask Hydration Treatment
set -euo pipefail

OUTFILE=""
MT=""
SC=""
SP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --mask_time_min) MT="$2"; shift 2 ;;
        --serum_pct) SC="$2"; shift 2 ;;
        --serum_ph) SP="$2"; shift 2 ;;
        --mask_material) shift 2 ;;
        --active) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MT" ] || [ -z "$SC" ] || [ -z "$SP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MT="$MT" -v SC="$SC" -v SP="$SP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mt = (MT - 20) / 10; sc = (SC - 5.5) / 4.5; sp = (SP - 4.75) / 1.25;
    hyd = 6.0 + 0.8*mt + 1.0*sc - 0.3*sp - 0.4*mt*mt - 0.3*sc*sc + 0.2*mt*sc;
    irr = 2.5 + 0.3*mt + 0.5*sc - 0.8*sp + 0.2*mt*mt + 0.3*sc*sc + 0.2*sc*sp;
    if (hyd < 1) hyd = 1; if (hyd > 10) hyd = 10;
    if (irr < 1) irr = 1; if (irr > 10) irr = 10;
    printf "{\"hydration_gain\": %.1f, \"irritation\": %.1f}", hyd + n1*0.3, irr + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
