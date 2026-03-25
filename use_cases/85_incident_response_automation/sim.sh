#!/usr/bin/env bash
# Simulated: Incident Response Automation
set -euo pipefail

OUTFILE=""
ATS=""
ED=""
AR=""
RTO=""
NC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --alert_threshold_severity) ATS="$2"; shift 2 ;;
        --escalation_delay_min) ED="$2"; shift 2 ;;
        --auto_remediation_enabled) AR="$2"; shift 2 ;;
        --runbook_timeout_sec) RTO="$2"; shift 2 ;;
        --notification_channels) NC="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$ATS" ] || [ -z "$ED" ] || [ -z "$AR" ] || [ -z "$RTO" ] || [ -z "$NC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v ATS="$ATS" -v ED="$ED" -v AR="$AR" -v RTO="$RTO" -v NC="$NC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ats = (ATS - 3) / 2;
    ed = (ED - 8) / 7;
    ar = (AR == "on") ? 1 : -1;
    rto = (RTO - 165) / 135;
    nc = (NC - 3) / 2;
    mttr = 30 + 8*ats + 10*ed - 15*ar + 5*rto - 3*nc + 3*ats*ed - 2*ar*rto + 4*ed*ed;
    fe = 8 - 3*ats + 2*ed + 4*ar - 1*rto + 1.5*nc + 1.5*ar*ats - 0.8*ed*nc + 2*ar*ar;
    if (mttr < 2) mttr = 2; if (fe < 0.5) fe = 0.5;
    printf "{\"mttr_min\": %.1f, \"false_escalation_pct\": %.1f}", mttr + n1*3, fe + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
