#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: IDS Signature Tuning
set -euo pipefail

OUTFILE=""
SPS=""
PMD=""
SRD=""
PB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --signature_pool_size) SPS="$2"; shift 2 ;;
        --pattern_match_depth) PMD="$2"; shift 2 ;;
        --stream_reassembly_depth) SRD="$2"; shift 2 ;;
        --pcap_buffer_mb) PB="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SPS" ] || [ -z "$PMD" ] || [ -z "$SRD" ] || [ -z "$PB" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SPS="$SPS" -v PMD="$PMD" -v SRD="$SRD" -v PB="$PB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sps = (SPS - 25500) / 24500;
    pmd = (PMD - 2176) / 1920;
    srd = (SRD - 34816) / 30720;
    pb = (PB - 544) / 480;
    acc = 85 + 5*sps + 4*pmd + 3*srd + 1*pb - 2*sps*sps - 1.5*pmd*pmd + 1.5*sps*pmd;
    drop = 5 + 4*sps + 3*pmd + 2*srd - 3*pb + 1.5*sps*pmd - 0.8*pb*srd;
    if (acc > 100) acc = 100; if (acc < 50) acc = 50;
    if (drop < 0.01) drop = 0.01;
    printf "{\"detection_accuracy_pct\": %.1f, \"packet_drop_rate\": %.2f}", acc + n1*2, drop + n2*0.8;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
