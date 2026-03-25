#!/usr/bin/env bash
# Simulated: Basketball Free Throw Form
set -euo pipefail

OUTFILE=""
RA=""
RH=""
BS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --release_angle_deg) RA="$2"; shift 2 ;;
        --release_height_m) RH="$2"; shift 2 ;;
        --backspin_rpm) BS="$2"; shift 2 ;;
        --distance) shift 2 ;;
        --ball) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$RA" ] || [ -z "$RH" ] || [ -z "$BS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v RA="$RA" -v RH="$RH" -v BS="$BS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ra = (RA - 50) / 5; rh = (RH - 2.25) / 0.25; bs = (BS - 200) / 100;
    acc = 72 + 3*ra + 4*rh + 2*bs - 4*ra*ra - 2*rh*rh - 1.5*bs*bs + 1*ra*rh;
    arc = 6.5 + 0.5*ra + 0.8*rh + 0.3*bs - 0.5*ra*ra - 0.4*rh*rh + 0.2*ra*bs;
    if (acc < 30) acc = 30; if (acc > 100) acc = 100;
    if (arc < 1) arc = 1; if (arc > 10) arc = 10;
    printf "{\"accuracy_pct\": %.0f, \"arc_consistency\": %.1f}", acc + n1*3, arc + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
