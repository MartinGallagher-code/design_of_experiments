#!/usr/bin/env bash
# Simulated: Firewall Rule Ordering
set -euo pipefail

OUTFILE=""
RC=""
CT=""
RO=""
HL=""
NF=""
BV=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --rule_count) RC="$2"; shift 2 ;;
        --conntrack_max) CT="$2"; shift 2 ;;
        --rule_ordering) RO="$2"; shift 2 ;;
        --hashlimit_burst) HL="$2"; shift 2 ;;
        --nf_tables) NF="$2"; shift 2 ;;
        --batch_verdict) BV="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$RC" ] || [ -z "$CT" ] || [ -z "$RO" ] || [ -z "$HL" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v RC="$RC" -v CT="$CT" -v RO="$RO" -v HL="$HL" -v NF="$NF" -v BV="$BV" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rc = (RC - 2550) / 2450;
    ct = (CT - 557056) / 491520;
    ro = (RO == "frequency") ? 1 : -1;
    hl = (HL - 52.5) / 47.5;
    nf = (NF == "nftables") ? 1 : -1;
    bv = (BV == "on") ? 1 : -1;
    thr = 2.5 - 0.8*rc + 0.3*ct + 0.5*ro - 0.1*hl + 0.6*nf + 0.4*bv + 0.2*ro*nf;
    lat = 15 + 8*rc - 2*ct - 4*ro + 1*hl - 5*nf - 3*bv + 2*rc*ro;
    if (thr < 0.1) thr = 0.1; if (lat < 1) lat = 1;
    printf "{\"throughput_mpps\": %.2f, \"latency_us\": %.1f}", thr + n1*0.15, lat + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
