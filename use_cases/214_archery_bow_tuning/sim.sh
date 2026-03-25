#!/usr/bin/env bash
# Simulated: Archery Bow Tuning
set -euo pipefail

OUTFILE=""
DW=""
AS=""
BH=""
NH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --draw_weight_lbs) DW="$2"; shift 2 ;;
        --arrow_spine) AS="$2"; shift 2 ;;
        --brace_height_in) BH="$2"; shift 2 ;;
        --nock_height_mm) NH="$2"; shift 2 ;;
        --bow_type) shift 2 ;;
        --distance) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DW" ] || [ -z "$AS" ] || [ -z "$BH" ] || [ -z "$NH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DW="$DW" -v AS="$AS" -v BH="$BH" -v NH="$NH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dw = (DW - 40) / 10; as_ = (AS - 550) / 150; bh = (BH - 7.5) / 1.5; nh = (NH - 3) / 3;
    grp = 8 - 1*dw + 0.5*as_ - 0.3*bh + 0.5*nh + 0.5*dw*dw + 0.8*as_*as_ + 0.3*bh*bh + 0.3*dw*as_;
    drift = 3 + 0.5*dw - 0.3*as_ + 0.2*bh + 1.5*nh + 0.3*nh*nh - 0.2*dw*nh;
    if (grp < 2) grp = 2; if (drift < 0) drift = 0;
    printf "{\"group_size_cm\": %.1f, \"vertical_drift_cm\": %.1f}", grp + n1*0.5, drift + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
