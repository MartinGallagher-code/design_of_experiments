#!/usr/bin/env bash
# Simulated: Fossil Preparation Technique
set -euo pipefail

OUTFILE=""
PR=""
ND=""
MG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pressure_psi) PR="$2"; shift 2 ;;
        --nozzle_mm) ND="$2"; shift 2 ;;
        --media_mesh) MG="$2"; shift 2 ;;
        --media_type) shift 2 ;;
        --fossil) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PR" ] || [ -z "$ND" ] || [ -z "$MG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PR="$PR" -v ND="$ND" -v MG="$MG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pr = (PR - 50) / 30; nd = (ND - 17.5) / 12.5; mg = (MG - 250) / 150;
    detail = 6.0 + 0.8*pr - 0.5*nd + 0.6*mg - 0.5*pr*pr - 0.2*nd*nd - 0.3*mg*mg + 0.2*pr*mg;
    dmg = 3.5 + 1.5*pr - 0.3*nd - 0.8*mg + 0.5*pr*pr + 0.2*nd*nd + 0.3*pr*nd;
    if (detail < 1) detail = 1; if (detail > 10) detail = 10;
    if (dmg < 1) dmg = 1; if (dmg > 10) dmg = 10;
    printf "{\"detail_score\": %.1f, \"damage_score\": %.1f}", detail + n1*0.3, dmg + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
