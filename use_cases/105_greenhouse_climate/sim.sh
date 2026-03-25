#!/usr/bin/env bash
# Simulated: Greenhouse Climate Control
set -euo pipefail

OUTFILE=""
VR=""
SP=""
CO=""
HS=""
MF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --vent_rate) VR="$2"; shift 2 ;;
        --shade_pct) SP="$2"; shift 2 ;;
        --co2_ppm) CO="$2"; shift 2 ;;
        --heat_setpoint) HS="$2"; shift 2 ;;
        --mist_freq) MF="$2"; shift 2 ;;
        --greenhouse_area) shift 2 ;;
        --crop) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$VR" ] || [ -z "$SP" ] || [ -z "$CO" ] || [ -z "$HS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v VR="$VR" -v SP="$SP" -v CO="$CO" -v HS="$HS" -v MF="$MF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    vr = (VR - 17.5) / 12.5;
    sp = (SP - 30) / 30;
    co = (CO - 800) / 400;
    hs = (HS - 20) / 5;
    mf = (MF - 6) / 6;
    gro = 6.0 + 0.5*vr - 0.8*sp + 1.2*co + 0.6*hs + 0.3*mf + 0.3*co*hs;
    eng = 15 + 3*vr + 0.5*sp + 2*co + 5*hs + 0.8*mf + 1.5*vr*hs;
    if (gro < 1) gro = 1; if (gro > 10) gro = 10;
    if (eng < 3) eng = 3;
    printf "{\"growth_index\": %.1f, \"energy_cost\": %.1f}", gro + n1*0.4, eng + n2*1.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
