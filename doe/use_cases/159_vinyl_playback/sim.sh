#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Vinyl Playback Optimization
set -euo pipefail

OUTFILE=""
TF=""
AS=""
OH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tracking_force_g) TF="$2"; shift 2 ;;
        --anti_skate_g) AS="$2"; shift 2 ;;
        --overhang_mm) OH="$2"; shift 2 ;;
        --turntable) shift 2 ;;
        --cartridge_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TF" ] || [ -z "$AS" ] || [ -z "$OH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TF="$TF" -v AS="$AS" -v OH="$OH" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    tf = (TF - 1.7) / 0.5;
    as_ = (AS - 1.25) / 0.75;
    oh = (OH - 16) / 2;
    fid = 7.0 + 0.5*tf + 0.3*as_ + 0.4*oh - 0.8*tf*tf - 0.5*as_*as_ - 0.6*oh*oh + 0.2*tf*as_;
    noise = -55 + 2*tf + 1*as_ - 0.5*oh + 1*tf*tf + 0.5*oh*oh;
    if (fid < 1) fid = 1; if (fid > 10) fid = 10;
    if (noise < -65) noise = -65;
    printf "{\"fidelity_score\": %.1f, \"surface_noise\": %.0f}", fid + n1*0.3, noise + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
