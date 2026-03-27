#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: MQTT Broker Tuning
set -euo pipefail

OUTFILE=""
MC=""
MQD=""
KA=""
QOS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --max_connections) MC="$2"; shift 2 ;;
        --message_queue_depth) MQD="$2"; shift 2 ;;
        --keepalive_sec) KA="$2"; shift 2 ;;
        --qos_level) QOS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$MC" ] || [ -z "$MQD" ] || [ -z "$KA" ] || [ -z "$QOS" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v MC="$MC" -v MQD="$MQD" -v KA="$KA" -v QOS="$QOS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mc = (MC - 5050) / 4950;
    mqd = (MQD - 2550) / 2450;
    ka = (KA - 157.5) / 142.5;
    if (QOS == "0") qos = -1; else if (QOS == "1") qos = 0; else qos = 1;
    thr = 50 + 15*mc + 5*mqd - 2*ka - 12*qos - 5*mc*mc + 3*mc*mqd - 2*qos*mc;
    mem = 256 + 100*mc + 80*mqd + 10*ka + 40*qos + 20*mc*mqd + 15*mqd*mqd;
    if (thr < 1) thr = 1; if (mem < 32) mem = 32;
    printf "{\"message_throughput_kps\": %.1f, \"memory_usage_mb\": %.0f}", thr + n1*3, mem + n2*20;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
