#!/usr/bin/env bash
# Simulated: Wind Tunnel Test Setup
set -euo pipefail
OUTFILE=""
SP=""
MS=""
TG=""
SA=""
RK=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --speed_ms) SP="$2"; shift 2 ;;
        --model_scale) MS="$2"; shift 2 ;;
        --turb_grid) TG="$2"; shift 2 ;;
        --sting_deg) SA="$2"; shift 2 ;;
        --rake_pct) RK="$2"; shift 2 ;;
        --tunnel) shift 2 ;;
        --test_section) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$SP" ] || [ -z "$MS" ] || [ -z "$TG" ] || [ -z "$SA" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v SP="$SP" -v MS="$MS" -v TG="$TG" -v SA="$SA" -v RK="$RK" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    sp=(SP-30)/20;ms=(MS-0.2)/0.1;tg=(TG-0.5)/0.5;sa=(SA-5)/10;rk=(RK-100)/50;
    acc=7+0.5*sp+0.8*ms+0.3*tg-0.2*sa-0.3*rk+0.2*sp*ms;
    rep=92+2*sp+1*ms-1*tg+0.5*sa-0.5*rk+0.3*sp*tg;
    if(acc<1)acc=1;if(acc>10)acc=10;if(rep<75)rep=75;if(rep>100)rep=100;
    printf "{\"data_accuracy\": %.1f, \"repeatability_pct\": %.0f}",acc+n1*0.3,rep+n2*1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
