#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Encryption Pipeline Optimization
set -euo pipefail

OUTFILE=""
CS=""
KS=""
CBE=""
HA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cipher_suite) CS="$2"; shift 2 ;;
        --key_size) KS="$2"; shift 2 ;;
        --compression_before_encrypt) CBE="$2"; shift 2 ;;
        --hardware_acceleration) HA="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CS" ] || [ -z "$KS" ] || [ -z "$CBE" ] || [ -z "$HA" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CS="$CS" -v KS="$KS" -v CBE="$CBE" -v HA="$HA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cs = (CS == "aes256") ? -1 : 1;
    ks = (KS - 192) / 64;
    cbe = (CBE == "on") ? 1 : -1;
    ha = (HA == "on") ? 1 : -1;
    thr = 800 + 100*cs - 80*ks + 60*cbe + 250*ha + 40*cs*ha + 20*cbe*ha;
    cpu = 35 - 5*cs + 8*ks - 3*cbe - 15*ha - 3*cs*ha + 2*ks*cbe;
    if (thr < 50) thr = 50; if (cpu < 2) cpu = 2;
    printf "{\"throughput_mbps\": %.0f, \"cpu_overhead_pct\": %.1f}", thr + n1*40, cpu + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
