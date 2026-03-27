#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: BLE Mesh Topology
set -euo pipefail

OUTFILE=""
RC=""
TTL=""
PI=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --relay_count) RC="$2"; shift 2 ;;
        --ttl_hops) TTL="$2"; shift 2 ;;
        --publish_interval_ms) PI="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$RC" ] || [ -z "$TTL" ] || [ -z "$PI" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v RC="$RC" -v TTL="$TTL" -v PI="$PI" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rc = (RC - 6) / 4;
    ttl = (TTL - 5) / 3;
    pi = (PI - 1050) / 950;
    del = 92 + 4*rc + 3*ttl - 2*pi - 2*rc*rc - 1.5*ttl*ttl + 1*rc*ttl + 0.8*pi*pi;
    lat = 80 + 15*rc + 20*ttl + 30*pi - 5*rc*rc + 8*ttl*ttl + 4*rc*ttl;
    if (del > 100) del = 100; if (del < 60) del = 60;
    if (lat < 10) lat = 10;
    printf "{\"message_delivery_pct\": %.1f, \"network_latency_ms\": %.0f}", del + n1*1.5, lat + n2*8;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
