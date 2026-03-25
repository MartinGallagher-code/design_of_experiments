#!/usr/bin/env bash
# Simulated: Serverless Cold Start
set -euo pipefail

OUTFILE=""
MEM=""
RT=""
PKG=""
VPC=""
LAY=""
PROV=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --memory_mb) MEM="$2"; shift 2 ;;
        --runtime) RT="$2"; shift 2 ;;
        --package_mb) PKG="$2"; shift 2 ;;
        --vpc_enabled) VPC="$2"; shift 2 ;;
        --layers_count) LAY="$2"; shift 2 ;;
        --provisioned) PROV="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$MEM" ] || [ -z "$RT" ] || [ -z "$PKG" ] || [ -z "$VPC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v MEM="$MEM" -v RT="$RT" -v PKG="$PKG" -v VPC="$VPC" -v LAY="$LAY" -v PROV="$PROV" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    mem = (MEM - 576) / 448;
    rt = (RT == "go") ? -1 : 1;
    pkg = (PKG - 27.5) / 22.5;
    vpc = (VPC == "yes") ? 1 : -1;
    lay = (LAY - 2.5) / 2.5;
    prov = (PROV - 5) / 5;
    cs = 800 - 200*mem + 150*rt + 120*pkg + 250*vpc + 60*lay - 350*prov + 40*mem*rt;
    cst = 3.5 - 0.5*mem + 0.8*rt + 0.3*pkg + 0.4*vpc + 0.2*lay + 2.0*prov;
    if (cs < 5) cs = 5; if (cst < 0.2) cst = 0.2;
    printf "{\"cold_start_ms\": %.0f, \"cost_per_million\": %.2f}", cs + n1*50, cst + n2*0.3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
