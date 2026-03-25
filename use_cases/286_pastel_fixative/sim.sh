#!/usr/bin/env bash
# Simulated: Pastel Fixative Application
set -euo pipefail
OUTFILE=""
SD=""
CT=""
DM=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --spray_dist_cm) SD="$2"; shift 2 ;;
        --coats) CT="$2"; shift 2 ;;
        --dry_min) DM="$2"; shift 2 ;;
        --fixative) shift 2 ;;
        --brand) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$SD" ] || [ -z "$CT" ] || [ -z "$DM" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v SD="$SD" -v CT="$CT" -v DM="$DM" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    sd=(SD-35)/15;ct=(CT-2.5)/1.5;dm=(DM-17.5)/12.5;
    col=7-0.3*sd-0.5*ct+0.2*dm+0.2*sd*sd+0.3*ct*ct+0.1*sd*ct;
    tex=3-0.2*sd+1.5*ct-0.3*dm+0.1*sd*sd+0.3*ct*ct+0.1*ct*dm;
    if(col<1)col=1;if(col>10)col=10;if(tex<1)tex=1;if(tex>10)tex=10;
    printf "{\"color_preservation\": %.1f, \"texture_loss\": %.1f}",col+n1*0.3,tex+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
