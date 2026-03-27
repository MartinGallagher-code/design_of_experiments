#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated laser cutting — produces edge_quality and kerf_width responses.
#
# Model:
#   edge_quality depends on power-to-speed ratio, frequency, focus, gas pressure
#   kerf_width depends on power, speed (inverse), focus offset, gas pressure

set -euo pipefail

OUTFILE=""
POWER=""
SPEED=""
FREQ=""
FOCUS=""
GAS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)                OUTFILE="$2"; shift 2 ;;
        --power)              POWER="$2";   shift 2 ;;
        --speed)              SPEED="$2";   shift 2 ;;
        --frequency)          FREQ="$2";    shift 2 ;;
        --focus_offset)       FOCUS="$2";   shift 2 ;;
        --gas_pressure)       GAS="$2";     shift 2 ;;
        --material_thickness) shift 2 ;;
        *)                    shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$POWER" || -z "$SPEED" || -z "$FREQ" || -z "$GAS" ]]; then
    echo "Usage: sim.sh --power P --speed S --frequency F --focus_offset FO --gas_pressure G --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v pw="$POWER" -v sp="$SPEED" -v fr="$FREQ" -v fo="$FOCUS" -v ga="$GAS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 4;
    n2 = (rand() - 0.5) * 0.04;

    # Coded variables centered and scaled
    pw_c = (pw - 60) / 20;
    sp_c = (sp - 300) / 200;
    fr_c = (fr - 15000) / 10000;
    fo_c = fo / 3;
    ga_c = (ga - 5) / 3;

    # Edge quality: higher power helps, moderate speed is best, focus near 0 best
    eq = 75 + 8*pw_c - 3*sp_c*sp_c + 5*fr_c - 10*fo_c*fo_c + 4*ga_c;
    eq = eq + 2*pw_c*fr_c - 3*sp_c*fo_c + n1;
    if (eq < 0) eq = 0;
    if (eq > 100) eq = 100;

    # Kerf width: wider with more power, narrower with speed, affected by focus
    kw = 0.25 + 0.06*pw_c - 0.04*sp_c + 0.03*fo_c*fo_c + 0.02*ga_c;
    kw = kw - 0.01*fr_c + 0.015*pw_c*ga_c + n2;
    if (kw < 0.05) kw = 0.05;
    if (kw > 0.8) kw = 0.8;

    printf "{\"edge_quality\": %.2f, \"kerf_width\": %.4f}", eq, kw;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
