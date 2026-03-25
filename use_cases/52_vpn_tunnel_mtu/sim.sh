#!/usr/bin/env bash
# Simulated: VPN Tunnel MTU
set -euo pipefail

OUTFILE=""
MTU=""
FRAG=""
KA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tunnel_mtu) MTU="$2"; shift 2 ;;
        --fragment_size) FRAG="$2"; shift 2 ;;
        --keepalive_interval) KA="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$MTU" ] || [ -z "$FRAG" ] || [ -z "$KA" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v MTU="$MTU" -v FRAG="$FRAG" -v KA="$KA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mtu = (MTU - 1350) / 150;
    frag = (FRAG - 700) / 700;
    ka = (KA - 65) / 55;
    thr = 850 + 80*mtu - 40*frag - 10*ka - 30*mtu*mtu + 15*frag*frag + 20*mtu*frag;
    rec = 8 + 1*mtu + 2*frag + 5*ka - 0.5*mtu*ka + 1.5*ka*ka;
    if (thr < 10) thr = 10; if (rec < 0.5) rec = 0.5;
    printf "{\"throughput_mbps\": %.0f, \"reconnect_time_s\": %.1f}", thr + n1*30, rec + n2*1.0;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
