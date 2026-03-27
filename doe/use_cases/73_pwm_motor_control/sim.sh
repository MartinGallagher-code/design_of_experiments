#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: PWM Motor Control
set -euo pipefail

OUTFILE=""
PF=""
DT=""
KP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --pwm_frequency_khz) PF="$2"; shift 2 ;;
        --dead_time_ns) DT="$2"; shift 2 ;;
        --pid_gain_kp) KP="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$PF" ] || [ -z "$DT" ] || [ -z "$KP" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v PF="$PF" -v DT="$DT" -v KP="$KP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pf = (PF - 27.5) / 22.5;
    dt = (DT - 1050) / 950;
    kp = (KP - 5.25) / 4.75;
    rip = 8 - 3*pf + 2*dt - 4*kp + 2*pf*pf + 1.5*dt*dt + 3*kp*kp - 1*pf*kp + 0.8*dt*kp;
    eff = 88 + 4*pf - 3*dt + 2*kp - 2*pf*pf - 1.5*dt*dt - 1*kp*kp + 1*pf*kp;
    if (rip < 0.5) rip = 0.5; if (eff > 98) eff = 98; if (eff < 60) eff = 60;
    printf "{\"torque_ripple_pct\": %.1f, \"efficiency_pct\": %.1f}", rip + n1*0.8, eff + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
