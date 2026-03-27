#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: DC Motor Speed Control
set -euo pipefail
OUTFILE=""
PW=""
DC=""
VT=""
LI=""
KP=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pwm_khz) PW="$2"; shift 2 ;;
        --duty_pct) DC="$2"; shift 2 ;;
        --voltage_v) VT="$2"; shift 2 ;;
        --load_kg_cm2) LI="$2"; shift 2 ;;
        --pid_kp) KP="$2"; shift 2 ;;
        --motor) shift 2 ;;
        --encoder) shift 2 ;;
        *) shift ;;
    esac
done
if [ -z "$PW" ] || [ -z "$DC" ] || [ -z "$VT" ] || [ -z "$LI" ]; then
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk -v PW="$PW" -v DC="$DC" -v VT="$VT" -v LI="$LI" -v KP="$KP" -v seed="$RANDOM" '
BEGIN {
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;
    pw=(PW-13)/12;dc=(DC-50)/30;vt=(VT-15)/9;li=(LI-5.5)/4.5;kp=(KP-2.75)/2.25;
    acc=92+2*pw+1*dc+1*vt-1*li+3*kp-1*pw*pw+0.5*kp*kp+0.3*pw*kp;
    eff=75+3*pw+2*dc+1*vt-2*li+0.5*kp-1*pw*pw-0.5*dc*dc+0.3*pw*dc;
    if(acc<70)acc=70;if(acc>100)acc=100;if(eff<50)eff=50;if(eff>95)eff=95;
    printf "{\"speed_accuracy_pct\": %.0f, \"efficiency_pct\": %.0f}",acc+n1*1,eff+n2*1;
}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
