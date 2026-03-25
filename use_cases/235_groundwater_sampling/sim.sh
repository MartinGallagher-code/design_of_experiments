#!/usr/bin/env bash
# Simulated: Groundwater Sampling Protocol
set -euo pipefail

OUTFILE=""
PV=""
PR=""
DH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --purge_volumes) PV="$2"; shift 2 ;;
        --pump_rate_lpm) PR="$2"; shift 2 ;;
        --dev_hrs) DH="$2"; shift 2 ;;
        --well_type) shift 2 ;;
        --analytes) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PV" ] || [ -z "$PR" ] || [ -z "$DH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PV="$PV" -v PR="$PR" -v DH="$DH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pv = (PV - 3) / 2; pr = (PR - 2.75) / 2.25; dh = (DH - 4.5) / 3.5;
    rep = 6.5 + 1.0*pv - 0.5*pr + 0.5*dh - 0.4*pv*pv + 0.2*pr*pr + 0.2*pv*dh;
    turb = 8 - 2*pv + 2*pr - 1.5*dh + 0.5*pv*pv + 0.3*pr*pr + 0.3*pr*dh;
    if (rep < 1) rep = 1; if (rep > 10) rep = 10; if (turb < 0.5) turb = 0.5;
    printf "{\"representativeness\": %.1f, \"sample_turbidity\": %.1f}", rep + n1*0.3, turb + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
