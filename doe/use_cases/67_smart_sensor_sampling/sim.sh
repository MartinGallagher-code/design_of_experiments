#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Smart Sensor Sampling
set -euo pipefail

OUTFILE=""
SR=""
ADC=""
AW=""
SMD=""
WI=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --sample_rate_hz) SR="$2"; shift 2 ;;
        --adc_resolution_bits) ADC="$2"; shift 2 ;;
        --averaging_window) AW="$2"; shift 2 ;;
        --sleep_mode_depth) SMD="$2"; shift 2 ;;
        --wakeup_interval_sec) WI="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SR" ] || [ -z "$ADC" ] || [ -z "$AW" ] || [ -z "$SMD" ] || [ -z "$WI" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SR="$SR" -v ADC="$ADC" -v AW="$AW" -v SMD="$SMD" -v WI="$WI" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sr = (SR - 50.5) / 49.5;
    adc = (ADC - 12) / 4;
    aw = (AW - 16.5) / 15.5;
    smd = (SMD - 2.5) / 1.5;
    wi = (WI - 30.5) / 29.5;
    acc = 88 + 4*sr + 6*adc + 5*aw - 1*smd - 2*wi - 1.5*sr*sr - 1*adc*adc + 2*sr*adc + 1.5*aw*sr;
    pwr = 50 + 25*sr + 10*adc - 2*aw - 15*smd - 20*wi + 5*sr*adc - 3*smd*wi;
    if (acc > 100) acc = 100; if (acc < 50) acc = 50;
    if (pwr < 0.5) pwr = 0.5;
    printf "{\"measurement_accuracy_pct\": %.1f, \"power_consumption_mw\": %.1f}", acc + n1*1.5, pwr + n2*3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
