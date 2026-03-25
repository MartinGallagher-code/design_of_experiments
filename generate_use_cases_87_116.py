#!/usr/bin/env python3
"""Generate 30 new use cases across 3 non-computer categories (87-116).

Categories:
  - Food & Cooking (87-96)
  - Agriculture & Gardening (97-106)
  - Healthcare & Fitness (107-116)
"""
import json, os, stat, textwrap

USE_CASES = [
    # ══════════════════════════════════════════════════
    # Category: Food & Cooking (87-96)
    # ══════════════════════════════════════════════════
    {
        "num": 87, "slug": "bread_baking",
        "name": "Bread Baking Optimization",
        "desc": "Box-Behnken design to optimize crust color, crumb texture, and rise height by tuning oven temperature, hydration, and proofing time",
        "design": "box_behnken", "category": "food",
        "factors": [
            {"name": "oven_temp", "levels": ["200", "260"], "type": "continuous", "unit": "C", "description": "Oven temperature in Celsius"},
            {"name": "hydration_pct", "levels": ["60", "80"], "type": "continuous", "unit": "%", "description": "Dough hydration percentage"},
            {"name": "proof_time", "levels": ["30", "120"], "type": "continuous", "unit": "min", "description": "Proofing time in minutes"},
        ],
        "fixed": {"flour_type": "bread_flour", "salt_pct": "2"},
        "responses": [
            {"name": "crust_score", "optimize": "maximize", "unit": "pts", "description": "Crust color and crispness score (1-10)"},
            {"name": "crumb_score", "optimize": "maximize", "unit": "pts", "description": "Crumb openness and texture score (1-10)"},
        ],
        "model": """
    ot = (OT - 230) / 30;
    hp = (HP - 70) / 10;
    pt = (PT - 75) / 45;
    crust = 6.5 + 1.2*ot - 0.4*hp + 0.8*pt - 0.6*ot*ot - 0.3*hp*hp + 0.5*ot*hp;
    crumb = 7.0 - 0.5*ot + 1.5*hp + 1.0*pt - 0.4*hp*hp - 0.7*pt*pt + 0.3*hp*pt;
    if (crust < 1) crust = 1; if (crust > 10) crust = 10;
    if (crumb < 1) crumb = 1; if (crumb > 10) crumb = 10;
    printf "{\\"crust_score\\": %.1f, \\"crumb_score\\": %.1f}", crust + n1*0.4, crumb + n2*0.3;
""",
        "factor_cases": '--oven_temp) OT="$2"; shift 2 ;;\n        --hydration_pct) HP="$2"; shift 2 ;;\n        --proof_time) PT="$2"; shift 2 ;;',
        "awk_vars": '-v OT="$OT" -v HP="$HP" -v PT="$PT"',
        "vars_init": 'OT=""\nHP=""\nPT=""',
        "validate": '[ -z "$OT" ] || [ -z "$HP" ] || [ -z "$PT" ]',
    },
    {
        "num": 88, "slug": "coffee_brewing",
        "name": "Coffee Brewing Extraction",
        "desc": "Central composite design to maximize flavor score and minimize bitterness by tuning grind size, water temperature, brew time, and coffee-to-water ratio",
        "design": "central_composite", "category": "food",
        "factors": [
            {"name": "grind_size", "levels": ["200", "800"], "type": "continuous", "unit": "um", "description": "Coffee grind particle size in microns"},
            {"name": "water_temp", "levels": ["85", "96"], "type": "continuous", "unit": "C", "description": "Water temperature in Celsius"},
            {"name": "brew_time", "levels": ["180", "300"], "type": "continuous", "unit": "sec", "description": "Total brew time in seconds"},
            {"name": "ratio", "levels": ["14", "18"], "type": "continuous", "unit": "g/g", "description": "Coffee-to-water ratio (grams water per gram coffee)"},
        ],
        "fixed": {"roast_level": "medium", "water_tds": "120"},
        "responses": [
            {"name": "flavor_score", "optimize": "maximize", "unit": "pts", "description": "Cupping flavor score (1-100)"},
            {"name": "bitterness", "optimize": "minimize", "unit": "pts", "description": "Perceived bitterness score (1-10)"},
        ],
        "model": """
    gs = (GS - 500) / 300;
    wt = (WT - 90.5) / 5.5;
    bt = (BT - 240) / 60;
    ra = (RA - 16) / 2;
    flav = 78 + 3*gs - 2*wt + 4*bt + 2*ra - 3*gs*gs - 2*wt*wt - 2*bt*bt - 1*ra*ra + 1.5*gs*bt + 1*wt*ra;
    bit = 5 - 1.5*gs + 1.2*wt + 0.8*bt - 0.5*ra + 0.6*wt*wt + 0.4*bt*bt + 0.5*wt*bt;
    if (flav < 50) flav = 50; if (flav > 100) flav = 100;
    if (bit < 1) bit = 1; if (bit > 10) bit = 10;
    printf "{\\"flavor_score\\": %.1f, \\"bitterness\\": %.1f}", flav + n1*2, bit + n2*0.4;
""",
        "factor_cases": '--grind_size) GS="$2"; shift 2 ;;\n        --water_temp) WT="$2"; shift 2 ;;\n        --brew_time) BT="$2"; shift 2 ;;\n        --ratio) RA="$2"; shift 2 ;;',
        "awk_vars": '-v GS="$GS" -v WT="$WT" -v BT="$BT" -v RA="$RA"',
        "vars_init": 'GS=""\nWT=""\nBT=""\nRA=""',
        "validate": '[ -z "$GS" ] || [ -z "$WT" ] || [ -z "$BT" ] || [ -z "$RA" ]',
    },
    {
        "num": 89, "slug": "pizza_dough",
        "name": "Pizza Dough Formulation",
        "desc": "Full factorial of flour protein content, yeast amount, olive oil, and fermentation time for chewiness and bubble structure",
        "design": "full_factorial", "category": "food",
        "factors": [
            {"name": "protein_pct", "levels": ["10", "14"], "type": "continuous", "unit": "%", "description": "Flour protein content percentage"},
            {"name": "yeast_g", "levels": ["2", "7"], "type": "continuous", "unit": "g", "description": "Yeast amount per 500g flour"},
            {"name": "oil_ml", "levels": ["10", "30"], "type": "continuous", "unit": "mL", "description": "Olive oil per 500g flour"},
            {"name": "ferment_hrs", "levels": ["4", "72"], "type": "continuous", "unit": "hrs", "description": "Cold fermentation time"},
        ],
        "fixed": {"salt_pct": "2.5", "water_temp": "20"},
        "responses": [
            {"name": "chewiness", "optimize": "maximize", "unit": "pts", "description": "Chewiness and bite score (1-10)"},
            {"name": "bubble_score", "optimize": "maximize", "unit": "pts", "description": "Bubble structure and leopard-spotting score (1-10)"},
        ],
        "model": """
    pp = (PP - 12) / 2;
    yg = (YG - 4.5) / 2.5;
    om = (OM - 20) / 10;
    fh = (FH - 38) / 34;
    chew = 6.0 + 1.5*pp - 0.3*yg + 0.6*om + 0.8*fh + 0.4*pp*fh - 0.3*yg*om;
    bub = 5.5 + 0.5*pp + 1.2*yg - 0.4*om + 1.5*fh + 0.6*yg*fh + 0.3*pp*yg;
    if (chew < 1) chew = 1; if (chew > 10) chew = 10;
    if (bub < 1) bub = 1; if (bub > 10) bub = 10;
    printf "{\\"chewiness\\": %.1f, \\"bubble_score\\": %.1f}", chew + n1*0.5, bub + n2*0.4;
""",
        "factor_cases": '--protein_pct) PP="$2"; shift 2 ;;\n        --yeast_g) YG="$2"; shift 2 ;;\n        --oil_ml) OM="$2"; shift 2 ;;\n        --ferment_hrs) FH="$2"; shift 2 ;;',
        "awk_vars": '-v PP="$PP" -v YG="$YG" -v OM="$OM" -v FH="$FH"',
        "vars_init": 'PP=""\nYG=""\nOM=""\nFH=""',
        "validate": '[ -z "$PP" ] || [ -z "$YG" ] || [ -z "$OM" ] || [ -z "$FH" ]',
    },
    {
        "num": 90, "slug": "chocolate_tempering",
        "name": "Chocolate Tempering Process",
        "desc": "Box-Behnken design to optimize snap quality and gloss by tuning seed temperature, cooling rate, and agitation speed",
        "design": "box_behnken", "category": "food",
        "factors": [
            {"name": "seed_temp", "levels": ["27", "32"], "type": "continuous", "unit": "C", "description": "Seeding temperature in Celsius"},
            {"name": "cool_rate", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "C/min", "description": "Cooling rate"},
            {"name": "agitation_rpm", "levels": ["20", "120"], "type": "continuous", "unit": "rpm", "description": "Agitation speed during tempering"},
        ],
        "fixed": {"cocoa_pct": "70", "cocoa_butter_pct": "35"},
        "responses": [
            {"name": "snap_score", "optimize": "maximize", "unit": "pts", "description": "Snap quality score (1-10)"},
            {"name": "gloss_score", "optimize": "maximize", "unit": "pts", "description": "Surface gloss score (1-10)"},
        ],
        "model": """
    st = (ST - 29.5) / 2.5;
    cr = (CR - 1.75) / 1.25;
    ar = (AR - 70) / 50;
    snap = 6.5 + 1.8*st - 0.6*cr + 0.4*ar - 2.0*st*st - 0.5*cr*cr + 0.7*st*cr;
    gloss = 7.0 + 1.5*st - 0.8*cr + 0.6*ar - 1.5*st*st - 0.3*cr*cr - 0.2*ar*ar + 0.4*st*ar;
    if (snap < 1) snap = 1; if (snap > 10) snap = 10;
    if (gloss < 1) gloss = 1; if (gloss > 10) gloss = 10;
    printf "{\\"snap_score\\": %.1f, \\"gloss_score\\": %.1f}", snap + n1*0.3, gloss + n2*0.3;
""",
        "factor_cases": '--seed_temp) ST="$2"; shift 2 ;;\n        --cool_rate) CR="$2"; shift 2 ;;\n        --agitation_rpm) AR="$2"; shift 2 ;;',
        "awk_vars": '-v ST="$ST" -v CR="$CR" -v AR="$AR"',
        "vars_init": 'ST=""\nCR=""\nAR=""',
        "validate": '[ -z "$ST" ] || [ -z "$CR" ] || [ -z "$AR" ]',
    },
    {
        "num": 91, "slug": "yogurt_fermentation",
        "name": "Yogurt Fermentation Optimization",
        "desc": "Central composite design to maximize probiotic count and minimize sourness by tuning temperature, starter culture, and fermentation time",
        "design": "central_composite", "category": "food",
        "factors": [
            {"name": "ferm_temp", "levels": ["37", "46"], "type": "continuous", "unit": "C", "description": "Fermentation temperature"},
            {"name": "starter_pct", "levels": ["1", "5"], "type": "continuous", "unit": "%", "description": "Starter culture percentage"},
            {"name": "ferm_time", "levels": ["4", "12"], "type": "continuous", "unit": "hrs", "description": "Fermentation duration in hours"},
        ],
        "fixed": {"milk_fat_pct": "3.5", "pasteurization": "72C_15s"},
        "responses": [
            {"name": "probiotic_cfu", "optimize": "maximize", "unit": "log_CFU/mL", "description": "Probiotic count (log CFU/mL)"},
            {"name": "sourness", "optimize": "minimize", "unit": "pts", "description": "Sourness score (1-10, lower is milder)"},
        ],
        "model": """
    ft = (FT - 41.5) / 4.5;
    sp = (SP - 3) / 2;
    fm = (FM - 8) / 4;
    pro = 8.5 + 0.6*ft + 0.8*sp + 1.2*fm - 0.3*ft*ft - 0.2*sp*sp - 0.4*fm*fm + 0.3*ft*sp;
    sour = 4.5 + 0.8*ft + 0.5*sp + 1.5*fm + 0.2*ft*ft + 0.3*fm*fm + 0.4*ft*fm;
    if (pro < 6) pro = 6; if (pro > 11) pro = 11;
    if (sour < 1) sour = 1; if (sour > 10) sour = 10;
    printf "{\\"probiotic_cfu\\": %.1f, \\"sourness\\": %.1f}", pro + n1*0.2, sour + n2*0.3;
""",
        "factor_cases": '--ferm_temp) FT="$2"; shift 2 ;;\n        --starter_pct) SP="$2"; shift 2 ;;\n        --ferm_time) FM="$2"; shift 2 ;;',
        "awk_vars": '-v FT="$FT" -v SP="$SP" -v FM="$FM"',
        "vars_init": 'FT=""\nSP=""\nFM=""',
        "validate": '[ -z "$FT" ] || [ -z "$SP" ] || [ -z "$FM" ]',
    },
    {
        "num": 92, "slug": "steak_sous_vide",
        "name": "Steak Sous Vide Cooking",
        "desc": "Full factorial of water bath temperature, cooking time, pre-sear, and rest time to maximize tenderness and juiciness",
        "design": "full_factorial", "category": "food",
        "factors": [
            {"name": "bath_temp", "levels": ["52", "62"], "type": "continuous", "unit": "C", "description": "Water bath temperature"},
            {"name": "cook_time", "levels": ["60", "240"], "type": "continuous", "unit": "min", "description": "Sous vide cooking time"},
            {"name": "sear_time", "levels": ["30", "90"], "type": "continuous", "unit": "sec", "description": "Post-sear time per side"},
            {"name": "rest_time", "levels": ["2", "10"], "type": "continuous", "unit": "min", "description": "Resting time before serving"},
        ],
        "fixed": {"cut": "ribeye", "thickness_mm": "38"},
        "responses": [
            {"name": "tenderness", "optimize": "maximize", "unit": "pts", "description": "Tenderness score (1-10)"},
            {"name": "juiciness", "optimize": "maximize", "unit": "pts", "description": "Juiciness score (1-10)"},
        ],
        "model": """
    bt = (BT - 57) / 5;
    ct = (CT - 150) / 90;
    se = (SE - 60) / 30;
    rt = (RT - 6) / 4;
    tend = 7.0 + 0.3*bt + 1.0*ct + 0.2*se + 0.3*rt - 0.5*bt*bt - 0.3*ct*ct + 0.2*bt*ct;
    juic = 7.5 - 0.8*bt - 0.3*ct - 0.5*se + 0.6*rt + 0.3*bt*bt + 0.2*se*rt;
    if (tend < 1) tend = 1; if (tend > 10) tend = 10;
    if (juic < 1) juic = 1; if (juic > 10) juic = 10;
    printf "{\\"tenderness\\": %.1f, \\"juiciness\\": %.1f}", tend + n1*0.4, juic + n2*0.3;
""",
        "factor_cases": '--bath_temp) BT="$2"; shift 2 ;;\n        --cook_time) CT="$2"; shift 2 ;;\n        --sear_time) SE="$2"; shift 2 ;;\n        --rest_time) RT="$2"; shift 2 ;;',
        "awk_vars": '-v BT="$BT" -v CT="$CT" -v SE="$SE" -v RT="$RT"',
        "vars_init": 'BT=""\nCT=""\nSE=""\nRT=""',
        "validate": '[ -z "$BT" ] || [ -z "$CT" ] || [ -z "$SE" ] || [ -z "$RT" ]',
    },
    {
        "num": 93, "slug": "salad_dressing_emulsion",
        "name": "Salad Dressing Emulsion Stability",
        "desc": "Plackett-Burman screening of oil ratio, vinegar acidity, mustard, egg yolk, blending speed, and temperature for emulsion stability and taste",
        "design": "plackett_burman", "category": "food",
        "factors": [
            {"name": "oil_ratio", "levels": ["50", "80"], "type": "continuous", "unit": "%", "description": "Oil percentage of total liquid"},
            {"name": "vinegar_acidity", "levels": ["4", "7"], "type": "continuous", "unit": "%", "description": "Vinegar acidity percentage"},
            {"name": "mustard_g", "levels": ["2", "15"], "type": "continuous", "unit": "g", "description": "Mustard amount (emulsifier)"},
            {"name": "egg_yolk_count", "levels": ["0", "3"], "type": "continuous", "unit": "count", "description": "Number of egg yolks"},
            {"name": "blend_speed", "levels": ["5000", "20000"], "type": "continuous", "unit": "rpm", "description": "Immersion blender speed"},
            {"name": "mix_temp", "levels": ["5", "25"], "type": "continuous", "unit": "C", "description": "Ingredient temperature at mixing"},
        ],
        "fixed": {"total_volume_ml": "500", "salt_g": "3"},
        "responses": [
            {"name": "stability_hrs", "optimize": "maximize", "unit": "hrs", "description": "Hours before visible separation"},
            {"name": "taste_score", "optimize": "maximize", "unit": "pts", "description": "Taste panel score (1-10)"},
        ],
        "model": """
    or_ = (OR - 65) / 15;
    va = (VA - 5.5) / 1.5;
    mg = (MG - 8.5) / 6.5;
    ey = (EY - 1.5) / 1.5;
    bs = (BS - 12500) / 7500;
    mt = (MT - 15) / 10;
    stab = 48 + 10*or_ + 5*va + 12*mg + 15*ey + 8*bs - 6*mt + 3*mg*ey + 2*or_*bs;
    taste = 6.5 - 0.3*or_ + 0.8*va + 0.5*mg + 0.4*ey - 0.2*bs + 0.3*mt + 0.2*va*mg;
    if (stab < 1) stab = 1;
    if (taste < 1) taste = 1; if (taste > 10) taste = 10;
    printf "{\\"stability_hrs\\": %.0f, \\"taste_score\\": %.1f}", stab + n1*5, taste + n2*0.4;
""",
        "factor_cases": '--oil_ratio) OR="$2"; shift 2 ;;\n        --vinegar_acidity) VA="$2"; shift 2 ;;\n        --mustard_g) MG="$2"; shift 2 ;;\n        --egg_yolk_count) EY="$2"; shift 2 ;;\n        --blend_speed) BS="$2"; shift 2 ;;\n        --mix_temp) MT="$2"; shift 2 ;;',
        "awk_vars": '-v OR="$OR" -v VA="$VA" -v MG="$MG" -v EY="$EY" -v BS="$BS" -v MT="$MT"',
        "vars_init": 'OR=""\nVA=""\nMG=""\nEY=""\nBS=""\nMT=""',
        "validate": '[ -z "$OR" ] || [ -z "$VA" ] || [ -z "$MG" ] || [ -z "$EY" ]',
    },
    {
        "num": 94, "slug": "sourdough_starter",
        "name": "Sourdough Starter Vitality",
        "desc": "Box-Behnken design to optimize rise speed and flavor complexity by tuning feeding ratio, ambient temperature, and flour blend",
        "design": "box_behnken", "category": "food",
        "factors": [
            {"name": "feed_ratio", "levels": ["1", "5"], "type": "continuous", "unit": "x", "description": "Flour-to-starter feeding ratio"},
            {"name": "ambient_temp", "levels": ["20", "30"], "type": "continuous", "unit": "C", "description": "Ambient temperature during fermentation"},
            {"name": "whole_grain_pct", "levels": ["0", "50"], "type": "continuous", "unit": "%", "description": "Percentage of whole grain flour in feed"},
        ],
        "fixed": {"hydration": "100", "feeding_schedule": "every_12h"},
        "responses": [
            {"name": "rise_speed", "optimize": "maximize", "unit": "mL/hr", "description": "Volume increase rate"},
            {"name": "flavor_complexity", "optimize": "maximize", "unit": "pts", "description": "Aroma and flavor complexity score (1-10)"},
        ],
        "model": """
    fr = (FR - 3) / 2;
    at = (AT - 25) / 5;
    wg = (WG - 25) / 25;
    rise = 15 + 3*fr + 5*at + 2*wg - 1.5*fr*fr - 2*at*at + 1*fr*at + 0.5*at*wg;
    flav = 6.0 - 0.5*fr + 0.8*at + 1.2*wg + 0.3*fr*fr - 0.4*at*at + 0.3*fr*wg;
    if (rise < 1) rise = 1;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    printf "{\\"rise_speed\\": %.1f, \\"flavor_complexity\\": %.1f}", rise + n1*1.5, flav + n2*0.3;
""",
        "factor_cases": '--feed_ratio) FR="$2"; shift 2 ;;\n        --ambient_temp) AT="$2"; shift 2 ;;\n        --whole_grain_pct) WG="$2"; shift 2 ;;',
        "awk_vars": '-v FR="$FR" -v AT="$AT" -v WG="$WG"',
        "vars_init": 'FR=""\nAT=""\nWG=""',
        "validate": '[ -z "$FR" ] || [ -z "$AT" ] || [ -z "$WG" ]',
    },
    {
        "num": 95, "slug": "cookie_texture",
        "name": "Cookie Texture Optimization",
        "desc": "Central composite design to control chewiness vs crispness by tuning butter ratio, sugar type blend, egg count, and baking time",
        "design": "central_composite", "category": "food",
        "factors": [
            {"name": "butter_pct", "levels": ["30", "50"], "type": "continuous", "unit": "%", "description": "Butter as percentage of flour weight"},
            {"name": "brown_sugar_ratio", "levels": ["0", "100"], "type": "continuous", "unit": "%", "description": "Brown sugar as percentage of total sugar"},
            {"name": "eggs", "levels": ["1", "3"], "type": "continuous", "unit": "count", "description": "Number of eggs per batch"},
            {"name": "bake_time", "levels": ["8", "14"], "type": "continuous", "unit": "min", "description": "Baking time at 175C"},
        ],
        "fixed": {"oven_temp": "175", "flour_type": "all_purpose"},
        "responses": [
            {"name": "chewiness_score", "optimize": "maximize", "unit": "pts", "description": "Chewiness score (1-10)"},
            {"name": "spread_ratio", "optimize": "maximize", "unit": "ratio", "description": "Cookie diameter-to-height spread ratio"},
        ],
        "model": """
    bp = (BP - 40) / 10;
    bs = (BS - 50) / 50;
    eg = (EG - 2) / 1;
    bt = (BK - 11) / 3;
    chew = 6.0 + 0.8*bp + 1.2*bs + 0.6*eg - 1.5*bt - 0.5*bp*bp - 0.3*bs*bs + 0.4*bp*bs - 0.5*eg*bt;
    spread = 3.5 + 0.5*bp - 0.3*bs - 0.4*eg + 0.6*bt + 0.2*bp*bt - 0.1*bs*eg;
    if (chew < 1) chew = 1; if (chew > 10) chew = 10;
    if (spread < 1.5) spread = 1.5; if (spread > 6) spread = 6;
    printf "{\\"chewiness_score\\": %.1f, \\"spread_ratio\\": %.2f}", chew + n1*0.4, spread + n2*0.2;
""",
        "factor_cases": '--butter_pct) BP="$2"; shift 2 ;;\n        --brown_sugar_ratio) BS="$2"; shift 2 ;;\n        --eggs) EG="$2"; shift 2 ;;\n        --bake_time) BK="$2"; shift 2 ;;',
        "awk_vars": '-v BP="$BP" -v BS="$BS" -v EG="$EG" -v BK="$BK"',
        "vars_init": 'BP=""\nBS=""\nEG=""\nBK=""',
        "validate": '[ -z "$BP" ] || [ -z "$BS" ] || [ -z "$EG" ] || [ -z "$BK" ]',
    },
    {
        "num": 96, "slug": "fermented_hot_sauce",
        "name": "Fermented Hot Sauce Formulation",
        "desc": "Fractional factorial screening of pepper type, salt concentration, garlic ratio, fermentation days, and vinegar addition for heat balance and umami depth",
        "design": "fractional_factorial", "category": "food",
        "factors": [
            {"name": "pepper_shu", "levels": ["5000", "100000"], "type": "continuous", "unit": "SHU", "description": "Pepper Scoville heat units"},
            {"name": "salt_pct", "levels": ["2", "6"], "type": "continuous", "unit": "%", "description": "Salt concentration by weight"},
            {"name": "garlic_pct", "levels": ["2", "10"], "type": "continuous", "unit": "%", "description": "Garlic percentage of total mash"},
            {"name": "ferm_days", "levels": ["7", "90"], "type": "continuous", "unit": "days", "description": "Fermentation duration"},
            {"name": "vinegar_pct", "levels": ["5", "25"], "type": "continuous", "unit": "%", "description": "Vinegar added post-fermentation"},
        ],
        "fixed": {"ferm_temp": "22", "jar_size": "1L"},
        "responses": [
            {"name": "heat_balance", "optimize": "maximize", "unit": "pts", "description": "Heat balance score (1-10, 10 = perfectly balanced)"},
            {"name": "umami_depth", "optimize": "maximize", "unit": "pts", "description": "Umami and flavor depth score (1-10)"},
        ],
        "model": """
    ps = (PS - 52500) / 47500;
    sc = (SC - 4) / 2;
    gp = (GP - 6) / 4;
    fd = (FD - 48.5) / 41.5;
    vp = (VP - 15) / 10;
    heat = 5.5 - 1.2*ps + 0.8*sc + 0.4*gp + 0.6*fd - 0.5*vp - 0.8*ps*ps + 0.3*sc*fd;
    umami = 5.0 + 0.3*ps + 0.5*sc + 1.0*gp + 1.5*fd - 0.3*vp + 0.4*gp*fd + 0.2*sc*gp;
    if (heat < 1) heat = 1; if (heat > 10) heat = 10;
    if (umami < 1) umami = 1; if (umami > 10) umami = 10;
    printf "{\\"heat_balance\\": %.1f, \\"umami_depth\\": %.1f}", heat + n1*0.4, umami + n2*0.3;
""",
        "factor_cases": '--pepper_shu) PS="$2"; shift 2 ;;\n        --salt_pct) SC="$2"; shift 2 ;;\n        --garlic_pct) GP="$2"; shift 2 ;;\n        --ferm_days) FD="$2"; shift 2 ;;\n        --vinegar_pct) VP="$2"; shift 2 ;;',
        "awk_vars": '-v PS="$PS" -v SC="$SC" -v GP="$GP" -v FD="$FD" -v VP="$VP"',
        "vars_init": 'PS=""\nSC=""\nGP=""\nFD=""\nVP=""',
        "validate": '[ -z "$PS" ] || [ -z "$SC" ] || [ -z "$GP" ] || [ -z "$FD" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: Agriculture & Gardening (97-106)
    # ══════════════════════════════════════════════════
    {
        "num": 97, "slug": "tomato_greenhouse",
        "name": "Tomato Greenhouse Yield",
        "desc": "Central composite design to maximize fruit yield and minimize blossom end rot by tuning temperature, humidity, and irrigation frequency",
        "design": "central_composite", "category": "agriculture",
        "factors": [
            {"name": "day_temp", "levels": ["22", "32"], "type": "continuous", "unit": "C", "description": "Daytime greenhouse temperature"},
            {"name": "humidity_pct", "levels": ["50", "85"], "type": "continuous", "unit": "%", "description": "Relative humidity"},
            {"name": "irrigation_freq", "levels": ["2", "6"], "type": "continuous", "unit": "per_day", "description": "Irrigation cycles per day"},
        ],
        "fixed": {"variety": "roma", "light_hours": "16"},
        "responses": [
            {"name": "yield_kg", "optimize": "maximize", "unit": "kg/plant", "description": "Fruit yield per plant"},
            {"name": "ber_pct", "optimize": "minimize", "unit": "%", "description": "Blossom end rot incidence percentage"},
        ],
        "model": """
    dt = (DT - 27) / 5;
    hm = (HM - 67.5) / 17.5;
    ir = (IR - 4) / 2;
    yld = 4.5 + 0.8*dt + 0.3*hm + 0.6*ir - 0.5*dt*dt - 0.2*hm*hm - 0.3*ir*ir + 0.2*dt*ir;
    ber = 8 + 3*dt - 2*hm - 1.5*ir + 1.5*dt*dt + 0.5*hm*hm + 1*dt*hm;
    if (yld < 0.5) yld = 0.5;
    if (ber < 0) ber = 0; if (ber > 40) ber = 40;
    printf "{\\"yield_kg\\": %.2f, \\"ber_pct\\": %.1f}", yld + n1*0.3, ber + n2*1.0;
""",
        "factor_cases": '--day_temp) DT="$2"; shift 2 ;;\n        --humidity_pct) HM="$2"; shift 2 ;;\n        --irrigation_freq) IR="$2"; shift 2 ;;',
        "awk_vars": '-v DT="$DT" -v HM="$HM" -v IR="$IR"',
        "vars_init": 'DT=""\nHM=""\nIR=""',
        "validate": '[ -z "$DT" ] || [ -z "$HM" ] || [ -z "$IR" ]',
    },
    {
        "num": 98, "slug": "compost_maturity",
        "name": "Compost Maturity Optimization",
        "desc": "Box-Behnken design to minimize maturation time and maximize nutrient content by tuning C:N ratio, moisture, and turning frequency",
        "design": "box_behnken", "category": "agriculture",
        "factors": [
            {"name": "cn_ratio", "levels": ["20", "40"], "type": "continuous", "unit": "ratio", "description": "Carbon-to-nitrogen ratio"},
            {"name": "moisture_pct", "levels": ["40", "65"], "type": "continuous", "unit": "%", "description": "Moisture content percentage"},
            {"name": "turn_freq", "levels": ["1", "7"], "type": "continuous", "unit": "per_week", "description": "Turning frequency per week"},
        ],
        "fixed": {"pile_volume": "1m3", "initial_material": "mixed_greens_browns"},
        "responses": [
            {"name": "maturity_weeks", "optimize": "minimize", "unit": "weeks", "description": "Weeks to reach mature compost"},
            {"name": "nutrient_score", "optimize": "maximize", "unit": "pts", "description": "NPK nutrient content score (1-10)"},
        ],
        "model": """
    cn = (CN - 30) / 10;
    mp = (MP - 52.5) / 12.5;
    tf = (TF - 4) / 3;
    mat = 12 - 2*cn + 1.5*mp - 3*tf + 1*cn*cn + 0.5*mp*mp + 0.8*tf*tf - 0.5*cn*tf;
    nut = 6.0 + 0.8*cn + 0.5*mp + 0.6*tf - 0.4*cn*cn - 0.3*mp*mp + 0.3*cn*mp;
    if (mat < 3) mat = 3;
    if (nut < 1) nut = 1; if (nut > 10) nut = 10;
    printf "{\\"maturity_weeks\\": %.1f, \\"nutrient_score\\": %.1f}", mat + n1*1.0, nut + n2*0.3;
""",
        "factor_cases": '--cn_ratio) CN="$2"; shift 2 ;;\n        --moisture_pct) MP="$2"; shift 2 ;;\n        --turn_freq) TF="$2"; shift 2 ;;',
        "awk_vars": '-v CN="$CN" -v MP="$MP" -v TF="$TF"',
        "vars_init": 'CN=""\nMP=""\nTF=""',
        "validate": '[ -z "$CN" ] || [ -z "$MP" ] || [ -z "$TF" ]',
    },
    {
        "num": 99, "slug": "seed_germination",
        "name": "Seed Germination Rate",
        "desc": "Full factorial of soil temperature, moisture level, seed depth, and light exposure to maximize germination percentage and minimize days to emergence",
        "design": "full_factorial", "category": "agriculture",
        "factors": [
            {"name": "soil_temp", "levels": ["15", "28"], "type": "continuous", "unit": "C", "description": "Soil temperature"},
            {"name": "moisture_level", "levels": ["30", "70"], "type": "continuous", "unit": "%", "description": "Soil moisture field capacity percentage"},
            {"name": "seed_depth", "levels": ["5", "25"], "type": "continuous", "unit": "mm", "description": "Planting depth in millimeters"},
            {"name": "light_hrs", "levels": ["8", "16"], "type": "continuous", "unit": "hrs", "description": "Daily light exposure hours"},
        ],
        "fixed": {"seed_variety": "lettuce", "medium": "potting_mix"},
        "responses": [
            {"name": "germination_pct", "optimize": "maximize", "unit": "%", "description": "Germination percentage"},
            {"name": "days_to_emerge", "optimize": "minimize", "unit": "days", "description": "Average days to seedling emergence"},
        ],
        "model": """
    st = (ST - 21.5) / 6.5;
    ml = (ML - 50) / 20;
    sd = (SD - 15) / 10;
    lh = (LH - 12) / 4;
    germ = 75 + 8*st + 6*ml - 4*sd + 3*lh - 5*st*st - 3*ml*ml + 2*st*ml - 1.5*sd*lh;
    days = 7 - 1.5*st - 0.5*ml + 1.2*sd - 0.3*lh + 0.8*st*st + 0.3*sd*sd;
    if (germ < 0) germ = 0; if (germ > 100) germ = 100;
    if (days < 2) days = 2;
    printf "{\\"germination_pct\\": %.1f, \\"days_to_emerge\\": %.1f}", germ + n1*4, days + n2*0.5;
""",
        "factor_cases": '--soil_temp) ST="$2"; shift 2 ;;\n        --moisture_level) ML="$2"; shift 2 ;;\n        --seed_depth) SD="$2"; shift 2 ;;\n        --light_hrs) LH="$2"; shift 2 ;;',
        "awk_vars": '-v ST="$ST" -v ML="$ML" -v SD="$SD" -v LH="$LH"',
        "vars_init": 'ST=""\nML=""\nSD=""\nLH=""',
        "validate": '[ -z "$ST" ] || [ -z "$ML" ] || [ -z "$SD" ] || [ -z "$LH" ]',
    },
    {
        "num": 100, "slug": "hydroponic_nutrient",
        "name": "Hydroponic Nutrient Solution",
        "desc": "Plackett-Burman screening of nitrogen, phosphorus, potassium, pH, EC, and calcium for lettuce growth rate and leaf color",
        "design": "plackett_burman", "category": "agriculture",
        "factors": [
            {"name": "nitrogen_ppm", "levels": ["100", "250"], "type": "continuous", "unit": "ppm", "description": "Nitrogen concentration"},
            {"name": "phosphorus_ppm", "levels": ["30", "80"], "type": "continuous", "unit": "ppm", "description": "Phosphorus concentration"},
            {"name": "potassium_ppm", "levels": ["150", "350"], "type": "continuous", "unit": "ppm", "description": "Potassium concentration"},
            {"name": "ph_level", "levels": ["5.5", "6.5"], "type": "continuous", "unit": "pH", "description": "Solution pH level"},
            {"name": "ec_level", "levels": ["1.0", "2.5"], "type": "continuous", "unit": "mS/cm", "description": "Electrical conductivity"},
            {"name": "calcium_ppm", "levels": ["100", "250"], "type": "continuous", "unit": "ppm", "description": "Calcium concentration"},
        ],
        "fixed": {"crop": "butterhead_lettuce", "system": "NFT"},
        "responses": [
            {"name": "growth_rate", "optimize": "maximize", "unit": "g/day", "description": "Daily biomass growth rate"},
            {"name": "color_score", "optimize": "maximize", "unit": "pts", "description": "Leaf color intensity score (1-10)"},
        ],
        "model": """
    n = (N - 175) / 75;
    p = (P - 55) / 25;
    k = (K - 250) / 100;
    ph = (PH - 6) / 0.5;
    ec = (EC - 1.75) / 0.75;
    ca = (CA - 175) / 75;
    gr = 3.5 + 0.8*n + 0.3*p + 0.5*k - 0.4*ph + 0.6*ec + 0.2*ca + 0.2*n*k + 0.15*ec*n;
    col = 7.0 + 1.0*n + 0.2*p + 0.3*k - 0.3*ph + 0.2*ec + 0.1*ca + 0.15*n*ph;
    if (gr < 0.5) gr = 0.5;
    if (col < 1) col = 1; if (col > 10) col = 10;
    printf "{\\"growth_rate\\": %.2f, \\"color_score\\": %.1f}", gr + n1*0.3, col + n2*0.3;
""",
        "factor_cases": '--nitrogen_ppm) N="$2"; shift 2 ;;\n        --phosphorus_ppm) P="$2"; shift 2 ;;\n        --potassium_ppm) K="$2"; shift 2 ;;\n        --ph_level) PH="$2"; shift 2 ;;\n        --ec_level) EC="$2"; shift 2 ;;\n        --calcium_ppm) CA="$2"; shift 2 ;;',
        "awk_vars": '-v N="$N" -v P="$P" -v K="$K" -v PH="$PH" -v EC="$EC" -v CA="$CA"',
        "vars_init": 'N=""\nP=""\nK=""\nPH=""\nEC=""\nCA=""',
        "validate": '[ -z "$N" ] || [ -z "$P" ] || [ -z "$K" ] || [ -z "$PH" ]',
    },
    {
        "num": 101, "slug": "lawn_grass_mix",
        "name": "Lawn Grass Seed Mix",
        "desc": "Box-Behnken design to optimize turf density and drought tolerance by tuning perennial ryegrass ratio, fescue ratio, and seeding rate",
        "design": "box_behnken", "category": "agriculture",
        "factors": [
            {"name": "ryegrass_pct", "levels": ["20", "60"], "type": "continuous", "unit": "%", "description": "Perennial ryegrass percentage of mix"},
            {"name": "fescue_pct", "levels": ["20", "60"], "type": "continuous", "unit": "%", "description": "Tall fescue percentage of mix"},
            {"name": "seed_rate", "levels": ["30", "80"], "type": "continuous", "unit": "g/m2", "description": "Seeding rate in grams per square meter"},
        ],
        "fixed": {"remaining_bluegrass_pct": "balance", "mowing_height_mm": "50"},
        "responses": [
            {"name": "density_score", "optimize": "maximize", "unit": "pts", "description": "Turf density score (1-10)"},
            {"name": "drought_tolerance", "optimize": "maximize", "unit": "pts", "description": "Drought tolerance score (1-10)"},
        ],
        "model": """
    rg = (RG - 40) / 20;
    fe = (FE - 40) / 20;
    sr = (SR - 55) / 25;
    dens = 6.5 + 1.0*rg + 0.5*fe + 1.2*sr - 0.4*rg*rg - 0.3*fe*fe - 0.5*sr*sr + 0.3*rg*fe;
    drght = 5.5 - 0.8*rg + 1.5*fe + 0.3*sr + 0.2*rg*rg - 0.4*fe*fe + 0.2*fe*sr;
    if (dens < 1) dens = 1; if (dens > 10) dens = 10;
    if (drght < 1) drght = 1; if (drght > 10) drght = 10;
    printf "{\\"density_score\\": %.1f, \\"drought_tolerance\\": %.1f}", dens + n1*0.4, drght + n2*0.3;
""",
        "factor_cases": '--ryegrass_pct) RG="$2"; shift 2 ;;\n        --fescue_pct) FE="$2"; shift 2 ;;\n        --seed_rate) SR="$2"; shift 2 ;;',
        "awk_vars": '-v RG="$RG" -v FE="$FE" -v SR="$SR"',
        "vars_init": 'RG=""\nFE=""\nSR=""',
        "validate": '[ -z "$RG" ] || [ -z "$FE" ] || [ -z "$SR" ]',
    },
    {
        "num": 102, "slug": "fruit_tree_pruning",
        "name": "Fruit Tree Pruning Strategy",
        "desc": "Full factorial of pruning intensity, timing, branch angle, and thinning ratio to maximize fruit size and total yield per tree",
        "design": "full_factorial", "category": "agriculture",
        "factors": [
            {"name": "prune_intensity", "levels": ["10", "40"], "type": "continuous", "unit": "%", "description": "Percentage of canopy removed"},
            {"name": "prune_month", "levels": ["1", "3"], "type": "continuous", "unit": "month", "description": "Pruning month (1=Jan, 3=Mar)"},
            {"name": "branch_angle", "levels": ["30", "60"], "type": "continuous", "unit": "deg", "description": "Target branch angle from vertical"},
            {"name": "thin_ratio", "levels": ["0", "50"], "type": "continuous", "unit": "%", "description": "Fruit thinning percentage"},
        ],
        "fixed": {"tree_age": "7yr", "variety": "honeycrisp_apple"},
        "responses": [
            {"name": "fruit_size_g", "optimize": "maximize", "unit": "g", "description": "Average fruit weight in grams"},
            {"name": "yield_kg", "optimize": "maximize", "unit": "kg/tree", "description": "Total yield per tree in kg"},
        ],
        "model": """
    pi = (PI - 25) / 15;
    pm = (PM - 2) / 1;
    ba = (BA - 45) / 15;
    tr = (TR - 25) / 25;
    sz = 180 + 15*pi + 5*pm + 10*ba + 25*tr - 8*pi*pi + 5*pi*tr + 3*ba*tr;
    yl = 45 - 8*pi + 3*pm - 2*ba - 12*tr + 3*pi*pi + 2*pm*ba - 4*pi*tr;
    if (sz < 80) sz = 80;
    if (yl < 10) yl = 10;
    printf "{\\"fruit_size_g\\": %.0f, \\"yield_kg\\": %.1f}", sz + n1*10, yl + n2*3;
""",
        "factor_cases": '--prune_intensity) PI="$2"; shift 2 ;;\n        --prune_month) PM="$2"; shift 2 ;;\n        --branch_angle) BA="$2"; shift 2 ;;\n        --thin_ratio) TR="$2"; shift 2 ;;',
        "awk_vars": '-v PI="$PI" -v PM="$PM" -v BA="$BA" -v TR="$TR"',
        "vars_init": 'PI=""\nPM=""\nBA=""\nTR=""',
        "validate": '[ -z "$PI" ] || [ -z "$PM" ] || [ -z "$BA" ] || [ -z "$TR" ]',
    },
    {
        "num": 103, "slug": "soil_amendment",
        "name": "Soil Amendment Blend",
        "desc": "Box-Behnken design to optimize soil pH and water retention by tuning lime application, organic matter addition, and gypsum rate",
        "design": "box_behnken", "category": "agriculture",
        "factors": [
            {"name": "lime_kg_ha", "levels": ["500", "3000"], "type": "continuous", "unit": "kg/ha", "description": "Agricultural lime application rate"},
            {"name": "organic_matter_pct", "levels": ["2", "8"], "type": "continuous", "unit": "%", "description": "Target organic matter percentage"},
            {"name": "gypsum_kg_ha", "levels": ["0", "2000"], "type": "continuous", "unit": "kg/ha", "description": "Gypsum application rate"},
        ],
        "fixed": {"soil_type": "clay_loam", "initial_ph": "5.2"},
        "responses": [
            {"name": "ph_achieved", "optimize": "maximize", "unit": "pH", "description": "Resulting soil pH (target 6.5)"},
            {"name": "water_retention", "optimize": "maximize", "unit": "mm/m", "description": "Available water capacity in mm per meter depth"},
        ],
        "model": """
    lm = (LM - 1750) / 1250;
    om = (OM - 5) / 3;
    gy = (GY - 1000) / 1000;
    ph = 6.0 + 0.5*lm + 0.1*om + 0.15*gy - 0.15*lm*lm - 0.05*om*om + 0.08*lm*om;
    wr = 150 + 10*lm + 30*om + 5*gy - 5*lm*lm - 8*om*om + 3*om*gy;
    if (ph < 4.5) ph = 4.5; if (ph > 8) ph = 8;
    if (wr < 80) wr = 80;
    printf "{\\"ph_achieved\\": %.2f, \\"water_retention\\": %.0f}", ph + n1*0.1, wr + n2*8;
""",
        "factor_cases": '--lime_kg_ha) LM="$2"; shift 2 ;;\n        --organic_matter_pct) OM="$2"; shift 2 ;;\n        --gypsum_kg_ha) GY="$2"; shift 2 ;;',
        "awk_vars": '-v LM="$LM" -v OM="$OM" -v GY="$GY"',
        "vars_init": 'LM=""\nOM=""\nGY=""',
        "validate": '[ -z "$LM" ] || [ -z "$OM" ] || [ -z "$GY" ]',
    },
    {
        "num": 104, "slug": "irrigation_scheduling",
        "name": "Drip Irrigation Scheduling",
        "desc": "Central composite design to minimize water usage and maximize crop yield by tuning drip rate, interval, and emitter spacing",
        "design": "central_composite", "category": "agriculture",
        "factors": [
            {"name": "drip_rate", "levels": ["1", "4"], "type": "continuous", "unit": "L/hr", "description": "Emitter drip rate"},
            {"name": "interval_hrs", "levels": ["6", "48"], "type": "continuous", "unit": "hrs", "description": "Irrigation interval"},
            {"name": "emitter_spacing", "levels": ["20", "50"], "type": "continuous", "unit": "cm", "description": "Distance between drip emitters"},
        ],
        "fixed": {"crop": "strawberry", "season": "summer"},
        "responses": [
            {"name": "water_use_L", "optimize": "minimize", "unit": "L/m2/wk", "description": "Weekly water consumption per square meter"},
            {"name": "crop_yield", "optimize": "maximize", "unit": "kg/m2", "description": "Crop yield per square meter"},
        ],
        "model": """
    dr = (DR - 2.5) / 1.5;
    ih = (IH - 27) / 21;
    es = (ES - 35) / 15;
    water = 25 + 8*dr - 6*ih - 3*es + 1.5*dr*dr + 2*ih*ih + 1*dr*ih;
    cyld = 2.5 + 0.5*dr - 0.8*ih - 0.3*es - 0.3*dr*dr - 0.5*ih*ih - 0.2*es*es + 0.2*dr*es;
    if (water < 5) water = 5;
    if (cyld < 0.5) cyld = 0.5;
    printf "{\\"water_use_L\\": %.1f, \\"crop_yield\\": %.2f}", water + n1*2, cyld + n2*0.15;
""",
        "factor_cases": '--drip_rate) DR="$2"; shift 2 ;;\n        --interval_hrs) IH="$2"; shift 2 ;;\n        --emitter_spacing) ES="$2"; shift 2 ;;',
        "awk_vars": '-v DR="$DR" -v IH="$IH" -v ES="$ES"',
        "vars_init": 'DR=""\nIH=""\nES=""',
        "validate": '[ -z "$DR" ] || [ -z "$IH" ] || [ -z "$ES" ]',
    },
    {
        "num": 105, "slug": "greenhouse_climate",
        "name": "Greenhouse Climate Control",
        "desc": "Plackett-Burman screening of ventilation rate, shade cloth, CO2 enrichment, heating setpoint, and misting frequency for plant growth and energy cost",
        "design": "plackett_burman", "category": "agriculture",
        "factors": [
            {"name": "vent_rate", "levels": ["5", "30"], "type": "continuous", "unit": "ach", "description": "Air changes per hour"},
            {"name": "shade_pct", "levels": ["0", "60"], "type": "continuous", "unit": "%", "description": "Shade cloth coverage percentage"},
            {"name": "co2_ppm", "levels": ["400", "1200"], "type": "continuous", "unit": "ppm", "description": "CO2 enrichment level"},
            {"name": "heat_setpoint", "levels": ["15", "25"], "type": "continuous", "unit": "C", "description": "Heating thermostat setpoint"},
            {"name": "mist_freq", "levels": ["0", "12"], "type": "continuous", "unit": "per_day", "description": "Misting cycles per day"},
        ],
        "fixed": {"greenhouse_area": "200m2", "crop": "cucumber"},
        "responses": [
            {"name": "growth_index", "optimize": "maximize", "unit": "pts", "description": "Plant growth index score (1-10)"},
            {"name": "energy_cost", "optimize": "minimize", "unit": "USD/day", "description": "Daily energy cost in USD"},
        ],
        "model": """
    vr = (VR - 17.5) / 12.5;
    sp = (SP - 30) / 30;
    co = (CO - 800) / 400;
    hs = (HS - 20) / 5;
    mf = (MF - 6) / 6;
    gro = 6.0 + 0.5*vr - 0.8*sp + 1.2*co + 0.6*hs + 0.3*mf + 0.3*co*hs;
    eng = 15 + 3*vr + 0.5*sp + 2*co + 5*hs + 0.8*mf + 1.5*vr*hs;
    if (gro < 1) gro = 1; if (gro > 10) gro = 10;
    if (eng < 3) eng = 3;
    printf "{\\"growth_index\\": %.1f, \\"energy_cost\\": %.1f}", gro + n1*0.4, eng + n2*1.5;
""",
        "factor_cases": '--vent_rate) VR="$2"; shift 2 ;;\n        --shade_pct) SP="$2"; shift 2 ;;\n        --co2_ppm) CO="$2"; shift 2 ;;\n        --heat_setpoint) HS="$2"; shift 2 ;;\n        --mist_freq) MF="$2"; shift 2 ;;',
        "awk_vars": '-v VR="$VR" -v SP="$SP" -v CO="$CO" -v HS="$HS" -v MF="$MF"',
        "vars_init": 'VR=""\nSP=""\nCO=""\nHS=""\nMF=""',
        "validate": '[ -z "$VR" ] || [ -z "$SP" ] || [ -z "$CO" ] || [ -z "$HS" ]',
    },
    {
        "num": 106, "slug": "raised_bed_mix",
        "name": "Raised Bed Soil Mix",
        "desc": "Box-Behnken design to optimize drainage and root growth by tuning peat moss ratio, perlite ratio, and compost ratio in a raised bed mix",
        "design": "box_behnken", "category": "agriculture",
        "factors": [
            {"name": "peat_pct", "levels": ["20", "50"], "type": "continuous", "unit": "%", "description": "Peat moss percentage of mix"},
            {"name": "perlite_pct", "levels": ["10", "35"], "type": "continuous", "unit": "%", "description": "Perlite percentage of mix"},
            {"name": "compost_pct", "levels": ["15", "45"], "type": "continuous", "unit": "%", "description": "Compost percentage of mix"},
        ],
        "fixed": {"bed_depth_cm": "30", "remaining_topsoil": "balance"},
        "responses": [
            {"name": "drainage_rate", "optimize": "maximize", "unit": "mm/hr", "description": "Water drainage rate"},
            {"name": "root_growth", "optimize": "maximize", "unit": "cm/week", "description": "Root growth rate"},
        ],
        "model": """
    pe = (PE - 35) / 15;
    pl = (PL - 22.5) / 12.5;
    co = (CO - 30) / 15;
    drain = 50 + 8*pe + 15*pl - 5*co - 3*pe*pe - 4*pl*pl + 2*pe*pl;
    root = 3.5 + 0.4*pe + 0.3*pl + 0.8*co - 0.2*pe*pe - 0.15*pl*pl - 0.3*co*co + 0.15*pl*co;
    if (drain < 10) drain = 10;
    if (root < 0.5) root = 0.5;
    printf "{\\"drainage_rate\\": %.0f, \\"root_growth\\": %.2f}", drain + n1*5, root + n2*0.2;
""",
        "factor_cases": '--peat_pct) PE="$2"; shift 2 ;;\n        --perlite_pct) PL="$2"; shift 2 ;;\n        --compost_pct) CO="$2"; shift 2 ;;',
        "awk_vars": '-v PE="$PE" -v PL="$PL" -v CO="$CO"',
        "vars_init": 'PE=""\nPL=""\nCO=""',
        "validate": '[ -z "$PE" ] || [ -z "$PL" ] || [ -z "$CO" ]',
    },

    # ══════════════════════════════════════════════════
    # Category: Healthcare & Fitness (107-116)
    # ══════════════════════════════════════════════════
    {
        "num": 107, "slug": "sleep_quality",
        "name": "Sleep Quality Optimization",
        "desc": "Central composite design to maximize sleep quality score and minimize wake-ups by tuning room temperature, screen cutoff time, and caffeine cutoff hour",
        "design": "central_composite", "category": "health",
        "factors": [
            {"name": "room_temp", "levels": ["16", "22"], "type": "continuous", "unit": "C", "description": "Bedroom temperature"},
            {"name": "screen_cutoff", "levels": ["30", "120"], "type": "continuous", "unit": "min", "description": "Minutes before bed screens are turned off"},
            {"name": "caffeine_cutoff", "levels": ["6", "14"], "type": "continuous", "unit": "hrs_before", "description": "Hours before bed to stop caffeine"},
        ],
        "fixed": {"bedtime": "22:30", "wake_time": "06:30"},
        "responses": [
            {"name": "sleep_score", "optimize": "maximize", "unit": "pts", "description": "Sleep quality score (1-100)"},
            {"name": "wake_count", "optimize": "minimize", "unit": "count", "description": "Number of nighttime wake-ups"},
        ],
        "model": """
    rt = (RT - 19) / 3;
    sc = (SC - 75) / 45;
    cc = (CC - 10) / 4;
    slp = 72 + 3*rt + 5*sc + 4*cc - 4*rt*rt - 2*sc*sc - 1.5*cc*cc + 1.5*rt*sc;
    wk = 2.5 - 0.4*rt - 0.6*sc - 0.5*cc + 0.3*rt*rt + 0.2*sc*sc + 0.15*rt*cc;
    if (slp < 20) slp = 20; if (slp > 100) slp = 100;
    if (wk < 0) wk = 0;
    printf "{\\"sleep_score\\": %.0f, \\"wake_count\\": %.1f}", slp + n1*4, wk + n2*0.4;
""",
        "factor_cases": '--room_temp) RT="$2"; shift 2 ;;\n        --screen_cutoff) SC="$2"; shift 2 ;;\n        --caffeine_cutoff) CC="$2"; shift 2 ;;',
        "awk_vars": '-v RT="$RT" -v SC="$SC" -v CC="$CC"',
        "vars_init": 'RT=""\nSC=""\nCC=""',
        "validate": '[ -z "$RT" ] || [ -z "$SC" ] || [ -z "$CC" ]',
    },
    {
        "num": 108, "slug": "running_performance",
        "name": "Running Training Plan",
        "desc": "Box-Behnken design to maximize VO2max improvement and minimize injury risk by tuning weekly mileage, long run percentage, and interval intensity",
        "design": "box_behnken", "category": "health",
        "factors": [
            {"name": "weekly_km", "levels": ["20", "60"], "type": "continuous", "unit": "km", "description": "Total weekly running distance"},
            {"name": "long_run_pct", "levels": ["20", "40"], "type": "continuous", "unit": "%", "description": "Long run as percentage of weekly volume"},
            {"name": "interval_pct_max", "levels": ["80", "100"], "type": "continuous", "unit": "%HR_max", "description": "Interval training intensity as % of max heart rate"},
        ],
        "fixed": {"rest_days": "2", "runner_level": "intermediate"},
        "responses": [
            {"name": "vo2max_gain", "optimize": "maximize", "unit": "mL/kg/min", "description": "VO2max improvement over 12 weeks"},
            {"name": "injury_risk", "optimize": "minimize", "unit": "%", "description": "Estimated injury risk percentage"},
        ],
        "model": """
    wk = (WK - 40) / 20;
    lr = (LR - 30) / 10;
    ip = (IP - 90) / 10;
    vo2 = 3.0 + 1.5*wk + 0.5*lr + 1.2*ip - 0.4*wk*wk - 0.3*lr*lr - 0.5*ip*ip + 0.3*wk*ip;
    inj = 15 + 8*wk + 3*lr + 5*ip + 2*wk*wk + 1.5*ip*ip + 2*wk*lr + 1.5*wk*ip;
    if (vo2 < 0.5) vo2 = 0.5;
    if (inj < 2) inj = 2; if (inj > 60) inj = 60;
    printf "{\\"vo2max_gain\\": %.1f, \\"injury_risk\\": %.0f}", vo2 + n1*0.3, inj + n2*2;
""",
        "factor_cases": '--weekly_km) WK="$2"; shift 2 ;;\n        --long_run_pct) LR="$2"; shift 2 ;;\n        --interval_pct_max) IP="$2"; shift 2 ;;',
        "awk_vars": '-v WK="$WK" -v LR="$LR" -v IP="$IP"',
        "vars_init": 'WK=""\nLR=""\nIP=""',
        "validate": '[ -z "$WK" ] || [ -z "$LR" ] || [ -z "$IP" ]',
    },
    {
        "num": 109, "slug": "strength_training",
        "name": "Strength Training Program",
        "desc": "Full factorial of sets, reps, rest period, and training frequency to maximize strength gain and minimize fatigue score",
        "design": "full_factorial", "category": "health",
        "factors": [
            {"name": "sets", "levels": ["3", "6"], "type": "continuous", "unit": "sets", "description": "Number of sets per exercise"},
            {"name": "reps", "levels": ["3", "12"], "type": "continuous", "unit": "reps", "description": "Repetitions per set"},
            {"name": "rest_sec", "levels": ["60", "180"], "type": "continuous", "unit": "sec", "description": "Rest period between sets"},
            {"name": "freq_per_week", "levels": ["2", "5"], "type": "continuous", "unit": "days/wk", "description": "Training frequency per week"},
        ],
        "fixed": {"exercise": "barbell_squat", "trainee_level": "intermediate"},
        "responses": [
            {"name": "strength_gain", "optimize": "maximize", "unit": "%", "description": "1RM strength gain percentage over 8 weeks"},
            {"name": "fatigue_score", "optimize": "minimize", "unit": "pts", "description": "Accumulated fatigue score (1-10)"},
        ],
        "model": """
    st = (ST - 4.5) / 1.5;
    rp = (RP - 7.5) / 4.5;
    rs = (RS - 120) / 60;
    fq = (FQ - 3.5) / 1.5;
    str_ = 8 + 2*st - 1.5*rp + 1.2*rs + 1.5*fq - 0.5*st*st + 0.8*rp*rp - 0.3*rs*rs - 0.4*fq*fq + 0.5*st*fq;
    fat = 4.5 + 1.2*st + 0.8*rp - 0.6*rs + 1.5*fq + 0.3*st*st + 0.4*st*fq - 0.2*rs*fq;
    if (str_ < 1) str_ = 1;
    if (fat < 1) fat = 1; if (fat > 10) fat = 10;
    printf "{\\"strength_gain\\": %.1f, \\"fatigue_score\\": %.1f}", str_ + n1*1.0, fat + n2*0.4;
""",
        "factor_cases": '--sets) ST="$2"; shift 2 ;;\n        --reps) RP="$2"; shift 2 ;;\n        --rest_sec) RS="$2"; shift 2 ;;\n        --freq_per_week) FQ="$2"; shift 2 ;;',
        "awk_vars": '-v ST="$ST" -v RP="$RP" -v RS="$RS" -v FQ="$FQ"',
        "vars_init": 'ST=""\nRP=""\nRS=""\nFQ=""',
        "validate": '[ -z "$ST" ] || [ -z "$RP" ] || [ -z "$RS" ] || [ -z "$FQ" ]',
    },
    {
        "num": 110, "slug": "meditation_routine",
        "name": "Meditation Routine Effectiveness",
        "desc": "Box-Behnken design to maximize stress reduction and focus improvement by tuning session duration, time of day, and technique",
        "design": "box_behnken", "category": "health",
        "factors": [
            {"name": "duration_min", "levels": ["5", "30"], "type": "continuous", "unit": "min", "description": "Session duration in minutes"},
            {"name": "time_of_day", "levels": ["6", "22"], "type": "continuous", "unit": "hour", "description": "Hour of day for practice (24h format)"},
            {"name": "guided_pct", "levels": ["0", "100"], "type": "continuous", "unit": "%", "description": "Percentage of guided vs silent meditation"},
        ],
        "fixed": {"frequency": "daily", "environment": "quiet_room"},
        "responses": [
            {"name": "stress_reduction", "optimize": "maximize", "unit": "pts", "description": "Perceived stress reduction score (1-10)"},
            {"name": "focus_score", "optimize": "maximize", "unit": "pts", "description": "Sustained attention improvement (1-10)"},
        ],
        "model": """
    dm = (DM - 17.5) / 12.5;
    td = (TD - 14) / 8;
    gp = (GP - 50) / 50;
    stress = 5.5 + 1.5*dm - 0.3*td + 0.5*gp - 0.5*dm*dm + 0.2*td*td - 0.3*gp*gp + 0.3*dm*gp;
    focus = 5.0 + 1.2*dm - 0.5*td - 0.3*gp - 0.4*dm*dm + 0.3*td*td + 0.2*dm*td;
    if (stress < 1) stress = 1; if (stress > 10) stress = 10;
    if (focus < 1) focus = 1; if (focus > 10) focus = 10;
    printf "{\\"stress_reduction\\": %.1f, \\"focus_score\\": %.1f}", stress + n1*0.4, focus + n2*0.3;
""",
        "factor_cases": '--duration_min) DM="$2"; shift 2 ;;\n        --time_of_day) TD="$2"; shift 2 ;;\n        --guided_pct) GP="$2"; shift 2 ;;',
        "awk_vars": '-v DM="$DM" -v TD="$TD" -v GP="$GP"',
        "vars_init": 'DM=""\nTD=""\nGP=""',
        "validate": '[ -z "$DM" ] || [ -z "$TD" ] || [ -z "$GP" ]',
    },
    {
        "num": 111, "slug": "ergonomic_workstation",
        "name": "Ergonomic Workstation Setup",
        "desc": "Central composite design to minimize discomfort and maximize productivity by tuning desk height, monitor distance, chair angle, and break frequency",
        "design": "central_composite", "category": "health",
        "factors": [
            {"name": "desk_height_cm", "levels": ["65", "80"], "type": "continuous", "unit": "cm", "description": "Desk surface height"},
            {"name": "monitor_dist_cm", "levels": ["50", "80"], "type": "continuous", "unit": "cm", "description": "Distance from eyes to monitor"},
            {"name": "chair_recline_deg", "levels": ["90", "115"], "type": "continuous", "unit": "deg", "description": "Chair backrest recline angle"},
            {"name": "break_freq_min", "levels": ["25", "90"], "type": "continuous", "unit": "min", "description": "Minutes between standing breaks"},
        ],
        "fixed": {"monitor_size": "27in", "chair_type": "ergonomic"},
        "responses": [
            {"name": "comfort_score", "optimize": "maximize", "unit": "pts", "description": "End-of-day comfort score (1-10)"},
            {"name": "productivity_pct", "optimize": "maximize", "unit": "%", "description": "Productivity relative to baseline"},
        ],
        "model": """
    dh = (DH - 72.5) / 7.5;
    md = (MD - 65) / 15;
    cr = (CR - 102.5) / 12.5;
    bf = (BF - 57.5) / 32.5;
    comf = 6.0 + 0.3*dh + 0.5*md + 0.8*cr - 0.6*bf - 0.8*dh*dh - 0.4*md*md - 0.3*cr*cr + 0.3*cr*bf;
    prod = 95 + 1*dh + 1.5*md + 0.5*cr - 2*bf - 1.5*dh*dh - 1*md*md + 0.5*md*bf;
    if (comf < 1) comf = 1; if (comf > 10) comf = 10;
    if (prod < 70) prod = 70; if (prod > 115) prod = 115;
    printf "{\\"comfort_score\\": %.1f, \\"productivity_pct\\": %.0f}", comf + n1*0.3, prod + n2*2;
""",
        "factor_cases": '--desk_height_cm) DH="$2"; shift 2 ;;\n        --monitor_dist_cm) MD="$2"; shift 2 ;;\n        --chair_recline_deg) CR="$2"; shift 2 ;;\n        --break_freq_min) BF="$2"; shift 2 ;;',
        "awk_vars": '-v DH="$DH" -v MD="$MD" -v CR="$CR" -v BF="$BF"',
        "vars_init": 'DH=""\nMD=""\nCR=""\nBF=""',
        "validate": '[ -z "$DH" ] || [ -z "$MD" ] || [ -z "$CR" ] || [ -z "$BF" ]',
    },
    {
        "num": 112, "slug": "hydration_strategy",
        "name": "Athletic Hydration Strategy",
        "desc": "Box-Behnken design to maximize endurance performance and minimize GI distress by tuning fluid intake rate, electrolyte concentration, and carbohydrate percentage",
        "design": "box_behnken", "category": "health",
        "factors": [
            {"name": "fluid_ml_hr", "levels": ["200", "800"], "type": "continuous", "unit": "mL/hr", "description": "Fluid intake rate during exercise"},
            {"name": "sodium_mg_L", "levels": ["200", "1000"], "type": "continuous", "unit": "mg/L", "description": "Sodium concentration in drink"},
            {"name": "carb_pct", "levels": ["2", "8"], "type": "continuous", "unit": "%", "description": "Carbohydrate percentage in drink"},
        ],
        "fixed": {"exercise_type": "marathon_training", "ambient_temp": "25C"},
        "responses": [
            {"name": "performance_index", "optimize": "maximize", "unit": "pts", "description": "Endurance performance index (1-100)"},
            {"name": "gi_distress", "optimize": "minimize", "unit": "pts", "description": "GI distress score (1-10)"},
        ],
        "model": """
    fl = (FL - 500) / 300;
    na = (NA - 600) / 400;
    cb = (CB - 5) / 3;
    perf = 72 + 5*fl + 3*na + 4*cb - 3*fl*fl - 1.5*na*na - 2*cb*cb + 1.5*fl*cb + 1*na*cb;
    gi = 3 + 1.5*fl + 0.5*na + 1.2*cb + 0.8*fl*fl + 0.3*cb*cb + 0.5*fl*cb;
    if (perf < 40) perf = 40; if (perf > 100) perf = 100;
    if (gi < 1) gi = 1; if (gi > 10) gi = 10;
    printf "{\\"performance_index\\": %.0f, \\"gi_distress\\": %.1f}", perf + n1*3, gi + n2*0.4;
""",
        "factor_cases": '--fluid_ml_hr) FL="$2"; shift 2 ;;\n        --sodium_mg_L) NA="$2"; shift 2 ;;\n        --carb_pct) CB="$2"; shift 2 ;;',
        "awk_vars": '-v FL="$FL" -v NA="$NA" -v CB="$CB"',
        "vars_init": 'FL=""\nNA=""\nCB=""',
        "validate": '[ -z "$FL" ] || [ -z "$NA" ] || [ -z "$CB" ]',
    },
    {
        "num": 113, "slug": "study_habit",
        "name": "Study Session Optimization",
        "desc": "Full factorial of study block length, break duration, technique, and environment noise level for retention and attention span",
        "design": "full_factorial", "category": "health",
        "factors": [
            {"name": "block_min", "levels": ["15", "50"], "type": "continuous", "unit": "min", "description": "Uninterrupted study block duration"},
            {"name": "break_min", "levels": ["3", "15"], "type": "continuous", "unit": "min", "description": "Break duration between blocks"},
            {"name": "active_recall_pct", "levels": ["0", "100"], "type": "continuous", "unit": "%", "description": "Percentage of time using active recall vs passive reading"},
            {"name": "noise_db", "levels": ["25", "65"], "type": "continuous", "unit": "dB", "description": "Background noise level"},
        ],
        "fixed": {"subject": "biology", "total_hours": "3"},
        "responses": [
            {"name": "retention_pct", "optimize": "maximize", "unit": "%", "description": "48-hour retention percentage on quiz"},
            {"name": "attention_score", "optimize": "maximize", "unit": "pts", "description": "Sustained attention score (1-10)"},
        ],
        "model": """
    bm = (BM - 32.5) / 17.5;
    br = (BR - 9) / 6;
    ar = (AR - 50) / 50;
    nd = (ND - 45) / 20;
    ret = 60 + 3*bm + 2*br + 10*ar - 2*nd - 2*bm*bm - 1*br*br + 1.5*ar*bm - 0.8*nd*nd;
    att = 6.5 - 0.8*bm + 0.6*br + 0.5*ar - 0.7*nd + 0.3*bm*bm + 0.2*bm*br;
    if (ret < 20) ret = 20; if (ret > 100) ret = 100;
    if (att < 1) att = 1; if (att > 10) att = 10;
    printf "{\\"retention_pct\\": %.0f, \\"attention_score\\": %.1f}", ret + n1*4, att + n2*0.4;
""",
        "factor_cases": '--block_min) BM="$2"; shift 2 ;;\n        --break_min) BR="$2"; shift 2 ;;\n        --active_recall_pct) AR="$2"; shift 2 ;;\n        --noise_db) ND="$2"; shift 2 ;;',
        "awk_vars": '-v BM="$BM" -v BR="$BR" -v AR="$AR" -v ND="$ND"',
        "vars_init": 'BM=""\nBR=""\nAR=""\nND=""',
        "validate": '[ -z "$BM" ] || [ -z "$BR" ] || [ -z "$AR" ] || [ -z "$ND" ]',
    },
    {
        "num": 114, "slug": "meal_timing",
        "name": "Meal Timing and Energy Levels",
        "desc": "Fractional factorial screening of meal count, eating window, protein ratio, carb timing, and meal size distribution for sustained energy and afternoon alertness",
        "design": "fractional_factorial", "category": "health",
        "factors": [
            {"name": "meals_per_day", "levels": ["2", "6"], "type": "continuous", "unit": "meals", "description": "Number of meals per day"},
            {"name": "eating_window_hrs", "levels": ["8", "16"], "type": "continuous", "unit": "hrs", "description": "Daily eating window duration"},
            {"name": "protein_pct", "levels": ["15", "35"], "type": "continuous", "unit": "%", "description": "Protein as percentage of total calories"},
            {"name": "morning_cal_pct", "levels": ["20", "50"], "type": "continuous", "unit": "%", "description": "Percentage of calories consumed before noon"},
            {"name": "fiber_g", "levels": ["15", "40"], "type": "continuous", "unit": "g", "description": "Daily fiber intake in grams"},
        ],
        "fixed": {"total_calories": "2200", "activity_level": "moderate"},
        "responses": [
            {"name": "energy_score", "optimize": "maximize", "unit": "pts", "description": "Sustained energy throughout day (1-10)"},
            {"name": "afternoon_alertness", "optimize": "maximize", "unit": "pts", "description": "2-4 PM alertness score (1-10)"},
        ],
        "model": """
    mp = (MP - 4) / 2;
    ew = (EW - 12) / 4;
    pp = (PP - 25) / 10;
    mc = (MC - 35) / 15;
    fb = (FB - 27.5) / 12.5;
    eng = 6.0 + 0.5*mp + 0.3*ew + 0.8*pp + 0.4*mc + 0.3*fb + 0.2*mp*ew + 0.15*pp*mc;
    alert = 5.5 + 0.4*mp - 0.3*ew + 0.6*pp + 0.8*mc + 0.2*fb + 0.2*pp*fb - 0.3*ew*mc;
    if (eng < 1) eng = 1; if (eng > 10) eng = 10;
    if (alert < 1) alert = 1; if (alert > 10) alert = 10;
    printf "{\\"energy_score\\": %.1f, \\"afternoon_alertness\\": %.1f}", eng + n1*0.4, alert + n2*0.3;
""",
        "factor_cases": '--meals_per_day) MP="$2"; shift 2 ;;\n        --eating_window_hrs) EW="$2"; shift 2 ;;\n        --protein_pct) PP="$2"; shift 2 ;;\n        --morning_cal_pct) MC="$2"; shift 2 ;;\n        --fiber_g) FB="$2"; shift 2 ;;',
        "awk_vars": '-v MP="$MP" -v EW="$EW" -v PP="$PP" -v MC="$MC" -v FB="$FB"',
        "vars_init": 'MP=""\nEW=""\nPP=""\nMC=""\nFB=""',
        "validate": '[ -z "$MP" ] || [ -z "$EW" ] || [ -z "$PP" ] || [ -z "$MC" ]',
    },
    {
        "num": 115, "slug": "stretching_protocol",
        "name": "Stretching Protocol Design",
        "desc": "Box-Behnken design to maximize flexibility gain and minimize soreness by tuning hold duration, session frequency, and warmup intensity",
        "design": "box_behnken", "category": "health",
        "factors": [
            {"name": "hold_sec", "levels": ["10", "60"], "type": "continuous", "unit": "sec", "description": "Hold duration per stretch"},
            {"name": "sessions_per_week", "levels": ["2", "7"], "type": "continuous", "unit": "per_week", "description": "Stretching sessions per week"},
            {"name": "warmup_min", "levels": ["0", "15"], "type": "continuous", "unit": "min", "description": "Warmup duration before stretching"},
        ],
        "fixed": {"stretch_type": "static", "target_area": "hamstrings"},
        "responses": [
            {"name": "flexibility_gain", "optimize": "maximize", "unit": "cm", "description": "Sit-and-reach improvement in cm over 6 weeks"},
            {"name": "soreness", "optimize": "minimize", "unit": "pts", "description": "Post-session soreness score (1-10)"},
        ],
        "model": """
    hs = (HS - 35) / 25;
    sf = (SF - 4.5) / 2.5;
    wm = (WM - 7.5) / 7.5;
    flex = 4.0 + 1.5*hs + 1.2*sf + 0.5*wm - 0.4*hs*hs - 0.3*sf*sf + 0.3*hs*sf + 0.2*sf*wm;
    sore = 3.5 + 1.0*hs + 0.5*sf - 0.8*wm + 0.3*hs*hs + 0.2*hs*sf - 0.3*wm*sf;
    if (flex < 0.5) flex = 0.5;
    if (sore < 1) sore = 1; if (sore > 10) sore = 10;
    printf "{\\"flexibility_gain\\": %.1f, \\"soreness\\": %.1f}", flex + n1*0.5, sore + n2*0.3;
""",
        "factor_cases": '--hold_sec) HS="$2"; shift 2 ;;\n        --sessions_per_week) SF="$2"; shift 2 ;;\n        --warmup_min) WM="$2"; shift 2 ;;',
        "awk_vars": '-v HS="$HS" -v SF="$SF" -v WM="$WM"',
        "vars_init": 'HS=""\nSF=""\nWM=""',
        "validate": '[ -z "$HS" ] || [ -z "$SF" ] || [ -z "$WM" ]',
    },
    {
        "num": 116, "slug": "sunscreen_formulation",
        "name": "Sunscreen SPF Formulation",
        "desc": "Central composite design to maximize SPF protection and minimize greasiness by tuning zinc oxide concentration, moisturizer ratio, and application thickness",
        "design": "central_composite", "category": "health",
        "factors": [
            {"name": "zinc_oxide_pct", "levels": ["5", "25"], "type": "continuous", "unit": "%", "description": "Zinc oxide concentration"},
            {"name": "moisturizer_pct", "levels": ["10", "40"], "type": "continuous", "unit": "%", "description": "Moisturizer percentage in formula"},
            {"name": "thickness_mg_cm2", "levels": ["1.0", "2.5"], "type": "continuous", "unit": "mg/cm2", "description": "Application thickness"},
        ],
        "fixed": {"base_type": "cream", "uva_filter": "avobenzone"},
        "responses": [
            {"name": "spf_value", "optimize": "maximize", "unit": "SPF", "description": "Measured SPF value"},
            {"name": "greasiness", "optimize": "minimize", "unit": "pts", "description": "Greasiness score (1-10)"},
        ],
        "model": """
    zo = (ZO - 15) / 10;
    mp = (MP - 25) / 15;
    th = (TH - 1.75) / 0.75;
    spf = 30 + 12*zo + 2*mp + 8*th - 3*zo*zo - 1*mp*mp + 2*zo*th + 1*mp*th;
    grs = 4.5 + 1.5*zo + 1.8*mp + 0.5*th + 0.3*zo*zo + 0.2*mp*mp + 0.4*zo*mp;
    if (spf < 5) spf = 5;
    if (grs < 1) grs = 1; if (grs > 10) grs = 10;
    printf "{\\"spf_value\\": %.0f, \\"greasiness\\": %.1f}", spf + n1*2, grs + n2*0.3;
""",
        "factor_cases": '--zinc_oxide_pct) ZO="$2"; shift 2 ;;\n        --moisturizer_pct) MP="$2"; shift 2 ;;\n        --thickness_mg_cm2) TH="$2"; shift 2 ;;',
        "awk_vars": '-v ZO="$ZO" -v MP="$MP" -v TH="$TH"',
        "vars_init": 'ZO=""\nMP=""\nTH=""',
        "validate": '[ -z "$ZO" ] || [ -z "$MP" ] || [ -z "$TH" ]',
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
            "test_script": f"use_cases/{num:02d}_{slug}/sim.sh",
            "operation": uc["design"],
            "processed_directory": f"use_cases/{num:02d}_{slug}/results/analysis",
            "out_directory": f"use_cases/{num:02d}_{slug}/results",
        },
    }


def main():
    for uc in USE_CASES:
        num = uc["num"]
        slug = uc["slug"]
        uc_dir = f"use_cases/{num:02d}_{slug}"
        os.makedirs(uc_dir, exist_ok=True)
        os.makedirs(os.path.join(uc_dir, "results"), exist_ok=True)

        # Write config.json
        config = build_config(uc)
        config_path = os.path.join(uc_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        # Write sim.sh
        sim_script = build_sim_script(uc)
        sim_path = os.path.join(uc_dir, "sim.sh")
        with open(sim_path, "w") as f:
            f.write(sim_script)
        os.chmod(sim_path, os.stat(sim_path).st_mode | stat.S_IEXEC)

        print(f"  [{num:03d}] {uc_dir}/")

    print(f"\n  {len(USE_CASES)} use cases created (87-116).")


if __name__ == "__main__":
    main()
