#!/usr/bin/env bash
# Simulated: Art Framing UV Protection
set -euo pipefail
OUTFILE=""
UC=""
AL=""
SP=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --uv_cutoff_nm) UC="$2"; shift 2 ;;
        --ar_layers) AL="$2"; shift 2 ;;
        --spacer_mm) SP="$2"; shift 2 ;;
        --frame) shift 2 ;;
        --mat) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$UC" ] || [ -z "$AL" ] || [ -z "$SP" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v UC="$UC" -v AL="$AL" -v SP="$SP" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    uc=(UC-400)/20;al=(AL-2)/2;sp=(SP-5)/3;
    uv=92+4*uc+1*al+0.5*sp-1*uc*uc+0.3*al*al+0.2*uc*al;
    glare=5-0.2*uc-2*al+0.3*sp+0.1*uc*uc+0.5*al*al+0.2*al*sp;
    if(uv<70)uv=70;if(uv>99.9)uv=99.9;if(glare<1)glare=1;if(glare>10)glare=10;
    printf "{\"uv_block_pct\": %.1f, \"glare_score\": %.1f}",uv+n1*0.5,glare+n2*0.3;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
