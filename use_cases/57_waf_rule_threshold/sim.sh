#!/usr/bin/env bash
# Simulated: WAF Rule Threshold Tuning
set -euo pipefail

OUTFILE=""
RL=""
BD=""
AST=""
PL=""
SQLI=""
XSS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --rate_limit_rps) RL="$2"; shift 2 ;;
        --body_inspection_depth) BD="$2"; shift 2 ;;
        --anomaly_score_threshold) AST="$2"; shift 2 ;;
        --paranoia_level) PL="$2"; shift 2 ;;
        --sql_injection_sensitivity) SQLI="$2"; shift 2 ;;
        --xss_detection_level) XSS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$RL" ] || [ -z "$BD" ] || [ -z "$AST" ] || [ -z "$PL" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v RL="$RL" -v BD="$BD" -v AST="$AST" -v PL="$PL" -v SQLI="$SQLI" -v XSS="$XSS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rl = (RL - 5050) / 4950;
    bd = (BD - 33268) / 32268;
    ast = (AST - 9) / 6;
    pl = (PL - 2.5) / 1.5;
    sqli = (SQLI - 5) / 4;
    xss = (XSS - 3) / 2;
    det = 82 + 3*rl + 5*bd - 6*ast + 8*pl + 4*sqli + 3*xss + 2*pl*sqli + 1.5*bd*xss;
    fp = 4 + 2*rl + 1.5*bd - 3*ast + 5*pl + 2.5*sqli + 2*xss + 1*pl*ast + 0.8*sqli*xss;
    if (det > 100) det = 100; if (det < 40) det = 40;
    if (fp < 0.1) fp = 0.1;
    printf "{\"detection_rate\": %.1f, \"false_positive_rate\": %.2f}", det + n1*2, fp + n2*0.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
