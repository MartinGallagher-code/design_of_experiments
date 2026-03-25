#!/usr/bin/env python3
"""Generate 52 new use cases (199-250).

Categories:
  - Woodworking & Carpentry (199-208)
  - Sports & Athletics (209-218)
  - Cosmetics & Personal Care (219-228)
  - Geology & Earth Science (229-238)
  - Brewing & Fermentation (239-248)
  - General (249-250)
"""
import json, os, stat, textwrap

USE_CASES = [
    # ══════════════════════════════════════════════════
    # Woodworking & Carpentry (199-208)
    # ══════════════════════════════════════════════════
    {"num": 199, "slug": "wood_glue_joint", "name": "Wood Glue Joint Strength",
     "desc": "Box-Behnken design to maximize joint strength and minimize cure time by tuning glue spread rate, clamping pressure, and open assembly time",
     "design": "box_behnken", "category": "woodworking",
     "factors": [
         {"name": "spread_g_m2", "levels": ["100", "250"], "type": "continuous", "unit": "g/m2", "description": "Glue spread rate"},
         {"name": "clamp_psi", "levels": ["50", "250"], "type": "continuous", "unit": "psi", "description": "Clamping pressure"},
         {"name": "open_time_min", "levels": ["1", "10"], "type": "continuous", "unit": "min", "description": "Open assembly time before clamping"},
     ],
     "fixed": {"glue_type": "PVA", "wood": "red_oak"},
     "responses": [
         {"name": "shear_strength_mpa", "optimize": "maximize", "unit": "MPa", "description": "Shear strength of glue joint"},
         {"name": "cure_hrs", "optimize": "minimize", "unit": "hrs", "description": "Time to full cure"},
     ],
     "model": """
    sr = (SR - 175) / 75; cp = (CP - 150) / 100; ot = (OT - 5.5) / 4.5;
    str_ = 8.0 + 1.5*sr + 1.0*cp - 0.5*ot - 0.8*sr*sr - 0.5*cp*cp - 0.3*ot*ot + 0.3*sr*cp;
    cure = 4.0 - 0.3*sr + 0.2*cp + 0.5*ot + 0.2*sr*sr - 0.1*cp*cp + 0.15*sr*ot;
    if (str_ < 2) str_ = 2; if (cure < 1) cure = 1;
    printf "{\\"shear_strength_mpa\\": %.1f, \\"cure_hrs\\": %.1f}", str_ + n1*0.4, cure + n2*0.3;
""",
     "factor_cases": '--spread_g_m2) SR="$2"; shift 2 ;;\n        --clamp_psi) CP="$2"; shift 2 ;;\n        --open_time_min) OT="$2"; shift 2 ;;',
     "awk_vars": '-v SR="$SR" -v CP="$CP" -v OT="$OT"',
     "vars_init": 'SR=""\nCP=""\nOT=""', "validate": '[ -z "$SR" ] || [ -z "$CP" ] || [ -z "$OT" ]'},

    {"num": 200, "slug": "table_saw_cut", "name": "Table Saw Cut Quality",
     "desc": "Central composite design to maximize cut smoothness and minimize tearout by tuning blade speed, feed rate, and blade tooth count",
     "design": "central_composite", "category": "woodworking",
     "factors": [
         {"name": "blade_rpm", "levels": ["3000", "5000"], "type": "continuous", "unit": "rpm", "description": "Blade rotation speed"},
         {"name": "feed_rate", "levels": ["1", "5"], "type": "continuous", "unit": "m/min", "description": "Workpiece feed rate"},
         {"name": "tooth_count", "levels": ["24", "80"], "type": "continuous", "unit": "teeth", "description": "Blade tooth count"},
     ],
     "fixed": {"blade_diam": "10in", "material": "maple"},
     "responses": [
         {"name": "smoothness", "optimize": "maximize", "unit": "pts", "description": "Cut surface smoothness (1-10)"},
         {"name": "tearout_score", "optimize": "minimize", "unit": "pts", "description": "Bottom-side tearout severity (1-10)"},
     ],
     "model": """
    br = (BR - 4000) / 1000; fr = (FR - 3) / 2; tc = (TC - 52) / 28;
    smooth = 6.5 + 0.8*br - 1.0*fr + 1.5*tc - 0.3*br*br - 0.2*fr*fr - 0.4*tc*tc + 0.3*br*tc;
    tear = 4.0 - 0.5*br + 1.2*fr - 1.0*tc + 0.2*br*br + 0.3*fr*fr + 0.2*tc*tc + 0.3*fr*tc;
    if (smooth < 1) smooth = 1; if (smooth > 10) smooth = 10;
    if (tear < 1) tear = 1; if (tear > 10) tear = 10;
    printf "{\\"smoothness\\": %.1f, \\"tearout_score\\": %.1f}", smooth + n1*0.3, tear + n2*0.3;
""",
     "factor_cases": '--blade_rpm) BR="$2"; shift 2 ;;\n        --feed_rate) FR="$2"; shift 2 ;;\n        --tooth_count) TC="$2"; shift 2 ;;',
     "awk_vars": '-v BR="$BR" -v FR="$FR" -v TC="$TC"',
     "vars_init": 'BR=""\nFR=""\nTC=""', "validate": '[ -z "$BR" ] || [ -z "$FR" ] || [ -z "$TC" ]'},

    {"num": 201, "slug": "wood_finish_drying", "name": "Wood Finish Drying Conditions",
     "desc": "Full factorial of temperature, humidity, air circulation, and coat thickness to minimize drying time and maximize film hardness",
     "design": "full_factorial", "category": "woodworking",
     "factors": [
         {"name": "temp_c", "levels": ["15", "30"], "type": "continuous", "unit": "C", "description": "Drying room temperature"},
         {"name": "humidity_pct", "levels": ["30", "70"], "type": "continuous", "unit": "%", "description": "Relative humidity"},
         {"name": "air_flow", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Fan-assisted air circulation"},
         {"name": "coat_mils", "levels": ["2", "6"], "type": "continuous", "unit": "mils", "description": "Wet film coat thickness"},
     ],
     "fixed": {"finish_type": "polyurethane", "wood": "cherry"},
     "responses": [
         {"name": "dry_time_hrs", "optimize": "minimize", "unit": "hrs", "description": "Time to tack-free"},
         {"name": "hardness_h", "optimize": "maximize", "unit": "H_pencil", "description": "Pencil hardness grade (1=6B to 10=4H)"},
     ],
     "model": """
    tp = (TP - 22.5) / 7.5; hm = (HM - 50) / 20; af = (AF == "on") ? 1 : -1; cm = (CM - 4) / 2;
    dry = 4.0 - 1.2*tp + 0.8*hm - 0.6*af + 1.0*cm + 0.3*tp*tp + 0.2*hm*cm;
    hard = 6.0 + 0.5*tp - 0.3*hm + 0.2*af - 0.4*cm - 0.2*tp*tp + 0.1*af*cm;
    if (dry < 0.5) dry = 0.5; if (hard < 1) hard = 1; if (hard > 10) hard = 10;
    printf "{\\"dry_time_hrs\\": %.1f, \\"hardness_h\\": %.1f}", dry + n1*0.3, hard + n2*0.3;
""",
     "factor_cases": '--temp_c) TP="$2"; shift 2 ;;\n        --humidity_pct) HM="$2"; shift 2 ;;\n        --air_flow) AF="$2"; shift 2 ;;\n        --coat_mils) CM="$2"; shift 2 ;;',
     "awk_vars": '-v TP="$TP" -v HM="$HM" -v AF="$AF" -v CM="$CM"',
     "vars_init": 'TP=""\nHM=""\nAF=""\nCM=""', "validate": '[ -z "$TP" ] || [ -z "$HM" ] || [ -z "$AF" ] || [ -z "$CM" ]'},

    {"num": 202, "slug": "mortise_tenon_fit", "name": "Mortise & Tenon Fit",
     "desc": "Box-Behnken design to maximize joint strength and minimize assembly difficulty by tuning tenon thickness tolerance, shoulder depth, and glue type viscosity",
     "design": "box_behnken", "category": "woodworking",
     "factors": [
         {"name": "tolerance_mm", "levels": ["0.05", "0.5"], "type": "continuous", "unit": "mm", "description": "Tenon-to-mortise gap tolerance"},
         {"name": "shoulder_mm", "levels": ["3", "10"], "type": "continuous", "unit": "mm", "description": "Tenon shoulder depth"},
         {"name": "glue_viscosity", "levels": ["1000", "8000"], "type": "continuous", "unit": "cP", "description": "Adhesive viscosity"},
     ],
     "fixed": {"joint_type": "through_tenon", "wood": "white_oak"},
     "responses": [
         {"name": "pull_strength_kn", "optimize": "maximize", "unit": "kN", "description": "Pull-apart strength"},
         {"name": "assembly_score", "optimize": "maximize", "unit": "pts", "description": "Ease of assembly score (1-10)"},
     ],
     "model": """
    tl = (TL - 0.275) / 0.225; sd = (SD - 6.5) / 3.5; gv = (GV - 4500) / 3500;
    pull = 3.5 - 0.8*tl + 0.6*sd + 0.3*gv + 0.5*tl*tl - 0.2*sd*sd + 0.2*tl*gv;
    asm_ = 6.0 + 1.2*tl - 0.3*sd - 0.5*gv - 0.3*tl*tl + 0.2*sd*sd + 0.2*tl*sd;
    if (pull < 0.5) pull = 0.5; if (asm_ < 1) asm_ = 1; if (asm_ > 10) asm_ = 10;
    printf "{\\"pull_strength_kn\\": %.2f, \\"assembly_score\\": %.1f}", pull + n1*0.2, asm_ + n2*0.3;
""",
     "factor_cases": '--tolerance_mm) TL="$2"; shift 2 ;;\n        --shoulder_mm) SD="$2"; shift 2 ;;\n        --glue_viscosity) GV="$2"; shift 2 ;;',
     "awk_vars": '-v TL="$TL" -v SD="$SD" -v GV="$GV"',
     "vars_init": 'TL=""\nSD=""\nGV=""', "validate": '[ -z "$TL" ] || [ -z "$SD" ] || [ -z "$GV" ]'},

    {"num": 203, "slug": "router_bit_speed", "name": "Router Bit Speed & Feed",
     "desc": "Central composite design to maximize edge quality and minimize burning by tuning router RPM, feed rate, and depth of cut",
     "design": "central_composite", "category": "woodworking",
     "factors": [
         {"name": "router_rpm", "levels": ["10000", "24000"], "type": "continuous", "unit": "rpm", "description": "Router spindle speed"},
         {"name": "feed_m_min", "levels": ["1", "6"], "type": "continuous", "unit": "m/min", "description": "Feed rate"},
         {"name": "depth_mm", "levels": ["3", "12"], "type": "continuous", "unit": "mm", "description": "Depth of cut per pass"},
     ],
     "fixed": {"bit_type": "spiral_upcut", "bit_diam": "12mm"},
     "responses": [
         {"name": "edge_quality", "optimize": "maximize", "unit": "pts", "description": "Edge smoothness and profile accuracy (1-10)"},
         {"name": "burn_score", "optimize": "minimize", "unit": "pts", "description": "Wood burning severity (1-10)"},
     ],
     "model": """
    rr = (RR - 17000) / 7000; fr = (FR - 3.5) / 2.5; dp = (DP - 7.5) / 4.5;
    edge = 6.5 + 0.5*rr + 0.8*fr - 0.3*dp - 0.5*rr*rr - 0.3*fr*fr + 0.2*rr*fr;
    burn = 4.0 + 1.2*rr - 0.8*fr + 0.3*dp + 0.5*rr*rr + 0.2*dp*dp + 0.3*rr*dp;
    if (edge < 1) edge = 1; if (edge > 10) edge = 10;
    if (burn < 1) burn = 1; if (burn > 10) burn = 10;
    printf "{\\"edge_quality\\": %.1f, \\"burn_score\\": %.1f}", edge + n1*0.3, burn + n2*0.3;
""",
     "factor_cases": '--router_rpm) RR="$2"; shift 2 ;;\n        --feed_m_min) FR="$2"; shift 2 ;;\n        --depth_mm) DP="$2"; shift 2 ;;',
     "awk_vars": '-v RR="$RR" -v FR="$FR" -v DP="$DP"',
     "vars_init": 'RR=""\nFR=""\nDP=""', "validate": '[ -z "$RR" ] || [ -z "$FR" ] || [ -z "$DP" ]'},

    {"num": 204, "slug": "wood_bending", "name": "Steam Bending Parameters",
     "desc": "Box-Behnken design to maximize bend radius achievable and minimize cracking by tuning steam time, wood moisture content, and bending speed",
     "design": "box_behnken", "category": "woodworking",
     "factors": [
         {"name": "steam_min", "levels": ["30", "120"], "type": "continuous", "unit": "min", "description": "Steaming duration"},
         {"name": "moisture_pct", "levels": ["15", "30"], "type": "continuous", "unit": "%", "description": "Wood moisture content"},
         {"name": "bend_speed", "levels": ["1", "5"], "type": "continuous", "unit": "deg/sec", "description": "Bending rate in degrees per second"},
     ],
     "fixed": {"wood_species": "white_ash", "thickness_mm": "20"},
     "responses": [
         {"name": "min_radius_cm", "optimize": "minimize", "unit": "cm", "description": "Minimum achievable bend radius without failure"},
         {"name": "crack_rate_pct", "optimize": "minimize", "unit": "%", "description": "Percentage of pieces that crack"},
     ],
     "model": """
    sm = (SM - 75) / 45; mc = (MC - 22.5) / 7.5; bs = (BS - 3) / 2;
    rad = 15 - 3*sm - 2*mc + 2*bs + 1*sm*sm + 0.5*mc*mc + 0.3*bs*bs - 0.5*sm*mc;
    crack = 15 - 5*sm - 3*mc + 8*bs + 2*sm*sm + 1*bs*bs + 3*mc*bs;
    if (rad < 3) rad = 3; if (crack < 0) crack = 0; if (crack > 50) crack = 50;
    printf "{\\"min_radius_cm\\": %.1f, \\"crack_rate_pct\\": %.0f}", rad + n1*1, crack + n2*2;
""",
     "factor_cases": '--steam_min) SM="$2"; shift 2 ;;\n        --moisture_pct) MC="$2"; shift 2 ;;\n        --bend_speed) BS="$2"; shift 2 ;;',
     "awk_vars": '-v SM="$SM" -v MC="$MC" -v BS="$BS"',
     "vars_init": 'SM=""\nMC=""\nBS=""', "validate": '[ -z "$SM" ] || [ -z "$MC" ] || [ -z "$BS" ]'},

    {"num": 205, "slug": "sandpaper_progression", "name": "Sandpaper Grit Progression",
     "desc": "Fractional factorial screening of starting grit, grit steps, sanding pressure, passes per grit, and dust extraction for surface finish and time efficiency",
     "design": "fractional_factorial", "category": "woodworking",
     "factors": [
         {"name": "start_grit", "levels": ["60", "120"], "type": "continuous", "unit": "grit", "description": "Starting sandpaper grit"},
         {"name": "grit_steps", "levels": ["2", "5"], "type": "continuous", "unit": "steps", "description": "Number of grit progression steps"},
         {"name": "pressure_kg", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "kg", "description": "Hand sanding pressure"},
         {"name": "passes", "levels": ["3", "10"], "type": "continuous", "unit": "passes", "description": "Passes per grit level"},
         {"name": "dust_extract", "levels": ["0", "1"], "type": "continuous", "unit": "bool", "description": "Dust extraction on/off"},
     ],
     "fixed": {"wood": "walnut", "final_grit": "220"},
     "responses": [
         {"name": "finish_score", "optimize": "maximize", "unit": "pts", "description": "Surface finish quality (1-10)"},
         {"name": "time_min", "optimize": "minimize", "unit": "min", "description": "Total sanding time"},
     ],
     "model": """
    sg = (SG - 90) / 30; gs = (GS - 3.5) / 1.5; pr = (PR - 1.75) / 1.25; pa = (PA - 6.5) / 3.5; de = (DE - 0.5) / 0.5;
    fin = 5.5 - 0.5*sg + 1.0*gs + 0.3*pr + 0.8*pa + 0.2*de + 0.2*gs*pa;
    time_ = 10 + 3*sg + 5*gs + 2*pr + 4*pa - 1*de + 1*gs*pa;
    if (fin < 1) fin = 1; if (fin > 10) fin = 10; if (time_ < 3) time_ = 3;
    printf "{\\"finish_score\\": %.1f, \\"time_min\\": %.0f}", fin + n1*0.3, time_ + n2*1;
""",
     "factor_cases": '--start_grit) SG="$2"; shift 2 ;;\n        --grit_steps) GS="$2"; shift 2 ;;\n        --pressure_kg) PR="$2"; shift 2 ;;\n        --passes) PA="$2"; shift 2 ;;\n        --dust_extract) DE="$2"; shift 2 ;;',
     "awk_vars": '-v SG="$SG" -v GS="$GS" -v PR="$PR" -v PA="$PA" -v DE="$DE"',
     "vars_init": 'SG=""\nGS=""\nPR=""\nPA=""\nDE=""', "validate": '[ -z "$SG" ] || [ -z "$GS" ] || [ -z "$PR" ] || [ -z "$PA" ]'},

    {"num": 206, "slug": "dovetail_joint", "name": "Dovetail Joint Aesthetics",
     "desc": "Box-Behnken design to maximize visual appeal and joint tightness by tuning tail angle, pin-to-tail ratio, and baseline offset",
     "design": "box_behnken", "category": "woodworking",
     "factors": [
         {"name": "tail_angle_deg", "levels": ["7", "14"], "type": "continuous", "unit": "deg", "description": "Dovetail angle from perpendicular"},
         {"name": "pin_tail_ratio", "levels": ["0.3", "0.8"], "type": "continuous", "unit": "ratio", "description": "Pin width to tail width ratio"},
         {"name": "baseline_mm", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "mm", "description": "Baseline scribe offset from edge"},
     ],
     "fixed": {"wood": "cherry", "board_thickness": "19mm"},
     "responses": [
         {"name": "visual_appeal", "optimize": "maximize", "unit": "pts", "description": "Visual appeal and proportion score (1-10)"},
         {"name": "tightness", "optimize": "maximize", "unit": "pts", "description": "Joint tightness and gap-free score (1-10)"},
     ],
     "model": """
    ta = (TA - 10.5) / 3.5; pt = (PT - 0.55) / 0.25; bl = (BL - 1.25) / 0.75;
    vis = 6.5 + 0.5*ta + 0.8*pt + 0.3*bl - 0.5*ta*ta - 0.4*pt*pt + 0.2*ta*pt;
    tight = 7.0 - 0.3*ta - 0.2*pt + 0.5*bl - 0.3*ta*ta + 0.2*pt*pt - 0.3*bl*bl + 0.2*ta*bl;
    if (vis < 1) vis = 1; if (vis > 10) vis = 10;
    if (tight < 1) tight = 1; if (tight > 10) tight = 10;
    printf "{\\"visual_appeal\\": %.1f, \\"tightness\\": %.1f}", vis + n1*0.3, tight + n2*0.3;
""",
     "factor_cases": '--tail_angle_deg) TA="$2"; shift 2 ;;\n        --pin_tail_ratio) PT="$2"; shift 2 ;;\n        --baseline_mm) BL="$2"; shift 2 ;;',
     "awk_vars": '-v TA="$TA" -v PT="$PT" -v BL="$BL"',
     "vars_init": 'TA=""\nPT=""\nBL=""', "validate": '[ -z "$TA" ] || [ -z "$PT" ] || [ -z "$BL" ]'},

    {"num": 207, "slug": "lathe_turning", "name": "Wood Lathe Turning Quality",
     "desc": "Central composite design to maximize surface quality and minimize chatter by tuning spindle speed, tool rest distance, and gouge angle",
     "design": "central_composite", "category": "woodworking",
     "factors": [
         {"name": "spindle_rpm", "levels": ["500", "3000"], "type": "continuous", "unit": "rpm", "description": "Lathe spindle speed"},
         {"name": "rest_mm", "levels": ["3", "15"], "type": "continuous", "unit": "mm", "description": "Tool rest distance from workpiece"},
         {"name": "gouge_angle", "levels": ["30", "60"], "type": "continuous", "unit": "deg", "description": "Bowl gouge grind angle"},
     ],
     "fixed": {"wood": "maple_burl", "blank_diam": "200mm"},
     "responses": [
         {"name": "surface_quality", "optimize": "maximize", "unit": "pts", "description": "Turned surface quality (1-10)"},
         {"name": "chatter_score", "optimize": "minimize", "unit": "pts", "description": "Chatter marks severity (1-10)"},
     ],
     "model": """
    sr = (SR - 1750) / 1250; rd = (RD - 9) / 6; ga = (GA - 45) / 15;
    surf = 6.5 + 0.8*sr - 0.5*rd + 0.4*ga - 0.5*sr*sr - 0.3*rd*rd - 0.3*ga*ga + 0.2*sr*ga;
    chat = 4.0 - 0.5*sr + 0.8*rd - 0.3*ga + 0.3*sr*sr + 0.2*rd*rd + 0.2*sr*rd;
    if (surf < 1) surf = 1; if (surf > 10) surf = 10;
    if (chat < 1) chat = 1; if (chat > 10) chat = 10;
    printf "{\\"surface_quality\\": %.1f, \\"chatter_score\\": %.1f}", surf + n1*0.3, chat + n2*0.3;
""",
     "factor_cases": '--spindle_rpm) SR="$2"; shift 2 ;;\n        --rest_mm) RD="$2"; shift 2 ;;\n        --gouge_angle) GA="$2"; shift 2 ;;',
     "awk_vars": '-v SR="$SR" -v RD="$RD" -v GA="$GA"',
     "vars_init": 'SR=""\nRD=""\nGA=""', "validate": '[ -z "$SR" ] || [ -z "$RD" ] || [ -z "$GA" ]'},

    {"num": 208, "slug": "plywood_layup", "name": "Plywood Layup Optimization",
     "desc": "Full factorial of veneer thickness, glue weight, press temperature, and press time to maximize bending strength and minimize delamination",
     "design": "full_factorial", "category": "woodworking",
     "factors": [
         {"name": "veneer_mm", "levels": ["1.0", "3.0"], "type": "continuous", "unit": "mm", "description": "Individual veneer sheet thickness"},
         {"name": "glue_g_m2", "levels": ["120", "220"], "type": "continuous", "unit": "g/m2", "description": "Glue spread weight"},
         {"name": "press_temp_c", "levels": ["100", "150"], "type": "continuous", "unit": "C", "description": "Hot press temperature"},
         {"name": "press_min", "levels": ["3", "10"], "type": "continuous", "unit": "min", "description": "Press cycle time"},
     ],
     "fixed": {"species": "birch", "layers": "5"},
     "responses": [
         {"name": "bend_strength_mpa", "optimize": "maximize", "unit": "MPa", "description": "Bending strength (MOR)"},
         {"name": "delam_score", "optimize": "minimize", "unit": "pts", "description": "Delamination risk score (1-10)"},
     ],
     "model": """
    vn = (VN - 2) / 1; gw = (GW - 170) / 50; pt = (PT - 125) / 25; pm = (PM - 6.5) / 3.5;
    bend = 60 - 5*vn + 3*gw + 4*pt + 2*pm + 1*vn*vn + 0.5*gw*pt;
    delam = 4.0 + 0.5*vn - 0.8*gw - 0.6*pt - 1.0*pm + 0.3*vn*vn + 0.2*gw*gw + 0.2*vn*pm;
    if (bend < 20) bend = 20; if (delam < 1) delam = 1; if (delam > 10) delam = 10;
    printf "{\\"bend_strength_mpa\\": %.0f, \\"delam_score\\": %.1f}", bend + n1*3, delam + n2*0.3;
""",
     "factor_cases": '--veneer_mm) VN="$2"; shift 2 ;;\n        --glue_g_m2) GW="$2"; shift 2 ;;\n        --press_temp_c) PT="$2"; shift 2 ;;\n        --press_min) PM="$2"; shift 2 ;;',
     "awk_vars": '-v VN="$VN" -v GW="$GW" -v PT="$PT" -v PM="$PM"',
     "vars_init": 'VN=""\nGW=""\nPT=""\nPM=""', "validate": '[ -z "$VN" ] || [ -z "$GW" ] || [ -z "$PT" ] || [ -z "$PM" ]'},

    # ══════════════════════════════════════════════════
    # Sports & Athletics (209-218)
    # ══════════════════════════════════════════════════
    {"num": 209, "slug": "golf_driver_launch", "name": "Golf Driver Launch Conditions",
     "desc": "Box-Behnken design to maximize carry distance and minimize side spin by tuning loft angle, shaft flex, and tee height",
     "design": "box_behnken", "category": "sports",
     "factors": [
         {"name": "loft_deg", "levels": ["8", "12"], "type": "continuous", "unit": "deg", "description": "Driver loft angle"},
         {"name": "shaft_flex", "levels": ["1", "5"], "type": "continuous", "unit": "rating", "description": "Shaft flex (1=stiff to 5=senior)"},
         {"name": "tee_height_mm", "levels": ["40", "70"], "type": "continuous", "unit": "mm", "description": "Tee height above ground"},
     ],
     "fixed": {"swing_speed": "95mph", "ball": "three_piece"},
     "responses": [
         {"name": "carry_yards", "optimize": "maximize", "unit": "yds", "description": "Carry distance in yards"},
         {"name": "side_spin_rpm", "optimize": "minimize", "unit": "rpm", "description": "Absolute side spin"},
     ],
     "model": """
    lo = (LO - 10) / 2; sf = (SF - 3) / 2; th = (TH - 55) / 15;
    carry = 240 + 5*lo + 3*sf + 4*th - 3*lo*lo - 2*sf*sf - 1.5*th*th + 1*lo*th;
    spin = 500 + 100*lo + 150*sf + 50*th + 50*lo*lo + 80*sf*sf + 30*lo*sf;
    if (carry < 180) carry = 180; if (spin < 50) spin = 50;
    printf "{\\"carry_yards\\": %.0f, \\"side_spin_rpm\\": %.0f}", carry + n1*5, spin + n2*30;
""",
     "factor_cases": '--loft_deg) LO="$2"; shift 2 ;;\n        --shaft_flex) SF="$2"; shift 2 ;;\n        --tee_height_mm) TH="$2"; shift 2 ;;',
     "awk_vars": '-v LO="$LO" -v SF="$SF" -v TH="$TH"',
     "vars_init": 'LO=""\nSF=""\nTH=""', "validate": '[ -z "$LO" ] || [ -z "$SF" ] || [ -z "$TH" ]'},

    {"num": 210, "slug": "swimming_stroke", "name": "Swimming Stroke Efficiency",
     "desc": "Central composite design to maximize speed and minimize energy expenditure by tuning stroke rate, stroke length, and kick tempo",
     "design": "central_composite", "category": "sports",
     "factors": [
         {"name": "stroke_rate", "levels": ["40", "70"], "type": "continuous", "unit": "strokes/min", "description": "Stroke rate"},
         {"name": "stroke_length_m", "levels": ["1.5", "2.5"], "type": "continuous", "unit": "m", "description": "Distance per stroke"},
         {"name": "kick_ratio", "levels": ["2", "6"], "type": "continuous", "unit": "kicks/stroke", "description": "Kick tempo per stroke cycle"},
     ],
     "fixed": {"stroke": "freestyle", "pool": "25m"},
     "responses": [
         {"name": "speed_m_s", "optimize": "maximize", "unit": "m/s", "description": "Swimming speed"},
         {"name": "energy_kj_100m", "optimize": "minimize", "unit": "kJ/100m", "description": "Energy cost per 100m"},
     ],
     "model": """
    sr = (SR - 55) / 15; sl = (SL - 2) / 0.5; kr = (KR - 4) / 2;
    spd = 1.5 + 0.15*sr + 0.2*sl + 0.05*kr - 0.05*sr*sr - 0.08*sl*sl + 0.03*sr*sl;
    eng = 30 + 3*sr - 4*sl + 2*kr + 1*sr*sr + 0.5*sl*sl + 0.8*kr*kr + 0.5*sr*kr;
    if (spd < 0.8) spd = 0.8; if (eng < 15) eng = 15;
    printf "{\\"speed_m_s\\": %.2f, \\"energy_kj_100m\\": %.0f}", spd + n1*0.03, eng + n2*1.5;
""",
     "factor_cases": '--stroke_rate) SR="$2"; shift 2 ;;\n        --stroke_length_m) SL="$2"; shift 2 ;;\n        --kick_ratio) KR="$2"; shift 2 ;;',
     "awk_vars": '-v SR="$SR" -v SL="$SL" -v KR="$KR"',
     "vars_init": 'SR=""\nSL=""\nKR=""', "validate": '[ -z "$SR" ] || [ -z "$SL" ] || [ -z "$KR" ]'},

    {"num": 211, "slug": "tennis_racket_string", "name": "Tennis Racket String Setup",
     "desc": "Box-Behnken design to maximize power and control by tuning main string tension, cross string tension, and string gauge",
     "design": "box_behnken", "category": "sports",
     "factors": [
         {"name": "main_tension_kg", "levels": ["20", "28"], "type": "continuous", "unit": "kg", "description": "Main string tension"},
         {"name": "cross_tension_kg", "levels": ["18", "26"], "type": "continuous", "unit": "kg", "description": "Cross string tension"},
         {"name": "gauge_mm", "levels": ["1.15", "1.35"], "type": "continuous", "unit": "mm", "description": "String gauge diameter"},
     ],
     "fixed": {"racket": "midplus_100", "string_material": "polyester"},
     "responses": [
         {"name": "power_score", "optimize": "maximize", "unit": "pts", "description": "Power and depth rating (1-10)"},
         {"name": "control_score", "optimize": "maximize", "unit": "pts", "description": "Placement control rating (1-10)"},
     ],
     "model": """
    mt = (MT - 24) / 4; ct = (CT - 22) / 4; ga = (GA - 1.25) / 0.1;
    pwr = 6.5 - 1.0*mt - 0.5*ct - 0.8*ga - 0.3*mt*mt + 0.2*ct*ct + 0.2*mt*ct;
    ctrl = 5.5 + 0.8*mt + 0.5*ct + 0.3*ga - 0.4*mt*mt - 0.2*ct*ct + 0.2*mt*ga;
    if (pwr < 1) pwr = 1; if (pwr > 10) pwr = 10;
    if (ctrl < 1) ctrl = 1; if (ctrl > 10) ctrl = 10;
    printf "{\\"power_score\\": %.1f, \\"control_score\\": %.1f}", pwr + n1*0.3, ctrl + n2*0.3;
""",
     "factor_cases": '--main_tension_kg) MT="$2"; shift 2 ;;\n        --cross_tension_kg) CT="$2"; shift 2 ;;\n        --gauge_mm) GA="$2"; shift 2 ;;',
     "awk_vars": '-v MT="$MT" -v CT="$CT" -v GA="$GA"',
     "vars_init": 'MT=""\nCT=""\nGA=""', "validate": '[ -z "$MT" ] || [ -z "$CT" ] || [ -z "$GA" ]'},

    {"num": 212, "slug": "basketball_shooting", "name": "Basketball Free Throw Form",
     "desc": "Central composite design to maximize accuracy and arc consistency by tuning release angle, release height, and backspin rate",
     "design": "central_composite", "category": "sports",
     "factors": [
         {"name": "release_angle_deg", "levels": ["45", "55"], "type": "continuous", "unit": "deg", "description": "Ball release angle from horizontal"},
         {"name": "release_height_m", "levels": ["2.0", "2.5"], "type": "continuous", "unit": "m", "description": "Ball release height"},
         {"name": "backspin_rpm", "levels": ["100", "300"], "type": "continuous", "unit": "rpm", "description": "Ball backspin rate"},
     ],
     "fixed": {"distance": "4.6m", "ball": "size_7"},
     "responses": [
         {"name": "accuracy_pct", "optimize": "maximize", "unit": "%", "description": "Free throw accuracy percentage"},
         {"name": "arc_consistency", "optimize": "maximize", "unit": "pts", "description": "Arc trajectory consistency (1-10)"},
     ],
     "model": """
    ra = (RA - 50) / 5; rh = (RH - 2.25) / 0.25; bs = (BS - 200) / 100;
    acc = 72 + 3*ra + 4*rh + 2*bs - 4*ra*ra - 2*rh*rh - 1.5*bs*bs + 1*ra*rh;
    arc = 6.5 + 0.5*ra + 0.8*rh + 0.3*bs - 0.5*ra*ra - 0.4*rh*rh + 0.2*ra*bs;
    if (acc < 30) acc = 30; if (acc > 100) acc = 100;
    if (arc < 1) arc = 1; if (arc > 10) arc = 10;
    printf "{\\"accuracy_pct\\": %.0f, \\"arc_consistency\\": %.1f}", acc + n1*3, arc + n2*0.3;
""",
     "factor_cases": '--release_angle_deg) RA="$2"; shift 2 ;;\n        --release_height_m) RH="$2"; shift 2 ;;\n        --backspin_rpm) BS="$2"; shift 2 ;;',
     "awk_vars": '-v RA="$RA" -v RH="$RH" -v BS="$BS"',
     "vars_init": 'RA=""\nRH=""\nBS=""', "validate": '[ -z "$RA" ] || [ -z "$RH" ] || [ -z "$BS" ]'},

    {"num": 213, "slug": "ski_wax_selection", "name": "Ski Wax Temperature Match",
     "desc": "Box-Behnken design to maximize glide speed and minimize drag by tuning wax temperature range, iron temperature, and number of wax layers",
     "design": "box_behnken", "category": "sports",
     "factors": [
         {"name": "wax_temp_mid_c", "levels": ["-15", "0"], "type": "continuous", "unit": "C", "description": "Wax rated midpoint temperature"},
         {"name": "iron_temp_c", "levels": ["110", "150"], "type": "continuous", "unit": "C", "description": "Waxing iron temperature"},
         {"name": "layers", "levels": ["1", "4"], "type": "continuous", "unit": "layers", "description": "Number of wax applications"},
     ],
     "fixed": {"snow_temp": "-8C", "ski_base": "sintered"},
     "responses": [
         {"name": "glide_speed_pct", "optimize": "maximize", "unit": "%", "description": "Glide speed relative to unwaxed baseline"},
         {"name": "durability_km", "optimize": "maximize", "unit": "km", "description": "Wax durability in kilometers"},
     ],
     "model": """
    wt = (WT - -7.5) / 7.5; it = (IT - 130) / 20; ly = (LY - 2.5) / 1.5;
    glide = 110 + 3*wt + 2*it + 4*ly - 5*wt*wt - 1*it*it - 1*ly*ly + 0.5*wt*it;
    dur = 15 + 2*wt + 1*it + 5*ly - 1*wt*wt + 0.5*it*ly;
    if (glide < 95) glide = 95; if (dur < 3) dur = 3;
    printf "{\\"glide_speed_pct\\": %.0f, \\"durability_km\\": %.0f}", glide + n1*2, dur + n2*1;
""",
     "factor_cases": '--wax_temp_mid_c) WT="$2"; shift 2 ;;\n        --iron_temp_c) IT="$2"; shift 2 ;;\n        --layers) LY="$2"; shift 2 ;;',
     "awk_vars": '-v WT="$WT" -v IT="$IT" -v LY="$LY"',
     "vars_init": 'WT=""\nIT=""\nLY=""', "validate": '[ -z "$WT" ] || [ -z "$IT" ] || [ -z "$LY" ]'},

    {"num": 214, "slug": "archery_bow_tuning", "name": "Archery Bow Tuning",
     "desc": "Full factorial of draw weight, arrow spine, brace height, and nocking point height to maximize grouping tightness and minimize vertical drift",
     "design": "full_factorial", "category": "sports",
     "factors": [
         {"name": "draw_weight_lbs", "levels": ["30", "50"], "type": "continuous", "unit": "lbs", "description": "Bow draw weight"},
         {"name": "arrow_spine", "levels": ["400", "700"], "type": "continuous", "unit": "spine", "description": "Arrow spine deflection rating"},
         {"name": "brace_height_in", "levels": ["6", "9"], "type": "continuous", "unit": "in", "description": "Brace height"},
         {"name": "nock_height_mm", "levels": ["0", "6"], "type": "continuous", "unit": "mm", "description": "Nocking point height above square"},
     ],
     "fixed": {"bow_type": "recurve", "distance": "18m"},
     "responses": [
         {"name": "group_size_cm", "optimize": "minimize", "unit": "cm", "description": "Average group diameter at 18m"},
         {"name": "vertical_drift_cm", "optimize": "minimize", "unit": "cm", "description": "Vertical point of impact drift"},
     ],
     "model": """
    dw = (DW - 40) / 10; as_ = (AS - 550) / 150; bh = (BH - 7.5) / 1.5; nh = (NH - 3) / 3;
    grp = 8 - 1*dw + 0.5*as_ - 0.3*bh + 0.5*nh + 0.5*dw*dw + 0.8*as_*as_ + 0.3*bh*bh + 0.3*dw*as_;
    drift = 3 + 0.5*dw - 0.3*as_ + 0.2*bh + 1.5*nh + 0.3*nh*nh - 0.2*dw*nh;
    if (grp < 2) grp = 2; if (drift < 0) drift = 0;
    printf "{\\"group_size_cm\\": %.1f, \\"vertical_drift_cm\\": %.1f}", grp + n1*0.5, drift + n2*0.3;
""",
     "factor_cases": '--draw_weight_lbs) DW="$2"; shift 2 ;;\n        --arrow_spine) AS="$2"; shift 2 ;;\n        --brace_height_in) BH="$2"; shift 2 ;;\n        --nock_height_mm) NH="$2"; shift 2 ;;',
     "awk_vars": '-v DW="$DW" -v AS="$AS" -v BH="$BH" -v NH="$NH"',
     "vars_init": 'DW=""\nAS=""\nBH=""\nNH=""', "validate": '[ -z "$DW" ] || [ -z "$AS" ] || [ -z "$BH" ] || [ -z "$NH" ]'},

    {"num": 215, "slug": "rock_climbing_route", "name": "Indoor Climbing Route Setting",
     "desc": "Box-Behnken design to maximize route quality rating and target a specific difficulty grade by tuning hold spacing, wall angle, and rest frequency",
     "design": "box_behnken", "category": "sports",
     "factors": [
         {"name": "hold_spacing_cm", "levels": ["20", "50"], "type": "continuous", "unit": "cm", "description": "Average distance between holds"},
         {"name": "wall_angle_deg", "levels": ["0", "30"], "type": "continuous", "unit": "deg", "description": "Wall overhang angle"},
         {"name": "rest_frequency", "levels": ["1", "5"], "type": "continuous", "unit": "per_route", "description": "Number of rest positions per route"},
     ],
     "fixed": {"wall_height": "12m", "hold_set": "medium_crimps"},
     "responses": [
         {"name": "quality_rating", "optimize": "maximize", "unit": "pts", "description": "Route quality and flow rating (1-10)"},
         {"name": "grade_accuracy", "optimize": "maximize", "unit": "pts", "description": "Grade accuracy vs target (1-10, 10=perfect match)"},
     ],
     "model": """
    hs = (HS - 35) / 15; wa = (WA - 15) / 15; rf = (RF - 3) / 2;
    qual = 6.5 + 0.3*hs + 0.8*wa + 0.5*rf - 0.4*hs*hs - 0.3*wa*wa - 0.3*rf*rf + 0.2*hs*wa;
    grade = 7.0 - 0.5*hs + 0.3*wa - 0.2*rf - 0.6*hs*hs - 0.4*wa*wa + 0.2*hs*rf;
    if (qual < 1) qual = 1; if (qual > 10) qual = 10;
    if (grade < 1) grade = 1; if (grade > 10) grade = 10;
    printf "{\\"quality_rating\\": %.1f, \\"grade_accuracy\\": %.1f}", qual + n1*0.3, grade + n2*0.3;
""",
     "factor_cases": '--hold_spacing_cm) HS="$2"; shift 2 ;;\n        --wall_angle_deg) WA="$2"; shift 2 ;;\n        --rest_frequency) RF="$2"; shift 2 ;;',
     "awk_vars": '-v HS="$HS" -v WA="$WA" -v RF="$RF"',
     "vars_init": 'HS=""\nWA=""\nRF=""', "validate": '[ -z "$HS" ] || [ -z "$WA" ] || [ -z "$RF" ]'},

    {"num": 216, "slug": "rowing_technique", "name": "Rowing Ergometer Performance",
     "desc": "Central composite design to maximize power output and minimize split time by tuning stroke rate, drive ratio, and drag factor",
     "design": "central_composite", "category": "sports",
     "factors": [
         {"name": "stroke_rate", "levels": ["22", "34"], "type": "continuous", "unit": "spm", "description": "Strokes per minute"},
         {"name": "drive_ratio", "levels": ["1.5", "3.0"], "type": "continuous", "unit": "ratio", "description": "Drive-to-recovery time ratio"},
         {"name": "drag_factor", "levels": ["100", "140"], "type": "continuous", "unit": "units", "description": "Concept2 drag factor setting"},
     ],
     "fixed": {"athlete": "intermediate_male", "piece": "2000m"},
     "responses": [
         {"name": "avg_watts", "optimize": "maximize", "unit": "W", "description": "Average power output"},
         {"name": "split_500m_sec", "optimize": "minimize", "unit": "sec", "description": "500m split time in seconds"},
     ],
     "model": """
    sr = (SR - 28) / 6; dr = (DR - 2.25) / 0.75; df = (DF - 120) / 20;
    watts = 220 + 20*sr + 10*dr + 8*df - 8*sr*sr - 5*dr*dr - 3*df*df + 3*sr*dr;
    split = 115 - 5*sr - 3*dr - 2*df + 2*sr*sr + 1*dr*dr + 0.5*df*df - 0.8*sr*dr;
    if (watts < 100) watts = 100; if (split < 85) split = 85;
    printf "{\\"avg_watts\\": %.0f, \\"split_500m_sec\\": %.0f}", watts + n1*5, split + n2*1;
""",
     "factor_cases": '--stroke_rate) SR="$2"; shift 2 ;;\n        --drive_ratio) DR="$2"; shift 2 ;;\n        --drag_factor) DF="$2"; shift 2 ;;',
     "awk_vars": '-v SR="$SR" -v DR="$DR" -v DF="$DF"',
     "vars_init": 'SR=""\nDR=""\nDF=""', "validate": '[ -z "$SR" ] || [ -z "$DR" ] || [ -z "$DF" ]'},

    {"num": 217, "slug": "yoga_sequence", "name": "Yoga Sequence Design",
     "desc": "Box-Behnken design to maximize flexibility gain and relaxation by tuning hold duration, transition speed, and warmup length",
     "design": "box_behnken", "category": "sports",
     "factors": [
         {"name": "hold_sec", "levels": ["15", "60"], "type": "continuous", "unit": "sec", "description": "Average pose hold duration"},
         {"name": "transition_pace", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "Transition speed (1=slow to 5=vinyasa)"},
         {"name": "warmup_min", "levels": ["5", "20"], "type": "continuous", "unit": "min", "description": "Warmup sequence duration"},
     ],
     "fixed": {"session_length": "60min", "level": "intermediate"},
     "responses": [
         {"name": "flexibility_gain", "optimize": "maximize", "unit": "pts", "description": "Session flexibility improvement (1-10)"},
         {"name": "relaxation_score", "optimize": "maximize", "unit": "pts", "description": "Post-session relaxation and calm (1-10)"},
     ],
     "model": """
    hs = (HS - 37.5) / 22.5; tp = (TP - 3) / 2; wm = (WM - 12.5) / 7.5;
    flex = 6.0 + 1.0*hs + 0.3*tp + 0.5*wm - 0.3*hs*hs - 0.2*tp*tp + 0.2*hs*wm;
    relax = 6.5 + 0.5*hs - 1.0*tp + 0.3*wm - 0.2*hs*hs + 0.3*tp*tp + 0.2*hs*tp;
    if (flex < 1) flex = 1; if (flex > 10) flex = 10;
    if (relax < 1) relax = 1; if (relax > 10) relax = 10;
    printf "{\\"flexibility_gain\\": %.1f, \\"relaxation_score\\": %.1f}", flex + n1*0.3, relax + n2*0.3;
""",
     "factor_cases": '--hold_sec) HS="$2"; shift 2 ;;\n        --transition_pace) TP="$2"; shift 2 ;;\n        --warmup_min) WM="$2"; shift 2 ;;',
     "awk_vars": '-v HS="$HS" -v TP="$TP" -v WM="$WM"',
     "vars_init": 'HS=""\nTP=""\nWM=""', "validate": '[ -z "$HS" ] || [ -z "$TP" ] || [ -z "$WM" ]'},

    {"num": 218, "slug": "soccer_passing_drill", "name": "Soccer Passing Drill Design",
     "desc": "Plackett-Burman screening of pass distance, player count, tempo, rest interval, and cone spacing for passing accuracy and decision speed",
     "design": "plackett_burman", "category": "sports",
     "factors": [
         {"name": "pass_dist_m", "levels": ["5", "20"], "type": "continuous", "unit": "m", "description": "Required pass distance"},
         {"name": "player_count", "levels": ["4", "10"], "type": "continuous", "unit": "players", "description": "Number of players in drill"},
         {"name": "tempo_bpm", "levels": ["60", "120"], "type": "continuous", "unit": "bpm", "description": "Drill tempo in beats per minute"},
         {"name": "rest_sec", "levels": ["10", "60"], "type": "continuous", "unit": "sec", "description": "Rest between repetitions"},
         {"name": "cone_spacing_m", "levels": ["2", "8"], "type": "continuous", "unit": "m", "description": "Cone gate spacing"},
     ],
     "fixed": {"ball_type": "size_5", "surface": "artificial_turf"},
     "responses": [
         {"name": "accuracy_pct", "optimize": "maximize", "unit": "%", "description": "Pass completion accuracy"},
         {"name": "decision_speed_ms", "optimize": "minimize", "unit": "ms", "description": "Average decision-making time"},
     ],
     "model": """
    pd = (PD - 12.5) / 7.5; pc = (PC - 7) / 3; tm = (TM - 90) / 30; rs = (RS - 35) / 25; cs = (CS - 5) / 3;
    acc = 75 - 5*pd + 2*pc - 3*tm + 2*rs + 1*cs - 1*pd*pd + 0.5*pc*tm;
    dec = 800 + 50*pd + 30*pc + 80*tm - 40*rs - 20*cs + 20*pd*tm;
    if (acc < 40) acc = 40; if (acc > 100) acc = 100; if (dec < 300) dec = 300;
    printf "{\\"accuracy_pct\\": %.0f, \\"decision_speed_ms\\": %.0f}", acc + n1*3, dec + n2*30;
""",
     "factor_cases": '--pass_dist_m) PD="$2"; shift 2 ;;\n        --player_count) PC="$2"; shift 2 ;;\n        --tempo_bpm) TM="$2"; shift 2 ;;\n        --rest_sec) RS="$2"; shift 2 ;;\n        --cone_spacing_m) CS="$2"; shift 2 ;;',
     "awk_vars": '-v PD="$PD" -v PC="$PC" -v TM="$TM" -v RS="$RS" -v CS="$CS"',
     "vars_init": 'PD=""\nPC=""\nTM=""\nRS=""\nCS=""', "validate": '[ -z "$PD" ] || [ -z "$PC" ] || [ -z "$TM" ] || [ -z "$RS" ]'},

    # ══════════════════════════════════════════════════
    # Cosmetics & Personal Care (219-228)
    # ══════════════════════════════════════════════════
    {"num": 219, "slug": "moisturizer_absorption", "name": "Moisturizer Absorption Rate",
     "desc": "Box-Behnken design to maximize hydration depth and minimize greasy residue by tuning hyaluronic acid concentration, emulsifier ratio, and application amount",
     "design": "box_behnken", "category": "cosmetics",
     "factors": [
         {"name": "ha_pct", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "%", "description": "Hyaluronic acid concentration"},
         {"name": "emulsifier_pct", "levels": ["2", "8"], "type": "continuous", "unit": "%", "description": "Emulsifier percentage"},
         {"name": "amount_mg_cm2", "levels": ["1", "4"], "type": "continuous", "unit": "mg/cm2", "description": "Application amount per area"},
     ],
     "fixed": {"base": "oil_in_water", "ph": "5.5"},
     "responses": [
         {"name": "hydration_depth", "optimize": "maximize", "unit": "pts", "description": "Skin hydration improvement at 4hr (1-10)"},
         {"name": "greasiness", "optimize": "minimize", "unit": "pts", "description": "Greasy residue score at 30min (1-10)"},
     ],
     "model": """
    ha = (HA - 1.75) / 1.25; em = (EM - 5) / 3; am = (AM - 2.5) / 1.5;
    hyd = 6.0 + 1.2*ha + 0.5*em + 0.8*am - 0.5*ha*ha - 0.3*em*em + 0.2*ha*am;
    grs = 3.5 + 0.3*ha + 0.8*em + 1.0*am + 0.2*em*em + 0.3*am*am + 0.2*em*am;
    if (hyd < 1) hyd = 1; if (hyd > 10) hyd = 10;
    if (grs < 1) grs = 1; if (grs > 10) grs = 10;
    printf "{\\"hydration_depth\\": %.1f, \\"greasiness\\": %.1f}", hyd + n1*0.3, grs + n2*0.3;
""",
     "factor_cases": '--ha_pct) HA="$2"; shift 2 ;;\n        --emulsifier_pct) EM="$2"; shift 2 ;;\n        --amount_mg_cm2) AM="$2"; shift 2 ;;',
     "awk_vars": '-v HA="$HA" -v EM="$EM" -v AM="$AM"',
     "vars_init": 'HA=""\nEM=""\nAM=""', "validate": '[ -z "$HA" ] || [ -z "$EM" ] || [ -z "$AM" ]'},

    {"num": 220, "slug": "shampoo_foam", "name": "Shampoo Foaming & Cleansing",
     "desc": "Central composite design to maximize foam volume and cleansing power while minimizing scalp dryness by tuning surfactant blend, pH, and viscosity",
     "design": "central_composite", "category": "cosmetics",
     "factors": [
         {"name": "surfactant_pct", "levels": ["8", "18"], "type": "continuous", "unit": "%", "description": "Primary surfactant concentration"},
         {"name": "ph_level", "levels": ["4.5", "6.5"], "type": "continuous", "unit": "pH", "description": "Product pH"},
         {"name": "viscosity_cp", "levels": ["2000", "8000"], "type": "continuous", "unit": "cP", "description": "Product viscosity"},
     ],
     "fixed": {"fragrance": "floral", "preservative": "phenoxyethanol"},
     "responses": [
         {"name": "foam_score", "optimize": "maximize", "unit": "pts", "description": "Foam volume and stability (1-10)"},
         {"name": "scalp_dryness", "optimize": "minimize", "unit": "pts", "description": "Post-wash scalp dryness (1-10)"},
     ],
     "model": """
    sf = (SF - 13) / 5; ph = (PH - 5.5) / 1; vs = (VS - 5000) / 3000;
    foam = 6.0 + 1.5*sf - 0.3*ph + 0.5*vs - 0.5*sf*sf + 0.2*ph*ph + 0.2*sf*vs;
    dry = 4.0 + 1.0*sf - 0.5*ph - 0.2*vs + 0.3*sf*sf + 0.2*ph*ph + 0.2*sf*ph;
    if (foam < 1) foam = 1; if (foam > 10) foam = 10;
    if (dry < 1) dry = 1; if (dry > 10) dry = 10;
    printf "{\\"foam_score\\": %.1f, \\"scalp_dryness\\": %.1f}", foam + n1*0.3, dry + n2*0.3;
""",
     "factor_cases": '--surfactant_pct) SF="$2"; shift 2 ;;\n        --ph_level) PH="$2"; shift 2 ;;\n        --viscosity_cp) VS="$2"; shift 2 ;;',
     "awk_vars": '-v SF="$SF" -v PH="$PH" -v VS="$VS"',
     "vars_init": 'SF=""\nPH=""\nVS=""', "validate": '[ -z "$SF" ] || [ -z "$PH" ] || [ -z "$VS" ]'},

    {"num": 221, "slug": "nail_polish_durability", "name": "Nail Polish Durability",
     "desc": "Box-Behnken design to maximize chip resistance and gloss retention by tuning base coat thickness, color coat layers, and top coat formula",
     "design": "box_behnken", "category": "cosmetics",
     "factors": [
         {"name": "base_coats", "levels": ["1", "2"], "type": "continuous", "unit": "coats", "description": "Number of base coat layers"},
         {"name": "color_coats", "levels": ["1", "3"], "type": "continuous", "unit": "coats", "description": "Number of color coat layers"},
         {"name": "topcoat_thickness", "levels": ["1", "3"], "type": "continuous", "unit": "mils", "description": "Top coat thickness in mils"},
     ],
     "fixed": {"prep": "dehydrator", "cure": "air_dry"},
     "responses": [
         {"name": "days_no_chip", "optimize": "maximize", "unit": "days", "description": "Days before first chip"},
         {"name": "gloss_retention_pct", "optimize": "maximize", "unit": "%", "description": "Gloss retention at day 5"},
     ],
     "model": """
    bc = (BC - 1.5) / 0.5; cc = (CC - 2) / 1; tt = (TT - 2) / 1;
    days = 5 + 1.5*bc + 1*cc + 2*tt - 0.5*bc*bc - 0.3*cc*cc + 0.3*bc*tt;
    gloss = 75 + 5*bc + 3*cc + 8*tt - 2*bc*bc - 1*cc*cc - 3*tt*tt + 1*cc*tt;
    if (days < 1) days = 1; if (gloss < 40) gloss = 40; if (gloss > 100) gloss = 100;
    printf "{\\"days_no_chip\\": %.0f, \\"gloss_retention_pct\\": %.0f}", days + n1*0.5, gloss + n2*3;
""",
     "factor_cases": '--base_coats) BC="$2"; shift 2 ;;\n        --color_coats) CC="$2"; shift 2 ;;\n        --topcoat_thickness) TT="$2"; shift 2 ;;',
     "awk_vars": '-v BC="$BC" -v CC="$CC" -v TT="$TT"',
     "vars_init": 'BC=""\nCC=""\nTT=""', "validate": '[ -z "$BC" ] || [ -z "$CC" ] || [ -z "$TT" ]'},

    {"num": 222, "slug": "lip_balm_texture", "name": "Lip Balm Texture Formulation",
     "desc": "Full factorial of beeswax ratio, shea butter ratio, oil type, and flavor load to maximize moisturizing feel and firmness",
     "design": "full_factorial", "category": "cosmetics",
     "factors": [
         {"name": "beeswax_pct", "levels": ["15", "30"], "type": "continuous", "unit": "%", "description": "Beeswax percentage"},
         {"name": "shea_pct", "levels": ["10", "30"], "type": "continuous", "unit": "%", "description": "Shea butter percentage"},
         {"name": "oil_type", "levels": ["coconut", "jojoba"], "type": "categorical", "unit": "", "description": "Carrier oil type"},
         {"name": "flavor_pct", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "%", "description": "Flavor oil percentage"},
     ],
     "fixed": {"vitamin_e": "1pct", "container": "tube"},
     "responses": [
         {"name": "moisture_score", "optimize": "maximize", "unit": "pts", "description": "Moisturizing feel score (1-10)"},
         {"name": "firmness_score", "optimize": "maximize", "unit": "pts", "description": "Product firmness and hold (1-10)"},
     ],
     "model": """
    bw = (BW - 22.5) / 7.5; sh = (SH - 20) / 10; ot = (OT == "jojoba") ? 1 : -1; fl = (FL - 1.75) / 1.25;
    moist = 6.0 - 0.5*bw + 1.0*sh + 0.3*ot + 0.2*fl + 0.2*bw*sh + 0.1*sh*ot;
    firm = 5.5 + 1.5*bw - 0.5*sh + 0.2*ot - 0.1*fl - 0.3*bw*bw + 0.1*bw*sh;
    if (moist < 1) moist = 1; if (moist > 10) moist = 10;
    if (firm < 1) firm = 1; if (firm > 10) firm = 10;
    printf "{\\"moisture_score\\": %.1f, \\"firmness_score\\": %.1f}", moist + n1*0.3, firm + n2*0.3;
""",
     "factor_cases": '--beeswax_pct) BW="$2"; shift 2 ;;\n        --shea_pct) SH="$2"; shift 2 ;;\n        --oil_type) OT="$2"; shift 2 ;;\n        --flavor_pct) FL="$2"; shift 2 ;;',
     "awk_vars": '-v BW="$BW" -v SH="$SH" -v OT="$OT" -v FL="$FL"',
     "vars_init": 'BW=""\nSH=""\nOT=""\nFL=""', "validate": '[ -z "$BW" ] || [ -z "$SH" ] || [ -z "$OT" ] || [ -z "$FL" ]'},

    {"num": 223, "slug": "hair_conditioner", "name": "Hair Conditioner Formulation",
     "desc": "Box-Behnken design to maximize detangling and shine by tuning cetyl alcohol, silicone dimethicone, and protein content",
     "design": "box_behnken", "category": "cosmetics",
     "factors": [
         {"name": "cetyl_pct", "levels": ["2", "6"], "type": "continuous", "unit": "%", "description": "Cetyl alcohol concentration"},
         {"name": "dimethicone_pct", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "%", "description": "Dimethicone silicone concentration"},
         {"name": "protein_pct", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "%", "description": "Hydrolyzed protein concentration"},
     ],
     "fixed": {"base_ph": "4.5", "preservative": "standard"},
     "responses": [
         {"name": "detangle_score", "optimize": "maximize", "unit": "pts", "description": "Wet detangling ease (1-10)"},
         {"name": "shine_score", "optimize": "maximize", "unit": "pts", "description": "Post-dry shine and smoothness (1-10)"},
     ],
     "model": """
    ca = (CA - 4) / 2; dm = (DM - 1.75) / 1.25; pr = (PR - 1.25) / 0.75;
    detangle = 6.0 + 0.8*ca + 1.0*dm + 0.3*pr - 0.3*ca*ca - 0.4*dm*dm + 0.2*ca*dm;
    shine = 6.5 + 0.3*ca + 1.2*dm + 0.5*pr - 0.2*ca*ca - 0.5*dm*dm - 0.2*pr*pr + 0.2*dm*pr;
    if (detangle < 1) detangle = 1; if (detangle > 10) detangle = 10;
    if (shine < 1) shine = 1; if (shine > 10) shine = 10;
    printf "{\\"detangle_score\\": %.1f, \\"shine_score\\": %.1f}", detangle + n1*0.3, shine + n2*0.3;
""",
     "factor_cases": '--cetyl_pct) CA="$2"; shift 2 ;;\n        --dimethicone_pct) DM="$2"; shift 2 ;;\n        --protein_pct) PR="$2"; shift 2 ;;',
     "awk_vars": '-v CA="$CA" -v DM="$DM" -v PR="$PR"',
     "vars_init": 'CA=""\nDM=""\nPR=""', "validate": '[ -z "$CA" ] || [ -z "$DM" ] || [ -z "$PR" ]'},

    {"num": 224, "slug": "perfume_longevity", "name": "Perfume Longevity & Sillage",
     "desc": "Central composite design to maximize scent longevity and sillage by tuning alcohol concentration, fixative percentage, and application amount",
     "design": "central_composite", "category": "cosmetics",
     "factors": [
         {"name": "alcohol_pct", "levels": ["60", "85"], "type": "continuous", "unit": "%", "description": "Ethanol concentration"},
         {"name": "fixative_pct", "levels": ["1", "5"], "type": "continuous", "unit": "%", "description": "Fixative ingredient percentage"},
         {"name": "sprays", "levels": ["2", "8"], "type": "continuous", "unit": "sprays", "description": "Number of spray applications"},
     ],
     "fixed": {"fragrance_type": "eau_de_parfum", "notes": "oriental"},
     "responses": [
         {"name": "longevity_hrs", "optimize": "maximize", "unit": "hrs", "description": "Scent detectable duration in hours"},
         {"name": "sillage_score", "optimize": "maximize", "unit": "pts", "description": "Scent projection score (1-10)"},
     ],
     "model": """
    al = (AL - 72.5) / 12.5; fx = (FX - 3) / 2; sp = (SP - 5) / 3;
    long = 6 - 1*al + 2*fx + 1.5*sp + 0.3*al*al - 0.5*fx*fx + 0.3*fx*sp;
    sil = 5.5 - 0.5*al + 0.8*fx + 1.2*sp - 0.3*al*al - 0.3*fx*fx - 0.4*sp*sp + 0.2*fx*sp;
    if (long < 1) long = 1; if (sil < 1) sil = 1; if (sil > 10) sil = 10;
    printf "{\\"longevity_hrs\\": %.1f, \\"sillage_score\\": %.1f}", long + n1*0.5, sil + n2*0.3;
""",
     "factor_cases": '--alcohol_pct) AL="$2"; shift 2 ;;\n        --fixative_pct) FX="$2"; shift 2 ;;\n        --sprays) SP="$2"; shift 2 ;;',
     "awk_vars": '-v AL="$AL" -v FX="$FX" -v SP="$SP"',
     "vars_init": 'AL=""\nFX=""\nSP=""', "validate": '[ -z "$AL" ] || [ -z "$FX" ] || [ -z "$SP" ]'},

    {"num": 225, "slug": "toothpaste_formulation", "name": "Toothpaste Cleaning Power",
     "desc": "Box-Behnken design to maximize cleaning efficacy and minimize abrasion by tuning silica abrasive content, fluoride concentration, and foam agent level",
     "design": "box_behnken", "category": "cosmetics",
     "factors": [
         {"name": "silica_pct", "levels": ["10", "25"], "type": "continuous", "unit": "%", "description": "Hydrated silica abrasive percentage"},
         {"name": "fluoride_ppm", "levels": ["500", "1500"], "type": "continuous", "unit": "ppm", "description": "Fluoride ion concentration"},
         {"name": "sls_pct", "levels": ["0.5", "2.5"], "type": "continuous", "unit": "%", "description": "Sodium lauryl sulfate foaming agent"},
     ],
     "fixed": {"flavor": "mint", "ph": "7.0"},
     "responses": [
         {"name": "cleaning_score", "optimize": "maximize", "unit": "pts", "description": "Stain removal efficacy (1-10)"},
         {"name": "rda_index", "optimize": "minimize", "unit": "RDA", "description": "Relative dentin abrasivity index"},
     ],
     "model": """
    si = (SI - 17.5) / 7.5; fl = (FL - 1000) / 500; sl = (SL - 1.5) / 1;
    clean = 6.0 + 1.2*si + 0.5*fl + 0.8*sl - 0.3*si*si + 0.2*si*sl;
    rda = 80 + 30*si + 5*fl + 10*sl + 10*si*si + 3*si*sl;
    if (clean < 1) clean = 1; if (clean > 10) clean = 10;
    if (rda < 30) rda = 30; if (rda > 200) rda = 200;
    printf "{\\"cleaning_score\\": %.1f, \\"rda_index\\": %.0f}", clean + n1*0.3, rda + n2*5;
""",
     "factor_cases": '--silica_pct) SI="$2"; shift 2 ;;\n        --fluoride_ppm) FL="$2"; shift 2 ;;\n        --sls_pct) SL="$2"; shift 2 ;;',
     "awk_vars": '-v SI="$SI" -v FL="$FL" -v SL="$SL"',
     "vars_init": 'SI=""\nFL=""\nSL=""', "validate": '[ -z "$SI" ] || [ -z "$FL" ] || [ -z "$SL" ]'},

    {"num": 226, "slug": "deodorant_efficacy", "name": "Natural Deodorant Efficacy",
     "desc": "Fractional factorial screening of baking soda, arrowroot powder, coconut oil, essential oil blend, and beeswax for odor control and skin sensitivity",
     "design": "fractional_factorial", "category": "cosmetics",
     "factors": [
         {"name": "baking_soda_pct", "levels": ["5", "25"], "type": "continuous", "unit": "%", "description": "Baking soda percentage"},
         {"name": "arrowroot_pct", "levels": ["10", "30"], "type": "continuous", "unit": "%", "description": "Arrowroot powder percentage"},
         {"name": "coconut_oil_pct", "levels": ["20", "50"], "type": "continuous", "unit": "%", "description": "Coconut oil percentage"},
         {"name": "eo_drops", "levels": ["5", "20"], "type": "continuous", "unit": "drops/oz", "description": "Essential oil drops per ounce"},
         {"name": "beeswax_pct", "levels": ["2", "10"], "type": "continuous", "unit": "%", "description": "Beeswax for firmness"},
     ],
     "fixed": {"container": "twist_up", "batch_size": "4oz"},
     "responses": [
         {"name": "odor_control_hrs", "optimize": "maximize", "unit": "hrs", "description": "Hours of effective odor control"},
         {"name": "sensitivity_score", "optimize": "minimize", "unit": "pts", "description": "Skin sensitivity/irritation (1-10)"},
     ],
     "model": """
    bs = (BS - 15) / 10; ar = (AR - 20) / 10; co = (CO - 35) / 15; eo = (EO - 12.5) / 7.5; bw = (BW - 6) / 4;
    odor = 6 + 3*bs + 1*ar + 0.5*co + 1.5*eo + 0.3*bw + 0.5*bs*eo;
    sens = 3 + 2*bs - 0.5*ar + 0.3*co + 0.8*eo + 0.2*bw + 0.5*bs*bs + 0.3*bs*eo;
    if (odor < 2) odor = 2; if (sens < 1) sens = 1; if (sens > 10) sens = 10;
    printf "{\\"odor_control_hrs\\": %.0f, \\"sensitivity_score\\": %.1f}", odor + n1*0.5, sens + n2*0.3;
""",
     "factor_cases": '--baking_soda_pct) BS="$2"; shift 2 ;;\n        --arrowroot_pct) AR="$2"; shift 2 ;;\n        --coconut_oil_pct) CO="$2"; shift 2 ;;\n        --eo_drops) EO="$2"; shift 2 ;;\n        --beeswax_pct) BW="$2"; shift 2 ;;',
     "awk_vars": '-v BS="$BS" -v AR="$AR" -v CO="$CO" -v EO="$EO" -v BW="$BW"',
     "vars_init": 'BS=""\nAR=""\nCO=""\nEO=""\nBW=""', "validate": '[ -z "$BS" ] || [ -z "$AR" ] || [ -z "$CO" ] || [ -z "$EO" ]'},

    {"num": 227, "slug": "face_mask_hydration", "name": "Face Mask Hydration Treatment",
     "desc": "Box-Behnken design to maximize skin hydration and minimize irritation by tuning sheet mask time, serum concentration, and active ingredient pH",
     "design": "box_behnken", "category": "cosmetics",
     "factors": [
         {"name": "mask_time_min", "levels": ["10", "30"], "type": "continuous", "unit": "min", "description": "Sheet mask wear time"},
         {"name": "serum_pct", "levels": ["1", "10"], "type": "continuous", "unit": "%", "description": "Active serum concentration"},
         {"name": "serum_ph", "levels": ["3.5", "6.0"], "type": "continuous", "unit": "pH", "description": "Serum pH level"},
     ],
     "fixed": {"mask_material": "biocellulose", "active": "niacinamide"},
     "responses": [
         {"name": "hydration_gain", "optimize": "maximize", "unit": "pts", "description": "Skin hydration increase at 2hr (1-10)"},
         {"name": "irritation", "optimize": "minimize", "unit": "pts", "description": "Skin irritation score (1-10)"},
     ],
     "model": """
    mt = (MT - 20) / 10; sc = (SC - 5.5) / 4.5; sp = (SP - 4.75) / 1.25;
    hyd = 6.0 + 0.8*mt + 1.0*sc - 0.3*sp - 0.4*mt*mt - 0.3*sc*sc + 0.2*mt*sc;
    irr = 2.5 + 0.3*mt + 0.5*sc - 0.8*sp + 0.2*mt*mt + 0.3*sc*sc + 0.2*sc*sp;
    if (hyd < 1) hyd = 1; if (hyd > 10) hyd = 10;
    if (irr < 1) irr = 1; if (irr > 10) irr = 10;
    printf "{\\"hydration_gain\\": %.1f, \\"irritation\\": %.1f}", hyd + n1*0.3, irr + n2*0.3;
""",
     "factor_cases": '--mask_time_min) MT="$2"; shift 2 ;;\n        --serum_pct) SC="$2"; shift 2 ;;\n        --serum_ph) SP="$2"; shift 2 ;;',
     "awk_vars": '-v MT="$MT" -v SC="$SC" -v SP="$SP"',
     "vars_init": 'MT=""\nSC=""\nSP=""', "validate": '[ -z "$MT" ] || [ -z "$SC" ] || [ -z "$SP" ]'},

    {"num": 228, "slug": "body_wash_mildness", "name": "Body Wash Mildness Optimization",
     "desc": "Central composite design to maximize cleansing while minimizing skin barrier disruption by tuning surfactant blend ratio, moisturizer add-back, and pH",
     "design": "central_composite", "category": "cosmetics",
     "factors": [
         {"name": "mild_surfactant_pct", "levels": ["5", "15"], "type": "continuous", "unit": "%", "description": "Mild co-surfactant concentration"},
         {"name": "moisturizer_pct", "levels": ["1", "5"], "type": "continuous", "unit": "%", "description": "Moisturizer add-back percentage"},
         {"name": "product_ph", "levels": ["4.5", "6.0"], "type": "continuous", "unit": "pH", "description": "Product pH"},
     ],
     "fixed": {"primary_surfactant": "cocamidopropyl_betaine", "fragrance": "lavender"},
     "responses": [
         {"name": "cleansing_score", "optimize": "maximize", "unit": "pts", "description": "Cleansing efficacy score (1-10)"},
         {"name": "barrier_disruption", "optimize": "minimize", "unit": "pts", "description": "Skin barrier disruption score (1-10)"},
     ],
     "model": """
    ms = (MS - 10) / 5; mp = (MP - 3) / 2; ph = (PH - 5.25) / 0.75;
    clean = 6.0 + 1.0*ms - 0.3*mp - 0.2*ph - 0.3*ms*ms + 0.2*ms*mp;
    barr = 4.0 + 0.8*ms - 0.5*mp - 0.6*ph + 0.2*ms*ms + 0.1*ph*ph + 0.2*ms*ph;
    if (clean < 1) clean = 1; if (clean > 10) clean = 10;
    if (barr < 1) barr = 1; if (barr > 10) barr = 10;
    printf "{\\"cleansing_score\\": %.1f, \\"barrier_disruption\\": %.1f}", clean + n1*0.3, barr + n2*0.3;
""",
     "factor_cases": '--mild_surfactant_pct) MS="$2"; shift 2 ;;\n        --moisturizer_pct) MP="$2"; shift 2 ;;\n        --product_ph) PH="$2"; shift 2 ;;',
     "awk_vars": '-v MS="$MS" -v MP="$MP" -v PH="$PH"',
     "vars_init": 'MS=""\nMP=""\nPH=""', "validate": '[ -z "$MS" ] || [ -z "$MP" ] || [ -z "$PH" ]'},

    # ══════════════════════════════════════════════════
    # Geology & Earth Science (229-238)
    # ══════════════════════════════════════════════════
    {"num": 229, "slug": "soil_compaction", "name": "Soil Compaction Testing",
     "desc": "Box-Behnken design to maximize dry density and identify optimal moisture content by tuning water content, compaction energy, and layer count",
     "design": "box_behnken", "category": "geology",
     "factors": [
         {"name": "water_pct", "levels": ["8", "20"], "type": "continuous", "unit": "%", "description": "Gravimetric water content"},
         {"name": "blows_per_layer", "levels": ["15", "56"], "type": "continuous", "unit": "blows", "description": "Compaction blows per layer"},
         {"name": "layers", "levels": ["3", "5"], "type": "continuous", "unit": "layers", "description": "Number of compaction layers"},
     ],
     "fixed": {"hammer_kg": "2.5", "mold": "proctor"},
     "responses": [
         {"name": "dry_density_kg_m3", "optimize": "maximize", "unit": "kg/m3", "description": "Maximum dry density"},
         {"name": "cbr_pct", "optimize": "maximize", "unit": "%", "description": "California bearing ratio"},
     ],
     "model": """
    wp = (WP - 14) / 6; bl = (BL - 35.5) / 20.5; ly = (LY - 4) / 1;
    dens = 1800 + 50*wp + 30*bl + 20*ly - 60*wp*wp - 10*bl*bl + 5*wp*bl;
    cbr = 15 - 3*wp + 5*bl + 3*ly + 4*wp*wp - 1*bl*bl + 1*wp*bl;
    if (dens < 1400) dens = 1400; if (cbr < 2) cbr = 2;
    printf "{\\"dry_density_kg_m3\\": %.0f, \\"cbr_pct\\": %.0f}", dens + n1*15, cbr + n2*1;
""",
     "factor_cases": '--water_pct) WP="$2"; shift 2 ;;\n        --blows_per_layer) BL="$2"; shift 2 ;;\n        --layers) LY="$2"; shift 2 ;;',
     "awk_vars": '-v WP="$WP" -v BL="$BL" -v LY="$LY"',
     "vars_init": 'WP=""\nBL=""\nLY=""', "validate": '[ -z "$WP" ] || [ -z "$BL" ] || [ -z "$LY" ]'},

    {"num": 230, "slug": "well_drilling", "name": "Water Well Drilling Parameters",
     "desc": "Central composite design to maximize flow rate and minimize turbidity by tuning drill depth, screen slot size, and gravel pack grade",
     "design": "central_composite", "category": "geology",
     "factors": [
         {"name": "depth_m", "levels": ["15", "60"], "type": "continuous", "unit": "m", "description": "Well depth"},
         {"name": "screen_slot_mm", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "mm", "description": "Well screen slot opening size"},
         {"name": "gravel_mm", "levels": ["2", "8"], "type": "continuous", "unit": "mm", "description": "Gravel pack grain size"},
     ],
     "fixed": {"aquifer": "alluvial_sand", "casing_diam": "150mm"},
     "responses": [
         {"name": "flow_rate_lpm", "optimize": "maximize", "unit": "L/min", "description": "Sustainable pumping rate"},
         {"name": "turbidity_ntu", "optimize": "minimize", "unit": "NTU", "description": "Water turbidity"},
     ],
     "model": """
    dp = (DP - 37.5) / 22.5; ss = (SS - 1.25) / 0.75; gp = (GP - 5) / 3;
    flow = 40 + 15*dp + 10*ss + 5*gp - 3*dp*dp - 4*ss*ss + 2*dp*ss;
    turb = 5 - 1*dp + 3*ss + 2*gp + 1*ss*ss + 0.5*gp*gp + 1*ss*gp;
    if (flow < 5) flow = 5; if (turb < 0.5) turb = 0.5;
    printf "{\\"flow_rate_lpm\\": %.0f, \\"turbidity_ntu\\": %.1f}", flow + n1*3, turb + n2*0.5;
""",
     "factor_cases": '--depth_m) DP="$2"; shift 2 ;;\n        --screen_slot_mm) SS="$2"; shift 2 ;;\n        --gravel_mm) GP="$2"; shift 2 ;;',
     "awk_vars": '-v DP="$DP" -v SS="$SS" -v GP="$GP"',
     "vars_init": 'DP=""\nSS=""\nGP=""', "validate": '[ -z "$DP" ] || [ -z "$SS" ] || [ -z "$GP" ]'},

    {"num": 231, "slug": "rock_thin_section", "name": "Rock Thin Section Preparation",
     "desc": "Box-Behnken design to maximize optical clarity and minimize thickness variation by tuning grinding speed, epoxy cure time, and final polish grit",
     "design": "box_behnken", "category": "geology",
     "factors": [
         {"name": "grind_rpm", "levels": ["100", "400"], "type": "continuous", "unit": "rpm", "description": "Grinding wheel speed"},
         {"name": "cure_hrs", "levels": ["12", "48"], "type": "continuous", "unit": "hrs", "description": "Epoxy cure time before grinding"},
         {"name": "polish_grit", "levels": ["600", "1200"], "type": "continuous", "unit": "grit", "description": "Final polishing grit"},
     ],
     "fixed": {"rock_type": "granite", "target_um": "30"},
     "responses": [
         {"name": "optical_clarity", "optimize": "maximize", "unit": "pts", "description": "Polarized light clarity score (1-10)"},
         {"name": "thickness_variation_um", "optimize": "minimize", "unit": "um", "description": "Thickness variation across section"},
     ],
     "model": """
    gr = (GR - 250) / 150; ch = (CH - 30) / 18; pg = (PG - 900) / 300;
    clar = 6.5 - 0.5*gr + 0.5*ch + 0.8*pg - 0.3*gr*gr - 0.2*ch*ch - 0.3*pg*pg + 0.2*ch*pg;
    var_ = 5 + 1.5*gr - 0.5*ch - 0.8*pg + 0.5*gr*gr + 0.2*ch*ch;
    if (clar < 1) clar = 1; if (clar > 10) clar = 10; if (var_ < 1) var_ = 1;
    printf "{\\"optical_clarity\\": %.1f, \\"thickness_variation_um\\": %.1f}", clar + n1*0.3, var_ + n2*0.5;
""",
     "factor_cases": '--grind_rpm) GR="$2"; shift 2 ;;\n        --cure_hrs) CH="$2"; shift 2 ;;\n        --polish_grit) PG="$2"; shift 2 ;;',
     "awk_vars": '-v GR="$GR" -v CH="$CH" -v PG="$PG"',
     "vars_init": 'GR=""\nCH=""\nPG=""', "validate": '[ -z "$GR" ] || [ -z "$CH" ] || [ -z "$PG" ]'},

    {"num": 232, "slug": "seismograph_placement", "name": "Seismograph Network Placement",
     "desc": "Full factorial of station spacing, depth of burial, sampling rate, and filter bandwidth to maximize event detection and minimize false triggers",
     "design": "full_factorial", "category": "geology",
     "factors": [
         {"name": "spacing_km", "levels": ["5", "25"], "type": "continuous", "unit": "km", "description": "Station spacing"},
         {"name": "burial_m", "levels": ["0", "3"], "type": "continuous", "unit": "m", "description": "Sensor burial depth"},
         {"name": "sample_hz", "levels": ["40", "200"], "type": "continuous", "unit": "Hz", "description": "Sampling rate"},
         {"name": "filter_hz", "levels": ["0.5", "10"], "type": "continuous", "unit": "Hz", "description": "Highpass filter cutoff"},
     ],
     "fixed": {"sensor": "broadband", "network_size": "8_stations"},
     "responses": [
         {"name": "detection_pct", "optimize": "maximize", "unit": "%", "description": "Earthquake event detection percentage"},
         {"name": "false_trigger_day", "optimize": "minimize", "unit": "per_day", "description": "False trigger rate per day"},
     ],
     "model": """
    sp = (SP - 15) / 10; br = (BR - 1.5) / 1.5; sr = (SR - 120) / 80; fh = (FH - 5.25) / 4.75;
    det = 80 - 8*sp + 5*br + 3*sr - 2*fh + 2*sp*sp + 1*br*sr;
    false_ = 5 - 1*sp - 2*br + 1*sr - 3*fh + 0.5*sp*sp + 1*sr*sr + 0.5*sr*fh;
    if (det < 40) det = 40; if (det > 100) det = 100; if (false_ < 0) false_ = 0;
    printf "{\\"detection_pct\\": %.0f, \\"false_trigger_day\\": %.1f}", det + n1*2, false_ + n2*0.3;
""",
     "factor_cases": '--spacing_km) SP="$2"; shift 2 ;;\n        --burial_m) BR="$2"; shift 2 ;;\n        --sample_hz) SR="$2"; shift 2 ;;\n        --filter_hz) FH="$2"; shift 2 ;;',
     "awk_vars": '-v SP="$SP" -v BR="$BR" -v SR="$SR" -v FH="$FH"',
     "vars_init": 'SP=""\nBR=""\nSR=""\nFH=""', "validate": '[ -z "$SP" ] || [ -z "$BR" ] || [ -z "$SR" ] || [ -z "$FH" ]'},

    {"num": 233, "slug": "erosion_control", "name": "Hillside Erosion Control",
     "desc": "Box-Behnken design to minimize soil loss and maximize vegetation establishment by tuning mulch depth, seed mix density, and terracing interval",
     "design": "box_behnken", "category": "geology",
     "factors": [
         {"name": "mulch_cm", "levels": ["2", "10"], "type": "continuous", "unit": "cm", "description": "Mulch layer depth"},
         {"name": "seed_g_m2", "levels": ["10", "50"], "type": "continuous", "unit": "g/m2", "description": "Seed mix application rate"},
         {"name": "terrace_m", "levels": ["5", "20"], "type": "continuous", "unit": "m", "description": "Terrace spacing interval"},
     ],
     "fixed": {"slope_pct": "30", "soil_type": "silt_loam"},
     "responses": [
         {"name": "soil_loss_t_ha", "optimize": "minimize", "unit": "t/ha/yr", "description": "Annual soil loss in tonnes per hectare"},
         {"name": "vegetation_pct", "optimize": "maximize", "unit": "%", "description": "Vegetation cover at 6 months"},
     ],
     "model": """
    mc = (MC - 6) / 4; sd = (SD - 30) / 20; tr = (TR - 12.5) / 7.5;
    loss = 12 - 4*mc - 2*sd - 3*tr + 1.5*mc*mc + 0.5*sd*sd + 1*tr*tr + 0.5*mc*tr;
    veg = 55 + 10*mc + 15*sd - 5*tr - 3*mc*mc - 4*sd*sd + 2*mc*sd;
    if (loss < 0.5) loss = 0.5; if (veg < 10) veg = 10; if (veg > 95) veg = 95;
    printf "{\\"soil_loss_t_ha\\": %.1f, \\"vegetation_pct\\": %.0f}", loss + n1*0.5, veg + n2*3;
""",
     "factor_cases": '--mulch_cm) MC="$2"; shift 2 ;;\n        --seed_g_m2) SD="$2"; shift 2 ;;\n        --terrace_m) TR="$2"; shift 2 ;;',
     "awk_vars": '-v MC="$MC" -v SD="$SD" -v TR="$TR"',
     "vars_init": 'MC=""\nSD=""\nTR=""', "validate": '[ -z "$MC" ] || [ -z "$SD" ] || [ -z "$TR" ]'},

    {"num": 234, "slug": "mineral_flotation", "name": "Mineral Flotation Separation",
     "desc": "Central composite design to maximize mineral recovery and grade by tuning collector dosage, frother concentration, and pulp pH",
     "design": "central_composite", "category": "geology",
     "factors": [
         {"name": "collector_g_t", "levels": ["20", "80"], "type": "continuous", "unit": "g/t", "description": "Collector reagent dosage"},
         {"name": "frother_g_t", "levels": ["10", "40"], "type": "continuous", "unit": "g/t", "description": "Frother dosage"},
         {"name": "pulp_ph", "levels": ["7", "11"], "type": "continuous", "unit": "pH", "description": "Pulp slurry pH"},
     ],
     "fixed": {"mineral": "chalcopyrite", "grind_size": "75um"},
     "responses": [
         {"name": "recovery_pct", "optimize": "maximize", "unit": "%", "description": "Mineral recovery percentage"},
         {"name": "grade_pct", "optimize": "maximize", "unit": "%Cu", "description": "Concentrate copper grade"},
     ],
     "model": """
    cl = (CL - 50) / 30; fr = (FR - 25) / 15; ph = (PH - 9) / 2;
    rec = 75 + 8*cl + 4*fr + 3*ph - 5*cl*cl - 3*fr*fr - 2*ph*ph + 2*cl*fr;
    grade = 22 - 3*cl - 1*fr + 2*ph + 2*cl*cl + 1*fr*fr - 1*ph*ph + 1*cl*ph;
    if (rec < 30) rec = 30; if (rec > 98) rec = 98;
    if (grade < 8) grade = 8; if (grade > 35) grade = 35;
    printf "{\\"recovery_pct\\": %.0f, \\"grade_pct\\": %.1f}", rec + n1*2, grade + n2*1;
""",
     "factor_cases": '--collector_g_t) CL="$2"; shift 2 ;;\n        --frother_g_t) FR="$2"; shift 2 ;;\n        --pulp_ph) PH="$2"; shift 2 ;;',
     "awk_vars": '-v CL="$CL" -v FR="$FR" -v PH="$PH"',
     "vars_init": 'CL=""\nFR=""\nPH=""', "validate": '[ -z "$CL" ] || [ -z "$FR" ] || [ -z "$PH" ]'},

    {"num": 235, "slug": "groundwater_sampling", "name": "Groundwater Sampling Protocol",
     "desc": "Box-Behnken design to maximize sample representativeness and minimize turbidity by tuning purge volume, pump rate, and well development time",
     "design": "box_behnken", "category": "geology",
     "factors": [
         {"name": "purge_volumes", "levels": ["1", "5"], "type": "continuous", "unit": "well_vols", "description": "Number of well volumes purged"},
         {"name": "pump_rate_lpm", "levels": ["0.5", "5.0"], "type": "continuous", "unit": "L/min", "description": "Pumping rate during sampling"},
         {"name": "dev_hrs", "levels": ["1", "8"], "type": "continuous", "unit": "hrs", "description": "Prior well development time"},
     ],
     "fixed": {"well_type": "monitoring", "analytes": "metals"},
     "responses": [
         {"name": "representativeness", "optimize": "maximize", "unit": "pts", "description": "Sample representativeness score (1-10)"},
         {"name": "sample_turbidity", "optimize": "minimize", "unit": "NTU", "description": "Sample turbidity"},
     ],
     "model": """
    pv = (PV - 3) / 2; pr = (PR - 2.75) / 2.25; dh = (DH - 4.5) / 3.5;
    rep = 6.5 + 1.0*pv - 0.5*pr + 0.5*dh - 0.4*pv*pv + 0.2*pr*pr + 0.2*pv*dh;
    turb = 8 - 2*pv + 2*pr - 1.5*dh + 0.5*pv*pv + 0.3*pr*pr + 0.3*pr*dh;
    if (rep < 1) rep = 1; if (rep > 10) rep = 10; if (turb < 0.5) turb = 0.5;
    printf "{\\"representativeness\\": %.1f, \\"sample_turbidity\\": %.1f}", rep + n1*0.3, turb + n2*0.5;
""",
     "factor_cases": '--purge_volumes) PV="$2"; shift 2 ;;\n        --pump_rate_lpm) PR="$2"; shift 2 ;;\n        --dev_hrs) DH="$2"; shift 2 ;;',
     "awk_vars": '-v PV="$PV" -v PR="$PR" -v DH="$DH"',
     "vars_init": 'PV=""\nPR=""\nDH=""', "validate": '[ -z "$PV" ] || [ -z "$PR" ] || [ -z "$DH" ]'},

    {"num": 236, "slug": "concrete_aggregate", "name": "Aggregate Gradation Optimization",
     "desc": "Plackett-Burman screening of coarse aggregate ratio, sand fineness modulus, max aggregate size, fines content, and angularity for workability and strength",
     "design": "plackett_burman", "category": "geology",
     "factors": [
         {"name": "coarse_pct", "levels": ["50", "75"], "type": "continuous", "unit": "%", "description": "Coarse aggregate percentage"},
         {"name": "fineness_mod", "levels": ["2.3", "3.1"], "type": "continuous", "unit": "FM", "description": "Sand fineness modulus"},
         {"name": "max_size_mm", "levels": ["10", "25"], "type": "continuous", "unit": "mm", "description": "Maximum nominal aggregate size"},
         {"name": "fines_pct", "levels": ["0", "5"], "type": "continuous", "unit": "%", "description": "Material passing 75um sieve"},
         {"name": "angularity", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "Coarse aggregate angularity (1=round, 5=crushed)"},
     ],
     "fixed": {"cement": "type_I", "target_slump": "100mm"},
     "responses": [
         {"name": "workability_score", "optimize": "maximize", "unit": "pts", "description": "Fresh concrete workability (1-10)"},
         {"name": "strength_28d_mpa", "optimize": "maximize", "unit": "MPa", "description": "28-day compressive strength"},
     ],
     "model": """
    ca = (CA - 62.5) / 12.5; fm = (FM - 2.7) / 0.4; ms = (MS - 17.5) / 7.5; fn = (FN - 2.5) / 2.5; an = (AN - 3) / 2;
    work = 6.0 - 0.5*ca + 0.3*fm + 0.5*ms + 0.2*fn - 0.8*an + 0.2*ca*fm;
    str_ = 30 + 2*ca + 1*fm - 1*ms - 1*fn + 2*an + 0.5*ca*an;
    if (work < 1) work = 1; if (work > 10) work = 10; if (str_ < 15) str_ = 15;
    printf "{\\"workability_score\\": %.1f, \\"strength_28d_mpa\\": %.0f}", work + n1*0.3, str_ + n2*1.5;
""",
     "factor_cases": '--coarse_pct) CA="$2"; shift 2 ;;\n        --fineness_mod) FM="$2"; shift 2 ;;\n        --max_size_mm) MS="$2"; shift 2 ;;\n        --fines_pct) FN="$2"; shift 2 ;;\n        --angularity) AN="$2"; shift 2 ;;',
     "awk_vars": '-v CA="$CA" -v FM="$FM" -v MS="$MS" -v FN="$FN" -v AN="$AN"',
     "vars_init": 'CA=""\nFM=""\nMS=""\nFN=""\nAN=""', "validate": '[ -z "$CA" ] || [ -z "$FM" ] || [ -z "$MS" ] || [ -z "$FN" ]'},

    {"num": 237, "slug": "fossil_preparation", "name": "Fossil Preparation Technique",
     "desc": "Box-Behnken design to maximize fossil detail preservation and minimize matrix damage by tuning air abrasive pressure, nozzle distance, and media grit",
     "design": "box_behnken", "category": "geology",
     "factors": [
         {"name": "pressure_psi", "levels": ["20", "80"], "type": "continuous", "unit": "psi", "description": "Air abrasive pressure"},
         {"name": "nozzle_mm", "levels": ["5", "30"], "type": "continuous", "unit": "mm", "description": "Nozzle-to-specimen distance"},
         {"name": "media_mesh", "levels": ["100", "400"], "type": "continuous", "unit": "mesh", "description": "Abrasive media grit size"},
     ],
     "fixed": {"media_type": "sodium_bicarbonate", "fossil": "trilobite"},
     "responses": [
         {"name": "detail_score", "optimize": "maximize", "unit": "pts", "description": "Fine detail preservation (1-10)"},
         {"name": "damage_score", "optimize": "minimize", "unit": "pts", "description": "Fossil surface damage risk (1-10)"},
     ],
     "model": """
    pr = (PR - 50) / 30; nd = (ND - 17.5) / 12.5; mg = (MG - 250) / 150;
    detail = 6.0 + 0.8*pr - 0.5*nd + 0.6*mg - 0.5*pr*pr - 0.2*nd*nd - 0.3*mg*mg + 0.2*pr*mg;
    dmg = 3.5 + 1.5*pr - 0.3*nd - 0.8*mg + 0.5*pr*pr + 0.2*nd*nd + 0.3*pr*nd;
    if (detail < 1) detail = 1; if (detail > 10) detail = 10;
    if (dmg < 1) dmg = 1; if (dmg > 10) dmg = 10;
    printf "{\\"detail_score\\": %.1f, \\"damage_score\\": %.1f}", detail + n1*0.3, dmg + n2*0.3;
""",
     "factor_cases": '--pressure_psi) PR="$2"; shift 2 ;;\n        --nozzle_mm) ND="$2"; shift 2 ;;\n        --media_mesh) MG="$2"; shift 2 ;;',
     "awk_vars": '-v PR="$PR" -v ND="$ND" -v MG="$MG"',
     "vars_init": 'PR=""\nND=""\nMG=""', "validate": '[ -z "$PR" ] || [ -z "$ND" ] || [ -z "$MG" ]'},

    {"num": 238, "slug": "geothermal_heat_loop", "name": "Geothermal Ground Loop Design",
     "desc": "Central composite design to maximize heat extraction and minimize installation cost by tuning loop depth, pipe diameter, and flow rate",
     "design": "central_composite", "category": "geology",
     "factors": [
         {"name": "loop_depth_m", "levels": ["30", "100"], "type": "continuous", "unit": "m", "description": "Vertical borehole depth"},
         {"name": "pipe_diam_mm", "levels": ["25", "40"], "type": "continuous", "unit": "mm", "description": "HDPE pipe inner diameter"},
         {"name": "flow_lpm", "levels": ["5", "15"], "type": "continuous", "unit": "L/min", "description": "Circulating fluid flow rate"},
     ],
     "fixed": {"soil_conductivity": "1.5_W_mK", "grout": "enhanced"},
     "responses": [
         {"name": "heat_kw", "optimize": "maximize", "unit": "kW", "description": "Heat extraction rate"},
         {"name": "install_cost", "optimize": "minimize", "unit": "USD", "description": "Installation cost"},
     ],
     "model": """
    ld = (LD - 65) / 35; pd = (PD - 32.5) / 7.5; fl = (FL - 10) / 5;
    heat = 6 + 3*ld + 1*pd + 1.5*fl - 0.8*ld*ld - 0.5*pd*pd - 0.5*fl*fl + 0.3*ld*fl;
    cost = 8000 + 3000*ld + 500*pd + 200*fl + 500*ld*ld;
    if (heat < 2) heat = 2; if (cost < 4000) cost = 4000;
    printf "{\\"heat_kw\\": %.1f, \\"install_cost\\": %.0f}", heat + n1*0.3, cost + n2*200;
""",
     "factor_cases": '--loop_depth_m) LD="$2"; shift 2 ;;\n        --pipe_diam_mm) PD="$2"; shift 2 ;;\n        --flow_lpm) FL="$2"; shift 2 ;;',
     "awk_vars": '-v LD="$LD" -v PD="$PD" -v FL="$FL"',
     "vars_init": 'LD=""\nPD=""\nFL=""', "validate": '[ -z "$LD" ] || [ -z "$PD" ] || [ -z "$FL" ]'},

    # ══════════════════════════════════════════════════
    # Brewing & Fermentation (239-248)
    # ══════════════════════════════════════════════════
    {"num": 239, "slug": "kombucha_brewing", "name": "Kombucha Brewing Balance",
     "desc": "Box-Behnken design to maximize fizz and flavor complexity while controlling acidity by tuning sugar amount, fermentation days, and tea strength",
     "design": "box_behnken", "category": "brewing",
     "factors": [
         {"name": "sugar_g_L", "levels": ["50", "100"], "type": "continuous", "unit": "g/L", "description": "Sugar concentration"},
         {"name": "ferm_days", "levels": ["5", "21"], "type": "continuous", "unit": "days", "description": "Primary fermentation duration"},
         {"name": "tea_g_L", "levels": ["5", "15"], "type": "continuous", "unit": "g/L", "description": "Tea leaf concentration"},
     ],
     "fixed": {"tea_type": "black", "scoby_age": "mature"},
     "responses": [
         {"name": "fizz_score", "optimize": "maximize", "unit": "pts", "description": "Carbonation and effervescence (1-10)"},
         {"name": "flavor_complexity", "optimize": "maximize", "unit": "pts", "description": "Flavor depth and balance (1-10)"},
     ],
     "model": """
    sg = (SG - 75) / 25; fd = (FD - 13) / 8; tg = (TG - 10) / 5;
    fizz = 6.0 + 0.8*sg + 1.2*fd + 0.3*tg - 0.3*sg*sg - 0.5*fd*fd + 0.2*sg*fd;
    flav = 6.5 + 0.3*sg + 0.8*fd + 0.6*tg - 0.2*sg*sg - 0.4*fd*fd - 0.2*tg*tg + 0.2*fd*tg;
    if (fizz < 1) fizz = 1; if (fizz > 10) fizz = 10;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    printf "{\\"fizz_score\\": %.1f, \\"flavor_complexity\\": %.1f}", fizz + n1*0.3, flav + n2*0.3;
""",
     "factor_cases": '--sugar_g_L) SG="$2"; shift 2 ;;\n        --ferm_days) FD="$2"; shift 2 ;;\n        --tea_g_L) TG="$2"; shift 2 ;;',
     "awk_vars": '-v SG="$SG" -v FD="$FD" -v TG="$TG"',
     "vars_init": 'SG=""\nFD=""\nTG=""', "validate": '[ -z "$SG" ] || [ -z "$FD" ] || [ -z "$TG" ]'},

    {"num": 240, "slug": "cider_making", "name": "Hard Cider Fermentation",
     "desc": "Central composite design to maximize flavor clarity and target ABV by tuning yeast pitch rate, fermentation temperature, and sugar addition",
     "design": "central_composite", "category": "brewing",
     "factors": [
         {"name": "pitch_rate_g_L", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "g/L", "description": "Yeast pitch rate"},
         {"name": "ferm_temp_c", "levels": ["12", "22"], "type": "continuous", "unit": "C", "description": "Fermentation temperature"},
         {"name": "sugar_add_g_L", "levels": ["0", "50"], "type": "continuous", "unit": "g/L", "description": "Supplemental sugar addition"},
     ],
     "fixed": {"apple_variety": "mixed_cider", "yeast": "champagne"},
     "responses": [
         {"name": "flavor_clarity", "optimize": "maximize", "unit": "pts", "description": "Flavor clarity and apple character (1-10)"},
         {"name": "abv_pct", "optimize": "maximize", "unit": "%", "description": "Alcohol by volume"},
     ],
     "model": """
    pr = (PR - 1.25) / 0.75; ft = (FT - 17) / 5; sa = (SA - 25) / 25;
    flav = 7.0 + 0.3*pr - 0.5*ft + 0.2*sa - 0.4*pr*pr + 0.3*ft*ft - 0.3*sa*sa + 0.2*pr*ft;
    abv = 5.5 + 0.3*pr + 0.2*ft + 1.5*sa - 0.1*pr*pr + 0.2*sa*sa + 0.1*pr*sa;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    if (abv < 3) abv = 3; if (abv > 10) abv = 10;
    printf "{\\"flavor_clarity\\": %.1f, \\"abv_pct\\": %.1f}", flav + n1*0.3, abv + n2*0.2;
""",
     "factor_cases": '--pitch_rate_g_L) PR="$2"; shift 2 ;;\n        --ferm_temp_c) FT="$2"; shift 2 ;;\n        --sugar_add_g_L) SA="$2"; shift 2 ;;',
     "awk_vars": '-v PR="$PR" -v FT="$FT" -v SA="$SA"',
     "vars_init": 'PR=""\nFT=""\nSA=""', "validate": '[ -z "$PR" ] || [ -z "$FT" ] || [ -z "$SA" ]'},

    {"num": 241, "slug": "mead_honey_wine", "name": "Mead (Honey Wine) Production",
     "desc": "Box-Behnken design to maximize honey character and minimize fermentation stalls by tuning honey-to-water ratio, nutrient additions, and pH adjustment",
     "design": "box_behnken", "category": "brewing",
     "factors": [
         {"name": "honey_ratio_kg_L", "levels": ["0.3", "0.5"], "type": "continuous", "unit": "kg/L", "description": "Honey per liter of water"},
         {"name": "nutrient_g_L", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "g/L", "description": "Yeast nutrient addition"},
         {"name": "ph_target", "levels": ["3.5", "4.5"], "type": "continuous", "unit": "pH", "description": "Must pH target"},
     ],
     "fixed": {"honey_type": "wildflower", "yeast": "d47"},
     "responses": [
         {"name": "honey_character", "optimize": "maximize", "unit": "pts", "description": "Honey aroma and flavor retention (1-10)"},
         {"name": "completion_days", "optimize": "minimize", "unit": "days", "description": "Days to fermentation completion"},
     ],
     "model": """
    hr = (HR - 0.4) / 0.1; ng = (NG - 1.75) / 1.25; ph = (PH - 4) / 0.5;
    honey = 6.5 + 0.8*hr - 0.3*ng + 0.3*ph - 0.5*hr*hr + 0.2*ng*ng + 0.2*hr*ph;
    days = 30 + 8*hr - 10*ng - 3*ph + 3*hr*hr + 2*ng*ng + 2*hr*ng;
    if (honey < 1) honey = 1; if (honey > 10) honey = 10; if (days < 10) days = 10;
    printf "{\\"honey_character\\": %.1f, \\"completion_days\\": %.0f}", honey + n1*0.3, days + n2*2;
""",
     "factor_cases": '--honey_ratio_kg_L) HR="$2"; shift 2 ;;\n        --nutrient_g_L) NG="$2"; shift 2 ;;\n        --ph_target) PH="$2"; shift 2 ;;',
     "awk_vars": '-v HR="$HR" -v NG="$NG" -v PH="$PH"',
     "vars_init": 'HR=""\nNG=""\nPH=""', "validate": '[ -z "$HR" ] || [ -z "$NG" ] || [ -z "$PH" ]'},

    {"num": 242, "slug": "sauerkraut_ferment", "name": "Sauerkraut Fermentation",
     "desc": "Full factorial of salt concentration, cabbage shred width, temperature, and pressing weight to maximize tang and crunch",
     "design": "full_factorial", "category": "brewing",
     "factors": [
         {"name": "salt_pct", "levels": ["2", "4"], "type": "continuous", "unit": "%", "description": "Salt as percentage of cabbage weight"},
         {"name": "shred_mm", "levels": ["2", "6"], "type": "continuous", "unit": "mm", "description": "Cabbage shred width"},
         {"name": "temp_c", "levels": ["15", "25"], "type": "continuous", "unit": "C", "description": "Fermentation temperature"},
         {"name": "weight_kg", "levels": ["1", "5"], "type": "continuous", "unit": "kg", "description": "Pressing weight on top"},
     ],
     "fixed": {"cabbage": "green", "vessel": "crock"},
     "responses": [
         {"name": "tang_score", "optimize": "maximize", "unit": "pts", "description": "Sour tang and flavor depth (1-10)"},
         {"name": "crunch_score", "optimize": "maximize", "unit": "pts", "description": "Crunch and texture retention (1-10)"},
     ],
     "model": """
    sp = (SP - 3) / 1; sw = (SW - 4) / 2; tp = (TP - 20) / 5; wt = (WT - 3) / 2;
    tang = 6.0 + 0.3*sp + 0.2*sw + 0.8*tp + 0.3*wt - 0.3*sp*sp - 0.2*tp*tp + 0.2*tp*wt;
    crunch = 6.5 + 0.5*sp + 0.8*sw - 0.5*tp - 0.2*wt - 0.2*sp*sp - 0.3*sw*sw + 0.2*sp*sw;
    if (tang < 1) tang = 1; if (tang > 10) tang = 10;
    if (crunch < 1) crunch = 1; if (crunch > 10) crunch = 10;
    printf "{\\"tang_score\\": %.1f, \\"crunch_score\\": %.1f}", tang + n1*0.3, crunch + n2*0.3;
""",
     "factor_cases": '--salt_pct) SP="$2"; shift 2 ;;\n        --shred_mm) SW="$2"; shift 2 ;;\n        --temp_c) TP="$2"; shift 2 ;;\n        --weight_kg) WT="$2"; shift 2 ;;',
     "awk_vars": '-v SP="$SP" -v SW="$SW" -v TP="$TP" -v WT="$WT"',
     "vars_init": 'SP=""\nSW=""\nTP=""\nWT=""', "validate": '[ -z "$SP" ] || [ -z "$SW" ] || [ -z "$TP" ] || [ -z "$WT" ]'},

    {"num": 243, "slug": "wine_malolactic", "name": "Wine Malolactic Fermentation",
     "desc": "Box-Behnken design to maximize MLF completion and minimize VA by tuning inoculation rate, cellar temperature, and free SO2 level",
     "design": "box_behnken", "category": "brewing",
     "factors": [
         {"name": "inoc_rate", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "g/hL", "description": "Bacteria inoculation rate"},
         {"name": "cellar_temp_c", "levels": ["15", "22"], "type": "continuous", "unit": "C", "description": "Cellar temperature"},
         {"name": "free_so2_ppm", "levels": ["5", "25"], "type": "continuous", "unit": "ppm", "description": "Free SO2 at inoculation"},
     ],
     "fixed": {"wine_type": "chardonnay", "ph": "3.4"},
     "responses": [
         {"name": "mlf_completion_pct", "optimize": "maximize", "unit": "%", "description": "MLF completion percentage"},
         {"name": "va_g_L", "optimize": "minimize", "unit": "g/L", "description": "Volatile acidity in g/L acetic acid"},
     ],
     "model": """
    ir = (IR - 1.25) / 0.75; ct = (CT - 18.5) / 3.5; so = (SO - 15) / 10;
    mlf = 80 + 8*ir + 5*ct - 10*so - 3*ir*ir - 2*ct*ct + 2*so*so + 2*ir*ct;
    va = 0.3 + 0.05*ir + 0.08*ct + 0.03*so + 0.02*ir*ir + 0.03*ct*ct - 0.01*so*so + 0.02*ir*ct;
    if (mlf < 20) mlf = 20; if (mlf > 100) mlf = 100;
    if (va < 0.1) va = 0.1; if (va > 1.0) va = 1.0;
    printf "{\\"mlf_completion_pct\\": %.0f, \\"va_g_L\\": %.2f}", mlf + n1*3, va + n2*0.02;
""",
     "factor_cases": '--inoc_rate) IR="$2"; shift 2 ;;\n        --cellar_temp_c) CT="$2"; shift 2 ;;\n        --free_so2_ppm) SO="$2"; shift 2 ;;',
     "awk_vars": '-v IR="$IR" -v CT="$CT" -v SO="$SO"',
     "vars_init": 'IR=""\nCT=""\nSO=""', "validate": '[ -z "$IR" ] || [ -z "$CT" ] || [ -z "$SO" ]'},

    {"num": 244, "slug": "kimchi_ferment", "name": "Kimchi Fermentation Timing",
     "desc": "Central composite design to optimize tang level and texture by tuning salt brine strength, fermentation temperature, and gochugaru amount",
     "design": "central_composite", "category": "brewing",
     "factors": [
         {"name": "brine_pct", "levels": ["3", "8"], "type": "continuous", "unit": "%", "description": "Salt brine concentration"},
         {"name": "ferm_temp_c", "levels": ["2", "22"], "type": "continuous", "unit": "C", "description": "Fermentation storage temperature"},
         {"name": "gochugaru_pct", "levels": ["3", "10"], "type": "continuous", "unit": "%", "description": "Red pepper flake percentage of cabbage weight"},
     ],
     "fixed": {"cabbage_type": "napa", "garlic_pct": "3"},
     "responses": [
         {"name": "tang_level", "optimize": "maximize", "unit": "pts", "description": "Fermented tang and umami depth (1-10)"},
         {"name": "texture_score", "optimize": "maximize", "unit": "pts", "description": "Crunch and texture preservation (1-10)"},
     ],
     "model": """
    bp = (BP - 5.5) / 2.5; ft = (FT - 12) / 10; gp = (GP - 6.5) / 3.5;
    tang = 6.0 + 0.3*bp + 1.2*ft + 0.5*gp - 0.2*bp*bp - 0.5*ft*ft + 0.2*bp*ft;
    tex = 7.0 + 0.5*bp - 0.8*ft + 0.2*gp - 0.2*bp*bp + 0.3*ft*ft - 0.1*gp*gp + 0.2*bp*ft;
    if (tang < 1) tang = 1; if (tang > 10) tang = 10;
    if (tex < 1) tex = 1; if (tex > 10) tex = 10;
    printf "{\\"tang_level\\": %.1f, \\"texture_score\\": %.1f}", tang + n1*0.3, tex + n2*0.3;
""",
     "factor_cases": '--brine_pct) BP="$2"; shift 2 ;;\n        --ferm_temp_c) FT="$2"; shift 2 ;;\n        --gochugaru_pct) GP="$2"; shift 2 ;;',
     "awk_vars": '-v BP="$BP" -v FT="$FT" -v GP="$GP"',
     "vars_init": 'BP=""\nFT=""\nGP=""', "validate": '[ -z "$BP" ] || [ -z "$FT" ] || [ -z "$GP" ]'},

    {"num": 245, "slug": "vinegar_mother", "name": "Vinegar Mother Cultivation",
     "desc": "Box-Behnken design to maximize acetic acid production and minimize off-flavors by tuning starting ABV, surface area, and temperature",
     "design": "box_behnken", "category": "brewing",
     "factors": [
         {"name": "start_abv_pct", "levels": ["5", "12"], "type": "continuous", "unit": "%", "description": "Starting alcohol percentage"},
         {"name": "surface_area_cm2", "levels": ["100", "500"], "type": "continuous", "unit": "cm2", "description": "Liquid surface area exposed to air"},
         {"name": "temp_c", "levels": ["20", "32"], "type": "continuous", "unit": "C", "description": "Fermentation temperature"},
     ],
     "fixed": {"mother_source": "existing_culture", "vessel": "ceramic_crock"},
     "responses": [
         {"name": "acidity_pct", "optimize": "maximize", "unit": "%", "description": "Final acetic acid percentage"},
         {"name": "off_flavor_score", "optimize": "minimize", "unit": "pts", "description": "Off-flavor intensity (1-10)"},
     ],
     "model": """
    ab = (AB - 8.5) / 3.5; sa = (SA - 300) / 200; tp = (TP - 26) / 6;
    acid = 5.0 + 1.5*ab + 0.5*sa + 0.8*tp - 0.5*ab*ab - 0.2*sa*sa - 0.4*tp*tp + 0.2*ab*tp;
    off = 3.0 + 0.5*ab + 0.2*sa + 0.8*tp + 0.3*ab*ab + 0.2*tp*tp + 0.2*ab*tp;
    if (acid < 2) acid = 2; if (off < 1) off = 1; if (off > 10) off = 10;
    printf "{\\"acidity_pct\\": %.1f, \\"off_flavor_score\\": %.1f}", acid + n1*0.2, off + n2*0.3;
""",
     "factor_cases": '--start_abv_pct) AB="$2"; shift 2 ;;\n        --surface_area_cm2) SA="$2"; shift 2 ;;\n        --temp_c) TP="$2"; shift 2 ;;',
     "awk_vars": '-v AB="$AB" -v SA="$SA" -v TP="$TP"',
     "vars_init": 'AB=""\nSA=""\nTP=""', "validate": '[ -z "$AB" ] || [ -z "$SA" ] || [ -z "$TP" ]'},

    {"num": 246, "slug": "kefir_grains", "name": "Kefir Grain Cultivation",
     "desc": "Fractional factorial screening of milk fat content, fermentation time, grain-to-milk ratio, temperature, and agitation for probiotic count and taste",
     "design": "fractional_factorial", "category": "brewing",
     "factors": [
         {"name": "fat_pct", "levels": ["0.5", "4.0"], "type": "continuous", "unit": "%", "description": "Milk fat content"},
         {"name": "ferm_hrs", "levels": ["12", "48"], "type": "continuous", "unit": "hrs", "description": "Fermentation time"},
         {"name": "grain_ratio_pct", "levels": ["3", "15"], "type": "continuous", "unit": "%", "description": "Grain-to-milk ratio by weight"},
         {"name": "temp_c", "levels": ["18", "28"], "type": "continuous", "unit": "C", "description": "Fermentation temperature"},
         {"name": "agitation", "levels": ["0", "3"], "type": "continuous", "unit": "per_day", "description": "Gentle agitation frequency per day"},
     ],
     "fixed": {"milk_type": "whole_cow", "vessel": "glass_jar"},
     "responses": [
         {"name": "probiotic_score", "optimize": "maximize", "unit": "pts", "description": "Probiotic diversity and count (1-10)"},
         {"name": "taste_score", "optimize": "maximize", "unit": "pts", "description": "Taste and drinkability (1-10)"},
     ],
     "model": """
    fp = (FP - 2.25) / 1.75; fh = (FH - 30) / 18; gr = (GR - 9) / 6; tp = (TP - 23) / 5; ag = (AG - 1.5) / 1.5;
    pro = 6.0 + 0.3*fp + 0.8*fh + 0.6*gr + 0.5*tp + 0.2*ag + 0.2*fh*gr;
    taste = 6.5 + 0.5*fp - 0.5*fh - 0.3*gr + 0.2*tp + 0.1*ag - 0.2*fh*fh + 0.1*fp*gr;
    if (pro < 1) pro = 1; if (pro > 10) pro = 10;
    if (taste < 1) taste = 1; if (taste > 10) taste = 10;
    printf "{\\"probiotic_score\\": %.1f, \\"taste_score\\": %.1f}", pro + n1*0.3, taste + n2*0.3;
""",
     "factor_cases": '--fat_pct) FP="$2"; shift 2 ;;\n        --ferm_hrs) FH="$2"; shift 2 ;;\n        --grain_ratio_pct) GR="$2"; shift 2 ;;\n        --temp_c) TP="$2"; shift 2 ;;\n        --agitation) AG="$2"; shift 2 ;;',
     "awk_vars": '-v FP="$FP" -v FH="$FH" -v GR="$GR" -v TP="$TP" -v AG="$AG"',
     "vars_init": 'FP=""\nFH=""\nGR=""\nTP=""\nAG=""', "validate": '[ -z "$FP" ] || [ -z "$FH" ] || [ -z "$GR" ] || [ -z "$TP" ]'},

    {"num": 247, "slug": "tempeh_incubation", "name": "Tempeh Incubation Conditions",
     "desc": "Box-Behnken design to maximize mycelium coverage and minimize ammonia by tuning incubation temperature, humidity, and perforation density",
     "design": "box_behnken", "category": "brewing",
     "factors": [
         {"name": "incub_temp_c", "levels": ["28", "35"], "type": "continuous", "unit": "C", "description": "Incubation temperature"},
         {"name": "humidity_pct", "levels": ["60", "90"], "type": "continuous", "unit": "%", "description": "Incubation humidity"},
         {"name": "holes_per_cm2", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "per_cm2", "description": "Bag perforation density"},
     ],
     "fixed": {"bean": "soybean", "starter": "rhizopus_oligosporus"},
     "responses": [
         {"name": "coverage_pct", "optimize": "maximize", "unit": "%", "description": "Mycelium surface coverage percentage"},
         {"name": "ammonia_score", "optimize": "minimize", "unit": "pts", "description": "Ammonia/over-fermentation score (1-10)"},
     ],
     "model": """
    it = (IT - 31.5) / 3.5; hm = (HM - 75) / 15; hp = (HP - 1.75) / 1.25;
    cov = 80 + 5*it + 3*hm + 4*hp - 5*it*it - 2*hm*hm - 1*hp*hp + 1*it*hm;
    amm = 3.0 + 1.5*it + 0.3*hm - 0.5*hp + 1*it*it + 0.2*hm*hm + 0.3*it*hm;
    if (cov < 20) cov = 20; if (cov > 100) cov = 100;
    if (amm < 1) amm = 1; if (amm > 10) amm = 10;
    printf "{\\"coverage_pct\\": %.0f, \\"ammonia_score\\": %.1f}", cov + n1*3, amm + n2*0.3;
""",
     "factor_cases": '--incub_temp_c) IT="$2"; shift 2 ;;\n        --humidity_pct) HM="$2"; shift 2 ;;\n        --holes_per_cm2) HP="$2"; shift 2 ;;',
     "awk_vars": '-v IT="$IT" -v HM="$HM" -v HP="$HP"',
     "vars_init": 'IT=""\nHM=""\nHP=""', "validate": '[ -z "$IT" ] || [ -z "$HM" ] || [ -z "$HP" ]'},

    {"num": 248, "slug": "ginger_beer", "name": "Ginger Beer Fermentation",
     "desc": "Central composite design to maximize ginger bite and carbonation while controlling sweetness by tuning ginger amount, sugar, and fermentation time",
     "design": "central_composite", "category": "brewing",
     "factors": [
         {"name": "ginger_g_L", "levels": ["20", "80"], "type": "continuous", "unit": "g/L", "description": "Fresh ginger per liter"},
         {"name": "sugar_g_L", "levels": ["40", "100"], "type": "continuous", "unit": "g/L", "description": "Sugar concentration"},
         {"name": "ferm_days", "levels": ["2", "7"], "type": "continuous", "unit": "days", "description": "Fermentation duration"},
     ],
     "fixed": {"starter": "ginger_bug", "lemon_juice": "15mL/L"},
     "responses": [
         {"name": "ginger_bite", "optimize": "maximize", "unit": "pts", "description": "Ginger heat and spiciness (1-10)"},
         {"name": "carbonation", "optimize": "maximize", "unit": "pts", "description": "Carbonation level (1-10)"},
     ],
     "model": """
    gg = (GG - 50) / 30; sg = (SG - 70) / 30; fd = (FD - 4.5) / 2.5;
    bite = 5.5 + 2.0*gg + 0.2*sg + 0.3*fd - 0.5*gg*gg + 0.1*sg*sg + 0.2*gg*fd;
    carb = 5.0 + 0.3*gg + 0.8*sg + 1.5*fd - 0.2*gg*gg - 0.3*sg*sg - 0.5*fd*fd + 0.2*sg*fd;
    if (bite < 1) bite = 1; if (bite > 10) bite = 10;
    if (carb < 1) carb = 1; if (carb > 10) carb = 10;
    printf "{\\"ginger_bite\\": %.1f, \\"carbonation\\": %.1f}", bite + n1*0.3, carb + n2*0.3;
""",
     "factor_cases": '--ginger_g_L) GG="$2"; shift 2 ;;\n        --sugar_g_L) SG="$2"; shift 2 ;;\n        --ferm_days) FD="$2"; shift 2 ;;',
     "awk_vars": '-v GG="$GG" -v SG="$SG" -v FD="$FD"',
     "vars_init": 'GG=""\nSG=""\nFD=""', "validate": '[ -z "$GG" ] || [ -z "$SG" ] || [ -z "$FD" ]'},

    # ══════════════════════════════════════════════════
    # General (249-250)
    # ══════════════════════════════════════════════════
    {"num": 249, "slug": "gift_wrapping", "name": "Gift Wrapping Efficiency",
     "desc": "Box-Behnken design to maximize presentation quality and minimize paper waste by tuning paper overhang, tape strips, and ribbon curl count",
     "design": "box_behnken", "category": "general",
     "factors": [
         {"name": "overhang_cm", "levels": ["2", "8"], "type": "continuous", "unit": "cm", "description": "Paper overhang beyond box edges"},
         {"name": "tape_strips", "levels": ["3", "8"], "type": "continuous", "unit": "strips", "description": "Number of tape strips used"},
         {"name": "ribbon_curls", "levels": ["0", "6"], "type": "continuous", "unit": "curls", "description": "Number of curled ribbon strands"},
     ],
     "fixed": {"paper_type": "glossy", "box_size": "medium"},
     "responses": [
         {"name": "presentation", "optimize": "maximize", "unit": "pts", "description": "Visual presentation score (1-10)"},
         {"name": "waste_pct", "optimize": "minimize", "unit": "%", "description": "Paper waste as percentage of used paper"},
     ],
     "model": """
    oh = (OH - 5) / 3; ts = (TS - 5.5) / 2.5; rc = (RC - 3) / 3;
    pres = 6.0 + 0.5*oh + 0.3*ts + 1.0*rc - 0.5*oh*oh - 0.2*ts*ts - 0.3*rc*rc + 0.2*oh*rc;
    waste = 10 + 5*oh + 0.5*ts + 1*rc + 1*oh*oh;
    if (pres < 1) pres = 1; if (pres > 10) pres = 10; if (waste < 2) waste = 2;
    printf "{\\"presentation\\": %.1f, \\"waste_pct\\": %.0f}", pres + n1*0.3, waste + n2*1;
""",
     "factor_cases": '--overhang_cm) OH="$2"; shift 2 ;;\n        --tape_strips) TS="$2"; shift 2 ;;\n        --ribbon_curls) RC="$2"; shift 2 ;;',
     "awk_vars": '-v OH="$OH" -v TS="$TS" -v RC="$RC"',
     "vars_init": 'OH=""\nTS=""\nRC=""', "validate": '[ -z "$OH" ] || [ -z "$TS" ] || [ -z "$RC" ]'},

    {"num": 250, "slug": "garage_sale_pricing", "name": "Garage Sale Pricing Strategy",
     "desc": "Central composite design to maximize total revenue and minimize unsold items by tuning starting price multiplier, discount schedule, and signage count",
     "design": "central_composite", "category": "general",
     "factors": [
         {"name": "price_multiplier", "levels": ["0.1", "0.4"], "type": "continuous", "unit": "x_retail", "description": "Starting price as fraction of retail"},
         {"name": "discount_per_hr_pct", "levels": ["0", "15"], "type": "continuous", "unit": "%/hr", "description": "Hourly price reduction percentage"},
         {"name": "signs", "levels": ["2", "10"], "type": "continuous", "unit": "count", "description": "Number of directional signs placed"},
     ],
     "fixed": {"duration": "6hrs", "items": "200"},
     "responses": [
         {"name": "revenue_usd", "optimize": "maximize", "unit": "USD", "description": "Total revenue in dollars"},
         {"name": "unsold_pct", "optimize": "minimize", "unit": "%", "description": "Percentage of items unsold"},
     ],
     "model": """
    pm = (PM - 0.25) / 0.15; dh = (DH - 7.5) / 7.5; sg = (SG - 6) / 4;
    rev = 350 + 60*pm - 30*dh + 40*sg - 40*pm*pm - 10*dh*dh + 10*pm*dh + 5*pm*sg;
    unsold = 30 + 10*pm - 8*dh - 5*sg + 5*pm*pm + 2*dh*dh + 2*pm*dh;
    if (rev < 50) rev = 50; if (unsold < 5) unsold = 5; if (unsold > 70) unsold = 70;
    printf "{\\"revenue_usd\\": %.0f, \\"unsold_pct\\": %.0f}", rev + n1*15, unsold + n2*2;
""",
     "factor_cases": '--price_multiplier) PM="$2"; shift 2 ;;\n        --discount_per_hr_pct) DH="$2"; shift 2 ;;\n        --signs) SG="$2"; shift 2 ;;',
     "awk_vars": '-v PM="$PM" -v DH="$DH" -v SG="$SG"',
     "vars_init": 'PM=""\nDH=""\nSG=""', "validate": '[ -z "$PM" ] || [ -z "$DH" ] || [ -z "$SG" ]'},
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
    return {
        "metadata": {"name": uc["name"], "description": uc["desc"]},
        "factors": uc["factors"],
        "fixed_factors": uc.get("fixed", {}),
        "responses": uc["responses"],
        "runner": {"arg_style": "double-dash"},
        "settings": {
            "block_count": 1,
            "test_script": f"use_cases/{uc['num']}_{uc['slug']}/sim.sh",
            "operation": uc["design"],
            "processed_directory": f"use_cases/{uc['num']}_{uc['slug']}/results/analysis",
            "out_directory": f"use_cases/{uc['num']}_{uc['slug']}/results",
        },
    }


def main():
    for uc in USE_CASES:
        num, slug = uc["num"], uc["slug"]
        uc_dir = f"use_cases/{num}_{slug}"
        os.makedirs(os.path.join(uc_dir, "results"), exist_ok=True)
        with open(os.path.join(uc_dir, "config.json"), "w") as f:
            json.dump(build_config(uc), f, indent=4)
        sim_path = os.path.join(uc_dir, "sim.sh")
        with open(sim_path, "w") as f:
            f.write(build_sim_script(uc))
        os.chmod(sim_path, os.stat(sim_path).st_mode | stat.S_IEXEC)
        print(f"  [{num:03d}] {uc_dir}/")
    print(f"\n  {len(USE_CASES)} use cases created (199-250).")


if __name__ == "__main__":
    main()
