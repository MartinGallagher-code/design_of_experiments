#!/usr/bin/env python3
"""Generate 30 new use cases across 3 categories (57-86)."""
import json, os, stat, textwrap

USE_CASES = [
    # ══════════════════════════════════════════════════
    # Category: Security & Compliance (57-66)
    # ══════════════════════════════════════════════════
    {
        "num": 57, "slug": "waf_rule_threshold",
        "name": "WAF Rule Threshold Tuning",
        "desc": "Plackett-Burman screening of 6 WAF parameters for detection rate and false positive rate",
        "design": "plackett_burman", "category": "security",
        "factors": [
            {"name": "rate_limit_rps", "levels": ["100", "10000"], "type": "continuous", "unit": "rps", "description": "Request rate limit per client"},
            {"name": "body_inspection_depth", "levels": ["1000", "65536"], "type": "continuous", "unit": "bytes", "description": "Request body inspection depth"},
            {"name": "anomaly_score_threshold", "levels": ["3", "15"], "type": "continuous", "unit": "score", "description": "Anomaly score blocking threshold"},
            {"name": "paranoia_level", "levels": ["1", "4"], "type": "continuous", "unit": "level", "description": "CRS paranoia level"},
            {"name": "sql_injection_sensitivity", "levels": ["1", "9"], "type": "continuous", "unit": "level", "description": "SQLi detection sensitivity"},
            {"name": "xss_detection_level", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "XSS detection sensitivity level"},
        ],
        "fixed": {"waf_engine": "modsecurity", "ruleset": "owasp_crs"},
        "responses": [
            {"name": "detection_rate", "optimize": "maximize", "unit": "%", "description": "Attack detection rate"},
            {"name": "false_positive_rate", "optimize": "minimize", "unit": "%", "description": "False positive rate on legitimate traffic"},
        ],
        "model": """
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
    printf "{\\"detection_rate\\": %.1f, \\"false_positive_rate\\": %.2f}", det + n1*2, fp + n2*0.5;
""",
        "factor_cases": '--rate_limit_rps) RL="$2"; shift 2 ;;\n        --body_inspection_depth) BD="$2"; shift 2 ;;\n        --anomaly_score_threshold) AST="$2"; shift 2 ;;\n        --paranoia_level) PL="$2"; shift 2 ;;\n        --sql_injection_sensitivity) SQLI="$2"; shift 2 ;;\n        --xss_detection_level) XSS="$2"; shift 2 ;;',
        "awk_vars": '-v RL="$RL" -v BD="$BD" -v AST="$AST" -v PL="$PL" -v SQLI="$SQLI" -v XSS="$XSS"',
        "vars_init": 'RL=""\nBD=""\nAST=""\nPL=""\nSQLI=""\nXSS=""',
        "validate": '[ -z "$RL" ] || [ -z "$BD" ] || [ -z "$AST" ] || [ -z "$PL" ]',
    },
    {
        "num": 58, "slug": "encryption_pipeline",
        "name": "Encryption Pipeline Optimization",
        "desc": "Full factorial of cipher suite, key size, compression, and hardware acceleration for throughput and CPU overhead",
        "design": "full_factorial", "category": "security",
        "factors": [
            {"name": "cipher_suite", "levels": ["aes128", "aes256"], "type": "categorical", "unit": "", "description": "Cipher suite selection"},
            {"name": "key_size", "levels": ["128", "256"], "type": "continuous", "unit": "bits", "description": "Encryption key size"},
            {"name": "compression_before_encrypt", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Compress before encryption"},
            {"name": "hardware_acceleration", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "AES-NI hardware acceleration"},
        ],
        "fixed": {"protocol": "tls1.3", "mode": "gcm"},
        "responses": [
            {"name": "throughput_mbps", "optimize": "maximize", "unit": "Mbps", "description": "Encryption throughput"},
            {"name": "cpu_overhead_pct", "optimize": "minimize", "unit": "%", "description": "CPU overhead from encryption"},
        ],
        "model": """
    cs = (CS == "aes256") ? -1 : 1;
    ks = (KS - 192) / 64;
    cbe = (CBE == "on") ? 1 : -1;
    ha = (HA == "on") ? 1 : -1;
    thr = 800 + 100*cs - 80*ks + 60*cbe + 250*ha + 40*cs*ha + 20*cbe*ha;
    cpu = 35 - 5*cs + 8*ks - 3*cbe - 15*ha - 3*cs*ha + 2*ks*cbe;
    if (thr < 50) thr = 50; if (cpu < 2) cpu = 2;
    printf "{\\"throughput_mbps\\": %.0f, \\"cpu_overhead_pct\\": %.1f}", thr + n1*40, cpu + n2*2;
""",
        "factor_cases": '--cipher_suite) CS="$2"; shift 2 ;;\n        --key_size) KS="$2"; shift 2 ;;\n        --compression_before_encrypt) CBE="$2"; shift 2 ;;\n        --hardware_acceleration) HA="$2"; shift 2 ;;',
        "awk_vars": '-v CS="$CS" -v KS="$KS" -v CBE="$CBE" -v HA="$HA"',
        "vars_init": 'CS=""\nKS=""\nCBE=""\nHA=""',
        "validate": '[ -z "$CS" ] || [ -z "$KS" ] || [ -z "$CBE" ] || [ -z "$HA" ]',
    },
    {
        "num": 59, "slug": "siem_alert_correlation",
        "name": "SIEM Alert Correlation",
        "desc": "Box-Behnken design to tune alert correlation window, similarity threshold, and event count for alert reduction",
        "design": "box_behnken", "category": "security",
        "factors": [
            {"name": "correlation_window_sec", "levels": ["30", "600"], "type": "continuous", "unit": "sec", "description": "Time window for correlating alerts"},
            {"name": "similarity_threshold", "levels": ["0.3", "0.9"], "type": "continuous", "unit": "ratio", "description": "Similarity threshold for grouping"},
            {"name": "min_event_count", "levels": ["2", "10"], "type": "continuous", "unit": "events", "description": "Minimum events to trigger correlation"},
        ],
        "fixed": {"siem_platform": "elastic_security", "log_sources": "12"},
        "responses": [
            {"name": "alert_reduction_pct", "optimize": "maximize", "unit": "%", "description": "Percentage of alerts reduced by correlation"},
            {"name": "missed_incident_rate", "optimize": "minimize", "unit": "%", "description": "Rate of missed real incidents"},
        ],
        "model": """
    cw = (CW - 315) / 285;
    st = (ST - 0.6) / 0.3;
    mec = (MEC - 6) / 4;
    red = 55 + 15*cw + 12*st + 8*mec - 5*cw*cw - 4*st*st + 3*cw*st + 2*st*mec;
    miss = 3 + 2*cw + 3*st + 4*mec - 1*cw*cw + 1.5*st*st + 2*mec*mec - 1*cw*mec;
    if (red > 95) red = 95; if (red < 10) red = 10;
    if (miss < 0.1) miss = 0.1;
    printf "{\\"alert_reduction_pct\\": %.1f, \\"missed_incident_rate\\": %.2f}", red + n1*3, miss + n2*0.5;
""",
        "factor_cases": '--correlation_window_sec) CW="$2"; shift 2 ;;\n        --similarity_threshold) ST="$2"; shift 2 ;;\n        --min_event_count) MEC="$2"; shift 2 ;;',
        "awk_vars": '-v CW="$CW" -v ST="$ST" -v MEC="$MEC"',
        "vars_init": 'CW=""\nST=""\nMEC=""',
        "validate": '[ -z "$CW" ] || [ -z "$ST" ] || [ -z "$MEC" ]',
    },
    {
        "num": 60, "slug": "vulnerability_scan_scheduling",
        "name": "Vulnerability Scan Scheduling",
        "desc": "Central Composite design to optimize scan threads, port range, and timeout for scan duration and coverage",
        "design": "central_composite", "category": "security",
        "factors": [
            {"name": "scan_threads", "levels": ["2", "32"], "type": "continuous", "unit": "threads", "description": "Number of parallel scan threads"},
            {"name": "port_range_size", "levels": ["100", "65535"], "type": "continuous", "unit": "ports", "description": "Number of ports to scan"},
            {"name": "timeout_ms", "levels": ["500", "10000"], "type": "continuous", "unit": "ms", "description": "Per-port scan timeout"},
        ],
        "fixed": {"scanner": "openvas", "target_network": "10.0.0.0/16"},
        "responses": [
            {"name": "scan_duration_min", "optimize": "minimize", "unit": "min", "description": "Total scan duration"},
            {"name": "coverage_pct", "optimize": "maximize", "unit": "%", "description": "Network scan coverage"},
        ],
        "model": """
    st = (ST - 17) / 15;
    pr = (PR - 32817.5) / 32717.5;
    to = (TO - 5250) / 4750;
    dur = 60 - 20*st + 30*pr + 15*to + 8*st*st + 5*pr*pr - 4*st*pr + 3*pr*to;
    cov = 75 + 8*st + 5*pr + 10*to - 3*st*st - 2*pr*pr - 4*to*to + 2*st*to;
    if (dur < 2) dur = 2; if (cov > 100) cov = 100; if (cov < 30) cov = 30;
    printf "{\\"scan_duration_min\\": %.1f, \\"coverage_pct\\": %.1f}", dur + n1*4, cov + n2*2;
""",
        "factor_cases": '--scan_threads) ST="$2"; shift 2 ;;\n        --port_range_size) PR="$2"; shift 2 ;;\n        --timeout_ms) TO="$2"; shift 2 ;;',
        "awk_vars": '-v ST="$ST" -v PR="$PR" -v TO="$TO"',
        "vars_init": 'ST=""\nPR=""\nTO=""',
        "validate": '[ -z "$ST" ] || [ -z "$PR" ] || [ -z "$TO" ]',
    },
    {
        "num": 61, "slug": "zero_trust_policy_eval",
        "name": "Zero Trust Policy Evaluation",
        "desc": "Fractional factorial of 5 zero trust parameters for auth latency and security score",
        "design": "fractional_factorial", "category": "security",
        "factors": [
            {"name": "policy_cache_ttl", "levels": ["10", "300"], "type": "continuous", "unit": "sec", "description": "Policy decision cache TTL"},
            {"name": "context_attributes", "levels": ["3", "12"], "type": "continuous", "unit": "count", "description": "Number of context attributes evaluated"},
            {"name": "risk_score_weight", "levels": ["0.1", "0.9"], "type": "continuous", "unit": "weight", "description": "Risk score weight in policy decision"},
            {"name": "session_timeout", "levels": ["300", "3600"], "type": "continuous", "unit": "sec", "description": "Session timeout duration"},
            {"name": "mfa_frequency", "levels": ["1", "24"], "type": "continuous", "unit": "hours", "description": "MFA re-authentication frequency"},
        ],
        "fixed": {"identity_provider": "okta", "policy_engine": "opa"},
        "responses": [
            {"name": "auth_latency_ms", "optimize": "minimize", "unit": "ms", "description": "Authentication decision latency"},
            {"name": "security_score", "optimize": "maximize", "unit": "score", "description": "Composite security posture score"},
        ],
        "model": """
    pct = (PCT - 155) / 145;
    ca = (CA - 7.5) / 4.5;
    rsw = (RSW - 0.5) / 0.4;
    sto = (STO - 1950) / 1650;
    mfa = (MFA - 12.5) / 11.5;
    lat = 25 - 12*pct + 8*ca + 3*rsw + 2*sto + 4*mfa + 2*pct*pct + 3*ca*ca - 2*pct*ca;
    sec = 72 - 5*pct + 8*ca + 10*rsw - 6*sto - 8*mfa + 3*rsw*ca - 2*sto*mfa;
    if (lat < 2) lat = 2; if (sec > 100) sec = 100; if (sec < 20) sec = 20;
    printf "{\\"auth_latency_ms\\": %.1f, \\"security_score\\": %.1f}", lat + n1*2, sec + n2*3;
""",
        "factor_cases": '--policy_cache_ttl) PCT="$2"; shift 2 ;;\n        --context_attributes) CA="$2"; shift 2 ;;\n        --risk_score_weight) RSW="$2"; shift 2 ;;\n        --session_timeout) STO="$2"; shift 2 ;;\n        --mfa_frequency) MFA="$2"; shift 2 ;;',
        "awk_vars": '-v PCT="$PCT" -v CA="$CA" -v RSW="$RSW" -v STO="$STO" -v MFA="$MFA"',
        "vars_init": 'PCT=""\nCA=""\nRSW=""\nSTO=""\nMFA=""',
        "validate": '[ -z "$PCT" ] || [ -z "$CA" ] || [ -z "$RSW" ] || [ -z "$STO" ] || [ -z "$MFA" ]',
    },
    {
        "num": 62, "slug": "certificate_rotation",
        "name": "Certificate Rotation Strategy",
        "desc": "Full factorial of cert lifetime, renewal window, and stapling cache for rotation success and downtime",
        "design": "full_factorial", "category": "security",
        "factors": [
            {"name": "cert_lifetime_days", "levels": ["30", "90"], "type": "continuous", "unit": "days", "description": "Certificate validity lifetime"},
            {"name": "renewal_window_pct", "levels": ["10", "30"], "type": "continuous", "unit": "%", "description": "Renewal window as percentage of lifetime"},
            {"name": "stapling_cache_sec", "levels": ["300", "3600"], "type": "continuous", "unit": "sec", "description": "OCSP stapling cache duration"},
        ],
        "fixed": {"ca": "letsencrypt", "key_type": "ecdsa_p256"},
        "responses": [
            {"name": "rotation_success_rate", "optimize": "maximize", "unit": "%", "description": "Certificate rotation success rate"},
            {"name": "downtime_sec", "optimize": "minimize", "unit": "sec", "description": "Downtime during rotation"},
        ],
        "model": """
    cl = (CL - 60) / 30;
    rw = (RW - 20) / 10;
    sc = (SC - 1950) / 1650;
    suc = 96 + 2*cl + 3*rw + 1*sc - 0.8*cl*cl - 0.5*rw*rw + 0.5*cl*rw;
    dt = 5 - 1.5*cl - 2*rw - 0.8*sc + 0.6*cl*cl + 0.4*rw*rw + 0.3*cl*rw;
    if (suc > 100) suc = 100; if (suc < 80) suc = 80;
    if (dt < 0) dt = 0;
    printf "{\\"rotation_success_rate\\": %.2f, \\"downtime_sec\\": %.1f}", suc + n1*0.5, dt + n2*0.8;
""",
        "factor_cases": '--cert_lifetime_days) CL="$2"; shift 2 ;;\n        --renewal_window_pct) RW="$2"; shift 2 ;;\n        --stapling_cache_sec) SC="$2"; shift 2 ;;',
        "awk_vars": '-v CL="$CL" -v RW="$RW" -v SC="$SC"',
        "vars_init": 'CL=""\nRW=""\nSC=""',
        "validate": '[ -z "$CL" ] || [ -z "$RW" ] || [ -z "$SC" ]',
    },
    {
        "num": 63, "slug": "ids_signature_tuning",
        "name": "IDS Signature Tuning",
        "desc": "Latin Hypercube exploration of 4 IDS parameters for detection accuracy and packet drop rate",
        "design": "latin_hypercube", "category": "security",
        "factors": [
            {"name": "signature_pool_size", "levels": ["1000", "50000"], "type": "continuous", "unit": "sigs", "description": "Active signature pool size"},
            {"name": "pattern_match_depth", "levels": ["256", "4096"], "type": "continuous", "unit": "bytes", "description": "Pattern matching inspection depth"},
            {"name": "stream_reassembly_depth", "levels": ["4096", "65536"], "type": "continuous", "unit": "bytes", "description": "TCP stream reassembly depth"},
            {"name": "pcap_buffer_mb", "levels": ["64", "1024"], "type": "continuous", "unit": "MB", "description": "Packet capture ring buffer size"},
        ],
        "fixed": {"ids_engine": "suricata", "ruleset": "et_open"},
        "responses": [
            {"name": "detection_accuracy_pct", "optimize": "maximize", "unit": "%", "description": "Signature detection accuracy"},
            {"name": "packet_drop_rate", "optimize": "minimize", "unit": "%", "description": "Packet drop rate under load"},
        ],
        "model": """
    sps = (SPS - 25500) / 24500;
    pmd = (PMD - 2176) / 1920;
    srd = (SRD - 34816) / 30720;
    pb = (PB - 544) / 480;
    acc = 85 + 5*sps + 4*pmd + 3*srd + 1*pb - 2*sps*sps - 1.5*pmd*pmd + 1.5*sps*pmd;
    drop = 5 + 4*sps + 3*pmd + 2*srd - 3*pb + 1.5*sps*pmd - 0.8*pb*srd;
    if (acc > 100) acc = 100; if (acc < 50) acc = 50;
    if (drop < 0.01) drop = 0.01;
    printf "{\\"detection_accuracy_pct\\": %.1f, \\"packet_drop_rate\\": %.2f}", acc + n1*2, drop + n2*0.8;
""",
        "factor_cases": '--signature_pool_size) SPS="$2"; shift 2 ;;\n        --pattern_match_depth) PMD="$2"; shift 2 ;;\n        --stream_reassembly_depth) SRD="$2"; shift 2 ;;\n        --pcap_buffer_mb) PB="$2"; shift 2 ;;',
        "awk_vars": '-v SPS="$SPS" -v PMD="$PMD" -v SRD="$SRD" -v PB="$PB"',
        "vars_init": 'SPS=""\nPMD=""\nSRD=""\nPB=""',
        "validate": '[ -z "$SPS" ] || [ -z "$PMD" ] || [ -z "$SRD" ] || [ -z "$PB" ]',
    },
    {
        "num": 64, "slug": "secrets_vault_performance",
        "name": "Secrets Vault Performance",
        "desc": "Box-Behnken design to optimize vault seal wrap threads, cache size, and lease TTL for latency and throughput",
        "design": "box_behnken", "category": "security",
        "factors": [
            {"name": "seal_wrap_threads", "levels": ["1", "8"], "type": "continuous", "unit": "threads", "description": "Seal wrap worker threads"},
            {"name": "cache_size_mb", "levels": ["64", "512"], "type": "continuous", "unit": "MB", "description": "Secret cache size"},
            {"name": "lease_ttl_sec", "levels": ["30", "600"], "type": "continuous", "unit": "sec", "description": "Secret lease time-to-live"},
        ],
        "fixed": {"vault_backend": "consul", "seal_type": "awskms"},
        "responses": [
            {"name": "read_latency_ms", "optimize": "minimize", "unit": "ms", "description": "Secret read latency"},
            {"name": "throughput_ops", "optimize": "maximize", "unit": "ops/s", "description": "Secret operations throughput"},
        ],
        "model": """
    sw = (SW - 4.5) / 3.5;
    csz = (CSZ - 288) / 224;
    lt = (LT - 315) / 285;
    lat = 15 - 4*sw - 6*csz + 2*lt + 2*sw*sw + 3*csz*csz + 1*lt*lt - 1.5*sw*csz;
    thr = 5000 + 1500*sw + 2000*csz - 500*lt - 600*sw*sw - 800*csz*csz + 400*sw*csz;
    if (lat < 0.5) lat = 0.5; if (thr < 100) thr = 100;
    printf "{\\"read_latency_ms\\": %.1f, \\"throughput_ops\\": %.0f}", lat + n1*1.5, thr + n2*300;
""",
        "factor_cases": '--seal_wrap_threads) SW="$2"; shift 2 ;;\n        --cache_size_mb) CSZ="$2"; shift 2 ;;\n        --lease_ttl_sec) LT="$2"; shift 2 ;;',
        "awk_vars": '-v SW="$SW" -v CSZ="$CSZ" -v LT="$LT"',
        "vars_init": 'SW=""\nCSZ=""\nLT=""',
        "validate": '[ -z "$SW" ] || [ -z "$CSZ" ] || [ -z "$LT" ]',
    },
    {
        "num": 65, "slug": "audit_log_pipeline",
        "name": "Audit Log Pipeline",
        "desc": "Fractional factorial of 5 audit log pipeline parameters for ingest rate and latency",
        "design": "fractional_factorial", "category": "security",
        "factors": [
            {"name": "batch_size", "levels": ["100", "10000"], "type": "continuous", "unit": "events", "description": "Events per batch"},
            {"name": "flush_interval_ms", "levels": ["100", "5000"], "type": "continuous", "unit": "ms", "description": "Flush interval"},
            {"name": "compression_level", "levels": ["1", "9"], "type": "continuous", "unit": "level", "description": "Compression level"},
            {"name": "buffer_pool_mb", "levels": ["32", "512"], "type": "continuous", "unit": "MB", "description": "In-memory buffer pool size"},
            {"name": "writer_threads", "levels": ["1", "8"], "type": "continuous", "unit": "threads", "description": "Parallel writer threads"},
        ],
        "fixed": {"storage": "s3", "format": "json_lines"},
        "responses": [
            {"name": "ingest_rate_eps", "optimize": "maximize", "unit": "events/s", "description": "Event ingestion rate"},
            {"name": "end_to_end_latency_ms", "optimize": "minimize", "unit": "ms", "description": "End-to-end event latency"},
        ],
        "model": """
    bs = (BS - 5050) / 4950;
    fi = (FI - 2550) / 2450;
    cl = (CL - 5) / 4;
    bp = (BP - 272) / 240;
    wt = (WT - 4.5) / 3.5;
    rate = 50000 + 15000*bs - 5000*fi - 3000*cl + 10000*bp + 12000*wt - 4000*bs*bs + 3000*bs*wt - 2000*cl*wt;
    lat = 200 - 40*bs + 80*fi + 20*cl - 30*bp - 25*wt + 15*fi*fi + 10*bs*fi - 8*bp*wt;
    if (rate < 1000) rate = 1000; if (lat < 5) lat = 5;
    printf "{\\"ingest_rate_eps\\": %.0f, \\"end_to_end_latency_ms\\": %.0f}", rate + n1*3000, lat + n2*15;
""",
        "factor_cases": '--batch_size) BS="$2"; shift 2 ;;\n        --flush_interval_ms) FI="$2"; shift 2 ;;\n        --compression_level) CL="$2"; shift 2 ;;\n        --buffer_pool_mb) BP="$2"; shift 2 ;;\n        --writer_threads) WT="$2"; shift 2 ;;',
        "awk_vars": '-v BS="$BS" -v FI="$FI" -v CL="$CL" -v BP="$BP" -v WT="$WT"',
        "vars_init": 'BS=""\nFI=""\nCL=""\nBP=""\nWT=""',
        "validate": '[ -z "$BS" ] || [ -z "$FI" ] || [ -z "$CL" ] || [ -z "$BP" ] || [ -z "$WT" ]',
    },
    {
        "num": 66, "slug": "container_image_scanning",
        "name": "Container Image Scanning",
        "desc": "Central Composite design to optimize layer parallelism, vuln DB cache, and max image size for scan time and CVE detection",
        "design": "central_composite", "category": "security",
        "factors": [
            {"name": "layer_parallelism", "levels": ["1", "8"], "type": "continuous", "unit": "threads", "description": "Parallel layer scan threads"},
            {"name": "vuln_db_cache_hours", "levels": ["1", "24"], "type": "continuous", "unit": "hours", "description": "Vulnerability DB cache freshness"},
            {"name": "max_image_size_gb", "levels": ["1", "10"], "type": "continuous", "unit": "GB", "description": "Maximum image size to scan"},
        ],
        "fixed": {"scanner": "trivy", "registry": "ecr"},
        "responses": [
            {"name": "scan_time_sec", "optimize": "minimize", "unit": "sec", "description": "Per-image scan time"},
            {"name": "cve_detection_rate", "optimize": "maximize", "unit": "%", "description": "CVE detection rate"},
        ],
        "model": """
    lp = (LP - 4.5) / 3.5;
    vdc = (VDC - 12.5) / 11.5;
    mis = (MIS - 5.5) / 4.5;
    st = 45 - 15*lp + 5*vdc + 20*mis + 4*lp*lp + 2*vdc*vdc + 3*mis*mis - 3*lp*mis;
    det = 92 + 2*lp - 4*vdc + 1*mis - 1*lp*lp - 2*vdc*vdc + 0.5*lp*vdc;
    if (st < 3) st = 3; if (det > 100) det = 100; if (det < 60) det = 60;
    printf "{\\"scan_time_sec\\": %.1f, \\"cve_detection_rate\\": %.1f}", st + n1*3, det + n2*1.5;
""",
        "factor_cases": '--layer_parallelism) LP="$2"; shift 2 ;;\n        --vuln_db_cache_hours) VDC="$2"; shift 2 ;;\n        --max_image_size_gb) MIS="$2"; shift 2 ;;',
        "awk_vars": '-v LP="$LP" -v VDC="$VDC" -v MIS="$MIS"',
        "vars_init": 'LP=""\nVDC=""\nMIS=""',
        "validate": '[ -z "$LP" ] || [ -z "$VDC" ] || [ -z "$MIS" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: IoT & Embedded Systems (67-76)
    # ══════════════════════════════════════════════════
    {
        "num": 67, "slug": "smart_sensor_sampling",
        "name": "Smart Sensor Sampling",
        "desc": "Fractional factorial of 5 sensor sampling parameters for measurement accuracy and power consumption",
        "design": "fractional_factorial", "category": "iot",
        "factors": [
            {"name": "sample_rate_hz", "levels": ["1", "100"], "type": "continuous", "unit": "Hz", "description": "ADC sample rate"},
            {"name": "adc_resolution_bits", "levels": ["8", "16"], "type": "continuous", "unit": "bits", "description": "ADC resolution"},
            {"name": "averaging_window", "levels": ["1", "32"], "type": "continuous", "unit": "samples", "description": "Moving average window size"},
            {"name": "sleep_mode_depth", "levels": ["1", "4"], "type": "continuous", "unit": "level", "description": "Deep sleep mode level"},
            {"name": "wakeup_interval_sec", "levels": ["1", "60"], "type": "continuous", "unit": "sec", "description": "Wakeup interval from sleep"},
        ],
        "fixed": {"mcu": "esp32", "sensor": "bme280"},
        "responses": [
            {"name": "measurement_accuracy_pct", "optimize": "maximize", "unit": "%", "description": "Measurement accuracy percentage"},
            {"name": "power_consumption_mw", "optimize": "minimize", "unit": "mW", "description": "Average power consumption"},
        ],
        "model": """
    sr = (SR - 50.5) / 49.5;
    adc = (ADC - 12) / 4;
    aw = (AW - 16.5) / 15.5;
    smd = (SMD - 2.5) / 1.5;
    wi = (WI - 30.5) / 29.5;
    acc = 88 + 4*sr + 6*adc + 5*aw - 1*smd - 2*wi - 1.5*sr*sr - 1*adc*adc + 2*sr*adc + 1.5*aw*sr;
    pwr = 50 + 25*sr + 10*adc - 2*aw - 15*smd - 20*wi + 5*sr*adc - 3*smd*wi;
    if (acc > 100) acc = 100; if (acc < 50) acc = 50;
    if (pwr < 0.5) pwr = 0.5;
    printf "{\\"measurement_accuracy_pct\\": %.1f, \\"power_consumption_mw\\": %.1f}", acc + n1*1.5, pwr + n2*3;
""",
        "factor_cases": '--sample_rate_hz) SR="$2"; shift 2 ;;\n        --adc_resolution_bits) ADC="$2"; shift 2 ;;\n        --averaging_window) AW="$2"; shift 2 ;;\n        --sleep_mode_depth) SMD="$2"; shift 2 ;;\n        --wakeup_interval_sec) WI="$2"; shift 2 ;;',
        "awk_vars": '-v SR="$SR" -v ADC="$ADC" -v AW="$AW" -v SMD="$SMD" -v WI="$WI"',
        "vars_init": 'SR=""\nADC=""\nAW=""\nSMD=""\nWI=""',
        "validate": '[ -z "$SR" ] || [ -z "$ADC" ] || [ -z "$AW" ] || [ -z "$SMD" ] || [ -z "$WI" ]',
    },
    {
        "num": 68, "slug": "ble_mesh_topology",
        "name": "BLE Mesh Topology",
        "desc": "Box-Behnken design to tune relay count, TTL hops, and publish interval for message delivery and latency",
        "design": "box_behnken", "category": "iot",
        "factors": [
            {"name": "relay_count", "levels": ["2", "10"], "type": "continuous", "unit": "nodes", "description": "Number of relay nodes in mesh"},
            {"name": "ttl_hops", "levels": ["2", "8"], "type": "continuous", "unit": "hops", "description": "Message TTL in hops"},
            {"name": "publish_interval_ms", "levels": ["100", "2000"], "type": "continuous", "unit": "ms", "description": "Message publish interval"},
        ],
        "fixed": {"ble_version": "5.0", "mesh_profile": "sig_mesh"},
        "responses": [
            {"name": "message_delivery_pct", "optimize": "maximize", "unit": "%", "description": "Message delivery success rate"},
            {"name": "network_latency_ms", "optimize": "minimize", "unit": "ms", "description": "End-to-end network latency"},
        ],
        "model": """
    rc = (RC - 6) / 4;
    ttl = (TTL - 5) / 3;
    pi = (PI - 1050) / 950;
    del = 92 + 4*rc + 3*ttl - 2*pi - 2*rc*rc - 1.5*ttl*ttl + 1*rc*ttl + 0.8*pi*pi;
    lat = 80 + 15*rc + 20*ttl + 30*pi - 5*rc*rc + 8*ttl*ttl + 4*rc*ttl;
    if (del > 100) del = 100; if (del < 60) del = 60;
    if (lat < 10) lat = 10;
    printf "{\\"message_delivery_pct\\": %.1f, \\"network_latency_ms\\": %.0f}", del + n1*1.5, lat + n2*8;
""",
        "factor_cases": '--relay_count) RC="$2"; shift 2 ;;\n        --ttl_hops) TTL="$2"; shift 2 ;;\n        --publish_interval_ms) PI="$2"; shift 2 ;;',
        "awk_vars": '-v RC="$RC" -v TTL="$TTL" -v PI="$PI"',
        "vars_init": 'RC=""\nTTL=""\nPI=""',
        "validate": '[ -z "$RC" ] || [ -z "$TTL" ] || [ -z "$PI" ]',
    },
    {
        "num": 69, "slug": "rtos_task_priority",
        "name": "RTOS Task Priority",
        "desc": "Full factorial of task priority levels, tick rate, stack size, and preemption threshold for latency and utilization",
        "design": "full_factorial", "category": "iot",
        "factors": [
            {"name": "task_priority_levels", "levels": ["4", "16"], "type": "continuous", "unit": "levels", "description": "Number of priority levels"},
            {"name": "tick_rate_hz", "levels": ["100", "1000"], "type": "continuous", "unit": "Hz", "description": "RTOS tick rate"},
            {"name": "stack_size_bytes", "levels": ["512", "4096"], "type": "continuous", "unit": "bytes", "description": "Task stack size"},
            {"name": "preemption_threshold", "levels": ["1", "8"], "type": "continuous", "unit": "level", "description": "Preemption threshold level"},
        ],
        "fixed": {"rtos": "freertos", "mcu_clock": "240MHz"},
        "responses": [
            {"name": "worst_case_latency_us", "optimize": "minimize", "unit": "us", "description": "Worst case task scheduling latency"},
            {"name": "cpu_utilization_pct", "optimize": "maximize", "unit": "%", "description": "CPU utilization efficiency"},
        ],
        "model": """
    tpl = (TPL - 10) / 6;
    tr = (TR - 550) / 450;
    ss = (SS - 2304) / 1792;
    pt = (PT - 4.5) / 3.5;
    lat = 50 - 10*tpl - 20*tr - 5*ss - 8*pt + 4*tpl*tpl + 6*tr*tr + 2*tpl*tr + 3*pt*pt;
    util = 65 + 8*tpl + 10*tr - 5*ss + 4*pt - 3*tpl*tpl - 4*tr*tr + 2*tpl*pt;
    if (lat < 1) lat = 1; if (util > 100) util = 100; if (util < 20) util = 20;
    printf "{\\"worst_case_latency_us\\": %.0f, \\"cpu_utilization_pct\\": %.1f}", lat + n1*5, util + n2*3;
""",
        "factor_cases": '--task_priority_levels) TPL="$2"; shift 2 ;;\n        --tick_rate_hz) TR="$2"; shift 2 ;;\n        --stack_size_bytes) SS="$2"; shift 2 ;;\n        --preemption_threshold) PT="$2"; shift 2 ;;',
        "awk_vars": '-v TPL="$TPL" -v TR="$TR" -v SS="$SS" -v PT="$PT"',
        "vars_init": 'TPL=""\nTR=""\nSS=""\nPT=""',
        "validate": '[ -z "$TPL" ] || [ -z "$TR" ] || [ -z "$SS" ] || [ -z "$PT" ]',
    },
    {
        "num": 70, "slug": "lorawan_parameters",
        "name": "LoRaWAN Parameters",
        "desc": "Central Composite design to optimize spreading factor, TX power, and coding rate for range and battery life",
        "design": "central_composite", "category": "iot",
        "factors": [
            {"name": "spreading_factor", "levels": ["7", "12"], "type": "continuous", "unit": "SF", "description": "LoRa spreading factor"},
            {"name": "tx_power_dbm", "levels": ["2", "20"], "type": "continuous", "unit": "dBm", "description": "Transmit power level"},
            {"name": "coding_rate", "levels": ["5", "8"], "type": "continuous", "unit": "CR", "description": "Forward error correction coding rate (4/x)"},
        ],
        "fixed": {"frequency": "915MHz", "bandwidth": "125kHz"},
        "responses": [
            {"name": "range_km", "optimize": "maximize", "unit": "km", "description": "Communication range"},
            {"name": "battery_life_days", "optimize": "maximize", "unit": "days", "description": "Estimated battery life"},
        ],
        "model": """
    sf = (SF - 9.5) / 2.5;
    tp = (TP - 11) / 9;
    cr = (CR - 6.5) / 1.5;
    rng = 5 + 3*sf + 2*tp + 0.8*cr + 0.5*sf*tp - 0.4*sf*sf + 0.3*tp*cr;
    bat = 365 - 80*sf - 60*tp - 20*cr + 15*sf*sf + 10*tp*tp - 5*sf*tp;
    if (rng < 0.5) rng = 0.5; if (bat < 10) bat = 10;
    printf "{\\"range_km\\": %.1f, \\"battery_life_days\\": %.0f}", rng + n1*0.5, bat + n2*20;
""",
        "factor_cases": '--spreading_factor) SF="$2"; shift 2 ;;\n        --tx_power_dbm) TP="$2"; shift 2 ;;\n        --coding_rate) CR="$2"; shift 2 ;;',
        "awk_vars": '-v SF="$SF" -v TP="$TP" -v CR="$CR"',
        "vars_init": 'SF=""\nTP=""\nCR=""',
        "validate": '[ -z "$SF" ] || [ -z "$TP" ] || [ -z "$CR" ]',
    },
    {
        "num": 71, "slug": "edge_inference_quantization",
        "name": "Edge Inference Quantization",
        "desc": "Plackett-Burman screening of 6 edge ML inference parameters for latency and accuracy loss",
        "design": "plackett_burman", "category": "iot",
        "factors": [
            {"name": "weight_bits", "levels": ["4", "16"], "type": "continuous", "unit": "bits", "description": "Weight quantization bit width"},
            {"name": "activation_bits", "levels": ["4", "16"], "type": "continuous", "unit": "bits", "description": "Activation quantization bit width"},
            {"name": "batch_size", "levels": ["1", "32"], "type": "continuous", "unit": "samples", "description": "Inference batch size"},
            {"name": "num_threads", "levels": ["1", "4"], "type": "continuous", "unit": "threads", "description": "Inference worker threads"},
            {"name": "cache_size_kb", "levels": ["64", "512"], "type": "continuous", "unit": "KB", "description": "Model cache size"},
            {"name": "memory_pool_mb", "levels": ["16", "128"], "type": "continuous", "unit": "MB", "description": "Runtime memory pool"},
        ],
        "fixed": {"framework": "tflite", "model": "mobilenet_v2"},
        "responses": [
            {"name": "inference_latency_ms", "optimize": "minimize", "unit": "ms", "description": "Per-sample inference latency"},
            {"name": "accuracy_loss_pct", "optimize": "minimize", "unit": "%", "description": "Accuracy degradation from quantization"},
        ],
        "model": """
    wb = (WB - 10) / 6;
    ab = (AB - 10) / 6;
    bs = (BS - 16.5) / 15.5;
    nt = (NT - 2.5) / 1.5;
    ck = (CK - 288) / 224;
    mp = (MP - 72) / 56;
    lat = 25 - 5*wb - 4*ab + 8*bs - 6*nt - 3*ck - 2*mp + 2*wb*ab + 1.5*bs*nt;
    aloss = 5 - 3*wb - 2.5*ab + 0.3*bs - 0.1*nt - 0.2*ck + 0.1*mp + 1.5*wb*ab + 0.5*wb*wb;
    if (lat < 1) lat = 1; if (aloss < 0.1) aloss = 0.1;
    printf "{\\"inference_latency_ms\\": %.1f, \\"accuracy_loss_pct\\": %.2f}", lat + n1*2, aloss + n2*0.3;
""",
        "factor_cases": '--weight_bits) WB="$2"; shift 2 ;;\n        --activation_bits) AB="$2"; shift 2 ;;\n        --batch_size) BS="$2"; shift 2 ;;\n        --num_threads) NT="$2"; shift 2 ;;\n        --cache_size_kb) CK="$2"; shift 2 ;;\n        --memory_pool_mb) MP="$2"; shift 2 ;;',
        "awk_vars": '-v WB="$WB" -v AB="$AB" -v BS="$BS" -v NT="$NT" -v CK="$CK" -v MP="$MP"',
        "vars_init": 'WB=""\nAB=""\nBS=""\nNT=""\nCK=""\nMP=""',
        "validate": '[ -z "$WB" ] || [ -z "$AB" ] || [ -z "$BS" ] || [ -z "$NT" ]',
    },
    {
        "num": 72, "slug": "mqtt_broker_tuning",
        "name": "MQTT Broker Tuning",
        "desc": "Latin Hypercube exploration of 4 MQTT broker parameters for message throughput and memory usage",
        "design": "latin_hypercube", "category": "iot",
        "factors": [
            {"name": "max_connections", "levels": ["100", "10000"], "type": "continuous", "unit": "conns", "description": "Maximum concurrent connections"},
            {"name": "message_queue_depth", "levels": ["100", "5000"], "type": "continuous", "unit": "msgs", "description": "Per-client message queue depth"},
            {"name": "keepalive_sec", "levels": ["15", "300"], "type": "continuous", "unit": "sec", "description": "Client keepalive interval"},
            {"name": "qos_level", "levels": ["0", "2"], "type": "categorical", "unit": "", "description": "MQTT QoS level"},
        ],
        "fixed": {"broker": "mosquitto", "protocol": "mqtt_v5"},
        "responses": [
            {"name": "message_throughput_kps", "optimize": "maximize", "unit": "kmsg/s", "description": "Message throughput in thousands per second"},
            {"name": "memory_usage_mb", "optimize": "minimize", "unit": "MB", "description": "Broker memory usage"},
        ],
        "model": """
    mc = (MC - 5050) / 4950;
    mqd = (MQD - 2550) / 2450;
    ka = (KA - 157.5) / 142.5;
    if (QOS == "0") qos = -1; else if (QOS == "1") qos = 0; else qos = 1;
    thr = 50 + 15*mc + 5*mqd - 2*ka - 12*qos - 5*mc*mc + 3*mc*mqd - 2*qos*mc;
    mem = 256 + 100*mc + 80*mqd + 10*ka + 40*qos + 20*mc*mqd + 15*mqd*mqd;
    if (thr < 1) thr = 1; if (mem < 32) mem = 32;
    printf "{\\"message_throughput_kps\\": %.1f, \\"memory_usage_mb\\": %.0f}", thr + n1*3, mem + n2*20;
""",
        "factor_cases": '--max_connections) MC="$2"; shift 2 ;;\n        --message_queue_depth) MQD="$2"; shift 2 ;;\n        --keepalive_sec) KA="$2"; shift 2 ;;\n        --qos_level) QOS="$2"; shift 2 ;;',
        "awk_vars": '-v MC="$MC" -v MQD="$MQD" -v KA="$KA" -v QOS="$QOS"',
        "vars_init": 'MC=""\nMQD=""\nKA=""\nQOS=""',
        "validate": '[ -z "$MC" ] || [ -z "$MQD" ] || [ -z "$KA" ] || [ -z "$QOS" ]',
    },
    {
        "num": 73, "slug": "pwm_motor_control",
        "name": "PWM Motor Control",
        "desc": "Box-Behnken design to tune PWM frequency, dead time, and PID gain for torque ripple and efficiency",
        "design": "box_behnken", "category": "iot",
        "factors": [
            {"name": "pwm_frequency_khz", "levels": ["5", "50"], "type": "continuous", "unit": "kHz", "description": "PWM switching frequency"},
            {"name": "dead_time_ns", "levels": ["100", "2000"], "type": "continuous", "unit": "ns", "description": "Dead time between high/low side switching"},
            {"name": "pid_gain_kp", "levels": ["0.5", "10.0"], "type": "continuous", "unit": "gain", "description": "PID proportional gain"},
        ],
        "fixed": {"motor_type": "bldc", "driver": "drv8305"},
        "responses": [
            {"name": "torque_ripple_pct", "optimize": "minimize", "unit": "%", "description": "Torque ripple percentage"},
            {"name": "efficiency_pct", "optimize": "maximize", "unit": "%", "description": "Motor drive efficiency"},
        ],
        "model": """
    pf = (PF - 27.5) / 22.5;
    dt = (DT - 1050) / 950;
    kp = (KP - 5.25) / 4.75;
    rip = 8 - 3*pf + 2*dt - 4*kp + 2*pf*pf + 1.5*dt*dt + 3*kp*kp - 1*pf*kp + 0.8*dt*kp;
    eff = 88 + 4*pf - 3*dt + 2*kp - 2*pf*pf - 1.5*dt*dt - 1*kp*kp + 1*pf*kp;
    if (rip < 0.5) rip = 0.5; if (eff > 98) eff = 98; if (eff < 60) eff = 60;
    printf "{\\"torque_ripple_pct\\": %.1f, \\"efficiency_pct\\": %.1f}", rip + n1*0.8, eff + n2*1.5;
""",
        "factor_cases": '--pwm_frequency_khz) PF="$2"; shift 2 ;;\n        --dead_time_ns) DT="$2"; shift 2 ;;\n        --pid_gain_kp) KP="$2"; shift 2 ;;',
        "awk_vars": '-v PF="$PF" -v DT="$DT" -v KP="$KP"',
        "vars_init": 'PF=""\nDT=""\nKP=""',
        "validate": '[ -z "$PF" ] || [ -z "$DT" ] || [ -z "$KP" ]',
    },
    {
        "num": 74, "slug": "zigbee_network_formation",
        "name": "Zigbee Network Formation",
        "desc": "Fractional factorial of 5 Zigbee network parameters for join time and stability",
        "design": "fractional_factorial", "category": "iot",
        "factors": [
            {"name": "scan_duration_exp", "levels": ["2", "7"], "type": "continuous", "unit": "exp", "description": "Channel scan duration exponent"},
            {"name": "max_children", "levels": ["4", "20"], "type": "continuous", "unit": "nodes", "description": "Maximum children per router"},
            {"name": "link_cost_threshold", "levels": ["1", "7"], "type": "continuous", "unit": "cost", "description": "Link cost threshold for neighbor table"},
            {"name": "route_table_size", "levels": ["10", "50"], "type": "continuous", "unit": "entries", "description": "Routing table size"},
            {"name": "poll_rate_ms", "levels": ["100", "2000"], "type": "continuous", "unit": "ms", "description": "End device poll rate"},
        ],
        "fixed": {"zigbee_stack": "z_stack", "channel": "15"},
        "responses": [
            {"name": "join_time_sec", "optimize": "minimize", "unit": "sec", "description": "Device join time"},
            {"name": "network_stability_pct", "optimize": "maximize", "unit": "%", "description": "Network stability percentage"},
        ],
        "model": """
    sd = (SD - 4.5) / 2.5;
    mc = (MC - 12) / 8;
    lc = (LC - 4) / 3;
    rt = (RT - 30) / 20;
    pr = (PR - 1050) / 950;
    jt = 15 + 5*sd - 3*mc + 2*lc - 2*rt + 4*pr + 1.5*sd*sd + 2*sd*pr - 1*mc*rt;
    stab = 88 + 3*sd + 5*mc - 4*lc + 4*rt - 3*pr - 1.5*sd*sd - 2*mc*mc + 1.5*mc*rt;
    if (jt < 1) jt = 1; if (stab > 100) stab = 100; if (stab < 50) stab = 50;
    printf "{\\"join_time_sec\\": %.1f, \\"network_stability_pct\\": %.1f}", jt + n1*2, stab + n2*2;
""",
        "factor_cases": '--scan_duration_exp) SD="$2"; shift 2 ;;\n        --max_children) MC="$2"; shift 2 ;;\n        --link_cost_threshold) LC="$2"; shift 2 ;;\n        --route_table_size) RT="$2"; shift 2 ;;\n        --poll_rate_ms) PR="$2"; shift 2 ;;',
        "awk_vars": '-v SD="$SD" -v MC="$MC" -v LC="$LC" -v RT="$RT" -v PR="$PR"',
        "vars_init": 'SD=""\nMC=""\nLC=""\nRT=""\nPR=""',
        "validate": '[ -z "$SD" ] || [ -z "$MC" ] || [ -z "$LC" ] || [ -z "$RT" ] || [ -z "$PR" ]',
    },
    {
        "num": 75, "slug": "firmware_ota_strategy",
        "name": "Firmware OTA Strategy",
        "desc": "Full factorial of chunk size, retry count, and delta encoding for update time and success rate",
        "design": "full_factorial", "category": "iot",
        "factors": [
            {"name": "chunk_size_kb", "levels": ["1", "64"], "type": "continuous", "unit": "KB", "description": "OTA transfer chunk size"},
            {"name": "retry_count", "levels": ["1", "5"], "type": "continuous", "unit": "retries", "description": "Chunk retry count on failure"},
            {"name": "delta_encoding", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Delta/differential firmware updates"},
        ],
        "fixed": {"transport": "coap", "compression": "lz4"},
        "responses": [
            {"name": "update_time_sec", "optimize": "minimize", "unit": "sec", "description": "Total firmware update time"},
            {"name": "success_rate_pct", "optimize": "maximize", "unit": "%", "description": "Update success rate"},
        ],
        "model": """
    cs = (CS - 32.5) / 31.5;
    rc = (RC - 3) / 2;
    de = (DE == "on") ? 1 : -1;
    ut = 120 - 40*cs + 10*rc - 35*de + 8*cs*cs + 3*rc*rc + 5*cs*rc - 4*cs*de;
    sr = 92 - 2*cs + 5*rc + 3*de - 1*cs*cs - 0.5*rc*rc + 1*cs*rc + 0.8*rc*de;
    if (ut < 5) ut = 5; if (sr > 100) sr = 100; if (sr < 70) sr = 70;
    printf "{\\"update_time_sec\\": %.0f, \\"success_rate_pct\\": %.1f}", ut + n1*8, sr + n2*1.5;
""",
        "factor_cases": '--chunk_size_kb) CS="$2"; shift 2 ;;\n        --retry_count) RC="$2"; shift 2 ;;\n        --delta_encoding) DE="$2"; shift 2 ;;',
        "awk_vars": '-v CS="$CS" -v RC="$RC" -v DE="$DE"',
        "vars_init": 'CS=""\nRC=""\nDE=""',
        "validate": '[ -z "$CS" ] || [ -z "$RC" ] || [ -z "$DE" ]',
    },
    {
        "num": 76, "slug": "battery_management_charging",
        "name": "Battery Management Charging",
        "desc": "Central Composite design to optimize charge current, CV threshold, and trickle cutoff for charge time and cycle life",
        "design": "central_composite", "category": "iot",
        "factors": [
            {"name": "charge_current_ma", "levels": ["500", "3000"], "type": "continuous", "unit": "mA", "description": "Constant current charging rate"},
            {"name": "cv_threshold_mv", "levels": ["3400", "3650"], "type": "continuous", "unit": "mV", "description": "Constant voltage threshold"},
            {"name": "trickle_cutoff_mv", "levels": ["2800", "3000"], "type": "continuous", "unit": "mV", "description": "Trickle charge cutoff voltage"},
        ],
        "fixed": {"chemistry": "lifepo4", "cell_count": "4s"},
        "responses": [
            {"name": "charge_time_min", "optimize": "minimize", "unit": "min", "description": "Full charge time"},
            {"name": "cycle_life_count", "optimize": "maximize", "unit": "cycles", "description": "Expected cycle life count"},
        ],
        "model": """
    cc = (CC - 1750) / 1250;
    cv = (CV - 3525) / 125;
    tc = (TC - 2900) / 100;
    ct = 90 - 30*cc + 10*cv + 5*tc + 8*cc*cc + 3*cv*cv + 2*cc*cv;
    cyc = 2000 - 400*cc - 300*cv + 100*tc + 150*cc*cc + 80*cv*cv - 50*cc*cv + 30*tc*tc;
    if (ct < 15) ct = 15; if (cyc < 200) cyc = 200;
    printf "{\\"charge_time_min\\": %.0f, \\"cycle_life_count\\": %.0f}", ct + n1*5, cyc + n2*100;
""",
        "factor_cases": '--charge_current_ma) CC="$2"; shift 2 ;;\n        --cv_threshold_mv) CV="$2"; shift 2 ;;\n        --trickle_cutoff_mv) TC="$2"; shift 2 ;;',
        "awk_vars": '-v CC="$CC" -v CV="$CV" -v TC="$TC"',
        "vars_init": 'CC=""\nCV=""\nTC=""',
        "validate": '[ -z "$CC" ] || [ -z "$CV" ] || [ -z "$TC" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: DevOps & CI/CD (77-86)
    # ══════════════════════════════════════════════════
    {
        "num": 77, "slug": "cicd_pipeline_parallelism",
        "name": "CI/CD Pipeline Parallelism",
        "desc": "Full factorial of parallel jobs, runner cores, cache strategy, and artifact compression for pipeline duration and cost",
        "design": "full_factorial", "category": "devops",
        "factors": [
            {"name": "parallel_jobs", "levels": ["1", "8"], "type": "continuous", "unit": "jobs", "description": "Number of parallel jobs"},
            {"name": "runner_cpu_cores", "levels": ["2", "8"], "type": "continuous", "unit": "cores", "description": "Runner CPU core count"},
            {"name": "cache_strategy", "levels": ["none", "aggressive"], "type": "categorical", "unit": "", "description": "Build cache strategy"},
            {"name": "artifact_compression", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Artifact compression enabled"},
        ],
        "fixed": {"ci_platform": "github_actions", "repo_size": "medium"},
        "responses": [
            {"name": "pipeline_duration_min", "optimize": "minimize", "unit": "min", "description": "Total pipeline duration"},
            {"name": "resource_cost_usd", "optimize": "minimize", "unit": "USD", "description": "Pipeline resource cost"},
        ],
        "model": """
    pj = (PJ - 4.5) / 3.5;
    rc = (RC - 5) / 3;
    cs = (CS == "aggressive") ? 1 : -1;
    ac = (AC == "on") ? 1 : -1;
    dur = 25 - 8*pj - 5*rc - 6*cs - 2*ac + 3*pj*pj + 2*rc*rc - 2*pj*cs + 1*rc*ac;
    cost = 1.5 + 0.8*pj + 1.2*rc + 0.3*cs + 0.1*ac + 0.4*pj*rc - 0.2*cs*ac;
    if (dur < 2) dur = 2; if (cost < 0.1) cost = 0.1;
    printf "{\\"pipeline_duration_min\\": %.1f, \\"resource_cost_usd\\": %.2f}", dur + n1*2, cost + n2*0.15;
""",
        "factor_cases": '--parallel_jobs) PJ="$2"; shift 2 ;;\n        --runner_cpu_cores) RC="$2"; shift 2 ;;\n        --cache_strategy) CS="$2"; shift 2 ;;\n        --artifact_compression) AC="$2"; shift 2 ;;',
        "awk_vars": '-v PJ="$PJ" -v RC="$RC" -v CS="$CS" -v AC="$AC"',
        "vars_init": 'PJ=""\nRC=""\nCS=""\nAC=""',
        "validate": '[ -z "$PJ" ] || [ -z "$RC" ] || [ -z "$CS" ] || [ -z "$AC" ]',
    },
    {
        "num": 78, "slug": "deployment_canary_rollout",
        "name": "Deployment Canary Rollout",
        "desc": "Box-Behnken design to tune canary percentage, evaluation window, and error threshold for rollout safety",
        "design": "box_behnken", "category": "devops",
        "factors": [
            {"name": "canary_pct", "levels": ["5", "25"], "type": "continuous", "unit": "%", "description": "Percentage of traffic to canary"},
            {"name": "evaluation_window_min", "levels": ["5", "30"], "type": "continuous", "unit": "min", "description": "Canary evaluation window"},
            {"name": "error_threshold_pct", "levels": ["0.5", "5.0"], "type": "continuous", "unit": "%", "description": "Error rate threshold for rollback"},
        ],
        "fixed": {"orchestrator": "kubernetes", "strategy": "canary"},
        "responses": [
            {"name": "rollout_safety_score", "optimize": "maximize", "unit": "score", "description": "Rollout safety confidence score"},
            {"name": "deployment_time_min", "optimize": "minimize", "unit": "min", "description": "Total deployment time"},
        ],
        "model": """
    cp = (CP - 15) / 10;
    ew = (EW - 17.5) / 12.5;
    et = (ET - 2.75) / 2.25;
    safe = 75 + 5*cp + 10*ew - 8*et - 2*cp*cp - 3*ew*ew + 2*cp*ew - 4*et*et + 1.5*ew*et;
    dt = 10 + 3*cp + 8*ew + 2*et + 1*cp*ew + 0.5*ew*ew;
    if (safe > 100) safe = 100; if (safe < 30) safe = 30;
    if (dt < 3) dt = 3;
    printf "{\\"rollout_safety_score\\": %.1f, \\"deployment_time_min\\": %.1f}", safe + n1*3, dt + n2*1.5;
""",
        "factor_cases": '--canary_pct) CP="$2"; shift 2 ;;\n        --evaluation_window_min) EW="$2"; shift 2 ;;\n        --error_threshold_pct) ET="$2"; shift 2 ;;',
        "awk_vars": '-v CP="$CP" -v EW="$EW" -v ET="$ET"',
        "vars_init": 'CP=""\nEW=""\nET=""',
        "validate": '[ -z "$CP" ] || [ -z "$EW" ] || [ -z "$ET" ]',
    },
    {
        "num": 79, "slug": "terraform_plan_optimization",
        "name": "Terraform Plan Optimization",
        "desc": "Plackett-Burman screening of 6 Terraform parameters for plan time and state drift detection",
        "design": "plackett_burman", "category": "devops",
        "factors": [
            {"name": "parallelism", "levels": ["1", "20"], "type": "continuous", "unit": "threads", "description": "Terraform operation parallelism"},
            {"name": "refresh_enabled", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "State refresh before plan"},
            {"name": "state_lock_timeout", "levels": ["5", "120"], "type": "continuous", "unit": "sec", "description": "State lock acquisition timeout"},
            {"name": "provider_cache", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Provider plugin caching"},
            {"name": "plan_out_format", "levels": ["text", "json"], "type": "categorical", "unit": "", "description": "Plan output format"},
            {"name": "detailed_exitcode", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Detailed exit code enabled"},
        ],
        "fixed": {"backend": "s3", "provider": "aws"},
        "responses": [
            {"name": "plan_time_sec", "optimize": "minimize", "unit": "sec", "description": "Terraform plan execution time"},
            {"name": "state_drift_detected", "optimize": "maximize", "unit": "count", "description": "Number of state drifts detected"},
        ],
        "model": """
    par = (PAR - 10.5) / 9.5;
    ref = (REF == "on") ? 1 : -1;
    slt = (SLT - 62.5) / 57.5;
    pc = (PC == "on") ? 1 : -1;
    pof = (POF == "json") ? 1 : -1;
    dec = (DEC == "on") ? 1 : -1;
    pt = 45 - 12*par + 8*ref + 2*slt - 5*pc + 1*pof + 0.5*dec + 3*par*par - 2*par*pc;
    drift = 5 + 0.5*par + 4*ref + 0.3*slt + 0.2*pc + 0.1*pof + 0.3*dec + 0.5*ref*dec;
    if (pt < 3) pt = 3; if (drift < 0) drift = 0;
    printf "{\\"plan_time_sec\\": %.1f, \\"state_drift_detected\\": %.0f}", pt + n1*3, drift + n2*1;
""",
        "factor_cases": '--parallelism) PAR="$2"; shift 2 ;;\n        --refresh_enabled) REF="$2"; shift 2 ;;\n        --state_lock_timeout) SLT="$2"; shift 2 ;;\n        --provider_cache) PC="$2"; shift 2 ;;\n        --plan_out_format) POF="$2"; shift 2 ;;\n        --detailed_exitcode) DEC="$2"; shift 2 ;;',
        "awk_vars": '-v PAR="$PAR" -v REF="$REF" -v SLT="$SLT" -v PC="$PC" -v POF="$POF" -v DEC="$DEC"',
        "vars_init": 'PAR=""\nREF=""\nSLT=""\nPC=""\nPOF=""\nDEC=""',
        "validate": '[ -z "$PAR" ] || [ -z "$REF" ] || [ -z "$SLT" ] || [ -z "$PC" ]',
    },
    {
        "num": 80, "slug": "docker_build_layer_caching",
        "name": "Docker Build Layer Caching",
        "desc": "Fractional factorial of 5 Docker build parameters for build time and image size",
        "design": "fractional_factorial", "category": "devops",
        "factors": [
            {"name": "build_cache_mode", "levels": ["inline", "registry"], "type": "categorical", "unit": "", "description": "Build cache mode"},
            {"name": "max_layers", "levels": ["5", "30"], "type": "continuous", "unit": "layers", "description": "Maximum Dockerfile layers"},
            {"name": "squash_enabled", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Layer squash enabled"},
            {"name": "build_arg_count", "levels": ["0", "10"], "type": "continuous", "unit": "args", "description": "Number of build arguments"},
            {"name": "multistage_stages", "levels": ["1", "5"], "type": "continuous", "unit": "stages", "description": "Multistage build stage count"},
        ],
        "fixed": {"builder": "buildkit", "registry": "ecr"},
        "responses": [
            {"name": "build_time_sec", "optimize": "minimize", "unit": "sec", "description": "Docker image build time"},
            {"name": "image_size_mb", "optimize": "minimize", "unit": "MB", "description": "Final image size"},
        ],
        "model": """
    bcm = (BCM == "registry") ? 1 : -1;
    ml = (ML - 17.5) / 12.5;
    sq = (SQ == "on") ? 1 : -1;
    bac = (BAC - 5) / 5;
    ms = (MS - 3) / 2;
    bt = 120 - 20*bcm + 15*ml - 10*sq + 8*bac - 12*ms + 5*ml*ml + 3*bcm*ml - 4*sq*ms;
    isz = 450 + 30*bcm + 50*ml - 80*sq + 20*bac - 40*ms + 15*ml*ml - 10*sq*ml;
    if (bt < 5) bt = 5; if (isz < 20) isz = 20;
    printf "{\\"build_time_sec\\": %.0f, \\"image_size_mb\\": %.0f}", bt + n1*8, isz + n2*25;
""",
        "factor_cases": '--build_cache_mode) BCM="$2"; shift 2 ;;\n        --max_layers) ML="$2"; shift 2 ;;\n        --squash_enabled) SQ="$2"; shift 2 ;;\n        --build_arg_count) BAC="$2"; shift 2 ;;\n        --multistage_stages) MS="$2"; shift 2 ;;',
        "awk_vars": '-v BCM="$BCM" -v ML="$ML" -v SQ="$SQ" -v BAC="$BAC" -v MS="$MS"',
        "vars_init": 'BCM=""\nML=""\nSQ=""\nBAC=""\nMS=""',
        "validate": '[ -z "$BCM" ] || [ -z "$ML" ] || [ -z "$SQ" ] || [ -z "$BAC" ] || [ -z "$MS" ]',
    },
    {
        "num": 81, "slug": "test_suite_sharding",
        "name": "Test Suite Sharding",
        "desc": "Central Composite design to optimize shard count, retry count, and timeout multiplier for wall time and flaky failures",
        "design": "central_composite", "category": "devops",
        "factors": [
            {"name": "shard_count", "levels": ["2", "16"], "type": "continuous", "unit": "shards", "description": "Number of test shards"},
            {"name": "retry_flaky_count", "levels": ["0", "3"], "type": "continuous", "unit": "retries", "description": "Flaky test retry count"},
            {"name": "timeout_multiplier", "levels": ["1.0", "3.0"], "type": "continuous", "unit": "x", "description": "Test timeout multiplier"},
        ],
        "fixed": {"framework": "pytest", "test_count": "4500"},
        "responses": [
            {"name": "total_wall_time_min", "optimize": "minimize", "unit": "min", "description": "Total wall clock time"},
            {"name": "flaky_failure_rate", "optimize": "minimize", "unit": "%", "description": "Flaky test failure rate"},
        ],
        "model": """
    sc = (SC - 9) / 7;
    rfc = (RFC - 1.5) / 1.5;
    tm = (TM - 2) / 1;
    wt = 30 - 12*sc + 3*rfc + 2*tm + 5*sc*sc + 1*rfc*rfc - 1.5*sc*rfc + 0.8*rfc*tm;
    flaky = 5 - 0.5*sc - 3*rfc + 1*tm + 0.3*sc*sc + 1*rfc*rfc - 0.5*rfc*tm;
    if (wt < 2) wt = 2; if (flaky < 0.1) flaky = 0.1;
    printf "{\\"total_wall_time_min\\": %.1f, \\"flaky_failure_rate\\": %.2f}", wt + n1*1.5, flaky + n2*0.5;
""",
        "factor_cases": '--shard_count) SC="$2"; shift 2 ;;\n        --retry_flaky_count) RFC="$2"; shift 2 ;;\n        --timeout_multiplier) TM="$2"; shift 2 ;;',
        "awk_vars": '-v SC="$SC" -v RFC="$RFC" -v TM="$TM"',
        "vars_init": 'SC=""\nRFC=""\nTM=""',
        "validate": '[ -z "$SC" ] || [ -z "$RFC" ] || [ -z "$TM" ]',
    },
    {
        "num": 82, "slug": "gitops_sync_interval",
        "name": "GitOps Sync Interval",
        "desc": "Full factorial of sync interval, health check timeout, and prune enabled for drift detection and reconciliation",
        "design": "full_factorial", "category": "devops",
        "factors": [
            {"name": "sync_interval_sec", "levels": ["30", "300"], "type": "continuous", "unit": "sec", "description": "GitOps sync interval"},
            {"name": "health_check_timeout", "levels": ["10", "60"], "type": "continuous", "unit": "sec", "description": "Health check timeout"},
            {"name": "prune_enabled", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Automatic resource pruning"},
        ],
        "fixed": {"tool": "argocd", "cluster_count": "3"},
        "responses": [
            {"name": "drift_detection_delay_sec", "optimize": "minimize", "unit": "sec", "description": "Drift detection delay"},
            {"name": "reconciliation_success_pct", "optimize": "maximize", "unit": "%", "description": "Reconciliation success rate"},
        ],
        "model": """
    si = (SI - 165) / 135;
    hct = (HCT - 35) / 25;
    pe = (PE == "on") ? 1 : -1;
    ddd = 30 + 25*si + 5*hct - 3*pe + 4*si*si + 1.5*hct*hct + 2*si*hct;
    rec = 95 - 3*si - 2*hct + 2*pe - 1*si*si + 0.5*pe*hct;
    if (ddd < 5) ddd = 5; if (rec > 100) rec = 100; if (rec < 70) rec = 70;
    printf "{\\"drift_detection_delay_sec\\": %.0f, \\"reconciliation_success_pct\\": %.1f}", ddd + n1*4, rec + n2*1.5;
""",
        "factor_cases": '--sync_interval_sec) SI="$2"; shift 2 ;;\n        --health_check_timeout) HCT="$2"; shift 2 ;;\n        --prune_enabled) PE="$2"; shift 2 ;;',
        "awk_vars": '-v SI="$SI" -v HCT="$HCT" -v PE="$PE"',
        "vars_init": 'SI=""\nHCT=""\nPE=""',
        "validate": '[ -z "$SI" ] || [ -z "$HCT" ] || [ -z "$PE" ]',
    },
    {
        "num": 83, "slug": "log_aggregation_pipeline",
        "name": "Log Aggregation Pipeline",
        "desc": "Latin Hypercube exploration of 4 log aggregation parameters for ingestion rate and query latency",
        "design": "latin_hypercube", "category": "devops",
        "factors": [
            {"name": "batch_size_kb", "levels": ["64", "2048"], "type": "continuous", "unit": "KB", "description": "Log batch size"},
            {"name": "flush_interval_sec", "levels": ["1", "30"], "type": "continuous", "unit": "sec", "description": "Flush interval to storage"},
            {"name": "parser_threads", "levels": ["1", "16"], "type": "continuous", "unit": "threads", "description": "Log parser threads"},
            {"name": "compression_ratio", "levels": ["1", "9"], "type": "continuous", "unit": "level", "description": "Log compression level"},
        ],
        "fixed": {"stack": "elk", "retention_days": "30"},
        "responses": [
            {"name": "ingestion_rate_gbps", "optimize": "maximize", "unit": "Gbps", "description": "Log ingestion throughput"},
            {"name": "query_latency_ms", "optimize": "minimize", "unit": "ms", "description": "Log query latency"},
        ],
        "model": """
    bsz = (BSZ - 1056) / 992;
    fi = (FI - 15.5) / 14.5;
    pt = (PT - 8.5) / 7.5;
    cr = (CR - 5) / 4;
    ing = 2.5 + 1.0*bsz - 0.3*fi + 0.8*pt - 0.4*cr - 0.3*bsz*bsz + 0.2*bsz*pt - 0.15*cr*pt;
    qlat = 80 - 15*bsz + 20*fi - 10*pt + 8*cr + 5*bsz*bsz + 3*fi*fi - 4*pt*bsz;
    if (ing < 0.1) ing = 0.1; if (qlat < 5) qlat = 5;
    printf "{\\"ingestion_rate_gbps\\": %.2f, \\"query_latency_ms\\": %.0f}", ing + n1*0.15, qlat + n2*6;
""",
        "factor_cases": '--batch_size_kb) BSZ="$2"; shift 2 ;;\n        --flush_interval_sec) FI="$2"; shift 2 ;;\n        --parser_threads) PT="$2"; shift 2 ;;\n        --compression_ratio) CR="$2"; shift 2 ;;',
        "awk_vars": '-v BSZ="$BSZ" -v FI="$FI" -v PT="$PT" -v CR="$CR"',
        "vars_init": 'BSZ=""\nFI=""\nPT=""\nCR=""',
        "validate": '[ -z "$BSZ" ] || [ -z "$FI" ] || [ -z "$PT" ] || [ -z "$CR" ]',
    },
    {
        "num": 84, "slug": "feature_flag_evaluation",
        "name": "Feature Flag Evaluation",
        "desc": "Box-Behnken design to tune cache TTL, rule complexity, and SDK polling interval for evaluation latency and cache hits",
        "design": "box_behnken", "category": "devops",
        "factors": [
            {"name": "cache_ttl_sec", "levels": ["5", "120"], "type": "continuous", "unit": "sec", "description": "Feature flag cache TTL"},
            {"name": "rule_complexity_score", "levels": ["1", "10"], "type": "continuous", "unit": "score", "description": "Targeting rule complexity score"},
            {"name": "sdk_polling_interval_sec", "levels": ["10", "300"], "type": "continuous", "unit": "sec", "description": "SDK polling interval"},
        ],
        "fixed": {"platform": "launchdarkly", "sdk": "server_side"},
        "responses": [
            {"name": "evaluation_latency_us", "optimize": "minimize", "unit": "us", "description": "Flag evaluation latency"},
            {"name": "cache_hit_rate_pct", "optimize": "maximize", "unit": "%", "description": "Cache hit rate"},
        ],
        "model": """
    ct = (CT - 62.5) / 57.5;
    rcs = (RCS - 5.5) / 4.5;
    spi = (SPI - 155) / 145;
    lat = 150 - 40*ct + 50*rcs + 10*spi + 15*ct*ct + 20*rcs*rcs + 5*spi*spi - 8*ct*rcs;
    hit = 80 + 12*ct - 5*rcs - 3*spi - 4*ct*ct - 2*rcs*rcs + 2*ct*spi;
    if (lat < 10) lat = 10; if (hit > 99.5) hit = 99.5; if (hit < 40) hit = 40;
    printf "{\\"evaluation_latency_us\\": %.0f, \\"cache_hit_rate_pct\\": %.1f}", lat + n1*12, hit + n2*2;
""",
        "factor_cases": '--cache_ttl_sec) CT="$2"; shift 2 ;;\n        --rule_complexity_score) RCS="$2"; shift 2 ;;\n        --sdk_polling_interval_sec) SPI="$2"; shift 2 ;;',
        "awk_vars": '-v CT="$CT" -v RCS="$RCS" -v SPI="$SPI"',
        "vars_init": 'CT=""\nRCS=""\nSPI=""',
        "validate": '[ -z "$CT" ] || [ -z "$RCS" ] || [ -z "$SPI" ]',
    },
    {
        "num": 85, "slug": "incident_response_automation",
        "name": "Incident Response Automation",
        "desc": "Fractional factorial of 5 incident response parameters for MTTR and false escalation rate",
        "design": "fractional_factorial", "category": "devops",
        "factors": [
            {"name": "alert_threshold_severity", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "Alert severity threshold for automation"},
            {"name": "escalation_delay_min", "levels": ["1", "15"], "type": "continuous", "unit": "min", "description": "Escalation delay before auto-action"},
            {"name": "auto_remediation_enabled", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Automatic remediation enabled"},
            {"name": "runbook_timeout_sec", "levels": ["30", "300"], "type": "continuous", "unit": "sec", "description": "Runbook execution timeout"},
            {"name": "notification_channels", "levels": ["1", "5"], "type": "continuous", "unit": "channels", "description": "Number of notification channels"},
        ],
        "fixed": {"platform": "pagerduty", "integration": "slack"},
        "responses": [
            {"name": "mttr_min", "optimize": "minimize", "unit": "min", "description": "Mean time to resolve"},
            {"name": "false_escalation_pct", "optimize": "minimize", "unit": "%", "description": "False escalation percentage"},
        ],
        "model": """
    ats = (ATS - 3) / 2;
    ed = (ED - 8) / 7;
    ar = (AR == "on") ? 1 : -1;
    rto = (RTO - 165) / 135;
    nc = (NC - 3) / 2;
    mttr = 30 + 8*ats + 10*ed - 15*ar + 5*rto - 3*nc + 3*ats*ed - 2*ar*rto + 4*ed*ed;
    fe = 8 - 3*ats + 2*ed + 4*ar - 1*rto + 1.5*nc + 1.5*ar*ats - 0.8*ed*nc + 2*ar*ar;
    if (mttr < 2) mttr = 2; if (fe < 0.5) fe = 0.5;
    printf "{\\"mttr_min\\": %.1f, \\"false_escalation_pct\\": %.1f}", mttr + n1*3, fe + n2*1.5;
""",
        "factor_cases": '--alert_threshold_severity) ATS="$2"; shift 2 ;;\n        --escalation_delay_min) ED="$2"; shift 2 ;;\n        --auto_remediation_enabled) AR="$2"; shift 2 ;;\n        --runbook_timeout_sec) RTO="$2"; shift 2 ;;\n        --notification_channels) NC="$2"; shift 2 ;;',
        "awk_vars": '-v ATS="$ATS" -v ED="$ED" -v AR="$AR" -v RTO="$RTO" -v NC="$NC"',
        "vars_init": 'ATS=""\nED=""\nAR=""\nRTO=""\nNC=""',
        "validate": '[ -z "$ATS" ] || [ -z "$ED" ] || [ -z "$AR" ] || [ -z "$RTO" ] || [ -z "$NC" ]',
    },
    {
        "num": 86, "slug": "chaos_engineering_blast_radius",
        "name": "Chaos Engineering Blast Radius",
        "desc": "Central Composite design to optimize failure injection, experiment duration, and steady state threshold for resilience",
        "design": "central_composite", "category": "devops",
        "factors": [
            {"name": "failure_injection_pct", "levels": ["5", "50"], "type": "continuous", "unit": "%", "description": "Failure injection percentage"},
            {"name": "experiment_duration_min", "levels": ["5", "30"], "type": "continuous", "unit": "min", "description": "Chaos experiment duration"},
            {"name": "steady_state_threshold", "levels": ["0.9", "0.99"], "type": "continuous", "unit": "ratio", "description": "Steady state success threshold"},
        ],
        "fixed": {"tool": "litmus", "target": "microservices"},
        "responses": [
            {"name": "resilience_score", "optimize": "maximize", "unit": "score", "description": "System resilience score"},
            {"name": "blast_radius_services", "optimize": "minimize", "unit": "count", "description": "Number of affected services"},
        ],
        "model": """
    fi = (FI - 27.5) / 22.5;
    edur = (EDUR - 17.5) / 12.5;
    sst = (SST - 0.945) / 0.045;
    res = 70 + 8*fi + 5*edur + 10*sst - 3*fi*fi - 2*edur*edur - 4*sst*sst + 2*fi*edur + 3*fi*sst;
    blast = 3 + 4*fi + 2*edur - 1.5*sst + 1*fi*fi + 0.5*edur*edur + 0.8*fi*edur;
    if (res > 100) res = 100; if (res < 20) res = 20;
    if (blast < 1) blast = 1;
    printf "{\\"resilience_score\\": %.1f, \\"blast_radius_services\\": %.0f}", res + n1*3, blast + n2*1;
""",
        "factor_cases": '--failure_injection_pct) FI="$2"; shift 2 ;;\n        --experiment_duration_min) EDUR="$2"; shift 2 ;;\n        --steady_state_threshold) SST="$2"; shift 2 ;;',
        "awk_vars": '-v FI="$FI" -v EDUR="$EDUR" -v SST="$SST"',
        "vars_init": 'FI=""\nEDUR=""\nSST=""',
        "validate": '[ -z "$FI" ] || [ -z "$EDUR" ] || [ -z "$SST" ]',
    },
]

DESIGN_NAMES = {
    "box_behnken": "Box-Behnken",
    "central_composite": "Central Composite",
    "full_factorial": "Full Factorial",
    "fractional_factorial": "Fractional Factorial",
    "plackett_burman": "Plackett-Burman",
    "latin_hypercube": "Latin Hypercube",
}

def make_config(uc):
    base = f"use_cases/{uc['num']:02d}_{uc['slug']}"
    return {
        "metadata": {"name": uc["name"], "description": uc["desc"]},
        "factors": uc["factors"],
        "fixed_factors": uc["fixed"],
        "responses": uc["responses"],
        "runner": {"arg_style": "double-dash"},
        "settings": {
            "block_count": 1,
            "test_script": f"{base}/sim.sh",
            "operation": uc["design"],
            "processed_directory": f"{base}/results/analysis",
            "out_directory": f"{base}/results",
        },
    }

SIM_TEMPLATE = '''#!/usr/bin/env bash
# Simulated: {name}
set -euo pipefail

OUTFILE=""
{vars_init}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        {factor_cases}
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || {validate}; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk {awk_vars} -v seed="$RANDOM" '
BEGIN {{
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;
{model}}}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
'''

def make_sim(uc):
    return SIM_TEMPLATE.format(**uc)

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    for uc in USE_CASES:
        d = os.path.join(root, "use_cases", f"{uc['num']:02d}_{uc['slug']}")
        os.makedirs(d, exist_ok=True)
        os.makedirs(os.path.join(d, "results"), exist_ok=True)

        # config.json
        cfg = make_config(uc)
        with open(os.path.join(d, "config.json"), "w") as f:
            json.dump(cfg, f, indent=4)
        print(f"  [{uc['num']:02d}] config.json")

        # sim.sh
        sim = make_sim(uc)
        sim_path = os.path.join(d, "sim.sh")
        with open(sim_path, "w") as f:
            f.write(sim)
        os.chmod(sim_path, os.stat(sim_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"  [{uc['num']:02d}] sim.sh")

    print(f"\nDone: {len(USE_CASES)} use cases generated.")

if __name__ == "__main__":
    main()
