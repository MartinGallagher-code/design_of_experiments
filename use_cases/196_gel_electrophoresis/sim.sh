#!/usr/bin/env bash
# Simulated: Gel Electrophoresis Resolution
set -euo pipefail

OUTFILE=""
GP=""
VL=""
LD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --gel_pct) GP="$2"; shift 2 ;;
        --voltage_v_cm) VL="$2"; shift 2 ;;
        --load_ul) LD="$2"; shift 2 ;;
        --buffer) shift 2 ;;
        --stain) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$GP" ] || [ -z "$VL" ] || [ -z "$LD" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v GP="$GP" -v VL="$VL" -v LD="$LD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    gp = (GP - 1.65) / 0.85; vl = (VL - 6.5) / 3.5; ld = (LD - 15) / 10;
    res = 6.5 + 0.8*gp - 0.5*vl - 0.3*ld - 0.4*gp*gp + 0.2*vl*vl + 0.2*gp*vl;
    run = 45 + 10*gp - 15*vl + 2*ld + 3*gp*gp + 2*vl*vl;
    if (res < 1) res = 1; if (res > 10) res = 10;
    if (run < 10) run = 10;
    printf "{\"resolution\": %.1f, \"run_time_min\": %.0f}", res + n1*0.3, run + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
