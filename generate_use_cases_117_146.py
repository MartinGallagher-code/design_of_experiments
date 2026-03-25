#!/usr/bin/env python3
"""Generate 30 new use cases across 3 non-computer categories (117-146).

Categories:
  - Automotive & Transportation (117-126)
  - Environmental & Energy (127-136)
  - Home & DIY (137-146)
"""
import json, os, stat, textwrap

USE_CASES = [
    # ══════════════════════════════════════════════════
    # Category: Automotive & Transportation (117-126)
    # ══════════════════════════════════════════════════
    {
        "num": 117, "slug": "tire_pressure_fuel",
        "name": "Tire Pressure & Fuel Economy",
        "desc": "Box-Behnken design to maximize fuel economy and minimize tire wear by tuning front pressure, rear pressure, and load weight",
        "design": "box_behnken", "category": "automotive",
        "factors": [
            {"name": "front_psi", "levels": ["28", "38"], "type": "continuous", "unit": "psi", "description": "Front tire pressure"},
            {"name": "rear_psi", "levels": ["28", "38"], "type": "continuous", "unit": "psi", "description": "Rear tire pressure"},
            {"name": "load_kg", "levels": ["100", "400"], "type": "continuous", "unit": "kg", "description": "Cargo load weight"},
        ],
        "fixed": {"vehicle": "sedan", "tire_model": "all_season"},
        "responses": [
            {"name": "mpg", "optimize": "maximize", "unit": "mpg", "description": "Miles per gallon fuel economy"},
            {"name": "wear_rate", "optimize": "minimize", "unit": "mm/10k_mi", "description": "Tire tread wear rate"},
        ],
        "model": """
    fp = (FP - 33) / 5;
    rp = (RP - 33) / 5;
    lk = (LK - 250) / 150;
    mpg = 32 + 1.5*fp + 1.2*rp - 2.5*lk - 0.8*fp*fp - 0.6*rp*rp + 0.4*fp*rp - 0.3*fp*lk;
    wear = 1.8 - 0.3*fp - 0.2*rp + 0.5*lk + 0.2*fp*fp + 0.15*rp*rp + 0.1*fp*lk;
    if (mpg < 15) mpg = 15;
    if (wear < 0.3) wear = 0.3;
    printf "{\\"mpg\\": %.1f, \\"wear_rate\\": %.2f}", mpg + n1*0.8, wear + n2*0.1;
""",
        "factor_cases": '--front_psi) FP="$2"; shift 2 ;;\n        --rear_psi) RP="$2"; shift 2 ;;\n        --load_kg) LK="$2"; shift 2 ;;',
        "awk_vars": '-v FP="$FP" -v RP="$RP" -v LK="$LK"',
        "vars_init": 'FP=""\nRP=""\nLK=""',
        "validate": '[ -z "$FP" ] || [ -z "$RP" ] || [ -z "$LK" ]',
    },
    {
        "num": 118, "slug": "engine_oil_change",
        "name": "Engine Oil Change Interval",
        "desc": "Central composite design to maximize engine longevity and minimize cost by tuning oil viscosity, change interval, and filter quality",
        "design": "central_composite", "category": "automotive",
        "factors": [
            {"name": "viscosity_w", "levels": ["0", "10"], "type": "continuous", "unit": "W", "description": "Oil winter viscosity grade (0W, 5W, 10W)"},
            {"name": "change_interval", "levels": ["3000", "10000"], "type": "continuous", "unit": "miles", "description": "Oil change interval in miles"},
            {"name": "filter_quality", "levels": ["1", "5"], "type": "continuous", "unit": "tier", "description": "Oil filter quality tier (1=economy, 5=premium)"},
        ],
        "fixed": {"engine_type": "gasoline_4cyl", "driving_style": "mixed"},
        "responses": [
            {"name": "engine_health", "optimize": "maximize", "unit": "pts", "description": "Engine health score based on oil analysis (1-100)"},
            {"name": "annual_cost", "optimize": "minimize", "unit": "USD", "description": "Annual oil maintenance cost"},
        ],
        "model": """
    vw = (VW - 5) / 5;
    ci = (CI - 6500) / 3500;
    fq = (FQ - 3) / 2;
    health = 82 + 3*vw - 8*ci + 5*fq - 1.5*vw*vw - 3*ci*ci - 1*fq*fq + 2*ci*fq;
    cost = 120 + 10*vw - 30*ci + 25*fq + 5*vw*fq;
    if (health < 30) health = 30; if (health > 100) health = 100;
    if (cost < 40) cost = 40;
    printf "{\\"engine_health\\": %.0f, \\"annual_cost\\": %.0f}", health + n1*3, cost + n2*8;
""",
        "factor_cases": '--viscosity_w) VW="$2"; shift 2 ;;\n        --change_interval) CI="$2"; shift 2 ;;\n        --filter_quality) FQ="$2"; shift 2 ;;',
        "awk_vars": '-v VW="$VW" -v CI="$CI" -v FQ="$FQ"',
        "vars_init": 'VW=""\nCI=""\nFQ=""',
        "validate": '[ -z "$VW" ] || [ -z "$CI" ] || [ -z "$FQ" ]',
    },
    {
        "num": 119, "slug": "ev_range_optimization",
        "name": "EV Range Optimization",
        "desc": "Full factorial of driving speed, cabin temperature, regenerative braking level, and tire type to maximize range and minimize energy consumption",
        "design": "full_factorial", "category": "automotive",
        "factors": [
            {"name": "speed_kph", "levels": ["60", "120"], "type": "continuous", "unit": "kph", "description": "Cruising speed"},
            {"name": "cabin_temp", "levels": ["18", "26"], "type": "continuous", "unit": "C", "description": "Cabin climate set temperature"},
            {"name": "regen_level", "levels": ["1", "3"], "type": "continuous", "unit": "level", "description": "Regenerative braking level"},
            {"name": "tire_type", "levels": ["standard", "low_rolling"], "type": "categorical", "unit": "", "description": "Tire rolling resistance type"},
        ],
        "fixed": {"battery_kwh": "75", "vehicle_type": "suv"},
        "responses": [
            {"name": "range_km", "optimize": "maximize", "unit": "km", "description": "Estimated driving range"},
            {"name": "kwh_per_100km", "optimize": "minimize", "unit": "kWh/100km", "description": "Energy consumption per 100 km"},
        ],
        "model": """
    sp = (SP - 90) / 30;
    ct = (CT - 22) / 4;
    rl = (RL - 2) / 1;
    tt = (TT == "low_rolling") ? 1 : -1;
    kwh = 18 + 4*sp + 1.5*ct - 1.2*rl - 1.5*tt + 1.5*sp*sp + 0.5*ct*ct + 0.3*sp*ct;
    range_ = 75 / kwh * 100;
    if (kwh < 10) kwh = 10;
    if (range_ < 150) range_ = 150;
    printf "{\\"range_km\\": %.0f, \\"kwh_per_100km\\": %.1f}", range_ + n1*8, kwh + n2*0.5;
""",
        "factor_cases": '--speed_kph) SP="$2"; shift 2 ;;\n        --cabin_temp) CT="$2"; shift 2 ;;\n        --regen_level) RL="$2"; shift 2 ;;\n        --tire_type) TT="$2"; shift 2 ;;',
        "awk_vars": '-v SP="$SP" -v CT="$CT" -v RL="$RL" -v TT="$TT"',
        "vars_init": 'SP=""\nCT=""\nRL=""\nTT=""',
        "validate": '[ -z "$SP" ] || [ -z "$CT" ] || [ -z "$RL" ] || [ -z "$TT" ]',
    },
    {
        "num": 120, "slug": "car_wash_quality",
        "name": "Car Wash Quality Optimization",
        "desc": "Box-Behnken design to maximize wash quality and minimize water usage by tuning water pressure, soap concentration, and rinse duration",
        "design": "box_behnken", "category": "automotive",
        "factors": [
            {"name": "water_pressure", "levels": ["800", "2000"], "type": "continuous", "unit": "psi", "description": "Pressure washer setting"},
            {"name": "soap_dilution", "levels": ["1", "10"], "type": "continuous", "unit": "ratio", "description": "Soap-to-water dilution ratio (1:X)"},
            {"name": "rinse_sec", "levels": ["30", "120"], "type": "continuous", "unit": "sec", "description": "Final rinse duration in seconds"},
        ],
        "fixed": {"wash_type": "touchless", "water_temp": "warm"},
        "responses": [
            {"name": "clean_score", "optimize": "maximize", "unit": "pts", "description": "Cleanliness score (1-10)"},
            {"name": "water_liters", "optimize": "minimize", "unit": "L", "description": "Total water consumption in liters"},
        ],
        "model": """
    wp = (WP - 1400) / 600;
    sd = (SD - 5.5) / 4.5;
    rs = (RS - 75) / 45;
    clean = 6.5 + 1.5*wp - 1.0*sd + 0.5*rs - 0.6*wp*wp + 0.3*sd*sd + 0.4*wp*sd;
    water = 80 + 20*wp - 5*sd + 15*rs + 5*wp*rs;
    if (clean < 1) clean = 1; if (clean > 10) clean = 10;
    if (water < 20) water = 20;
    printf "{\\"clean_score\\": %.1f, \\"water_liters\\": %.0f}", clean + n1*0.3, water + n2*5;
""",
        "factor_cases": '--water_pressure) WP="$2"; shift 2 ;;\n        --soap_dilution) SD="$2"; shift 2 ;;\n        --rinse_sec) RS="$2"; shift 2 ;;',
        "awk_vars": '-v WP="$WP" -v SD="$SD" -v RS="$RS"',
        "vars_init": 'WP=""\nSD=""\nRS=""',
        "validate": '[ -z "$WP" ] || [ -z "$SD" ] || [ -z "$RS" ]',
    },
    {
        "num": 121, "slug": "bicycle_gear_cadence",
        "name": "Bicycle Gearing & Cadence",
        "desc": "Central composite design to maximize average speed and minimize perceived effort by tuning gear ratio, cadence, and tire pressure",
        "design": "central_composite", "category": "automotive",
        "factors": [
            {"name": "gear_ratio", "levels": ["2.0", "4.0"], "type": "continuous", "unit": "ratio", "description": "Front-to-rear gear ratio"},
            {"name": "cadence_rpm", "levels": ["60", "100"], "type": "continuous", "unit": "rpm", "description": "Pedaling cadence"},
            {"name": "tire_psi", "levels": ["60", "110"], "type": "continuous", "unit": "psi", "description": "Tire inflation pressure"},
        ],
        "fixed": {"terrain": "rolling_hills", "rider_weight": "75kg"},
        "responses": [
            {"name": "avg_speed_kph", "optimize": "maximize", "unit": "kph", "description": "Average speed over test course"},
            {"name": "effort_score", "optimize": "minimize", "unit": "pts", "description": "Perceived effort score (1-10)"},
        ],
        "model": """
    gr = (GR - 3) / 1;
    cd = (CD - 80) / 20;
    tp = (TP - 85) / 25;
    spd = 25 + 2*gr + 1.5*cd + 0.8*tp - 1*gr*gr - 0.8*cd*cd - 0.3*tp*tp + 0.5*gr*cd;
    eff = 5.0 + 1.2*gr + 0.8*cd - 0.2*tp + 0.5*gr*gr + 0.3*cd*cd + 0.4*gr*cd;
    if (spd < 10) spd = 10;
    if (eff < 1) eff = 1; if (eff > 10) eff = 10;
    printf "{\\"avg_speed_kph\\": %.1f, \\"effort_score\\": %.1f}", spd + n1*0.8, eff + n2*0.3;
""",
        "factor_cases": '--gear_ratio) GR="$2"; shift 2 ;;\n        --cadence_rpm) CD="$2"; shift 2 ;;\n        --tire_psi) TP="$2"; shift 2 ;;',
        "awk_vars": '-v GR="$GR" -v CD="$CD" -v TP="$TP"',
        "vars_init": 'GR=""\nCD=""\nTP=""',
        "validate": '[ -z "$GR" ] || [ -z "$CD" ] || [ -z "$TP" ]',
    },
    {
        "num": 122, "slug": "traffic_signal_timing",
        "name": "Traffic Signal Timing",
        "desc": "Plackett-Burman screening of green phase duration, cycle length, offset, pedestrian phase, left-turn phase, and sensor delay for throughput and average wait time",
        "design": "plackett_burman", "category": "automotive",
        "factors": [
            {"name": "green_sec", "levels": ["15", "60"], "type": "continuous", "unit": "sec", "description": "Main road green phase duration"},
            {"name": "cycle_sec", "levels": ["60", "150"], "type": "continuous", "unit": "sec", "description": "Total signal cycle length"},
            {"name": "offset_pct", "levels": ["0", "50"], "type": "continuous", "unit": "%", "description": "Offset percentage for coordination"},
            {"name": "ped_phase_sec", "levels": ["10", "30"], "type": "continuous", "unit": "sec", "description": "Pedestrian crossing phase"},
            {"name": "left_turn_sec", "levels": ["0", "20"], "type": "continuous", "unit": "sec", "description": "Protected left-turn phase"},
            {"name": "sensor_delay", "levels": ["1", "5"], "type": "continuous", "unit": "sec", "description": "Vehicle detection sensor delay"},
        ],
        "fixed": {"intersection_type": "4_way", "time_of_day": "peak"},
        "responses": [
            {"name": "throughput_vph", "optimize": "maximize", "unit": "veh/hr", "description": "Vehicle throughput per hour"},
            {"name": "avg_wait_sec", "optimize": "minimize", "unit": "sec", "description": "Average vehicle wait time"},
        ],
        "model": """
    gs = (GS - 37.5) / 22.5;
    cs = (CS - 105) / 45;
    op = (OP - 25) / 25;
    pp = (PP - 20) / 10;
    lt = (LT - 10) / 10;
    sd = (SD - 3) / 2;
    thr = 1200 + 150*gs - 100*cs + 80*op - 60*pp - 40*lt - 30*sd + 20*gs*op;
    wait = 45 - 10*gs + 15*cs - 8*op + 5*pp + 4*lt + 3*sd + 3*cs*pp;
    if (thr < 400) thr = 400;
    if (wait < 5) wait = 5;
    printf "{\\"throughput_vph\\": %.0f, \\"avg_wait_sec\\": %.0f}", thr + n1*40, wait + n2*3;
""",
        "factor_cases": '--green_sec) GS="$2"; shift 2 ;;\n        --cycle_sec) CS="$2"; shift 2 ;;\n        --offset_pct) OP="$2"; shift 2 ;;\n        --ped_phase_sec) PP="$2"; shift 2 ;;\n        --left_turn_sec) LT="$2"; shift 2 ;;\n        --sensor_delay) SD="$2"; shift 2 ;;',
        "awk_vars": '-v GS="$GS" -v CS="$CS" -v OP="$OP" -v PP="$PP" -v LT="$LT" -v SD="$SD"',
        "vars_init": 'GS=""\nCS=""\nOP=""\nPP=""\nLT=""\nSD=""',
        "validate": '[ -z "$GS" ] || [ -z "$CS" ] || [ -z "$OP" ] || [ -z "$PP" ]',
    },
    {
        "num": 123, "slug": "suspension_tuning",
        "name": "Suspension Comfort Tuning",
        "desc": "Box-Behnken design to maximize ride comfort and minimize body roll by tuning spring rate, damper setting, and anti-roll bar stiffness",
        "design": "box_behnken", "category": "automotive",
        "factors": [
            {"name": "spring_rate", "levels": ["25", "60"], "type": "continuous", "unit": "N/mm", "description": "Coil spring rate"},
            {"name": "damper_setting", "levels": ["1", "10"], "type": "continuous", "unit": "clicks", "description": "Adjustable damper click setting"},
            {"name": "arb_stiffness", "levels": ["15", "40"], "type": "continuous", "unit": "N/mm", "description": "Anti-roll bar stiffness"},
        ],
        "fixed": {"vehicle_weight": "1500kg", "tire_size": "225/45R17"},
        "responses": [
            {"name": "comfort_score", "optimize": "maximize", "unit": "pts", "description": "Ride comfort score (1-10)"},
            {"name": "body_roll_deg", "optimize": "minimize", "unit": "deg", "description": "Body roll in degrees during cornering"},
        ],
        "model": """
    sr = (SR - 42.5) / 17.5;
    ds = (DS - 5.5) / 4.5;
    ab = (AB - 27.5) / 12.5;
    comf = 6.5 - 1.2*sr - 0.8*ds - 0.4*ab - 0.5*sr*sr - 0.3*ds*ds + 0.3*sr*ds;
    roll = 3.5 - 0.8*sr - 0.5*ds - 0.6*ab + 0.2*sr*sr + 0.15*ds*ds + 0.2*sr*ab;
    if (comf < 1) comf = 1; if (comf > 10) comf = 10;
    if (roll < 0.5) roll = 0.5;
    printf "{\\"comfort_score\\": %.1f, \\"body_roll_deg\\": %.1f}", comf + n1*0.3, roll + n2*0.2;
""",
        "factor_cases": '--spring_rate) SR="$2"; shift 2 ;;\n        --damper_setting) DS="$2"; shift 2 ;;\n        --arb_stiffness) AB="$2"; shift 2 ;;',
        "awk_vars": '-v SR="$SR" -v DS="$DS" -v AB="$AB"',
        "vars_init": 'SR=""\nDS=""\nAB=""',
        "validate": '[ -z "$SR" ] || [ -z "$DS" ] || [ -z "$AB" ]',
    },
    {
        "num": 124, "slug": "headlight_alignment",
        "name": "Headlight Beam Alignment",
        "desc": "Full factorial of vertical aim, horizontal aim, bulb wattage, and lens clarity to maximize road illumination and minimize oncoming glare",
        "design": "full_factorial", "category": "automotive",
        "factors": [
            {"name": "vertical_deg", "levels": ["-2", "2"], "type": "continuous", "unit": "deg", "description": "Vertical aim angle (negative = down)"},
            {"name": "horizontal_deg", "levels": ["-1", "1"], "type": "continuous", "unit": "deg", "description": "Horizontal aim angle"},
            {"name": "bulb_watts", "levels": ["35", "65"], "type": "continuous", "unit": "W", "description": "Bulb wattage"},
            {"name": "lens_clarity", "levels": ["50", "100"], "type": "continuous", "unit": "%", "description": "Lens clarity after restoration"},
        ],
        "fixed": {"headlight_type": "reflector", "beam": "low"},
        "responses": [
            {"name": "illumination_lux", "optimize": "maximize", "unit": "lux", "description": "Road illumination at 30m"},
            {"name": "glare_score", "optimize": "minimize", "unit": "pts", "description": "Oncoming driver glare score (1-10)"},
        ],
        "model": """
    vd = (VD - 0) / 2;
    hd = (HD - 0) / 1;
    bw = (BW - 50) / 15;
    lc = (LC - 75) / 25;
    illum = 120 - 20*vd + 5*hd + 30*bw + 25*lc + 5*bw*lc;
    glare = 5 + 2.5*vd + 0.5*hd + 1.2*bw + 0.8*lc + 0.5*vd*bw;
    if (illum < 20) illum = 20;
    if (glare < 1) glare = 1; if (glare > 10) glare = 10;
    printf "{\\"illumination_lux\\": %.0f, \\"glare_score\\": %.1f}", illum + n1*8, glare + n2*0.3;
""",
        "factor_cases": '--vertical_deg) VD="$2"; shift 2 ;;\n        --horizontal_deg) HD="$2"; shift 2 ;;\n        --bulb_watts) BW="$2"; shift 2 ;;\n        --lens_clarity) LC="$2"; shift 2 ;;',
        "awk_vars": '-v VD="$VD" -v HD="$HD" -v BW="$BW" -v LC="$LC"',
        "vars_init": 'VD=""\nHD=""\nBW=""\nLC=""',
        "validate": '[ -z "$VD" ] || [ -z "$HD" ] || [ -z "$BW" ] || [ -z "$LC" ]',
    },
    {
        "num": 125, "slug": "parking_lot_layout",
        "name": "Parking Lot Layout Design",
        "desc": "Box-Behnken design to maximize capacity and minimize average walking distance by tuning stall angle, aisle width, and stall width",
        "design": "box_behnken", "category": "automotive",
        "factors": [
            {"name": "stall_angle", "levels": ["45", "90"], "type": "continuous", "unit": "deg", "description": "Parking stall angle"},
            {"name": "aisle_width", "levels": ["4.5", "7.5"], "type": "continuous", "unit": "m", "description": "Driving aisle width"},
            {"name": "stall_width", "levels": ["2.4", "3.0"], "type": "continuous", "unit": "m", "description": "Individual stall width"},
        ],
        "fixed": {"lot_area_m2": "5000", "handicap_pct": "5"},
        "responses": [
            {"name": "capacity", "optimize": "maximize", "unit": "spaces", "description": "Total parking capacity"},
            {"name": "avg_walk_m", "optimize": "minimize", "unit": "m", "description": "Average walking distance to entrance"},
        ],
        "model": """
    sa = (SA - 67.5) / 22.5;
    aw = (AW - 6) / 1.5;
    sw = (SW - 2.7) / 0.3;
    cap = 180 + 15*sa - 20*aw - 25*sw - 5*sa*sa + 3*sa*aw;
    walk = 45 + 5*sa + 3*aw + 2*sw - 2*sa*sa + 1.5*aw*sw;
    if (cap < 80) cap = 80;
    if (walk < 15) walk = 15;
    printf "{\\"capacity\\": %.0f, \\"avg_walk_m\\": %.0f}", cap + n1*5, walk + n2*3;
""",
        "factor_cases": '--stall_angle) SA="$2"; shift 2 ;;\n        --aisle_width) AW="$2"; shift 2 ;;\n        --stall_width) SW="$2"; shift 2 ;;',
        "awk_vars": '-v SA="$SA" -v AW="$AW" -v SW="$SW"',
        "vars_init": 'SA=""\nAW=""\nSW=""',
        "validate": '[ -z "$SA" ] || [ -z "$AW" ] || [ -z "$SW" ]',
    },
    {
        "num": 126, "slug": "windshield_defog",
        "name": "Windshield Defog Strategy",
        "desc": "Fractional factorial of fan speed, temperature setting, AC mode, recirculation, and rear defrost to minimize defog time and energy use",
        "design": "fractional_factorial", "category": "automotive",
        "factors": [
            {"name": "fan_speed", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "HVAC fan speed setting"},
            {"name": "temp_setting", "levels": ["18", "30"], "type": "continuous", "unit": "C", "description": "Temperature dial setting"},
            {"name": "ac_on", "levels": ["0", "1"], "type": "continuous", "unit": "bool", "description": "Air conditioning compressor on/off"},
            {"name": "recirc", "levels": ["0", "1"], "type": "continuous", "unit": "bool", "description": "Recirculation mode on/off"},
            {"name": "rear_defrost", "levels": ["0", "1"], "type": "continuous", "unit": "bool", "description": "Rear defroster on/off"},
        ],
        "fixed": {"ambient_temp": "2C", "humidity": "85pct"},
        "responses": [
            {"name": "defog_time_sec", "optimize": "minimize", "unit": "sec", "description": "Time to clear windshield fog"},
            {"name": "energy_watts", "optimize": "minimize", "unit": "W", "description": "Average power draw during defogging"},
        ],
        "model": """
    fs = (FS - 3) / 2;
    ts = (TS - 24) / 6;
    ac = (AC - 0.5) / 0.5;
    rc = (RC - 0.5) / 0.5;
    rd = (RD - 0.5) / 0.5;
    defog = 120 - 25*fs - 15*ts - 30*ac + 20*rc - 5*rd + 5*fs*ts + 10*ac*rc;
    energy = 300 + 80*fs + 40*ts + 120*ac + 10*rc + 60*rd + 15*fs*ac;
    if (defog < 15) defog = 15;
    if (energy < 100) energy = 100;
    printf "{\\"defog_time_sec\\": %.0f, \\"energy_watts\\": %.0f}", defog + n1*8, energy + n2*20;
""",
        "factor_cases": '--fan_speed) FS="$2"; shift 2 ;;\n        --temp_setting) TS="$2"; shift 2 ;;\n        --ac_on) AC="$2"; shift 2 ;;\n        --recirc) RC="$2"; shift 2 ;;\n        --rear_defrost) RD="$2"; shift 2 ;;',
        "awk_vars": '-v FS="$FS" -v TS="$TS" -v AC="$AC" -v RC="$RC" -v RD="$RD"',
        "vars_init": 'FS=""\nTS=""\nAC=""\nRC=""\nRD=""',
        "validate": '[ -z "$FS" ] || [ -z "$TS" ] || [ -z "$AC" ] || [ -z "$RC" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: Environmental & Energy (127-136)
    # ══════════════════════════════════════════════════
    {
        "num": 127, "slug": "solar_panel_tilt",
        "name": "Solar Panel Tilt & Orientation",
        "desc": "Central composite design to maximize annual energy yield and minimize peak temperature by tuning tilt angle, azimuth, and row spacing",
        "design": "central_composite", "category": "environment",
        "factors": [
            {"name": "tilt_deg", "levels": ["10", "50"], "type": "continuous", "unit": "deg", "description": "Panel tilt angle from horizontal"},
            {"name": "azimuth_deg", "levels": ["150", "210"], "type": "continuous", "unit": "deg", "description": "Panel azimuth (180 = due south)"},
            {"name": "row_spacing_m", "levels": ["1.5", "4.0"], "type": "continuous", "unit": "m", "description": "Row-to-row spacing"},
        ],
        "fixed": {"latitude": "40N", "panel_watt": "400W"},
        "responses": [
            {"name": "annual_kwh", "optimize": "maximize", "unit": "kWh/panel", "description": "Annual energy yield per panel"},
            {"name": "peak_temp_c", "optimize": "minimize", "unit": "C", "description": "Peak panel operating temperature"},
        ],
        "model": """
    ti = (TI - 30) / 20;
    az = (AZ - 180) / 30;
    rs = (RS - 2.75) / 1.25;
    kwh = 580 + 30*ti - 15*az + 10*rs - 20*ti*ti - 10*az*az + 5*ti*rs;
    temp = 65 + 3*ti - 2*az - 4*rs + 1.5*ti*ti + 1*az*az;
    if (kwh < 300) kwh = 300;
    if (temp < 40) temp = 40;
    printf "{\\"annual_kwh\\": %.0f, \\"peak_temp_c\\": %.0f}", kwh + n1*15, temp + n2*2;
""",
        "factor_cases": '--tilt_deg) TI="$2"; shift 2 ;;\n        --azimuth_deg) AZ="$2"; shift 2 ;;\n        --row_spacing_m) RS="$2"; shift 2 ;;',
        "awk_vars": '-v TI="$TI" -v AZ="$AZ" -v RS="$RS"',
        "vars_init": 'TI=""\nAZ=""\nRS=""',
        "validate": '[ -z "$TI" ] || [ -z "$AZ" ] || [ -z "$RS" ]',
    },
    {
        "num": 128, "slug": "rainwater_harvesting",
        "name": "Rainwater Harvesting System",
        "desc": "Box-Behnken design to maximize water captured and minimize overflow by tuning tank size, gutter area, and first-flush diverter volume",
        "design": "box_behnken", "category": "environment",
        "factors": [
            {"name": "tank_liters", "levels": ["500", "5000"], "type": "continuous", "unit": "L", "description": "Storage tank volume"},
            {"name": "gutter_area_m2", "levels": ["50", "200"], "type": "continuous", "unit": "m2", "description": "Roof catchment area connected to gutters"},
            {"name": "first_flush_L", "levels": ["10", "80"], "type": "continuous", "unit": "L", "description": "First-flush diverter volume"},
        ],
        "fixed": {"annual_rainfall_mm": "900", "usage_L_day": "50"},
        "responses": [
            {"name": "capture_pct", "optimize": "maximize", "unit": "%", "description": "Percentage of annual rainfall captured"},
            {"name": "overflow_pct", "optimize": "minimize", "unit": "%", "description": "Percentage lost to overflow"},
        ],
        "model": """
    tk = (TK - 2750) / 2250;
    ga = (GA - 125) / 75;
    ff = (FF - 45) / 35;
    cap = 55 + 15*tk + 10*ga - 5*ff - 5*tk*tk - 3*ga*ga + 3*tk*ga;
    over = 30 - 12*tk - 5*ga + 3*ff + 4*tk*tk + 2*ga*ga - 2*tk*ga;
    if (cap < 10) cap = 10; if (cap > 95) cap = 95;
    if (over < 2) over = 2;
    printf "{\\"capture_pct\\": %.1f, \\"overflow_pct\\": %.1f}", cap + n1*3, over + n2*2;
""",
        "factor_cases": '--tank_liters) TK="$2"; shift 2 ;;\n        --gutter_area_m2) GA="$2"; shift 2 ;;\n        --first_flush_L) FF="$2"; shift 2 ;;',
        "awk_vars": '-v TK="$TK" -v GA="$GA" -v FF="$FF"',
        "vars_init": 'TK=""\nGA=""\nFF=""',
        "validate": '[ -z "$TK" ] || [ -z "$GA" ] || [ -z "$FF" ]',
    },
    {
        "num": 129, "slug": "home_insulation",
        "name": "Home Insulation Optimization",
        "desc": "Full factorial of attic R-value, wall R-value, window U-factor, and air sealing effort to minimize heating cost and maximize comfort",
        "design": "full_factorial", "category": "environment",
        "factors": [
            {"name": "attic_r", "levels": ["19", "49"], "type": "continuous", "unit": "R-value", "description": "Attic insulation R-value"},
            {"name": "wall_r", "levels": ["11", "21"], "type": "continuous", "unit": "R-value", "description": "Wall insulation R-value"},
            {"name": "window_u", "levels": ["0.25", "0.65"], "type": "continuous", "unit": "U-factor", "description": "Window U-factor (lower = better)"},
            {"name": "air_seal_ach", "levels": ["2", "8"], "type": "continuous", "unit": "ACH50", "description": "Air changes per hour at 50 Pa"},
        ],
        "fixed": {"climate_zone": "5A", "house_sqft": "2000"},
        "responses": [
            {"name": "annual_heat_cost", "optimize": "minimize", "unit": "USD", "description": "Annual heating cost"},
            {"name": "comfort_score", "optimize": "maximize", "unit": "pts", "description": "Temperature uniformity comfort score (1-10)"},
        ],
        "model": """
    ar = (AR - 34) / 15;
    wr = (WR - 16) / 5;
    wu = (WU - 0.45) / 0.2;
    as_ = (AS - 5) / 3;
    cost = 1200 - 150*ar - 100*wr + 200*wu + 180*as_ + 30*ar*ar + 20*wr*wr + 40*wu*as_;
    comf = 6.5 + 0.8*ar + 0.6*wr - 1.0*wu - 0.8*as_ - 0.2*ar*ar + 0.3*wr*ar;
    if (cost < 300) cost = 300;
    if (comf < 1) comf = 1; if (comf > 10) comf = 10;
    printf "{\\"annual_heat_cost\\": %.0f, \\"comfort_score\\": %.1f}", cost + n1*30, comf + n2*0.3;
""",
        "factor_cases": '--attic_r) AR="$2"; shift 2 ;;\n        --wall_r) WR="$2"; shift 2 ;;\n        --window_u) WU="$2"; shift 2 ;;\n        --air_seal_ach) AS="$2"; shift 2 ;;',
        "awk_vars": '-v AR="$AR" -v WR="$WR" -v WU="$WU" -v AS="$AS"',
        "vars_init": 'AR=""\nWR=""\nWU=""\nAS=""',
        "validate": '[ -z "$AR" ] || [ -z "$WR" ] || [ -z "$WU" ] || [ -z "$AS" ]',
    },
    {
        "num": 130, "slug": "wind_turbine_siting",
        "name": "Small Wind Turbine Siting",
        "desc": "Box-Behnken design to maximize annual energy output and minimize noise by tuning tower height, rotor diameter, and distance from obstacles",
        "design": "box_behnken", "category": "environment",
        "factors": [
            {"name": "tower_height_m", "levels": ["10", "30"], "type": "continuous", "unit": "m", "description": "Tower height above ground"},
            {"name": "rotor_diam_m", "levels": ["2", "7"], "type": "continuous", "unit": "m", "description": "Rotor diameter"},
            {"name": "obstacle_dist_m", "levels": ["20", "100"], "type": "continuous", "unit": "m", "description": "Distance from nearest obstacle"},
        ],
        "fixed": {"avg_wind_speed": "5.5m/s", "terrain": "suburban"},
        "responses": [
            {"name": "annual_kwh", "optimize": "maximize", "unit": "kWh", "description": "Annual energy production"},
            {"name": "noise_dba", "optimize": "minimize", "unit": "dBA", "description": "Noise level at nearest property line"},
        ],
        "model": """
    th = (TH - 20) / 10;
    rd = (RD - 4.5) / 2.5;
    od = (OD - 60) / 40;
    kwh = 3000 + 800*th + 1200*rd + 400*od - 150*th*th - 200*rd*rd + 100*th*rd;
    noise = 42 + 3*th + 5*rd - 6*od + 1*rd*rd + 2*th*rd;
    if (kwh < 500) kwh = 500;
    if (noise < 25) noise = 25;
    printf "{\\"annual_kwh\\": %.0f, \\"noise_dba\\": %.0f}", kwh + n1*150, noise + n2*2;
""",
        "factor_cases": '--tower_height_m) TH="$2"; shift 2 ;;\n        --rotor_diam_m) RD="$2"; shift 2 ;;\n        --obstacle_dist_m) OD="$2"; shift 2 ;;',
        "awk_vars": '-v TH="$TH" -v RD="$RD" -v OD="$OD"',
        "vars_init": 'TH=""\nRD=""\nOD=""',
        "validate": '[ -z "$TH" ] || [ -z "$RD" ] || [ -z "$OD" ]',
    },
    {
        "num": 131, "slug": "composting_bin",
        "name": "Backyard Composting Bin Design",
        "desc": "Central composite design to maximize decomposition rate and minimize odor by tuning bin volume, ventilation holes, and insulation thickness",
        "design": "central_composite", "category": "environment",
        "factors": [
            {"name": "volume_L", "levels": ["100", "600"], "type": "continuous", "unit": "L", "description": "Composting bin volume"},
            {"name": "vent_holes", "levels": ["4", "24"], "type": "continuous", "unit": "count", "description": "Number of ventilation holes"},
            {"name": "insulation_mm", "levels": ["0", "50"], "type": "continuous", "unit": "mm", "description": "Wall insulation thickness"},
        ],
        "fixed": {"material": "recycled_plastic", "location": "shaded"},
        "responses": [
            {"name": "decomp_rate", "optimize": "maximize", "unit": "kg/week", "description": "Organic matter decomposition rate"},
            {"name": "odor_score", "optimize": "minimize", "unit": "pts", "description": "Odor intensity score (1-10)"},
        ],
        "model": """
    vl = (VL - 350) / 250;
    vh = (VH - 14) / 10;
    im = (IM - 25) / 25;
    decomp = 2.5 + 0.8*vl + 0.5*vh + 0.4*im - 0.3*vl*vl - 0.2*vh*vh + 0.2*vl*vh;
    odor = 4.5 - 0.3*vl + 1.2*vh - 0.5*im + 0.2*vh*vh + 0.3*vl*vh;
    if (decomp < 0.3) decomp = 0.3;
    if (odor < 1) odor = 1; if (odor > 10) odor = 10;
    printf "{\\"decomp_rate\\": %.2f, \\"odor_score\\": %.1f}", decomp + n1*0.2, odor + n2*0.3;
""",
        "factor_cases": '--volume_L) VL="$2"; shift 2 ;;\n        --vent_holes) VH="$2"; shift 2 ;;\n        --insulation_mm) IM="$2"; shift 2 ;;',
        "awk_vars": '-v VL="$VL" -v VH="$VH" -v IM="$IM"',
        "vars_init": 'VL=""\nVH=""\nIM=""',
        "validate": '[ -z "$VL" ] || [ -z "$VH" ] || [ -z "$IM" ]',
    },
    {
        "num": 132, "slug": "water_heater_efficiency",
        "name": "Water Heater Efficiency",
        "desc": "Plackett-Burman screening of thermostat setting, tank insulation, pipe insulation, recirculation timer, and inlet temperature for energy savings and hot water availability",
        "design": "plackett_burman", "category": "environment",
        "factors": [
            {"name": "thermostat_c", "levels": ["48", "65"], "type": "continuous", "unit": "C", "description": "Tank thermostat temperature setting"},
            {"name": "tank_r_value", "levels": ["6", "18"], "type": "continuous", "unit": "R-value", "description": "Tank insulation R-value"},
            {"name": "pipe_insulation", "levels": ["0", "1"], "type": "continuous", "unit": "bool", "description": "Hot water pipe insulation installed"},
            {"name": "recirc_timer", "levels": ["0", "1"], "type": "continuous", "unit": "bool", "description": "Recirculation pump timer enabled"},
            {"name": "inlet_temp_c", "levels": ["5", "20"], "type": "continuous", "unit": "C", "description": "Cold water inlet temperature"},
        ],
        "fixed": {"tank_size_L": "200", "household_size": "4"},
        "responses": [
            {"name": "monthly_kwh", "optimize": "minimize", "unit": "kWh", "description": "Monthly energy consumption"},
            {"name": "availability_pct", "optimize": "maximize", "unit": "%", "description": "Hot water availability percentage"},
        ],
        "model": """
    ts = (TS - 56.5) / 8.5;
    tr = (TR - 12) / 6;
    pi = (PI - 0.5) / 0.5;
    rt = (RT - 0.5) / 0.5;
    it = (IT - 12.5) / 7.5;
    kwh = 350 + 40*ts - 30*tr - 15*pi - 20*rt - 25*it + 10*ts*it;
    avail = 85 + 5*ts + 2*tr + 1*pi + 3*rt + 3*it + 1.5*ts*tr;
    if (kwh < 150) kwh = 150;
    if (avail < 60) avail = 60; if (avail > 100) avail = 100;
    printf "{\\"monthly_kwh\\": %.0f, \\"availability_pct\\": %.0f}", kwh + n1*12, avail + n2*2;
""",
        "factor_cases": '--thermostat_c) TS="$2"; shift 2 ;;\n        --tank_r_value) TR="$2"; shift 2 ;;\n        --pipe_insulation) PI="$2"; shift 2 ;;\n        --recirc_timer) RT="$2"; shift 2 ;;\n        --inlet_temp_c) IT="$2"; shift 2 ;;',
        "awk_vars": '-v TS="$TS" -v TR="$TR" -v PI="$PI" -v RT="$RT" -v IT="$IT"',
        "vars_init": 'TS=""\nTR=""\nPI=""\nRT=""\nIT=""',
        "validate": '[ -z "$TS" ] || [ -z "$TR" ] || [ -z "$PI" ] || [ -z "$RT" ]',
    },
    {
        "num": 133, "slug": "led_grow_light",
        "name": "LED Grow Light Spectrum",
        "desc": "Box-Behnken design to maximize photosynthesis rate and minimize heat output by tuning red-to-blue ratio, intensity, and photoperiod",
        "design": "box_behnken", "category": "environment",
        "factors": [
            {"name": "red_blue_ratio", "levels": ["1", "8"], "type": "continuous", "unit": "ratio", "description": "Red-to-blue wavelength ratio"},
            {"name": "ppfd", "levels": ["200", "800"], "type": "continuous", "unit": "umol/m2/s", "description": "Photosynthetic photon flux density"},
            {"name": "photoperiod_hrs", "levels": ["12", "20"], "type": "continuous", "unit": "hrs", "description": "Daily light-on hours"},
        ],
        "fixed": {"plant_type": "leafy_greens", "distance_cm": "30"},
        "responses": [
            {"name": "growth_rate_g", "optimize": "maximize", "unit": "g/day", "description": "Fresh weight growth rate per day"},
            {"name": "heat_watts", "optimize": "minimize", "unit": "W", "description": "Heat output at canopy level"},
        ],
        "model": """
    rb = (RB - 4.5) / 3.5;
    pp = (PP - 500) / 300;
    ph = (PH - 16) / 4;
    growth = 5.0 + 0.8*rb + 2.0*pp + 1.0*ph - 0.5*rb*rb - 0.6*pp*pp - 0.3*ph*ph + 0.3*rb*pp;
    heat = 50 + 5*rb + 25*pp + 8*ph + 3*pp*pp + 2*rb*pp;
    if (growth < 0.5) growth = 0.5;
    if (heat < 15) heat = 15;
    printf "{\\"growth_rate_g\\": %.1f, \\"heat_watts\\": %.0f}", growth + n1*0.3, heat + n2*3;
""",
        "factor_cases": '--red_blue_ratio) RB="$2"; shift 2 ;;\n        --ppfd) PP="$2"; shift 2 ;;\n        --photoperiod_hrs) PH="$2"; shift 2 ;;',
        "awk_vars": '-v RB="$RB" -v PP="$PP" -v PH="$PH"',
        "vars_init": 'RB=""\nPP=""\nPH=""',
        "validate": '[ -z "$RB" ] || [ -z "$PP" ] || [ -z "$PH" ]',
    },
    {
        "num": 134, "slug": "heat_pump_sizing",
        "name": "Heat Pump Sizing & Settings",
        "desc": "Full factorial of unit capacity, backup heat threshold, defrost interval, and fan speed to minimize annual energy cost and maximize comfort hours",
        "design": "full_factorial", "category": "environment",
        "factors": [
            {"name": "capacity_kw", "levels": ["5", "12"], "type": "continuous", "unit": "kW", "description": "Heat pump heating capacity"},
            {"name": "backup_threshold_c", "levels": ["-10", "5"], "type": "continuous", "unit": "C", "description": "Outdoor temp to enable backup heating"},
            {"name": "defrost_interval", "levels": ["30", "90"], "type": "continuous", "unit": "min", "description": "Defrost cycle interval"},
            {"name": "fan_speed", "levels": ["low", "high"], "type": "categorical", "unit": "", "description": "Indoor fan speed setting"},
        ],
        "fixed": {"house_sqft": "1800", "climate_zone": "5A"},
        "responses": [
            {"name": "annual_cost", "optimize": "minimize", "unit": "USD", "description": "Annual heating energy cost"},
            {"name": "comfort_hrs_pct", "optimize": "maximize", "unit": "%", "description": "Percentage of hours within comfort range"},
        ],
        "model": """
    ck = (CK - 8.5) / 3.5;
    bt = (BT - -2.5) / 7.5;
    di = (DI - 60) / 30;
    fs = (FS == "high") ? 1 : -1;
    cost = 900 + 60*ck - 40*bt + 20*di + 30*fs + 15*ck*bt - 10*di*fs;
    comf = 88 + 4*ck + 2*bt - 1*di + 1.5*fs - 1*ck*ck + 0.5*ck*fs;
    if (cost < 400) cost = 400;
    if (comf < 60) comf = 60; if (comf > 100) comf = 100;
    printf "{\\"annual_cost\\": %.0f, \\"comfort_hrs_pct\\": %.0f}", cost + n1*25, comf + n2*1.5;
""",
        "factor_cases": '--capacity_kw) CK="$2"; shift 2 ;;\n        --backup_threshold_c) BT="$2"; shift 2 ;;\n        --defrost_interval) DI="$2"; shift 2 ;;\n        --fan_speed) FS="$2"; shift 2 ;;',
        "awk_vars": '-v CK="$CK" -v BT="$BT" -v DI="$DI" -v FS="$FS"',
        "vars_init": 'CK=""\nBT=""\nDI=""\nFS=""',
        "validate": '[ -z "$CK" ] || [ -z "$BT" ] || [ -z "$DI" ] || [ -z "$FS" ]',
    },
    {
        "num": 135, "slug": "aquaponics_balance",
        "name": "Aquaponics System Balance",
        "desc": "Box-Behnken design to maximize fish growth and plant yield by tuning fish density, feeding rate, and water flow rate",
        "design": "box_behnken", "category": "environment",
        "factors": [
            {"name": "fish_density", "levels": ["10", "40"], "type": "continuous", "unit": "fish/m3", "description": "Fish stocking density"},
            {"name": "feed_rate_pct", "levels": ["1", "4"], "type": "continuous", "unit": "%BW/day", "description": "Daily feeding rate as % of body weight"},
            {"name": "flow_rate_lph", "levels": ["200", "800"], "type": "continuous", "unit": "L/hr", "description": "Water circulation flow rate"},
        ],
        "fixed": {"fish_species": "tilapia", "plant": "basil"},
        "responses": [
            {"name": "fish_growth_g", "optimize": "maximize", "unit": "g/week", "description": "Average fish weight gain per week"},
            {"name": "plant_yield_g", "optimize": "maximize", "unit": "g/m2/wk", "description": "Plant harvest yield per square meter per week"},
        ],
        "model": """
    fd = (FD - 25) / 15;
    fr = (FR - 2.5) / 1.5;
    fl = (FL - 500) / 300;
    fish = 25 + 5*fd + 8*fr + 3*fl - 3*fd*fd - 2*fr*fr - 1*fl*fl + 2*fd*fr;
    plant = 80 + 15*fd + 20*fr + 10*fl - 8*fd*fd - 5*fr*fr - 3*fl*fl + 5*fd*fl;
    if (fish < 5) fish = 5;
    if (plant < 20) plant = 20;
    printf "{\\"fish_growth_g\\": %.1f, \\"plant_yield_g\\": %.0f}", fish + n1*2, plant + n2*5;
""",
        "factor_cases": '--fish_density) FD="$2"; shift 2 ;;\n        --feed_rate_pct) FR="$2"; shift 2 ;;\n        --flow_rate_lph) FL="$2"; shift 2 ;;',
        "awk_vars": '-v FD="$FD" -v FR="$FR" -v FL="$FL"',
        "vars_init": 'FD=""\nFR=""\nFL=""',
        "validate": '[ -z "$FD" ] || [ -z "$FR" ] || [ -z "$FL" ]',
    },
    {
        "num": 136, "slug": "rain_garden_sizing",
        "name": "Rain Garden Design",
        "desc": "Central composite design to maximize stormwater infiltration and minimize ponding time by tuning garden area, soil depth, and berm height",
        "design": "central_composite", "category": "environment",
        "factors": [
            {"name": "area_m2", "levels": ["5", "20"], "type": "continuous", "unit": "m2", "description": "Rain garden surface area"},
            {"name": "soil_depth_cm", "levels": ["30", "90"], "type": "continuous", "unit": "cm", "description": "Engineered soil media depth"},
            {"name": "berm_height_cm", "levels": ["10", "30"], "type": "continuous", "unit": "cm", "description": "Perimeter berm height"},
        ],
        "fixed": {"drainage_area_m2": "200", "soil_type": "sandy_loam"},
        "responses": [
            {"name": "infiltration_pct", "optimize": "maximize", "unit": "%", "description": "Stormwater volume infiltrated during 1-yr storm"},
            {"name": "ponding_hrs", "optimize": "minimize", "unit": "hrs", "description": "Maximum ponding duration"},
        ],
        "model": """
    ar = (AR - 12.5) / 7.5;
    sd = (SD - 60) / 30;
    bh = (BH - 20) / 10;
    infil = 70 + 10*ar + 8*sd + 5*bh - 3*ar*ar - 2*sd*sd + 2*ar*sd + 1.5*ar*bh;
    pond = 18 - 4*ar - 3*sd + 2*bh + 1.5*ar*ar + 1*sd*sd - 0.5*ar*sd;
    if (infil < 20) infil = 20; if (infil > 100) infil = 100;
    if (pond < 1) pond = 1;
    printf "{\\"infiltration_pct\\": %.0f, \\"ponding_hrs\\": %.1f}", infil + n1*3, pond + n2*1;
""",
        "factor_cases": '--area_m2) AR="$2"; shift 2 ;;\n        --soil_depth_cm) SD="$2"; shift 2 ;;\n        --berm_height_cm) BH="$2"; shift 2 ;;',
        "awk_vars": '-v AR="$AR" -v SD="$SD" -v BH="$BH"',
        "vars_init": 'AR=""\nSD=""\nBH=""',
        "validate": '[ -z "$AR" ] || [ -z "$SD" ] || [ -z "$BH" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: Home & DIY (137-146)
    # ══════════════════════════════════════════════════
    {
        "num": 137, "slug": "paint_finish_quality",
        "name": "Interior Paint Finish Quality",
        "desc": "Box-Behnken design to maximize coverage and minimize drying time by tuning coat thickness, humidity, and paint dilution ratio",
        "design": "box_behnken", "category": "home",
        "factors": [
            {"name": "coat_mils", "levels": ["3", "8"], "type": "continuous", "unit": "mils", "description": "Wet coat thickness in mils"},
            {"name": "humidity_pct", "levels": ["30", "70"], "type": "continuous", "unit": "%", "description": "Room relative humidity"},
            {"name": "dilution_pct", "levels": ["0", "15"], "type": "continuous", "unit": "%", "description": "Water dilution percentage for latex paint"},
        ],
        "fixed": {"paint_type": "latex_eggshell", "surface": "drywall"},
        "responses": [
            {"name": "coverage_score", "optimize": "maximize", "unit": "pts", "description": "Coverage and hiding score (1-10)"},
            {"name": "dry_time_min", "optimize": "minimize", "unit": "min", "description": "Touch-dry time in minutes"},
        ],
        "model": """
    cm = (CM - 5.5) / 2.5;
    hp = (HP - 50) / 20;
    dp = (DP - 7.5) / 7.5;
    cov = 7.0 + 1.5*cm - 0.3*hp - 0.8*dp - 0.4*cm*cm + 0.2*cm*hp;
    dry = 45 + 10*cm + 15*hp + 5*dp + 3*cm*hp + 2*hp*dp;
    if (cov < 1) cov = 1; if (cov > 10) cov = 10;
    if (dry < 15) dry = 15;
    printf "{\\"coverage_score\\": %.1f, \\"dry_time_min\\": %.0f}", cov + n1*0.3, dry + n2*4;
""",
        "factor_cases": '--coat_mils) CM="$2"; shift 2 ;;\n        --humidity_pct) HP="$2"; shift 2 ;;\n        --dilution_pct) DP="$2"; shift 2 ;;',
        "awk_vars": '-v CM="$CM" -v HP="$HP" -v DP="$DP"',
        "vars_init": 'CM=""\nHP=""\nDP=""',
        "validate": '[ -z "$CM" ] || [ -z "$HP" ] || [ -z "$DP" ]',
    },
    {
        "num": 138, "slug": "concrete_mix",
        "name": "DIY Concrete Mix Design",
        "desc": "Central composite design to maximize compressive strength and minimize cost by tuning cement ratio, water-cement ratio, and aggregate size",
        "design": "central_composite", "category": "home",
        "factors": [
            {"name": "cement_pct", "levels": ["10", "20"], "type": "continuous", "unit": "%", "description": "Cement percentage of total mix by weight"},
            {"name": "water_cement_ratio", "levels": ["0.35", "0.65"], "type": "continuous", "unit": "ratio", "description": "Water-to-cement ratio"},
            {"name": "aggregate_mm", "levels": ["10", "25"], "type": "continuous", "unit": "mm", "description": "Maximum aggregate size"},
        ],
        "fixed": {"sand_type": "sharp", "admixture": "none"},
        "responses": [
            {"name": "strength_mpa", "optimize": "maximize", "unit": "MPa", "description": "28-day compressive strength"},
            {"name": "cost_per_m3", "optimize": "minimize", "unit": "USD/m3", "description": "Material cost per cubic meter"},
        ],
        "model": """
    cp = (CP - 15) / 5;
    wc = (WC - 0.5) / 0.15;
    ag = (AG - 17.5) / 7.5;
    str_ = 25 + 8*cp - 10*wc + 2*ag - 2*cp*cp - 3*wc*wc + 1.5*cp*ag;
    cost = 90 + 20*cp - 5*wc - 3*ag + 5*cp*cp;
    if (str_ < 5) str_ = 5;
    if (cost < 50) cost = 50;
    printf "{\\"strength_mpa\\": %.1f, \\"cost_per_m3\\": %.0f}", str_ + n1*1.5, cost + n2*4;
""",
        "factor_cases": '--cement_pct) CP="$2"; shift 2 ;;\n        --water_cement_ratio) WC="$2"; shift 2 ;;\n        --aggregate_mm) AG="$2"; shift 2 ;;',
        "awk_vars": '-v CP="$CP" -v WC="$WC" -v AG="$AG"',
        "vars_init": 'CP=""\nWC=""\nAG=""',
        "validate": '[ -z "$CP" ] || [ -z "$WC" ] || [ -z "$AG" ]',
    },
    {
        "num": 139, "slug": "laundry_stain_removal",
        "name": "Laundry Stain Removal",
        "desc": "Plackett-Burman screening of water temperature, detergent dose, soak time, agitation level, bleach type, and spin speed for stain removal and fabric care",
        "design": "plackett_burman", "category": "home",
        "factors": [
            {"name": "water_temp_c", "levels": ["20", "60"], "type": "continuous", "unit": "C", "description": "Wash water temperature"},
            {"name": "detergent_ml", "levels": ["15", "60"], "type": "continuous", "unit": "mL", "description": "Detergent dose per load"},
            {"name": "soak_min", "levels": ["0", "30"], "type": "continuous", "unit": "min", "description": "Pre-soak duration"},
            {"name": "agitation", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "Agitation intensity level"},
            {"name": "bleach_ml", "levels": ["0", "30"], "type": "continuous", "unit": "mL", "description": "Oxygen bleach amount"},
            {"name": "spin_rpm", "levels": ["600", "1400"], "type": "continuous", "unit": "rpm", "description": "Final spin speed"},
        ],
        "fixed": {"load_size": "medium", "fabric": "cotton"},
        "responses": [
            {"name": "stain_removal_pct", "optimize": "maximize", "unit": "%", "description": "Stain removal percentage"},
            {"name": "fabric_wear", "optimize": "minimize", "unit": "pts", "description": "Fabric wear score (1-10, lower is gentler)"},
        ],
        "model": """
    wt = (WT - 40) / 20;
    dd = (DD - 37.5) / 22.5;
    sm = (SM - 15) / 15;
    ag = (AG - 3) / 2;
    bl = (BL - 15) / 15;
    sr = (SR - 1000) / 400;
    stain = 70 + 8*wt + 6*dd + 5*sm + 4*ag + 7*bl + 1*sr + 2*wt*bl;
    wear = 3 + 0.8*wt + 0.3*dd + 0.2*sm + 1.2*ag + 0.5*bl + 0.6*sr + 0.3*ag*sr;
    if (stain > 100) stain = 100; if (stain < 30) stain = 30;
    if (wear < 1) wear = 1; if (wear > 10) wear = 10;
    printf "{\\"stain_removal_pct\\": %.0f, \\"fabric_wear\\": %.1f}", stain + n1*3, wear + n2*0.3;
""",
        "factor_cases": '--water_temp_c) WT="$2"; shift 2 ;;\n        --detergent_ml) DD="$2"; shift 2 ;;\n        --soak_min) SM="$2"; shift 2 ;;\n        --agitation) AG="$2"; shift 2 ;;\n        --bleach_ml) BL="$2"; shift 2 ;;\n        --spin_rpm) SR="$2"; shift 2 ;;',
        "awk_vars": '-v WT="$WT" -v DD="$DD" -v SM="$SM" -v AG="$AG" -v BL="$BL" -v SR="$SR"',
        "vars_init": 'WT=""\nDD=""\nSM=""\nAG=""\nBL=""\nSR=""',
        "validate": '[ -z "$WT" ] || [ -z "$DD" ] || [ -z "$SM" ] || [ -z "$AG" ]',
    },
    {
        "num": 140, "slug": "candle_making",
        "name": "Candle Making Optimization",
        "desc": "Box-Behnken design to maximize burn time and scent throw by tuning wick size, fragrance load, and pour temperature",
        "design": "box_behnken", "category": "home",
        "factors": [
            {"name": "wick_size", "levels": ["4", "10"], "type": "continuous", "unit": "mm", "description": "Wick diameter in millimeters"},
            {"name": "fragrance_pct", "levels": ["4", "12"], "type": "continuous", "unit": "%", "description": "Fragrance oil load percentage"},
            {"name": "pour_temp_c", "levels": ["55", "80"], "type": "continuous", "unit": "C", "description": "Wax pouring temperature"},
        ],
        "fixed": {"wax_type": "soy", "container": "8oz_jar"},
        "responses": [
            {"name": "burn_hrs", "optimize": "maximize", "unit": "hrs", "description": "Total burn time in hours"},
            {"name": "scent_throw", "optimize": "maximize", "unit": "pts", "description": "Hot scent throw score (1-10)"},
        ],
        "model": """
    ws = (WS - 7) / 3;
    fp = (FP - 8) / 4;
    pt = (PT - 67.5) / 12.5;
    burn = 40 - 8*ws - 2*fp + 1*pt + 2*ws*ws - 0.5*fp*fp + 0.3*ws*fp;
    scent = 5.5 + 1.0*ws + 1.8*fp + 0.5*pt - 0.4*ws*ws - 0.3*fp*fp + 0.2*ws*fp;
    if (burn < 10) burn = 10;
    if (scent < 1) scent = 1; if (scent > 10) scent = 10;
    printf "{\\"burn_hrs\\": %.0f, \\"scent_throw\\": %.1f}", burn + n1*2, scent + n2*0.3;
""",
        "factor_cases": '--wick_size) WS="$2"; shift 2 ;;\n        --fragrance_pct) FP="$2"; shift 2 ;;\n        --pour_temp_c) PT="$2"; shift 2 ;;',
        "awk_vars": '-v WS="$WS" -v FP="$FP" -v PT="$PT"',
        "vars_init": 'WS=""\nFP=""\nPT=""',
        "validate": '[ -z "$WS" ] || [ -z "$FP" ] || [ -z "$PT" ]',
    },
    {
        "num": 141, "slug": "wood_stain_finish",
        "name": "Wood Stain & Finish",
        "desc": "Full factorial of stain dilution, number of coats, drying time between coats, and topcoat type to maximize color depth and durability",
        "design": "full_factorial", "category": "home",
        "factors": [
            {"name": "stain_dilution", "levels": ["0", "50"], "type": "continuous", "unit": "%", "description": "Stain dilution with mineral spirits"},
            {"name": "num_coats", "levels": ["1", "3"], "type": "continuous", "unit": "coats", "description": "Number of stain coats"},
            {"name": "dry_hrs", "levels": ["2", "24"], "type": "continuous", "unit": "hrs", "description": "Drying time between coats"},
            {"name": "topcoat_coats", "levels": ["1", "3"], "type": "continuous", "unit": "coats", "description": "Number of polyurethane topcoats"},
        ],
        "fixed": {"wood_type": "oak", "stain_color": "walnut"},
        "responses": [
            {"name": "color_depth", "optimize": "maximize", "unit": "pts", "description": "Color richness and depth score (1-10)"},
            {"name": "durability", "optimize": "maximize", "unit": "pts", "description": "Scratch and water resistance (1-10)"},
        ],
        "model": """
    sd = (SD - 25) / 25;
    nc = (NC - 2) / 1;
    dh = (DH - 13) / 11;
    tc = (TC - 2) / 1;
    color = 6.0 - 1.5*sd + 1.2*nc + 0.3*dh + 0.2*tc + 0.4*sd*sd - 0.3*nc*nc + 0.2*nc*dh;
    dur = 5.0 + 0.2*sd + 0.3*nc + 0.4*dh + 2.0*tc - 0.3*tc*tc + 0.2*nc*tc;
    if (color < 1) color = 1; if (color > 10) color = 10;
    if (dur < 1) dur = 1; if (dur > 10) dur = 10;
    printf "{\\"color_depth\\": %.1f, \\"durability\\": %.1f}", color + n1*0.4, dur + n2*0.3;
""",
        "factor_cases": '--stain_dilution) SD="$2"; shift 2 ;;\n        --num_coats) NC="$2"; shift 2 ;;\n        --dry_hrs) DH="$2"; shift 2 ;;\n        --topcoat_coats) TC="$2"; shift 2 ;;',
        "awk_vars": '-v SD="$SD" -v NC="$NC" -v DH="$DH" -v TC="$TC"',
        "vars_init": 'SD=""\nNC=""\nDH=""\nTC=""',
        "validate": '[ -z "$SD" ] || [ -z "$NC" ] || [ -z "$DH" ] || [ -z "$TC" ]',
    },
    {
        "num": 142, "slug": "home_brewing_beer",
        "name": "Home Brewing Beer",
        "desc": "Central composite design to maximize flavor balance and minimize off-flavors by tuning mash temperature, boil duration, and fermentation temperature",
        "design": "central_composite", "category": "home",
        "factors": [
            {"name": "mash_temp_c", "levels": ["63", "70"], "type": "continuous", "unit": "C", "description": "Mash temperature"},
            {"name": "boil_min", "levels": ["45", "90"], "type": "continuous", "unit": "min", "description": "Wort boil duration"},
            {"name": "ferm_temp_c", "levels": ["16", "22"], "type": "continuous", "unit": "C", "description": "Primary fermentation temperature"},
        ],
        "fixed": {"yeast_strain": "US05", "og_target": "1.055"},
        "responses": [
            {"name": "flavor_balance", "optimize": "maximize", "unit": "pts", "description": "Overall flavor balance score (1-10)"},
            {"name": "off_flavor_score", "optimize": "minimize", "unit": "pts", "description": "Off-flavor intensity score (1-10)"},
        ],
        "model": """
    mt = (MT - 66.5) / 3.5;
    bd = (BD - 67.5) / 22.5;
    ft = (FT - 19) / 3;
    flav = 7.0 + 0.5*mt + 0.8*bd - 0.3*ft - 1.0*mt*mt - 0.5*bd*bd - 0.8*ft*ft + 0.3*mt*bd;
    off = 3.0 + 0.5*mt - 0.3*bd + 1.2*ft + 0.3*mt*mt + 0.2*ft*ft + 0.4*mt*ft;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    if (off < 1) off = 1; if (off > 10) off = 10;
    printf "{\\"flavor_balance\\": %.1f, \\"off_flavor_score\\": %.1f}", flav + n1*0.3, off + n2*0.3;
""",
        "factor_cases": '--mash_temp_c) MT="$2"; shift 2 ;;\n        --boil_min) BD="$2"; shift 2 ;;\n        --ferm_temp_c) FT="$2"; shift 2 ;;',
        "awk_vars": '-v MT="$MT" -v BD="$BD" -v FT="$FT"',
        "vars_init": 'MT=""\nBD=""\nFT=""',
        "validate": '[ -z "$MT" ] || [ -z "$BD" ] || [ -z "$FT" ]',
    },
    {
        "num": 143, "slug": "epoxy_resin_art",
        "name": "Epoxy Resin Art Curing",
        "desc": "Box-Behnken design to maximize surface clarity and minimize bubbles by tuning resin-hardener ratio, ambient temperature, and degassing time",
        "design": "box_behnken", "category": "home",
        "factors": [
            {"name": "resin_ratio", "levels": ["1.8", "2.2"], "type": "continuous", "unit": "ratio", "description": "Resin-to-hardener ratio by volume"},
            {"name": "ambient_temp_c", "levels": ["18", "28"], "type": "continuous", "unit": "C", "description": "Room temperature during curing"},
            {"name": "degas_min", "levels": ["0", "15"], "type": "continuous", "unit": "min", "description": "Vacuum degassing time"},
        ],
        "fixed": {"resin_type": "table_top", "mold": "silicone"},
        "responses": [
            {"name": "clarity_score", "optimize": "maximize", "unit": "pts", "description": "Surface clarity and gloss score (1-10)"},
            {"name": "bubble_count", "optimize": "minimize", "unit": "per_cm2", "description": "Visible bubbles per square centimeter"},
        ],
        "model": """
    rr = (RR - 2.0) / 0.2;
    at = (AT - 23) / 5;
    dg = (DG - 7.5) / 7.5;
    clar = 7.0 + 0.3*rr + 0.5*at + 1.5*dg - 1.5*rr*rr - 0.3*at*at - 0.4*dg*dg + 0.2*at*dg;
    bub = 8 - 0.5*rr - 1.0*at - 3.0*dg + 1.0*rr*rr + 0.5*at*at + 0.5*dg*dg - 0.3*at*dg;
    if (clar < 1) clar = 1; if (clar > 10) clar = 10;
    if (bub < 0) bub = 0;
    printf "{\\"clarity_score\\": %.1f, \\"bubble_count\\": %.1f}", clar + n1*0.3, bub + n2*0.5;
""",
        "factor_cases": '--resin_ratio) RR="$2"; shift 2 ;;\n        --ambient_temp_c) AT="$2"; shift 2 ;;\n        --degas_min) DG="$2"; shift 2 ;;',
        "awk_vars": '-v RR="$RR" -v AT="$AT" -v DG="$DG"',
        "vars_init": 'RR=""\nAT=""\nDG=""',
        "validate": '[ -z "$RR" ] || [ -z "$AT" ] || [ -z "$DG" ]',
    },
    {
        "num": 144, "slug": "soap_making",
        "name": "Handmade Soap Formulation",
        "desc": "Fractional factorial screening of coconut oil ratio, olive oil ratio, lye concentration, essential oil, and cure time for lather quality and hardness",
        "design": "fractional_factorial", "category": "home",
        "factors": [
            {"name": "coconut_pct", "levels": ["15", "40"], "type": "continuous", "unit": "%", "description": "Coconut oil as percentage of total oils"},
            {"name": "olive_pct", "levels": ["30", "70"], "type": "continuous", "unit": "%", "description": "Olive oil as percentage of total oils"},
            {"name": "lye_concentration", "levels": ["28", "38"], "type": "continuous", "unit": "%", "description": "Sodium hydroxide solution concentration"},
            {"name": "essential_oil_pct", "levels": ["1", "4"], "type": "continuous", "unit": "%", "description": "Essential oil fragrance load"},
            {"name": "cure_weeks", "levels": ["4", "8"], "type": "continuous", "unit": "weeks", "description": "Cold process cure time"},
        ],
        "fixed": {"superfat_pct": "5", "method": "cold_process"},
        "responses": [
            {"name": "lather_score", "optimize": "maximize", "unit": "pts", "description": "Lather volume and quality score (1-10)"},
            {"name": "hardness_score", "optimize": "maximize", "unit": "pts", "description": "Bar hardness and longevity score (1-10)"},
        ],
        "model": """
    co = (CO - 27.5) / 12.5;
    ol = (OL - 50) / 20;
    ly = (LY - 33) / 5;
    eo = (EO - 2.5) / 1.5;
    cw = (CW - 6) / 2;
    lath = 5.5 + 1.5*co - 0.5*ol + 0.3*ly + 0.2*eo + 0.4*cw + 0.3*co*ly;
    hard = 5.0 + 1.0*co - 0.8*ol + 0.5*ly - 0.1*eo + 0.8*cw + 0.2*co*cw;
    if (lath < 1) lath = 1; if (lath > 10) lath = 10;
    if (hard < 1) hard = 1; if (hard > 10) hard = 10;
    printf "{\\"lather_score\\": %.1f, \\"hardness_score\\": %.1f}", lath + n1*0.4, hard + n2*0.3;
""",
        "factor_cases": '--coconut_pct) CO="$2"; shift 2 ;;\n        --olive_pct) OL="$2"; shift 2 ;;\n        --lye_concentration) LY="$2"; shift 2 ;;\n        --essential_oil_pct) EO="$2"; shift 2 ;;\n        --cure_weeks) CW="$2"; shift 2 ;;',
        "awk_vars": '-v CO="$CO" -v OL="$OL" -v LY="$LY" -v EO="$EO" -v CW="$CW"',
        "vars_init": 'CO=""\nOL=""\nLY=""\nEO=""\nCW=""',
        "validate": '[ -z "$CO" ] || [ -z "$OL" ] || [ -z "$LY" ] || [ -z "$EO" ]',
    },
    {
        "num": 145, "slug": "aquarium_water_chemistry",
        "name": "Aquarium Water Chemistry",
        "desc": "Box-Behnken design to maximize fish health and plant growth by tuning pH, CO2 injection rate, and fertilizer dose",
        "design": "box_behnken", "category": "home",
        "factors": [
            {"name": "target_ph", "levels": ["6.2", "7.2"], "type": "continuous", "unit": "pH", "description": "Target water pH"},
            {"name": "co2_bps", "levels": ["1", "5"], "type": "continuous", "unit": "bubbles/sec", "description": "CO2 injection rate in bubbles per second"},
            {"name": "fert_ml_wk", "levels": ["5", "25"], "type": "continuous", "unit": "mL/week", "description": "Liquid fertilizer dose per week"},
        ],
        "fixed": {"tank_size_L": "200", "lighting": "medium"},
        "responses": [
            {"name": "fish_health", "optimize": "maximize", "unit": "pts", "description": "Fish activity and health score (1-10)"},
            {"name": "plant_growth", "optimize": "maximize", "unit": "cm/week", "description": "Average plant stem growth per week"},
        ],
        "model": """
    ph = (PH - 6.7) / 0.5;
    co = (CO - 3) / 2;
    fe = (FE - 15) / 10;
    fish = 7.0 + 0.3*ph - 0.5*co + 0.2*fe - 0.8*ph*ph - 0.3*co*co - 0.2*fe*fe + 0.2*ph*co;
    plant = 3.0 - 0.5*ph + 1.2*co + 0.8*fe - 0.3*ph*ph - 0.4*co*co - 0.2*fe*fe + 0.3*co*fe;
    if (fish < 1) fish = 1; if (fish > 10) fish = 10;
    if (plant < 0.5) plant = 0.5;
    printf "{\\"fish_health\\": %.1f, \\"plant_growth\\": %.1f}", fish + n1*0.3, plant + n2*0.2;
""",
        "factor_cases": '--target_ph) PH="$2"; shift 2 ;;\n        --co2_bps) CO="$2"; shift 2 ;;\n        --fert_ml_wk) FE="$2"; shift 2 ;;',
        "awk_vars": '-v PH="$PH" -v CO="$CO" -v FE="$FE"',
        "vars_init": 'PH=""\nCO=""\nFE=""',
        "validate": '[ -z "$PH" ] || [ -z "$CO" ] || [ -z "$FE" ]',
    },
    {
        "num": 146, "slug": "3d_print_quality",
        "name": "3D Print Quality Tuning",
        "desc": "Central composite design to maximize surface quality and minimize print time by tuning layer height, print speed, nozzle temperature, and infill percentage",
        "design": "central_composite", "category": "home",
        "factors": [
            {"name": "layer_height_mm", "levels": ["0.1", "0.3"], "type": "continuous", "unit": "mm", "description": "Layer height"},
            {"name": "print_speed", "levels": ["30", "80"], "type": "continuous", "unit": "mm/s", "description": "Print head speed"},
            {"name": "nozzle_temp_c", "levels": ["190", "220"], "type": "continuous", "unit": "C", "description": "Nozzle temperature for PLA"},
            {"name": "infill_pct", "levels": ["10", "50"], "type": "continuous", "unit": "%", "description": "Infill percentage"},
        ],
        "fixed": {"material": "PLA", "bed_temp": "60C"},
        "responses": [
            {"name": "surface_quality", "optimize": "maximize", "unit": "pts", "description": "Surface quality score (1-10)"},
            {"name": "print_time_min", "optimize": "minimize", "unit": "min", "description": "Total print time for benchmark part"},
        ],
        "model": """
    lh = (LH - 0.2) / 0.1;
    ps = (PS - 55) / 25;
    nt = (NT - 205) / 15;
    ip = (IP - 30) / 20;
    surf = 7.0 - 1.5*lh - 0.8*ps + 0.5*nt - 0.2*ip - 0.3*lh*lh + 0.2*ps*ps - 0.4*nt*nt + 0.3*lh*ps;
    time_ = 60 - 15*lh - 12*ps + 0.5*nt + 8*ip + 3*lh*lh + 2*ps*ps + 1.5*lh*ip;
    if (surf < 1) surf = 1; if (surf > 10) surf = 10;
    if (time_ < 15) time_ = 15;
    printf "{\\"surface_quality\\": %.1f, \\"print_time_min\\": %.0f}", surf + n1*0.3, time_ + n2*3;
""",
        "factor_cases": '--layer_height_mm) LH="$2"; shift 2 ;;\n        --print_speed) PS="$2"; shift 2 ;;\n        --nozzle_temp_c) NT="$2"; shift 2 ;;\n        --infill_pct) IP="$2"; shift 2 ;;',
        "awk_vars": '-v LH="$LH" -v PS="$PS" -v NT="$NT" -v IP="$IP"',
        "vars_init": 'LH=""\nPS=""\nNT=""\nIP=""',
        "validate": '[ -z "$LH" ] || [ -z "$PS" ] || [ -z "$NT" ] || [ -z "$IP" ]',
    },
]


def build_sim_script(uc):
    fixed_cases = ""
    for k in uc.get("fixed", {}):
        fixed_cases += f"\n        --{k}) shift 2 ;;"
    return textwrap.dedent(f"""\
#!/usr/bin/env bash
# Simulated: {uc['name']}
set -euo pipefail

OUTFILE=""
{uc['vars_init']}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        {uc['factor_cases']}{fixed_cases}
        *) shift ;;
    esac
done

if {uc['validate']}; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk {uc['awk_vars']} -v seed="$RANDOM" '
BEGIN {{
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;
{uc['model']}
}}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
""")


def build_config(uc):
    slug = uc["slug"]
    num = uc["num"]
    return {
        "metadata": {
            "name": uc["name"],
            "description": uc["desc"],
        },
        "factors": uc["factors"],
        "fixed_factors": uc.get("fixed", {}),
        "responses": uc["responses"],
        "runner": {"arg_style": "double-dash"},
        "settings": {
            "block_count": 1,
            "test_script": f"use_cases/{num}_{slug}/sim.sh",
            "operation": uc["design"],
            "processed_directory": f"use_cases/{num}_{slug}/results/analysis",
            "out_directory": f"use_cases/{num}_{slug}/results",
        },
    }


def main():
    for uc in USE_CASES:
        num = uc["num"]
        slug = uc["slug"]
        uc_dir = f"use_cases/{num}_{slug}"
        os.makedirs(uc_dir, exist_ok=True)
        os.makedirs(os.path.join(uc_dir, "results"), exist_ok=True)

        config = build_config(uc)
        config_path = os.path.join(uc_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        sim_script = build_sim_script(uc)
        sim_path = os.path.join(uc_dir, "sim.sh")
        with open(sim_path, "w") as f:
            f.write(sim_script)
        os.chmod(sim_path, os.stat(sim_path).st_mode | stat.S_IEXEC)

        print(f"  [{num:03d}] {uc_dir}/")

    print(f"\n  {len(USE_CASES)} use cases created (117-146).")


if __name__ == "__main__":
    main()
