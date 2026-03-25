#!/usr/bin/env bash
# Simulated: UV-Vis Spectrophotometry
set -euo pipefail

OUTFILE=""
SL=""
SS=""
PL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --slit_nm) SL="$2"; shift 2 ;;
        --scan_speed) SS="$2"; shift 2 ;;
        --path_cm) PL="$2"; shift 2 ;;
        --lamp) shift 2 ;;
        --wavelength) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SL" ] || [ -z "$SS" ] || [ -z "$PL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SL="$SL" -v SS="$SS" -v PL="$PL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sl = (SL - 2.75) / 2.25; ss = (SS - 550) / 450; pl = (PL - 2.55) / 2.45;
    snr = 200 + 50*sl - 30*ss + 40*pl - 15*sl*sl + 10*ss*ss + 5*sl*pl;
    drift = 0.005 + 0.001*sl + 0.002*ss + 0.0005*pl + 0.0003*ss*ss;
    if (snr < 20) snr = 20;
    if (drift < 0.001) drift = 0.001;
    printf "{\"snr\": %.0f, \"baseline_drift\": %.4f}", snr + n1*10, drift + n2*0.0005;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
