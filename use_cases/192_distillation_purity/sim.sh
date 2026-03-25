#!/usr/bin/env bash
# Simulated: Lab Distillation Purity
set -euo pipefail

OUTFILE=""
RR=""
HR=""
PC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --reflux_ratio) RR="$2"; shift 2 ;;
        --heat_rate_c_min) HR="$2"; shift 2 ;;
        --packing_cm) PC="$2"; shift 2 ;;
        --mixture) shift 2 ;;
        --column_diam) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$RR" ] || [ -z "$HR" ] || [ -z "$PC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v RR="$RR" -v HR="$HR" -v PC="$PC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rr = (RR - 3) / 2; hr = (HR - 1.75) / 1.25; pc = (PC - 30) / 20;
    pur = 88 + 3*rr - 2*hr + 4*pc - 1*rr*rr + 0.5*hr*hr - 1*pc*pc + 0.5*rr*pc;
    rec = 75 - 5*rr + 3*hr - 2*pc + 1*rr*rr - 1*hr*hr + 0.5*rr*hr;
    if (pur < 70) pur = 70; if (pur > 99.9) pur = 99.9;
    if (rec < 40) rec = 40; if (rec > 98) rec = 98;
    printf "{\"purity_pct\": %.1f, \"recovery_pct\": %.0f}", pur + n1*0.5, rec + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
