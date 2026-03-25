#!/usr/bin/env python3
"""Generate 30 new use cases across 3 categories (27-56)."""
import json, os, stat, textwrap

USE_CASES = [
    # ══════════════════════════════════════════════════
    # Category: Cloud & Microservices (27-36)
    # ══════════════════════════════════════════════════
    {
        "num": 27, "slug": "kubernetes_pod_autoscaling",
        "name": "Kubernetes Pod Autoscaling",
        "desc": "Central Composite design to optimize HPA target CPU, scale-up window, and replica bounds for request latency and cost",
        "design": "central_composite", "category": "cloud",
        "factors": [
            {"name": "target_cpu_pct", "levels": ["40", "80"], "type": "continuous", "unit": "%", "description": "HPA target CPU utilization"},
            {"name": "scaleup_window", "levels": ["15", "120"], "type": "continuous", "unit": "s", "description": "Stabilization window for scale-up"},
            {"name": "max_replicas", "levels": ["5", "30"], "type": "continuous", "unit": "pods", "description": "Maximum replica count"},
        ],
        "fixed": {"min_replicas": "2", "namespace": "production"},
        "responses": [
            {"name": "p99_latency_ms", "optimize": "minimize", "unit": "ms", "description": "99th percentile request latency"},
            {"name": "hourly_cost", "optimize": "minimize", "unit": "USD", "description": "Hourly compute cost"},
        ],
        "model": """
    cpu = (CPU - 60) / 20;
    win = (WIN - 67.5) / 52.5;
    rep = (REP - 17.5) / 12.5;
    lat = 120 - 25*cpu + 15*win - 20*rep + 8*cpu*cpu + 6*win*win + 3*rep*rep - 5*cpu*win + 4*cpu*rep;
    cost = 4.5 + 1.2*cpu - 0.3*win + 2.5*rep + 0.4*cpu*rep + 0.3*rep*rep;
    if (lat < 10) lat = 10; if (cost < 0.5) cost = 0.5;
    printf "{\\"p99_latency_ms\\": %.1f, \\"hourly_cost\\": %.2f}", lat + n1, cost + n2*0.3;
""",
        "factor_vars": 'CPU="$2"', "factor_cases": '--target_cpu_pct) CPU="$2"; shift 2 ;;\n        --scaleup_window) WIN="$2"; shift 2 ;;\n        --max_replicas) REP="$2"; shift 2 ;;',
        "awk_vars": '-v CPU="$CPU" -v WIN="$WIN" -v REP="$REP"',
        "vars_init": 'CPU=""\nWIN=""\nREP=""',
        "validate": '[ -z "$CPU" ] || [ -z "$WIN" ] || [ -z "$REP" ]',
    },
    {
        "num": 28, "slug": "microservice_circuit_breaker",
        "name": "Microservice Circuit Breaker",
        "desc": "Box-Behnken design to tune circuit breaker thresholds for error rate and recovery time",
        "design": "box_behnken", "category": "cloud",
        "factors": [
            {"name": "failure_threshold", "levels": ["3", "15"], "type": "continuous", "unit": "count", "description": "Failures before circuit opens"},
            {"name": "timeout_ms", "levels": ["500", "5000"], "type": "continuous", "unit": "ms", "description": "Request timeout"},
            {"name": "reset_interval", "levels": ["5", "60"], "type": "continuous", "unit": "s", "description": "Half-open retry interval"},
        ],
        "fixed": {"backend_pool_size": "10", "health_check_interval": "5"},
        "responses": [
            {"name": "error_rate", "optimize": "minimize", "unit": "%", "description": "End-user visible error rate"},
            {"name": "recovery_time", "optimize": "minimize", "unit": "s", "description": "Time to recover from cascade failure"},
        ],
        "model": """
    ft = (FT - 9) / 6;
    to = (TO - 2750) / 2250;
    ri = (RI - 32.5) / 27.5;
    err = 5.0 - 2.5*ft + 1.8*to - 1.2*ri + 1.5*ft*ft + 0.8*to*to + 0.6*ft*to;
    rec = 30 + 8*ft + 5*to + 12*ri - 3*ft*ri + 2*to*ri + 1.5*ri*ri;
    if (err < 0.1) err = 0.1; if (rec < 2) rec = 2;
    printf "{\\"error_rate\\": %.2f, \\"recovery_time\\": %.1f}", err + n1*0.5, rec + n2*2;
""",
        "factor_cases": '--failure_threshold) FT="$2"; shift 2 ;;\n        --timeout_ms) TO="$2"; shift 2 ;;\n        --reset_interval) RI="$2"; shift 2 ;;',
        "awk_vars": '-v FT="$FT" -v TO="$TO" -v RI="$RI"',
        "vars_init": 'FT=""\nTO=""\nRI=""',
        "validate": '[ -z "$FT" ] || [ -z "$TO" ] || [ -z "$RI" ]',
    },
    {
        "num": 29, "slug": "cdn_cache_optimization",
        "name": "CDN Cache Hit Optimization",
        "desc": "Full factorial with categorical and continuous factors for cache hit ratio and origin bandwidth",
        "design": "full_factorial", "category": "cloud",
        "factors": [
            {"name": "ttl_hours", "levels": ["1", "24"], "type": "continuous", "unit": "h", "description": "Cache time-to-live"},
            {"name": "cache_policy", "levels": ["lru", "lfu"], "type": "categorical", "unit": "", "description": "Eviction policy"},
            {"name": "cache_size_gb", "levels": ["50", "200"], "type": "continuous", "unit": "GB", "description": "Edge cache size"},
            {"name": "prefetch", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Predictive prefetch"},
        ],
        "fixed": {"origin_region": "us-east-1", "compression": "brotli"},
        "responses": [
            {"name": "hit_ratio", "optimize": "maximize", "unit": "%", "description": "Cache hit ratio"},
            {"name": "origin_bandwidth", "optimize": "minimize", "unit": "Gbps", "description": "Origin server bandwidth"},
        ],
        "model": """
    ttl = (TTL - 12.5) / 11.5;
    pol = (POL == "lfu") ? 1 : -1;
    sz = (SZ - 125) / 75;
    pf = (PF == "on") ? 1 : -1;
    hit = 72 + 8*ttl + 4*pol + 10*sz + 6*pf + 3*ttl*sz + 2*pol*pf - 1.5*ttl*ttl;
    bw = 15 - 4*ttl - 2*pol - 6*sz - 3*pf - 1.5*ttl*sz;
    if (hit > 99) hit = 99; if (hit < 30) hit = 30;
    if (bw < 0.5) bw = 0.5;
    printf "{\\"hit_ratio\\": %.1f, \\"origin_bandwidth\\": %.2f}", hit + n1*2, bw + n2*0.8;
""",
        "factor_cases": '--ttl_hours) TTL="$2"; shift 2 ;;\n        --cache_policy) POL="$2"; shift 2 ;;\n        --cache_size_gb) SZ="$2"; shift 2 ;;\n        --prefetch) PF="$2"; shift 2 ;;',
        "awk_vars": '-v TTL="$TTL" -v POL="$POL" -v SZ="$SZ" -v PF="$PF"',
        "vars_init": 'TTL=""\nPOL=""\nSZ=""\nPF=""',
        "validate": '[ -z "$TTL" ] || [ -z "$POL" ] || [ -z "$SZ" ] || [ -z "$PF" ]',
    },
    {
        "num": 30, "slug": "serverless_cold_start",
        "name": "Serverless Cold Start",
        "desc": "Plackett-Burman screening of 6 Lambda config knobs affecting cold start latency and cost",
        "design": "plackett_burman", "category": "cloud",
        "factors": [
            {"name": "memory_mb", "levels": ["128", "1024"], "type": "continuous", "unit": "MB", "description": "Function memory allocation"},
            {"name": "runtime", "levels": ["python", "go"], "type": "categorical", "unit": "", "description": "Runtime language"},
            {"name": "package_mb", "levels": ["5", "50"], "type": "continuous", "unit": "MB", "description": "Deployment package size"},
            {"name": "vpc_enabled", "levels": ["no", "yes"], "type": "categorical", "unit": "", "description": "VPC attachment"},
            {"name": "layers_count", "levels": ["0", "5"], "type": "continuous", "unit": "count", "description": "Lambda layers attached"},
            {"name": "provisioned", "levels": ["0", "10"], "type": "continuous", "unit": "count", "description": "Provisioned concurrency"},
        ],
        "fixed": {"region": "us-east-1", "trigger": "api-gateway"},
        "responses": [
            {"name": "cold_start_ms", "optimize": "minimize", "unit": "ms", "description": "Cold start initialization latency"},
            {"name": "cost_per_million", "optimize": "minimize", "unit": "USD", "description": "Cost per million invocations"},
        ],
        "model": """
    mem = (MEM - 576) / 448;
    rt = (RT == "go") ? -1 : 1;
    pkg = (PKG - 27.5) / 22.5;
    vpc = (VPC == "yes") ? 1 : -1;
    lay = (LAY - 2.5) / 2.5;
    prov = (PROV - 5) / 5;
    cs = 800 - 200*mem + 150*rt + 120*pkg + 250*vpc + 60*lay - 350*prov + 40*mem*rt;
    cst = 3.5 - 0.5*mem + 0.8*rt + 0.3*pkg + 0.4*vpc + 0.2*lay + 2.0*prov;
    if (cs < 5) cs = 5; if (cst < 0.2) cst = 0.2;
    printf "{\\"cold_start_ms\\": %.0f, \\"cost_per_million\\": %.2f}", cs + n1*50, cst + n2*0.3;
""",
        "factor_cases": '--memory_mb) MEM="$2"; shift 2 ;;\n        --runtime) RT="$2"; shift 2 ;;\n        --package_mb) PKG="$2"; shift 2 ;;\n        --vpc_enabled) VPC="$2"; shift 2 ;;\n        --layers_count) LAY="$2"; shift 2 ;;\n        --provisioned) PROV="$2"; shift 2 ;;',
        "awk_vars": '-v MEM="$MEM" -v RT="$RT" -v PKG="$PKG" -v VPC="$VPC" -v LAY="$LAY" -v PROV="$PROV"',
        "vars_init": 'MEM=""\nRT=""\nPKG=""\nVPC=""\nLAY=""\nPROV=""',
        "validate": '[ -z "$MEM" ] || [ -z "$RT" ] || [ -z "$PKG" ] || [ -z "$VPC" ]',
    },
    {
        "num": 31, "slug": "database_connection_pooling",
        "name": "Database Connection Pooling",
        "desc": "Box-Behnken design to optimize connection pool size, idle timeout, and max lifetime for throughput",
        "design": "box_behnken", "category": "cloud",
        "factors": [
            {"name": "pool_size", "levels": ["5", "50"], "type": "continuous", "unit": "conns", "description": "Maximum pool connections"},
            {"name": "idle_timeout", "levels": ["30", "300"], "type": "continuous", "unit": "s", "description": "Idle connection timeout"},
            {"name": "max_lifetime", "levels": ["300", "3600"], "type": "continuous", "unit": "s", "description": "Connection max lifetime"},
        ],
        "fixed": {"db_engine": "postgresql", "ssl": "true"},
        "responses": [
            {"name": "throughput_qps", "optimize": "maximize", "unit": "qps", "description": "Queries per second"},
            {"name": "p95_latency_ms", "optimize": "minimize", "unit": "ms", "description": "95th percentile query latency"},
        ],
        "model": """
    ps = (PS - 27.5) / 22.5;
    it = (IT - 165) / 135;
    ml = (ML - 1950) / 1650;
    thr = 5000 + 1500*ps - 300*it + 200*ml - 800*ps*ps - 200*it*it + 150*ps*it;
    lat = 12 - 4*ps + 2*it - 1*ml + 3*ps*ps + 1.5*it*it - 0.8*ps*ml;
    if (thr < 100) thr = 100; if (lat < 1) lat = 1;
    printf "{\\"throughput_qps\\": %.0f, \\"p95_latency_ms\\": %.1f}", thr + n1*200, lat + n2*1.5;
""",
        "factor_cases": '--pool_size) PS="$2"; shift 2 ;;\n        --idle_timeout) IT="$2"; shift 2 ;;\n        --max_lifetime) ML="$2"; shift 2 ;;',
        "awk_vars": '-v PS="$PS" -v IT="$IT" -v ML="$ML"',
        "vars_init": 'PS=""\nIT=""\nML=""',
        "validate": '[ -z "$PS" ] || [ -z "$IT" ] || [ -z "$ML" ]',
    },
    {
        "num": 32, "slug": "load_balancer_algorithm",
        "name": "Load Balancer Algorithm",
        "desc": "Full factorial of balancing algorithm, health check interval, and connection draining for availability",
        "design": "full_factorial", "category": "cloud",
        "factors": [
            {"name": "algorithm", "levels": ["round_robin", "least_conn", "ip_hash"], "type": "categorical", "unit": "", "description": "Load balancing algorithm"},
            {"name": "health_interval", "levels": ["5", "30"], "type": "continuous", "unit": "s", "description": "Health check interval"},
            {"name": "drain_timeout", "levels": ["10", "60"], "type": "continuous", "unit": "s", "description": "Connection draining timeout"},
        ],
        "fixed": {"backend_count": "4", "protocol": "http2"},
        "responses": [
            {"name": "availability", "optimize": "maximize", "unit": "%", "description": "Service availability (nines)"},
            {"name": "imbalance_pct", "optimize": "minimize", "unit": "%", "description": "Load imbalance across backends"},
        ],
        "model": """
    if (ALG == "round_robin") a = 0; else if (ALG == "least_conn") a = 1; else a = -0.5;
    hi = (HI - 17.5) / 12.5;
    dt = (DT - 35) / 25;
    avail = 99.5 + 0.3*a - 0.15*hi + 0.1*dt + 0.05*a*dt;
    imb = 8 - 5*a + 2*hi - 1.5*dt + 1.2*a*hi;
    if (avail > 99.999) avail = 99.999; if (avail < 95) avail = 95;
    if (imb < 0.5) imb = 0.5;
    printf "{\\"availability\\": %.3f, \\"imbalance_pct\\": %.1f}", avail + n1*0.05, imb + n2*1.5;
""",
        "factor_cases": '--algorithm) ALG="$2"; shift 2 ;;\n        --health_interval) HI="$2"; shift 2 ;;\n        --drain_timeout) DT="$2"; shift 2 ;;',
        "awk_vars": '-v ALG="$ALG" -v HI="$HI" -v DT="$DT"',
        "vars_init": 'ALG=""\nHI=""\nDT=""',
        "validate": '[ -z "$ALG" ] || [ -z "$HI" ] || [ -z "$DT" ]',
    },
    {
        "num": 33, "slug": "api_rate_limiter",
        "name": "API Rate Limiter Tuning",
        "desc": "Fractional factorial of 5 rate limiting parameters for throughput and fairness",
        "design": "fractional_factorial", "category": "cloud",
        "factors": [
            {"name": "requests_per_sec", "levels": ["100", "1000"], "type": "continuous", "unit": "rps", "description": "Base rate limit per client"},
            {"name": "burst_size", "levels": ["10", "100"], "type": "continuous", "unit": "requests", "description": "Token bucket burst size"},
            {"name": "window_type", "levels": ["sliding", "fixed"], "type": "categorical", "unit": "", "description": "Rate window type"},
            {"name": "penalty_duration", "levels": ["10", "300"], "type": "continuous", "unit": "s", "description": "Penalty period after limit hit"},
            {"name": "global_limit", "levels": ["5000", "50000"], "type": "continuous", "unit": "rps", "description": "Global rate limit across all clients"},
        ],
        "fixed": {"backend_capacity": "20000", "cache_backend": "redis"},
        "responses": [
            {"name": "goodput_rps", "optimize": "maximize", "unit": "rps", "description": "Successful requests per second"},
            {"name": "fairness_index", "optimize": "maximize", "unit": "0-1", "description": "Jain's fairness index"},
        ],
        "model": """
    rps = (RPS - 550) / 450;
    bs = (BS - 55) / 45;
    wt = (WT == "sliding") ? 1 : -1;
    pd = (PD - 155) / 145;
    gl = (GL - 27500) / 22500;
    gp = 8500 + 2000*rps + 800*bs + 500*wt - 600*pd + 3000*gl - 400*rps*pd + 300*bs*gl;
    fair = 0.85 + 0.06*wt - 0.04*rps + 0.03*bs - 0.08*pd + 0.02*gl + 0.02*wt*pd;
    if (gp < 100) gp = 100; if (fair > 1) fair = 1; if (fair < 0.3) fair = 0.3;
    printf "{\\"goodput_rps\\": %.0f, \\"fairness_index\\": %.3f}", gp + n1*300, fair + n2*0.02;
""",
        "factor_cases": '--requests_per_sec) RPS="$2"; shift 2 ;;\n        --burst_size) BS="$2"; shift 2 ;;\n        --window_type) WT="$2"; shift 2 ;;\n        --penalty_duration) PD="$2"; shift 2 ;;\n        --global_limit) GL="$2"; shift 2 ;;',
        "awk_vars": '-v RPS="$RPS" -v BS="$BS" -v WT="$WT" -v PD="$PD" -v GL="$GL"',
        "vars_init": 'RPS=""\nBS=""\nWT=""\nPD=""\nGL=""',
        "validate": '[ -z "$RPS" ] || [ -z "$BS" ] || [ -z "$WT" ] || [ -z "$PD" ] || [ -z "$GL" ]',
    },
    {
        "num": 34, "slug": "container_resource_limits",
        "name": "Container Resource Limits",
        "desc": "Central Composite design optimizing CPU/memory requests and limits for utilization and stability",
        "design": "central_composite", "category": "cloud",
        "factors": [
            {"name": "cpu_request_m", "levels": ["100", "1000"], "type": "continuous", "unit": "millicores", "description": "CPU request"},
            {"name": "cpu_limit_m", "levels": ["500", "2000"], "type": "continuous", "unit": "millicores", "description": "CPU limit"},
            {"name": "memory_request_mb", "levels": ["128", "1024"], "type": "continuous", "unit": "MB", "description": "Memory request"},
        ],
        "fixed": {"memory_limit_mb": "2048", "qos_class": "burstable"},
        "responses": [
            {"name": "utilization_pct", "optimize": "maximize", "unit": "%", "description": "Resource utilization efficiency"},
            {"name": "oom_kills_per_day", "optimize": "minimize", "unit": "count", "description": "OOM kill events per day"},
        ],
        "model": """
    cr = (CR - 550) / 450;
    cl = (CL - 1250) / 750;
    mr = (MR - 576) / 448;
    util = 65 + 15*cr - 8*cl + 10*mr - 6*cr*cr - 4*cl*cl + 3*cr*cl + 2*mr*cr;
    oom = 5 - 2*cr - 1.5*cl - 3*mr + 2*cr*cr + 1*cl*cl + 0.8*mr*mr + 0.5*cr*cl;
    if (util > 100) util = 100; if (util < 5) util = 5;
    if (oom < 0) oom = 0;
    printf "{\\"utilization_pct\\": %.1f, \\"oom_kills_per_day\\": %.1f}", util + n1*3, oom + n2*0.8;
""",
        "factor_cases": '--cpu_request_m) CR="$2"; shift 2 ;;\n        --cpu_limit_m) CL="$2"; shift 2 ;;\n        --memory_request_mb) MR="$2"; shift 2 ;;',
        "awk_vars": '-v CR="$CR" -v CL="$CL" -v MR="$MR"',
        "vars_init": 'CR=""\nCL=""\nMR=""',
        "validate": '[ -z "$CR" ] || [ -z "$CL" ] || [ -z "$MR" ]',
    },
    {
        "num": 35, "slug": "service_mesh_sidecar",
        "name": "Service Mesh Sidecar",
        "desc": "Plackett-Burman screening of 6 Envoy sidecar parameters for latency overhead and resource usage",
        "design": "plackett_burman", "category": "cloud",
        "factors": [
            {"name": "concurrency", "levels": ["1", "8"], "type": "continuous", "unit": "threads", "description": "Envoy worker threads"},
            {"name": "circuit_breaker_max", "levels": ["100", "10000"], "type": "continuous", "unit": "conns", "description": "Max circuit breaker connections"},
            {"name": "access_log", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Access logging enabled"},
            {"name": "tracing_sample_pct", "levels": ["1", "100"], "type": "continuous", "unit": "%", "description": "Distributed tracing sample rate"},
            {"name": "compression", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Response compression"},
            {"name": "connection_pool", "levels": ["100", "1000"], "type": "continuous", "unit": "conns", "description": "Upstream connection pool size"},
        ],
        "fixed": {"mesh": "istio", "protocol": "http2"},
        "responses": [
            {"name": "latency_overhead_ms", "optimize": "minimize", "unit": "ms", "description": "Added proxy latency"},
            {"name": "sidecar_cpu_pct", "optimize": "minimize", "unit": "%", "description": "Sidecar CPU usage"},
        ],
        "model": """
    con = (CON - 4.5) / 3.5;
    cb = (CB - 5050) / 4950;
    al = (AL == "on") ? 1 : -1;
    tr = (TR - 50.5) / 49.5;
    comp = (COMP == "on") ? 1 : -1;
    cp = (CP - 550) / 450;
    lat = 3.0 - 1.2*con + 0.3*cb + 0.8*al + 1.5*tr + 0.6*comp - 0.4*cp + 0.3*al*tr;
    cpu = 8 + 5*con + 1*cb + 3*al + 4*tr + 2*comp + 1.5*cp + 1*con*tr;
    if (lat < 0.2) lat = 0.2; if (cpu < 1) cpu = 1;
    printf "{\\"latency_overhead_ms\\": %.1f, \\"sidecar_cpu_pct\\": %.1f}", lat + n1*0.3, cpu + n2*1.5;
""",
        "factor_cases": '--concurrency) CON="$2"; shift 2 ;;\n        --circuit_breaker_max) CB="$2"; shift 2 ;;\n        --access_log) AL="$2"; shift 2 ;;\n        --tracing_sample_pct) TR="$2"; shift 2 ;;\n        --compression) COMP="$2"; shift 2 ;;\n        --connection_pool) CP="$2"; shift 2 ;;',
        "awk_vars": '-v CON="$CON" -v CB="$CB" -v AL="$AL" -v TR="$TR" -v COMP="$COMP" -v CP="$CP"',
        "vars_init": 'CON=""\nCB=""\nAL=""\nTR=""\nCOMP=""\nCP=""',
        "validate": '[ -z "$CON" ] || [ -z "$CB" ] || [ -z "$AL" ] || [ -z "$TR" ]',
    },
    {
        "num": 36, "slug": "message_queue_consumer",
        "name": "Message Queue Consumer Tuning",
        "desc": "Latin Hypercube exploration of 4 Kafka consumer parameters for throughput and lag",
        "design": "latin_hypercube", "category": "cloud",
        "factors": [
            {"name": "fetch_min_bytes", "levels": ["1", "1048576"], "type": "continuous", "unit": "bytes", "description": "Minimum fetch size"},
            {"name": "max_poll_records", "levels": ["100", "5000"], "type": "continuous", "unit": "records", "description": "Max records per poll"},
            {"name": "num_consumers", "levels": ["1", "12"], "type": "continuous", "unit": "count", "description": "Consumer group size"},
            {"name": "session_timeout", "levels": ["6000", "45000"], "type": "continuous", "unit": "ms", "description": "Session timeout"},
        ],
        "fixed": {"partitions": "12", "replication_factor": "3"},
        "responses": [
            {"name": "throughput_mbps", "optimize": "maximize", "unit": "MB/s", "description": "Consumer throughput"},
            {"name": "consumer_lag", "optimize": "minimize", "unit": "records", "description": "Consumer lag"},
        ],
        "model": """
    fb = (FB - 524288) / 524288;
    mpr = (MPR - 2550) / 2450;
    nc = (NC - 6.5) / 5.5;
    st = (ST - 25500) / 19500;
    thr = 120 + 30*fb + 25*mpr + 40*nc - 5*st + 10*fb*mpr - 15*nc*nc - 8*fb*fb;
    lag = 50000 - 15000*fb - 10000*mpr - 20000*nc + 5000*st + 8000*nc*nc + 3000*fb*st;
    if (thr < 1) thr = 1; if (lag < 0) lag = 0;
    printf "{\\"throughput_mbps\\": %.1f, \\"consumer_lag\\": %.0f}", thr + n1*8, lag + n2*3000;
""",
        "factor_cases": '--fetch_min_bytes) FB="$2"; shift 2 ;;\n        --max_poll_records) MPR="$2"; shift 2 ;;\n        --num_consumers) NC="$2"; shift 2 ;;\n        --session_timeout) ST="$2"; shift 2 ;;',
        "awk_vars": '-v FB="$FB" -v MPR="$MPR" -v NC="$NC" -v ST="$ST"',
        "vars_init": 'FB=""\nMPR=""\nNC=""\nST=""',
        "validate": '[ -z "$FB" ] || [ -z "$MPR" ] || [ -z "$NC" ] || [ -z "$ST" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: Data Engineering & Analytics (37-46)
    # ══════════════════════════════════════════════════
    {
        "num": 37, "slug": "spark_shuffle_optimization",
        "name": "Spark Shuffle Optimization",
        "desc": "Central Composite design to optimize Spark shuffle partitions, buffer size, and compression for job time",
        "design": "central_composite", "category": "data",
        "factors": [
            {"name": "shuffle_partitions", "levels": ["50", "500"], "type": "continuous", "unit": "count", "description": "spark.sql.shuffle.partitions"},
            {"name": "shuffle_buffer_kb", "levels": ["32", "256"], "type": "continuous", "unit": "KB", "description": "Shuffle write buffer size"},
            {"name": "compress_codec", "levels": ["lz4", "zstd"], "type": "categorical", "unit": "", "description": "Shuffle compression codec"},
        ],
        "fixed": {"executor_memory": "8g", "executor_cores": "4"},
        "responses": [
            {"name": "job_time_min", "optimize": "minimize", "unit": "min", "description": "Total job execution time"},
            {"name": "shuffle_spill_gb", "optimize": "minimize", "unit": "GB", "description": "Shuffle data spilled to disk"},
        ],
        "model": """
    sp = (SP - 275) / 225;
    sb = (SB - 144) / 112;
    cc = (CC == "zstd") ? 1 : -1;
    jt = 25 - 5*sp + 3*sb - 2*cc + 4*sp*sp + 2*sb*sb - 1.5*sp*sb + 0.8*sp*cc;
    spill = 15 - 4*sp - 6*sb - 3*cc + 3*sp*sp + 2*sb*sb + 1*sp*sb;
    if (jt < 2) jt = 2; if (spill < 0) spill = 0;
    printf "{\\"job_time_min\\": %.1f, \\"shuffle_spill_gb\\": %.1f}", jt + n1*1.5, spill + n2*1.2;
""",
        "factor_cases": '--shuffle_partitions) SP="$2"; shift 2 ;;\n        --shuffle_buffer_kb) SB="$2"; shift 2 ;;\n        --compress_codec) CC="$2"; shift 2 ;;',
        "awk_vars": '-v SP="$SP" -v SB="$SB" -v CC="$CC"',
        "vars_init": 'SP=""\nSB=""\nCC=""',
        "validate": '[ -z "$SP" ] || [ -z "$SB" ] || [ -z "$CC" ]',
    },
    {
        "num": 38, "slug": "data_lake_partitioning",
        "name": "Data Lake Partitioning",
        "desc": "Full factorial of partitioning strategy, file format, and compaction for query speed and storage cost",
        "design": "full_factorial", "category": "data",
        "factors": [
            {"name": "partition_cols", "levels": ["date", "date_hour", "date_hour_region"], "type": "categorical", "unit": "", "description": "Partition column strategy"},
            {"name": "file_format", "levels": ["parquet", "orc"], "type": "categorical", "unit": "", "description": "Columnar file format"},
            {"name": "target_file_mb", "levels": ["64", "256"], "type": "continuous", "unit": "MB", "description": "Target file size after compaction"},
            {"name": "z_order", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Z-order optimization"},
        ],
        "fixed": {"table_size_tb": "5", "retention_days": "90"},
        "responses": [
            {"name": "query_time_s", "optimize": "minimize", "unit": "s", "description": "Median analytical query time"},
            {"name": "storage_cost_month", "optimize": "minimize", "unit": "USD", "description": "Monthly storage cost"},
        ],
        "model": """
    if (PC == "date") pc = -1; else if (PC == "date_hour") pc = 0; else pc = 1;
    ff = (FF == "parquet") ? 1 : -1;
    tf = (TF - 160) / 96;
    zo = (ZO == "on") ? 1 : -1;
    qt = 12 - 3*pc + 1.5*ff - 2*tf - 4*zo + 1*pc*zo + 0.5*pc*pc;
    stc = 250 + 30*pc - 10*ff - 15*tf + 5*zo + 8*pc*tf;
    if (qt < 0.5) qt = 0.5; if (stc < 50) stc = 50;
    printf "{\\"query_time_s\\": %.1f, \\"storage_cost_month\\": %.0f}", qt + n1*1.5, stc + n2*20;
""",
        "factor_cases": '--partition_cols) PC="$2"; shift 2 ;;\n        --file_format) FF="$2"; shift 2 ;;\n        --target_file_mb) TF="$2"; shift 2 ;;\n        --z_order) ZO="$2"; shift 2 ;;',
        "awk_vars": '-v PC="$PC" -v FF="$FF" -v TF="$TF" -v ZO="$ZO"',
        "vars_init": 'PC=""\nFF=""\nTF=""\nZO=""',
        "validate": '[ -z "$PC" ] || [ -z "$FF" ] || [ -z "$TF" ] || [ -z "$ZO" ]',
    },
    {
        "num": 39, "slug": "stream_processing_windowing",
        "name": "Stream Processing Windowing",
        "desc": "Box-Behnken design to tune Flink window size, watermark delay, and parallelism for latency and accuracy",
        "design": "box_behnken", "category": "data",
        "factors": [
            {"name": "window_size_s", "levels": ["5", "120"], "type": "continuous", "unit": "s", "description": "Tumbling window size"},
            {"name": "watermark_delay_s", "levels": ["1", "30"], "type": "continuous", "unit": "s", "description": "Allowed event-time lateness"},
            {"name": "parallelism", "levels": ["4", "32"], "type": "continuous", "unit": "slots", "description": "Job parallelism"},
        ],
        "fixed": {"checkpoint_interval_ms": "10000", "state_backend": "rocksdb"},
        "responses": [
            {"name": "end_to_end_latency_ms", "optimize": "minimize", "unit": "ms", "description": "End-to-end processing latency"},
            {"name": "result_accuracy", "optimize": "maximize", "unit": "%", "description": "Result completeness/accuracy"},
        ],
        "model": """
    ws = (WS - 62.5) / 57.5;
    wd = (WD - 15.5) / 14.5;
    par = (PAR - 18) / 14;
    lat = 500 + 300*ws + 200*wd - 150*par + 50*ws*ws + 30*wd*wd + 80*ws*wd - 40*par*ws;
    acc = 92 + 3*ws + 5*wd - 0.5*par - 1.5*ws*ws - 2*wd*wd + 0.8*ws*wd;
    if (lat < 20) lat = 20; if (acc > 100) acc = 100; if (acc < 70) acc = 70;
    printf "{\\"end_to_end_latency_ms\\": %.0f, \\"result_accuracy\\": %.1f}", lat + n1*30, acc + n2*1.0;
""",
        "factor_cases": '--window_size_s) WS="$2"; shift 2 ;;\n        --watermark_delay_s) WD="$2"; shift 2 ;;\n        --parallelism) PAR="$2"; shift 2 ;;',
        "awk_vars": '-v WS="$WS" -v WD="$WD" -v PAR="$PAR"',
        "vars_init": 'WS=""\nWD=""\nPAR=""',
        "validate": '[ -z "$WS" ] || [ -z "$WD" ] || [ -z "$PAR" ]',
    },
    {
        "num": 40, "slug": "etl_batch_size_tuning",
        "name": "ETL Batch Size Tuning",
        "desc": "Fractional factorial of 5 ETL pipeline parameters for throughput and resource efficiency",
        "design": "fractional_factorial", "category": "data",
        "factors": [
            {"name": "batch_size", "levels": ["1000", "100000"], "type": "continuous", "unit": "rows", "description": "Rows per batch"},
            {"name": "writer_threads", "levels": ["1", "16"], "type": "continuous", "unit": "threads", "description": "Parallel writer threads"},
            {"name": "commit_interval", "levels": ["1000", "50000"], "type": "continuous", "unit": "rows", "description": "Commit frequency"},
            {"name": "transform_mode", "levels": ["row", "vectorized"], "type": "categorical", "unit": "", "description": "Transform execution mode"},
            {"name": "buffer_mb", "levels": ["64", "512"], "type": "continuous", "unit": "MB", "description": "In-memory buffer size"},
        ],
        "fixed": {"source": "postgresql", "sink": "s3_parquet"},
        "responses": [
            {"name": "rows_per_sec", "optimize": "maximize", "unit": "rows/s", "description": "ETL throughput"},
            {"name": "peak_memory_gb", "optimize": "minimize", "unit": "GB", "description": "Peak memory consumption"},
        ],
        "model": """
    bs = (BS - 50500) / 49500;
    wt = (WT - 8.5) / 7.5;
    ci = (CI - 25500) / 24500;
    tm = (TM == "vectorized") ? 1 : -1;
    buf = (BUF - 288) / 224;
    rps = 50000 + 20000*bs + 15000*wt + 5000*ci + 12000*tm + 8000*buf - 5000*bs*bs - 3000*wt*wt + 4000*bs*wt;
    mem = 2.0 + 1.5*bs + 0.8*wt + 0.3*ci + 0.5*tm + 2.0*buf - 0.3*wt*buf;
    if (rps < 1000) rps = 1000; if (mem < 0.5) mem = 0.5;
    printf "{\\"rows_per_sec\\": %.0f, \\"peak_memory_gb\\": %.1f}", rps + n1*3000, mem + n2*0.3;
""",
        "factor_cases": '--batch_size) BS="$2"; shift 2 ;;\n        --writer_threads) WT="$2"; shift 2 ;;\n        --commit_interval) CI="$2"; shift 2 ;;\n        --transform_mode) TM="$2"; shift 2 ;;\n        --buffer_mb) BUF="$2"; shift 2 ;;',
        "awk_vars": '-v BS="$BS" -v WT="$WT" -v CI="$CI" -v TM="$TM" -v BUF="$BUF"',
        "vars_init": 'BS=""\nWT=""\nCI=""\nTM=""\nBUF=""',
        "validate": '[ -z "$BS" ] || [ -z "$WT" ] || [ -z "$CI" ] || [ -z "$TM" ] || [ -z "$BUF" ]',
    },
    {
        "num": 41, "slug": "columnar_compression",
        "name": "Columnar Compression",
        "desc": "Full factorial of compression codec, dictionary encoding, page size, and row group size for ratio vs speed",
        "design": "full_factorial", "category": "data",
        "factors": [
            {"name": "codec", "levels": ["snappy", "zstd"], "type": "categorical", "unit": "", "description": "Compression codec"},
            {"name": "dictionary", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Dictionary encoding"},
            {"name": "page_size_kb", "levels": ["64", "1024"], "type": "continuous", "unit": "KB", "description": "Column page size"},
            {"name": "row_group_mb", "levels": ["32", "256"], "type": "continuous", "unit": "MB", "description": "Row group size"},
        ],
        "fixed": {"format": "parquet", "data_type": "mixed_analytics"},
        "responses": [
            {"name": "compression_ratio", "optimize": "maximize", "unit": "x", "description": "Compression ratio (uncompressed/compressed)"},
            {"name": "read_speed_mbps", "optimize": "maximize", "unit": "MB/s", "description": "Sequential read throughput"},
        ],
        "model": """
    co = (CO == "zstd") ? 1 : -1;
    di = (DI == "on") ? 1 : -1;
    ps = (PS - 544) / 480;
    rg = (RG - 144) / 112;
    ratio = 4.5 + 1.5*co + 1.2*di + 0.3*ps + 0.5*rg + 0.4*co*di + 0.2*di*ps;
    speed = 800 - 200*co + 100*di + 50*ps + 80*rg - 60*co*di + 30*ps*rg;
    if (ratio < 1) ratio = 1; if (speed < 100) speed = 100;
    printf "{\\"compression_ratio\\": %.2f, \\"read_speed_mbps\\": %.0f}", ratio + n1*0.3, speed + n2*40;
""",
        "factor_cases": '--codec) CO="$2"; shift 2 ;;\n        --dictionary) DI="$2"; shift 2 ;;\n        --page_size_kb) PS="$2"; shift 2 ;;\n        --row_group_mb) RG="$2"; shift 2 ;;',
        "awk_vars": '-v CO="$CO" -v DI="$DI" -v PS="$PS" -v RG="$RG"',
        "vars_init": 'CO=""\nDI=""\nPS=""\nRG=""',
        "validate": '[ -z "$CO" ] || [ -z "$DI" ] || [ -z "$PS" ] || [ -z "$RG" ]',
    },
    {
        "num": 42, "slug": "query_engine_join_strategy",
        "name": "Query Engine Join Strategy",
        "desc": "Plackett-Burman screening of 6 query engine parameters for join performance and memory pressure",
        "design": "plackett_burman", "category": "data",
        "factors": [
            {"name": "join_algorithm", "levels": ["hash", "sort_merge"], "type": "categorical", "unit": "", "description": "Join algorithm preference"},
            {"name": "hash_table_mb", "levels": ["256", "4096"], "type": "continuous", "unit": "MB", "description": "Hash table memory budget"},
            {"name": "sort_buffer_mb", "levels": ["64", "512"], "type": "continuous", "unit": "MB", "description": "Sort buffer size"},
            {"name": "broadcast_threshold_mb", "levels": ["10", "256"], "type": "continuous", "unit": "MB", "description": "Broadcast join threshold"},
            {"name": "adaptive_execution", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Adaptive query execution"},
            {"name": "partitions", "levels": ["50", "400"], "type": "continuous", "unit": "count", "description": "Shuffle partition count"},
        ],
        "fixed": {"engine": "spark_sql", "data_size_gb": "100"},
        "responses": [
            {"name": "query_time_s", "optimize": "minimize", "unit": "s", "description": "Query execution time"},
            {"name": "peak_memory_gb", "optimize": "minimize", "unit": "GB", "description": "Peak executor memory"},
        ],
        "model": """
    ja = (JA == "hash") ? 1 : -1;
    ht = (HT - 2176) / 1920;
    sb = (SB - 288) / 224;
    bt = (BT - 133) / 123;
    ae = (AE == "on") ? 1 : -1;
    pt = (PT - 225) / 175;
    qt = 45 - 8*ja - 5*ht - 3*sb - 4*bt - 6*ae - 2*pt + 3*ja*ht + 2*ae*pt;
    mem = 12 + 4*ja + 5*ht + 2*sb + 3*bt - 2*ae + 1.5*pt + 1*ja*ht;
    if (qt < 5) qt = 5; if (mem < 2) mem = 2;
    printf "{\\"query_time_s\\": %.1f, \\"peak_memory_gb\\": %.1f}", qt + n1*3, mem + n2*1.5;
""",
        "factor_cases": '--join_algorithm) JA="$2"; shift 2 ;;\n        --hash_table_mb) HT="$2"; shift 2 ;;\n        --sort_buffer_mb) SB="$2"; shift 2 ;;\n        --broadcast_threshold_mb) BT="$2"; shift 2 ;;\n        --adaptive_execution) AE="$2"; shift 2 ;;\n        --partitions) PT="$2"; shift 2 ;;',
        "awk_vars": '-v JA="$JA" -v HT="$HT" -v SB="$SB" -v BT="$BT" -v AE="$AE" -v PT="$PT"',
        "vars_init": 'JA=""\nHT=""\nSB=""\nBT=""\nAE=""\nPT=""',
        "validate": '[ -z "$JA" ] || [ -z "$HT" ] || [ -z "$SB" ] || [ -z "$BT" ]',
    },
    {
        "num": 43, "slug": "index_selection_optimization",
        "name": "Index Selection Optimization",
        "desc": "Box-Behnken design optimizing index fill factor, page size, and parallel workers for throughput",
        "design": "box_behnken", "category": "data",
        "factors": [
            {"name": "fill_factor", "levels": ["50", "100"], "type": "continuous", "unit": "%", "description": "Index page fill factor"},
            {"name": "maintenance_work_mem_mb", "levels": ["64", "2048"], "type": "continuous", "unit": "MB", "description": "Memory for index operations"},
            {"name": "parallel_workers", "levels": ["0", "8"], "type": "continuous", "unit": "count", "description": "Parallel index build workers"},
        ],
        "fixed": {"table_rows": "50000000", "index_type": "btree"},
        "responses": [
            {"name": "build_time_s", "optimize": "minimize", "unit": "s", "description": "Index build time"},
            {"name": "query_speedup", "optimize": "maximize", "unit": "x", "description": "Query speedup over sequential scan"},
        ],
        "model": """
    ff = (FF - 75) / 25;
    mw = (MW - 1056) / 992;
    pw = (PW - 4) / 4;
    bt = 180 - 20*ff - 60*mw - 40*pw + 15*ff*ff + 10*mw*mw + 5*pw*pw + 8*ff*mw;
    qs = 25 + 8*ff + 3*mw + 5*pw - 2*ff*ff - 1*mw*mw + 1.5*ff*pw;
    if (bt < 10) bt = 10; if (qs < 1) qs = 1;
    printf "{\\"build_time_s\\": %.0f, \\"query_speedup\\": %.1f}", bt + n1*12, qs + n2*2;
""",
        "factor_cases": '--fill_factor) FF="$2"; shift 2 ;;\n        --maintenance_work_mem_mb) MW="$2"; shift 2 ;;\n        --parallel_workers) PW="$2"; shift 2 ;;',
        "awk_vars": '-v FF="$FF" -v MW="$MW" -v PW="$PW"',
        "vars_init": 'FF=""\nMW=""\nPW=""',
        "validate": '[ -z "$FF" ] || [ -z "$MW" ] || [ -z "$PW" ]',
    },
    {
        "num": 44, "slug": "data_replication_lag",
        "name": "Data Replication Lag",
        "desc": "Fractional factorial of 5 replication parameters for lag and failover readiness",
        "design": "fractional_factorial", "category": "data",
        "factors": [
            {"name": "sync_mode", "levels": ["async", "semi_sync"], "type": "categorical", "unit": "", "description": "Replication sync mode"},
            {"name": "binlog_batch_size", "levels": ["1", "100"], "type": "continuous", "unit": "txns", "description": "Binlog batch size"},
            {"name": "parallel_workers", "levels": ["1", "16"], "type": "continuous", "unit": "threads", "description": "Replica applier workers"},
            {"name": "network_buffer_kb", "levels": ["64", "1024"], "type": "continuous", "unit": "KB", "description": "Replication network buffer"},
            {"name": "compression", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Binlog compression"},
        ],
        "fixed": {"engine": "mysql_8", "gtid": "on"},
        "responses": [
            {"name": "replication_lag_ms", "optimize": "minimize", "unit": "ms", "description": "Median replication lag"},
            {"name": "failover_ready_pct", "optimize": "maximize", "unit": "%", "description": "Percentage of time replica is within RPO"},
        ],
        "model": """
    sm = (SM == "semi_sync") ? 1 : -1;
    bb = (BB - 50.5) / 49.5;
    pw = (PW - 8.5) / 7.5;
    nb = (NB - 544) / 480;
    comp = (COMP == "on") ? 1 : -1;
    lag = 200 + 150*sm - 80*bb - 100*pw - 40*nb - 30*comp + 50*sm*bb + 30*pw*nb;
    ready = 92 - 4*sm + 3*bb + 5*pw + 2*nb + 2*comp - 2*sm*pw;
    if (lag < 1) lag = 1; if (ready > 100) ready = 100; if (ready < 50) ready = 50;
    printf "{\\"replication_lag_ms\\": %.0f, \\"failover_ready_pct\\": %.1f}", lag + n1*30, ready + n2*1.5;
""",
        "factor_cases": '--sync_mode) SM="$2"; shift 2 ;;\n        --binlog_batch_size) BB="$2"; shift 2 ;;\n        --parallel_workers) PW="$2"; shift 2 ;;\n        --network_buffer_kb) NB="$2"; shift 2 ;;\n        --compression) COMP="$2"; shift 2 ;;',
        "awk_vars": '-v SM="$SM" -v BB="$BB" -v PW="$PW" -v NB="$NB" -v COMP="$COMP"',
        "vars_init": 'SM=""\nBB=""\nPW=""\nNB=""\nCOMP=""',
        "validate": '[ -z "$SM" ] || [ -z "$BB" ] || [ -z "$PW" ] || [ -z "$NB" ] || [ -z "$COMP" ]',
    },
    {
        "num": 45, "slug": "time_series_downsampling",
        "name": "Time-Series Downsampling",
        "desc": "Central Composite design for downsampling interval, retention policy, and aggregation for query speed",
        "design": "central_composite", "category": "data",
        "factors": [
            {"name": "downsample_interval_m", "levels": ["1", "60"], "type": "continuous", "unit": "min", "description": "Downsampling interval"},
            {"name": "retention_days", "levels": ["7", "365"], "type": "continuous", "unit": "days", "description": "Raw data retention"},
            {"name": "agg_functions", "levels": ["2", "8"], "type": "continuous", "unit": "count", "description": "Number of pre-computed aggregations"},
        ],
        "fixed": {"db_engine": "timescaledb", "ingestion_rate": "100000"},
        "responses": [
            {"name": "query_p95_ms", "optimize": "minimize", "unit": "ms", "description": "95th percentile query latency"},
            {"name": "storage_gb", "optimize": "minimize", "unit": "GB", "description": "Total storage footprint"},
        ],
        "model": """
    di = (DI - 30.5) / 29.5;
    ret = (RET - 186) / 179;
    af = (AF - 5) / 3;
    qp = 80 - 30*di + 40*ret - 20*af + 10*di*di + 15*ret*ret + 5*af*af + 8*di*ret;
    sg = 50 - 15*di + 35*ret + 5*af - 4*di*di + 8*ret*ret - 2*di*ret;
    if (qp < 5) qp = 5; if (sg < 1) sg = 1;
    printf "{\\"query_p95_ms\\": %.0f, \\"storage_gb\\": %.0f}", qp + n1*8, sg + n2*5;
""",
        "factor_cases": '--downsample_interval_m) DI="$2"; shift 2 ;;\n        --retention_days) RET="$2"; shift 2 ;;\n        --agg_functions) AF="$2"; shift 2 ;;',
        "awk_vars": '-v DI="$DI" -v RET="$RET" -v AF="$AF"',
        "vars_init": 'DI=""\nRET=""\nAF=""',
        "validate": '[ -z "$DI" ] || [ -z "$RET" ] || [ -z "$AF" ]',
    },
    {
        "num": 46, "slug": "feature_store_freshness",
        "name": "Feature Store Freshness",
        "desc": "Latin Hypercube of 4 feature store parameters for serving latency and feature freshness",
        "design": "latin_hypercube", "category": "data",
        "factors": [
            {"name": "materialization_interval_m", "levels": ["1", "60"], "type": "continuous", "unit": "min", "description": "Feature materialization interval"},
            {"name": "cache_ttl_s", "levels": ["10", "300"], "type": "continuous", "unit": "s", "description": "Online store cache TTL"},
            {"name": "batch_size", "levels": ["100", "10000"], "type": "continuous", "unit": "rows", "description": "Materialization batch size"},
            {"name": "online_replicas", "levels": ["1", "6"], "type": "continuous", "unit": "count", "description": "Online store replica count"},
        ],
        "fixed": {"offline_store": "s3_parquet", "online_store": "redis"},
        "responses": [
            {"name": "serving_latency_ms", "optimize": "minimize", "unit": "ms", "description": "Feature serving p99 latency"},
            {"name": "freshness_lag_min", "optimize": "minimize", "unit": "min", "description": "Feature freshness lag"},
        ],
        "model": """
    mi = (MI - 30.5) / 29.5;
    ct = (CT - 155) / 145;
    bs = (BS - 5050) / 4950;
    orep = (OREP - 3.5) / 2.5;
    slat = 5 + 2*mi + 3*ct - 4*orep + 0.5*bs + 1.5*ct*ct + 0.8*mi*ct - 1.2*orep*ct;
    fl = 3 + 8*mi - 2*ct + 1*bs - 0.5*orep + 2*mi*mi + 1.5*mi*bs;
    if (slat < 0.5) slat = 0.5; if (fl < 0.5) fl = 0.5;
    printf "{\\"serving_latency_ms\\": %.1f, \\"freshness_lag_min\\": %.1f}", slat + n1*0.8, fl + n2*1.0;
""",
        "factor_cases": '--materialization_interval_m) MI="$2"; shift 2 ;;\n        --cache_ttl_s) CT="$2"; shift 2 ;;\n        --batch_size) BS="$2"; shift 2 ;;\n        --online_replicas) OREP="$2"; shift 2 ;;',
        "awk_vars": '-v MI="$MI" -v CT="$CT" -v BS="$BS" -v OREP="$OREP"',
        "vars_init": 'MI=""\nCT=""\nBS=""\nOREP=""',
        "validate": '[ -z "$MI" ] || [ -z "$CT" ] || [ -z "$BS" ] || [ -z "$OREP" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: Networking & Protocol Tuning (47-56)
    # ══════════════════════════════════════════════════
    {
        "num": 47, "slug": "tcp_congestion_control",
        "name": "TCP Congestion Control",
        "desc": "Full factorial of congestion algorithm, initial window, buffer sizes, and ECN for throughput and fairness",
        "design": "full_factorial", "category": "networking",
        "factors": [
            {"name": "congestion_algo", "levels": ["cubic", "bbr"], "type": "categorical", "unit": "", "description": "TCP congestion control algorithm"},
            {"name": "init_cwnd", "levels": ["10", "40"], "type": "continuous", "unit": "segments", "description": "Initial congestion window"},
            {"name": "rmem_max_kb", "levels": ["256", "4096"], "type": "continuous", "unit": "KB", "description": "Maximum receive buffer"},
            {"name": "ecn", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Explicit Congestion Notification"},
        ],
        "fixed": {"mtu": "1500", "link_speed": "10Gbps"},
        "responses": [
            {"name": "throughput_gbps", "optimize": "maximize", "unit": "Gbps", "description": "Sustained TCP throughput"},
            {"name": "retransmit_pct", "optimize": "minimize", "unit": "%", "description": "Retransmission rate"},
        ],
        "model": """
    ca = (CA == "bbr") ? 1 : -1;
    iw = (IW - 25) / 15;
    rm = (RM - 2176) / 1920;
    ecn = (ECN == "on") ? 1 : -1;
    thr = 7.5 + 1.5*ca + 0.8*iw + 1.2*rm + 0.3*ecn + 0.4*ca*rm + 0.2*iw*rm;
    ret = 1.5 - 0.5*ca - 0.3*iw - 0.2*rm - 0.4*ecn + 0.15*ca*ecn + 0.1*iw*ecn;
    if (thr < 0.1) thr = 0.1; if (thr > 10) thr = 10;
    if (ret < 0.01) ret = 0.01;
    printf "{\\"throughput_gbps\\": %.2f, \\"retransmit_pct\\": %.3f}", thr + n1*0.3, ret + n2*0.15;
""",
        "factor_cases": '--congestion_algo) CA="$2"; shift 2 ;;\n        --init_cwnd) IW="$2"; shift 2 ;;\n        --rmem_max_kb) RM="$2"; shift 2 ;;\n        --ecn) ECN="$2"; shift 2 ;;',
        "awk_vars": '-v CA="$CA" -v IW="$IW" -v RM="$RM" -v ECN="$ECN"',
        "vars_init": 'CA=""\nIW=""\nRM=""\nECN=""',
        "validate": '[ -z "$CA" ] || [ -z "$IW" ] || [ -z "$RM" ] || [ -z "$ECN" ]',
    },
    {
        "num": 48, "slug": "tls_handshake_optimization",
        "name": "TLS Handshake Optimization",
        "desc": "Box-Behnken design for TLS version, cipher choice, and session cache for handshake speed",
        "design": "box_behnken", "category": "networking",
        "factors": [
            {"name": "session_cache_size", "levels": ["1000", "100000"], "type": "continuous", "unit": "entries", "description": "TLS session cache size"},
            {"name": "session_timeout_s", "levels": ["60", "86400"], "type": "continuous", "unit": "s", "description": "Session ticket timeout"},
            {"name": "ocsp_stapling_workers", "levels": ["1", "8"], "type": "continuous", "unit": "threads", "description": "OCSP stapling worker threads"},
        ],
        "fixed": {"tls_version": "1.3", "cipher": "AES-256-GCM"},
        "responses": [
            {"name": "handshake_ms", "optimize": "minimize", "unit": "ms", "description": "Full TLS handshake latency"},
            {"name": "resumption_rate", "optimize": "maximize", "unit": "%", "description": "Session resumption rate"},
        ],
        "model": """
    sc = (SC - 50500) / 49500;
    st = (ST - 43230) / 43170;
    ow = (OW - 4.5) / 3.5;
    hs = 45 - 12*sc - 8*st - 5*ow + 4*sc*sc + 3*st*st + 1*ow*ow + 2*sc*st;
    res = 55 + 20*sc + 15*st + 3*ow - 5*sc*sc - 4*st*st + 3*sc*st;
    if (hs < 2) hs = 2; if (res > 99) res = 99; if (res < 10) res = 10;
    printf "{\\"handshake_ms\\": %.1f, \\"resumption_rate\\": %.1f}", hs + n1*3, res + n2*3;
""",
        "factor_cases": '--session_cache_size) SC="$2"; shift 2 ;;\n        --session_timeout_s) ST="$2"; shift 2 ;;\n        --ocsp_stapling_workers) OW="$2"; shift 2 ;;',
        "awk_vars": '-v SC="$SC" -v ST="$ST" -v OW="$OW"',
        "vars_init": 'SC=""\nST=""\nOW=""',
        "validate": '[ -z "$SC" ] || [ -z "$ST" ] || [ -z "$OW" ]',
    },
    {
        "num": 49, "slug": "firewall_rule_ordering",
        "name": "Firewall Rule Ordering",
        "desc": "Plackett-Burman screening of 6 iptables/nftables parameters for packet processing throughput",
        "design": "plackett_burman", "category": "networking",
        "factors": [
            {"name": "rule_count", "levels": ["100", "5000"], "type": "continuous", "unit": "rules", "description": "Total number of firewall rules"},
            {"name": "conntrack_max", "levels": ["65536", "1048576"], "type": "continuous", "unit": "entries", "description": "Connection tracking table size"},
            {"name": "rule_ordering", "levels": ["frequency", "sequential"], "type": "categorical", "unit": "", "description": "Rule evaluation ordering strategy"},
            {"name": "hashlimit_burst", "levels": ["5", "100"], "type": "continuous", "unit": "packets", "description": "Hashlimit burst size"},
            {"name": "nf_tables", "levels": ["iptables", "nftables"], "type": "categorical", "unit": "", "description": "Firewall framework"},
            {"name": "batch_verdict", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Batch verdict processing"},
        ],
        "fixed": {"interface": "eth0", "protocol_mix": "80_tcp_20_udp"},
        "responses": [
            {"name": "throughput_mpps", "optimize": "maximize", "unit": "Mpps", "description": "Packet throughput in millions per second"},
            {"name": "latency_us", "optimize": "minimize", "unit": "us", "description": "Per-packet processing latency"},
        ],
        "model": """
    rc = (RC - 2550) / 2450;
    ct = (CT - 557056) / 491520;
    ro = (RO == "frequency") ? 1 : -1;
    hl = (HL - 52.5) / 47.5;
    nf = (NF == "nftables") ? 1 : -1;
    bv = (BV == "on") ? 1 : -1;
    thr = 2.5 - 0.8*rc + 0.3*ct + 0.5*ro - 0.1*hl + 0.6*nf + 0.4*bv + 0.2*ro*nf;
    lat = 15 + 8*rc - 2*ct - 4*ro + 1*hl - 5*nf - 3*bv + 2*rc*ro;
    if (thr < 0.1) thr = 0.1; if (lat < 1) lat = 1;
    printf "{\\"throughput_mpps\\": %.2f, \\"latency_us\\": %.1f}", thr + n1*0.15, lat + n2*2;
""",
        "factor_cases": '--rule_count) RC="$2"; shift 2 ;;\n        --conntrack_max) CT="$2"; shift 2 ;;\n        --rule_ordering) RO="$2"; shift 2 ;;\n        --hashlimit_burst) HL="$2"; shift 2 ;;\n        --nf_tables) NF="$2"; shift 2 ;;\n        --batch_verdict) BV="$2"; shift 2 ;;',
        "awk_vars": '-v RC="$RC" -v CT="$CT" -v RO="$RO" -v HL="$HL" -v NF="$NF" -v BV="$BV"',
        "vars_init": 'RC=""\nCT=""\nRO=""\nHL=""\nNF=""\nBV=""',
        "validate": '[ -z "$RC" ] || [ -z "$CT" ] || [ -z "$RO" ] || [ -z "$HL" ]',
    },
    {
        "num": 50, "slug": "dns_resolver_caching",
        "name": "DNS Resolver Caching",
        "desc": "Central Composite design for DNS cache size, TTL override, and prefetch threshold for resolution time",
        "design": "central_composite", "category": "networking",
        "factors": [
            {"name": "cache_size", "levels": ["10000", "500000"], "type": "continuous", "unit": "entries", "description": "Resolver cache size"},
            {"name": "min_ttl_s", "levels": ["30", "3600"], "type": "continuous", "unit": "s", "description": "Minimum TTL override"},
            {"name": "prefetch_pct", "levels": ["0", "90"], "type": "continuous", "unit": "%", "description": "Prefetch threshold (% of TTL remaining)"},
        ],
        "fixed": {"resolver": "unbound", "dnssec": "on"},
        "responses": [
            {"name": "avg_resolution_ms", "optimize": "minimize", "unit": "ms", "description": "Average DNS resolution time"},
            {"name": "cache_hit_rate", "optimize": "maximize", "unit": "%", "description": "Cache hit rate"},
        ],
        "model": """
    cs = (CS - 255000) / 245000;
    mt = (MT - 1815) / 1785;
    pf = (PF - 45) / 45;
    res = 25 - 8*cs - 6*mt - 10*pf + 3*cs*cs + 2*mt*mt + 4*pf*pf + 1.5*cs*mt;
    hit = 72 + 10*cs + 8*mt + 12*pf - 3*cs*cs - 2*mt*mt - 4*pf*pf + 2*cs*pf;
    if (res < 0.5) res = 0.5; if (hit > 99.5) hit = 99.5; if (hit < 20) hit = 20;
    printf "{\\"avg_resolution_ms\\": %.1f, \\"cache_hit_rate\\": %.1f}", res + n1*2, hit + n2*2;
""",
        "factor_cases": '--cache_size) CS="$2"; shift 2 ;;\n        --min_ttl_s) MT="$2"; shift 2 ;;\n        --prefetch_pct) PF="$2"; shift 2 ;;',
        "awk_vars": '-v CS="$CS" -v MT="$MT" -v PF="$PF"',
        "vars_init": 'CS=""\nMT=""\nPF=""',
        "validate": '[ -z "$CS" ] || [ -z "$MT" ] || [ -z "$PF" ]',
    },
    {
        "num": 51, "slug": "bgp_route_convergence",
        "name": "BGP Route Convergence",
        "desc": "Fractional factorial of 5 BGP timer and dampening parameters for convergence speed",
        "design": "fractional_factorial", "category": "networking",
        "factors": [
            {"name": "keepalive_s", "levels": ["10", "60"], "type": "continuous", "unit": "s", "description": "BGP keepalive interval"},
            {"name": "hold_time_s", "levels": ["30", "180"], "type": "continuous", "unit": "s", "description": "BGP hold time"},
            {"name": "mrai_s", "levels": ["5", "30"], "type": "continuous", "unit": "s", "description": "Minimum route advertisement interval"},
            {"name": "dampening", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Route flap dampening"},
            {"name": "bfd", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Bidirectional forwarding detection"},
        ],
        "fixed": {"as_count": "50", "topology": "partial_mesh"},
        "responses": [
            {"name": "convergence_time_s", "optimize": "minimize", "unit": "s", "description": "Network convergence time"},
            {"name": "route_stability", "optimize": "maximize", "unit": "%", "description": "Route stability index"},
        ],
        "model": """
    ka = (KA - 35) / 25;
    ht = (HT - 105) / 75;
    mr = (MR - 17.5) / 12.5;
    dmp = (DMP == "on") ? 1 : -1;
    bfd = (BFD == "on") ? 1 : -1;
    conv = 45 + 12*ka + 15*ht + 8*mr + 5*dmp - 20*bfd + 3*ka*ht - 4*bfd*ka;
    stab = 85 - 3*ka - 5*ht - 2*mr + 8*dmp + 3*bfd - 2*ka*ht + 3*dmp*bfd;
    if (conv < 1) conv = 1; if (stab > 100) stab = 100; if (stab < 50) stab = 50;
    printf "{\\"convergence_time_s\\": %.1f, \\"route_stability\\": %.1f}", conv + n1*4, stab + n2*2;
""",
        "factor_cases": '--keepalive_s) KA="$2"; shift 2 ;;\n        --hold_time_s) HT="$2"; shift 2 ;;\n        --mrai_s) MR="$2"; shift 2 ;;\n        --dampening) DMP="$2"; shift 2 ;;\n        --bfd) BFD="$2"; shift 2 ;;',
        "awk_vars": '-v KA="$KA" -v HT="$HT" -v MR="$MR" -v DMP="$DMP" -v BFD="$BFD"',
        "vars_init": 'KA=""\nHT=""\nMR=""\nDMP=""\nBFD=""',
        "validate": '[ -z "$KA" ] || [ -z "$HT" ] || [ -z "$MR" ] || [ -z "$DMP" ] || [ -z "$BFD" ]',
    },
    {
        "num": 52, "slug": "vpn_tunnel_mtu",
        "name": "VPN Tunnel MTU",
        "desc": "Box-Behnken design for MTU, fragmentation, and keepalive to optimize throughput and reconnect time",
        "design": "box_behnken", "category": "networking",
        "factors": [
            {"name": "tunnel_mtu", "levels": ["1200", "1500"], "type": "continuous", "unit": "bytes", "description": "VPN tunnel MTU"},
            {"name": "fragment_size", "levels": ["0", "1400"], "type": "continuous", "unit": "bytes", "description": "Fragment size (0=disabled)"},
            {"name": "keepalive_interval", "levels": ["10", "120"], "type": "continuous", "unit": "s", "description": "Tunnel keepalive interval"},
        ],
        "fixed": {"protocol": "wireguard", "encryption": "chacha20"},
        "responses": [
            {"name": "throughput_mbps", "optimize": "maximize", "unit": "Mbps", "description": "Sustained tunnel throughput"},
            {"name": "reconnect_time_s", "optimize": "minimize", "unit": "s", "description": "Tunnel reconnect time after drop"},
        ],
        "model": """
    mtu = (MTU - 1350) / 150;
    frag = (FRAG - 700) / 700;
    ka = (KA - 65) / 55;
    thr = 850 + 80*mtu - 40*frag - 10*ka - 30*mtu*mtu + 15*frag*frag + 20*mtu*frag;
    rec = 8 + 1*mtu + 2*frag + 5*ka - 0.5*mtu*ka + 1.5*ka*ka;
    if (thr < 10) thr = 10; if (rec < 0.5) rec = 0.5;
    printf "{\\"throughput_mbps\\": %.0f, \\"reconnect_time_s\\": %.1f}", thr + n1*30, rec + n2*1.0;
""",
        "factor_cases": '--tunnel_mtu) MTU="$2"; shift 2 ;;\n        --fragment_size) FRAG="$2"; shift 2 ;;\n        --keepalive_interval) KA="$2"; shift 2 ;;',
        "awk_vars": '-v MTU="$MTU" -v FRAG="$FRAG" -v KA="$KA"',
        "vars_init": 'MTU=""\nFRAG=""\nKA=""',
        "validate": '[ -z "$MTU" ] || [ -z "$FRAG" ] || [ -z "$KA" ]',
    },
    {
        "num": 53, "slug": "ddos_mitigation_threshold",
        "name": "DDoS Mitigation Threshold",
        "desc": "Plackett-Burman screening of 6 anti-DDoS parameters for detection accuracy and clean traffic impact",
        "design": "plackett_burman", "category": "networking",
        "factors": [
            {"name": "syn_rate_limit", "levels": ["1000", "50000"], "type": "continuous", "unit": "pps", "description": "SYN flood rate limit threshold"},
            {"name": "connection_limit", "levels": ["100", "10000"], "type": "continuous", "unit": "conns/IP", "description": "Per-IP connection limit"},
            {"name": "challenge_mode", "levels": ["off", "javascript"], "type": "categorical", "unit": "", "description": "Client challenge type"},
            {"name": "geo_blocking", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Geographic IP blocking"},
            {"name": "anomaly_window_s", "levels": ["10", "300"], "type": "continuous", "unit": "s", "description": "Anomaly detection window"},
            {"name": "whitelist_size", "levels": ["100", "10000"], "type": "continuous", "unit": "IPs", "description": "Trusted IP whitelist size"},
        ],
        "fixed": {"mitigation_provider": "in_house", "baseline_traffic": "5000_rps"},
        "responses": [
            {"name": "detection_rate", "optimize": "maximize", "unit": "%", "description": "Attack detection rate"},
            {"name": "false_positive_pct", "optimize": "minimize", "unit": "%", "description": "Legitimate traffic blocked"},
        ],
        "model": """
    sr = (SR - 25500) / 24500;
    cl = (CL - 5050) / 4950;
    cm = (CM == "javascript") ? 1 : -1;
    gb = (GB == "on") ? 1 : -1;
    aw = (AW - 155) / 145;
    wl = (WL - 5050) / 4950;
    det = 88 + 4*sr + 3*cl + 5*cm + 2*gb + 3*aw - 1*wl + 1.5*cm*aw;
    fp = 3 + 2*sr + 1.5*cl + 3*cm + 4*gb + 1*aw - 2*wl + 0.8*cm*gb;
    if (det > 100) det = 100; if (det < 50) det = 50;
    if (fp < 0.1) fp = 0.1;
    printf "{\\"detection_rate\\": %.1f, \\"false_positive_pct\\": %.2f}", det + n1*2, fp + n2*0.5;
""",
        "factor_cases": '--syn_rate_limit) SR="$2"; shift 2 ;;\n        --connection_limit) CL="$2"; shift 2 ;;\n        --challenge_mode) CM="$2"; shift 2 ;;\n        --geo_blocking) GB="$2"; shift 2 ;;\n        --anomaly_window_s) AW="$2"; shift 2 ;;\n        --whitelist_size) WL="$2"; shift 2 ;;',
        "awk_vars": '-v SR="$SR" -v CL="$CL" -v CM="$CM" -v GB="$GB" -v AW="$AW" -v WL="$WL"',
        "vars_init": 'SR=""\nCL=""\nCM=""\nGB=""\nAW=""\nWL=""',
        "validate": '[ -z "$SR" ] || [ -z "$CL" ] || [ -z "$CM" ] || [ -z "$GB" ]',
    },
    {
        "num": 54, "slug": "http2_stream_multiplexing",
        "name": "HTTP/2 Stream Multiplexing",
        "desc": "Full factorial of max concurrent streams, window size, header table size, and priority for page load time",
        "design": "full_factorial", "category": "networking",
        "factors": [
            {"name": "max_concurrent_streams", "levels": ["50", "250"], "type": "continuous", "unit": "streams", "description": "Max concurrent HTTP/2 streams"},
            {"name": "window_size_kb", "levels": ["64", "1024"], "type": "continuous", "unit": "KB", "description": "Flow control window size"},
            {"name": "header_table_kb", "levels": ["4", "64"], "type": "continuous", "unit": "KB", "description": "HPACK header table size"},
            {"name": "priority_enabled", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Stream priority scheduling"},
        ],
        "fixed": {"tls": "1.3", "server": "nginx"},
        "responses": [
            {"name": "page_load_ms", "optimize": "minimize", "unit": "ms", "description": "Full page load time"},
            {"name": "ttfb_ms", "optimize": "minimize", "unit": "ms", "description": "Time to first byte"},
        ],
        "model": """
    mcs = (MCS - 150) / 100;
    ws = (WS - 544) / 480;
    ht = (HT - 34) / 30;
    pr = (PR == "on") ? 1 : -1;
    plt = 1200 - 150*mcs - 200*ws - 80*ht - 100*pr + 40*mcs*mcs + 30*ws*ws + 20*mcs*ws;
    ttfb = 120 - 15*mcs - 30*ws - 10*ht - 20*pr + 5*mcs*ws + 8*ws*ws;
    if (plt < 200) plt = 200; if (ttfb < 20) ttfb = 20;
    printf "{\\"page_load_ms\\": %.0f, \\"ttfb_ms\\": %.0f}", plt + n1*60, ttfb + n2*10;
""",
        "factor_cases": '--max_concurrent_streams) MCS="$2"; shift 2 ;;\n        --window_size_kb) WS="$2"; shift 2 ;;\n        --header_table_kb) HT="$2"; shift 2 ;;\n        --priority_enabled) PR="$2"; shift 2 ;;',
        "awk_vars": '-v MCS="$MCS" -v WS="$WS" -v HT="$HT" -v PR="$PR"',
        "vars_init": 'MCS=""\nWS=""\nHT=""\nPR=""',
        "validate": '[ -z "$MCS" ] || [ -z "$WS" ] || [ -z "$HT" ] || [ -z "$PR" ]',
    },
    {
        "num": 55, "slug": "network_buffer_sizing",
        "name": "Network Buffer Sizing",
        "desc": "Latin Hypercube of 4 kernel network buffer parameters for throughput and latency",
        "design": "latin_hypercube", "category": "networking",
        "factors": [
            {"name": "netdev_budget", "levels": ["128", "1024"], "type": "continuous", "unit": "packets", "description": "NAPI polling budget"},
            {"name": "txqueuelen", "levels": ["500", "10000"], "type": "continuous", "unit": "packets", "description": "Transmit queue length"},
            {"name": "tcp_wmem_max_kb", "levels": ["256", "16384"], "type": "continuous", "unit": "KB", "description": "Max TCP write buffer"},
            {"name": "backlog_max", "levels": ["1000", "65536"], "type": "continuous", "unit": "packets", "description": "Netdev backlog max"},
        ],
        "fixed": {"nic": "mlx5", "ring_buffer": "4096"},
        "responses": [
            {"name": "throughput_gbps", "optimize": "maximize", "unit": "Gbps", "description": "Network throughput"},
            {"name": "softirq_pct", "optimize": "minimize", "unit": "%", "description": "CPU time in softirq"},
        ],
        "model": """
    nb = (NB - 576) / 448;
    tq = (TQ - 5250) / 4750;
    tw = (TW - 8320) / 8064;
    bl = (BL - 33268) / 32268;
    thr = 8 + 1.5*nb + 0.5*tq + 2*tw + 0.8*bl - 0.6*nb*nb + 0.3*nb*tw - 0.4*tq*tq;
    sirq = 12 + 5*nb - 1*tq + 2*tw + 3*bl + 1.5*nb*bl - 0.8*nb*nb;
    if (thr < 0.5) thr = 0.5; if (thr > 25) thr = 25;
    if (sirq < 1) sirq = 1;
    printf "{\\"throughput_gbps\\": %.1f, \\"softirq_pct\\": %.1f}", thr + n1*0.5, sirq + n2*1.5;
""",
        "factor_cases": '--netdev_budget) NB="$2"; shift 2 ;;\n        --txqueuelen) TQ="$2"; shift 2 ;;\n        --tcp_wmem_max_kb) TW="$2"; shift 2 ;;\n        --backlog_max) BL="$2"; shift 2 ;;',
        "awk_vars": '-v NB="$NB" -v TQ="$TQ" -v TW="$TW" -v BL="$BL"',
        "vars_init": 'NB=""\nTQ=""\nTW=""\nBL=""',
        "validate": '[ -z "$NB" ] || [ -z "$TQ" ] || [ -z "$TW" ] || [ -z "$BL" ]',
    },
    {
        "num": 56, "slug": "wifi_channel_power",
        "name": "WiFi Channel & Power",
        "desc": "Fractional factorial of 5 WiFi AP parameters for throughput and coverage",
        "design": "fractional_factorial", "category": "networking",
        "factors": [
            {"name": "channel_width", "levels": ["20", "80"], "type": "continuous", "unit": "MHz", "description": "Channel bandwidth"},
            {"name": "tx_power", "levels": ["10", "23"], "type": "continuous", "unit": "dBm", "description": "Transmit power level"},
            {"name": "guard_interval", "levels": ["short", "long"], "type": "categorical", "unit": "", "description": "Guard interval"},
            {"name": "beamforming", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Explicit beamforming"},
            {"name": "spatial_streams", "levels": ["1", "4"], "type": "continuous", "unit": "count", "description": "MIMO spatial streams"},
        ],
        "fixed": {"standard": "wifi6", "band": "5GHz"},
        "responses": [
            {"name": "throughput_mbps", "optimize": "maximize", "unit": "Mbps", "description": "Average client throughput"},
            {"name": "coverage_m", "optimize": "maximize", "unit": "m", "description": "Effective coverage radius"},
        ],
        "model": """
    cw = (CW - 50) / 30;
    tp = (TP - 16.5) / 6.5;
    gi = (GI == "short") ? 1 : -1;
    bf = (BF == "on") ? 1 : -1;
    ss = (SS - 2.5) / 1.5;
    thr = 500 + 200*cw + 50*tp + 40*gi + 60*bf + 150*ss + 30*cw*ss - 20*cw*cw;
    cov = 25 - 5*cw + 8*tp - 1*gi + 4*bf + 2*ss + 1.5*tp*bf - 2*cw*tp;
    if (thr < 10) thr = 10; if (cov < 5) cov = 5;
    printf "{\\"throughput_mbps\\": %.0f, \\"coverage_m\\": %.0f}", thr + n1*30, cov + n2*2;
""",
        "factor_cases": '--channel_width) CW="$2"; shift 2 ;;\n        --tx_power) TP="$2"; shift 2 ;;\n        --guard_interval) GI="$2"; shift 2 ;;\n        --beamforming) BF="$2"; shift 2 ;;\n        --spatial_streams) SS="$2"; shift 2 ;;',
        "awk_vars": '-v CW="$CW" -v TP="$TP" -v GI="$GI" -v BF="$BF" -v SS="$SS"',
        "vars_init": 'CW=""\nTP=""\nGI=""\nBF=""\nSS=""',
        "validate": '[ -z "$CW" ] || [ -z "$TP" ] || [ -z "$GI" ] || [ -z "$BF" ] || [ -z "$SS" ]',
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
