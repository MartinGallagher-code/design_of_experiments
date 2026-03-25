#!/usr/bin/env python3
"""Generate 52 new use cases (147-198).

Categories:
  - Photography & Optics (147-156)
  - Music & Audio (157-166)
  - Pet Care & Animal Science (167-176)
  - Textiles & Fashion (177-186)
  - Chemistry & Lab Science (187-196)
  - General (197-198)
"""
import json, os, stat, textwrap

USE_CASES = [
    # ══════════════════════════════════════════════════
    # Photography & Optics (147-156)
    # ══════════════════════════════════════════════════
    {"num": 147, "slug": "landscape_exposure", "name": "Landscape Photo Exposure",
     "desc": "Box-Behnken design to maximize dynamic range and minimize noise by tuning ISO, aperture, and shutter speed",
     "design": "box_behnken", "category": "photography",
     "factors": [
         {"name": "iso", "levels": ["100", "3200"], "type": "continuous", "unit": "ISO", "description": "Sensor sensitivity"},
         {"name": "aperture", "levels": ["2.8", "16"], "type": "continuous", "unit": "f-stop", "description": "Lens aperture f-number"},
         {"name": "shutter_speed_ms", "levels": ["1", "1000"], "type": "continuous", "unit": "ms", "description": "Shutter speed in milliseconds"},
     ],
     "fixed": {"lens_mm": "24", "white_balance": "daylight"},
     "responses": [
         {"name": "dynamic_range_ev", "optimize": "maximize", "unit": "EV", "description": "Usable dynamic range in stops"},
         {"name": "noise_score", "optimize": "minimize", "unit": "pts", "description": "Luminance noise score (1-10)"},
     ],
     "model": """
    iso_ = (ISO - 1650) / 1550;
    ap = (AP - 9.4) / 6.6;
    ss = (SS - 500.5) / 499.5;
    dr = 11 - 2*iso_ + 1.5*ap + 0.5*ss - 0.8*iso_*iso_ - 0.5*ap*ap + 0.3*iso_*ap;
    noise = 3 + 3*iso_ - 0.5*ap + 0.2*ss + 1*iso_*iso_ + 0.3*iso_*ss;
    if (dr < 5) dr = 5; if (dr > 15) dr = 15;
    if (noise < 1) noise = 1; if (noise > 10) noise = 10;
    printf "{\\"dynamic_range_ev\\": %.1f, \\"noise_score\\": %.1f}", dr + n1*0.3, noise + n2*0.3;
""",
     "factor_cases": '--iso) ISO="$2"; shift 2 ;;\n        --aperture) AP="$2"; shift 2 ;;\n        --shutter_speed_ms) SS="$2"; shift 2 ;;',
     "awk_vars": '-v ISO="$ISO" -v AP="$AP" -v SS="$SS"',
     "vars_init": 'ISO=""\nAP=""\nSS=""', "validate": '[ -z "$ISO" ] || [ -z "$AP" ] || [ -z "$SS" ]'},

    {"num": 148, "slug": "studio_lighting", "name": "Studio Portrait Lighting",
     "desc": "Central composite design to maximize skin tone accuracy and minimize harsh shadows by tuning key light power, fill ratio, and modifier size",
     "design": "central_composite", "category": "photography",
     "factors": [
         {"name": "key_power_ws", "levels": ["100", "500"], "type": "continuous", "unit": "Ws", "description": "Key light power in watt-seconds"},
         {"name": "fill_ratio", "levels": ["2", "8"], "type": "continuous", "unit": "ratio", "description": "Key-to-fill light ratio"},
         {"name": "modifier_cm", "levels": ["60", "150"], "type": "continuous", "unit": "cm", "description": "Light modifier diameter"},
     ],
     "fixed": {"background": "grey", "distance_m": "2"},
     "responses": [
         {"name": "skin_accuracy", "optimize": "maximize", "unit": "pts", "description": "Skin tone color accuracy (1-10)"},
         {"name": "shadow_harshness", "optimize": "minimize", "unit": "pts", "description": "Shadow transition harshness (1-10)"},
     ],
     "model": """
    kp = (KP - 300) / 200;
    fr = (FR - 5) / 3;
    mc = (MC - 105) / 45;
    skin = 7.0 + 0.5*kp - 0.8*fr + 0.6*mc - 0.6*kp*kp - 0.3*fr*fr + 0.2*kp*mc;
    shadow = 5.0 + 0.5*kp + 1.2*fr - 1.5*mc + 0.3*kp*kp + 0.2*fr*fr + 0.3*kp*fr;
    if (skin < 1) skin = 1; if (skin > 10) skin = 10;
    if (shadow < 1) shadow = 1; if (shadow > 10) shadow = 10;
    printf "{\\"skin_accuracy\\": %.1f, \\"shadow_harshness\\": %.1f}", skin + n1*0.3, shadow + n2*0.3;
""",
     "factor_cases": '--key_power_ws) KP="$2"; shift 2 ;;\n        --fill_ratio) FR="$2"; shift 2 ;;\n        --modifier_cm) MC="$2"; shift 2 ;;',
     "awk_vars": '-v KP="$KP" -v FR="$FR" -v MC="$MC"',
     "vars_init": 'KP=""\nFR=""\nMC=""', "validate": '[ -z "$KP" ] || [ -z "$FR" ] || [ -z "$MC" ]'},

    {"num": 149, "slug": "lens_sharpness", "name": "Lens Sharpness Testing",
     "desc": "Full factorial of aperture, focal length, focus distance, and image stabilization to maximize center sharpness and minimize corner softness",
     "design": "full_factorial", "category": "photography",
     "factors": [
         {"name": "aperture_f", "levels": ["2.8", "11"], "type": "continuous", "unit": "f-stop", "description": "Aperture f-number"},
         {"name": "focal_length", "levels": ["24", "70"], "type": "continuous", "unit": "mm", "description": "Focal length"},
         {"name": "focus_dist_m", "levels": ["1", "10"], "type": "continuous", "unit": "m", "description": "Focus distance"},
         {"name": "stabilization", "levels": ["off", "on"], "type": "categorical", "unit": "", "description": "Image stabilization"},
     ],
     "fixed": {"body": "full_frame", "iso": "200"},
     "responses": [
         {"name": "center_lpmm", "optimize": "maximize", "unit": "lp/mm", "description": "Center resolution in line pairs per mm"},
         {"name": "corner_falloff_pct", "optimize": "minimize", "unit": "%", "description": "Corner sharpness falloff percentage"},
     ],
     "model": """
    af = (AF - 6.9) / 4.1;
    fl = (FL - 47) / 23;
    fd = (FD - 5.5) / 4.5;
    st = (ST == "on") ? 1 : -1;
    center = 80 + 5*af - 3*fl + 2*fd + 3*st - 8*af*af + 2*fl*fl + 1*af*fl;
    corner = 25 - 8*af + 5*fl - 2*fd + 1*st + 5*af*af + 2*fl*fl;
    if (center < 30) center = 30; if (center > 120) center = 120;
    if (corner < 5) corner = 5; if (corner > 60) corner = 60;
    printf "{\\"center_lpmm\\": %.0f, \\"corner_falloff_pct\\": %.0f}", center + n1*3, corner + n2*2;
""",
     "factor_cases": '--aperture_f) AF="$2"; shift 2 ;;\n        --focal_length) FL="$2"; shift 2 ;;\n        --focus_dist_m) FD="$2"; shift 2 ;;\n        --stabilization) ST="$2"; shift 2 ;;',
     "awk_vars": '-v AF="$AF" -v FL="$FL" -v FD="$FD" -v ST="$ST"',
     "vars_init": 'AF=""\nFL=""\nFD=""\nST=""', "validate": '[ -z "$AF" ] || [ -z "$FL" ] || [ -z "$FD" ] || [ -z "$ST" ]'},

    {"num": 150, "slug": "timelapse_settings", "name": "Timelapse Interval Settings",
     "desc": "Box-Behnken design to maximize smoothness and minimize flicker by tuning capture interval, exposure ramp rate, and deflicker strength",
     "design": "box_behnken", "category": "photography",
     "factors": [
         {"name": "interval_sec", "levels": ["2", "30"], "type": "continuous", "unit": "sec", "description": "Capture interval between frames"},
         {"name": "ramp_rate", "levels": ["0.1", "2.0"], "type": "continuous", "unit": "EV/min", "description": "Exposure ramping rate for sunset transitions"},
         {"name": "deflicker_pct", "levels": ["0", "100"], "type": "continuous", "unit": "%", "description": "Deflicker processing strength"},
     ],
     "fixed": {"resolution": "4K", "codec": "h265"},
     "responses": [
         {"name": "smoothness", "optimize": "maximize", "unit": "pts", "description": "Motion smoothness score (1-10)"},
         {"name": "flicker_score", "optimize": "minimize", "unit": "pts", "description": "Visible flicker intensity (1-10)"},
     ],
     "model": """
    iv = (IV - 16) / 14;
    rr = (RR - 1.05) / 0.95;
    df = (DF - 50) / 50;
    smooth = 6.5 - 1.5*iv + 0.3*rr + 0.5*df - 0.4*iv*iv + 0.2*iv*df;
    flick = 4.0 + 0.5*iv + 1.2*rr - 2.0*df + 0.3*rr*rr + 0.4*df*df + 0.5*rr*df;
    if (smooth < 1) smooth = 1; if (smooth > 10) smooth = 10;
    if (flick < 1) flick = 1; if (flick > 10) flick = 10;
    printf "{\\"smoothness\\": %.1f, \\"flicker_score\\": %.1f}", smooth + n1*0.3, flick + n2*0.3;
""",
     "factor_cases": '--interval_sec) IV="$2"; shift 2 ;;\n        --ramp_rate) RR="$2"; shift 2 ;;\n        --deflicker_pct) DF="$2"; shift 2 ;;',
     "awk_vars": '-v IV="$IV" -v RR="$RR" -v DF="$DF"',
     "vars_init": 'IV=""\nRR=""\nDF=""', "validate": '[ -z "$IV" ] || [ -z "$RR" ] || [ -z "$DF" ]'},

    {"num": 151, "slug": "microscope_imaging", "name": "Microscope Imaging Quality",
     "desc": "Central composite design to maximize resolution and minimize chromatic aberration by tuning objective magnification, illumination intensity, and condenser aperture",
     "design": "central_composite", "category": "photography",
     "factors": [
         {"name": "magnification", "levels": ["10", "100"], "type": "continuous", "unit": "x", "description": "Objective magnification"},
         {"name": "illumination_pct", "levels": ["20", "100"], "type": "continuous", "unit": "%", "description": "Illumination intensity percentage"},
         {"name": "condenser_na", "levels": ["0.2", "0.9"], "type": "continuous", "unit": "NA", "description": "Condenser numerical aperture"},
     ],
     "fixed": {"specimen": "stained_tissue", "camera": "cmos_sensor"},
     "responses": [
         {"name": "resolution_um", "optimize": "minimize", "unit": "um", "description": "Minimum resolvable feature size in microns"},
         {"name": "aberration_score", "optimize": "minimize", "unit": "pts", "description": "Chromatic aberration score (1-10)"},
     ],
     "model": """
    mg = (MG - 55) / 45;
    il = (IL - 60) / 40;
    cn = (CN - 0.55) / 0.35;
    res = 2.0 - 0.8*mg - 0.2*il - 0.3*cn + 0.3*mg*mg + 0.1*il*il;
    aber = 4.0 + 1.5*mg + 0.5*il + 0.3*cn + 0.4*mg*mg - 0.2*cn*cn + 0.3*mg*il;
    if (res < 0.2) res = 0.2;
    if (aber < 1) aber = 1; if (aber > 10) aber = 10;
    printf "{\\"resolution_um\\": %.2f, \\"aberration_score\\": %.1f}", res + n1*0.1, aber + n2*0.3;
""",
     "factor_cases": '--magnification) MG="$2"; shift 2 ;;\n        --illumination_pct) IL="$2"; shift 2 ;;\n        --condenser_na) CN="$2"; shift 2 ;;',
     "awk_vars": '-v MG="$MG" -v IL="$IL" -v CN="$CN"',
     "vars_init": 'MG=""\nIL=""\nCN=""', "validate": '[ -z "$MG" ] || [ -z "$IL" ] || [ -z "$CN" ]'},

    {"num": 152, "slug": "film_development", "name": "Film Development Process",
     "desc": "Box-Behnken design to maximize tonal range and minimize grain by tuning developer temperature, agitation frequency, and development time",
     "design": "box_behnken", "category": "photography",
     "factors": [
         {"name": "dev_temp_c", "levels": ["18", "24"], "type": "continuous", "unit": "C", "description": "Developer temperature"},
         {"name": "agitation_per_min", "levels": ["1", "6"], "type": "continuous", "unit": "inversions/min", "description": "Agitation inversions per minute"},
         {"name": "dev_time_min", "levels": ["6", "14"], "type": "continuous", "unit": "min", "description": "Development time"},
     ],
     "fixed": {"film_type": "ilford_hp5", "developer": "rodinal"},
     "responses": [
         {"name": "tonal_range", "optimize": "maximize", "unit": "zones", "description": "Usable tonal zones (out of 10)"},
         {"name": "grain_score", "optimize": "minimize", "unit": "pts", "description": "Visible grain score (1-10)"},
     ],
     "model": """
    dt = (DT - 21) / 3;
    ag = (AG - 3.5) / 2.5;
    dm = (DM - 10) / 4;
    tonal = 7.0 + 0.5*dt + 0.3*ag + 0.8*dm - 0.4*dt*dt - 0.3*ag*ag - 0.5*dm*dm + 0.2*dt*dm;
    grain = 4.0 + 0.8*dt + 0.6*ag + 0.4*dm + 0.3*dt*dt + 0.2*ag*ag + 0.2*dt*ag;
    if (tonal < 3) tonal = 3; if (tonal > 10) tonal = 10;
    if (grain < 1) grain = 1; if (grain > 10) grain = 10;
    printf "{\\"tonal_range\\": %.1f, \\"grain_score\\": %.1f}", tonal + n1*0.3, grain + n2*0.3;
""",
     "factor_cases": '--dev_temp_c) DT="$2"; shift 2 ;;\n        --agitation_per_min) AG="$2"; shift 2 ;;\n        --dev_time_min) DM="$2"; shift 2 ;;',
     "awk_vars": '-v DT="$DT" -v AG="$AG" -v DM="$DM"',
     "vars_init": 'DT=""\nAG=""\nDM=""', "validate": '[ -z "$DT" ] || [ -z "$AG" ] || [ -z "$DM" ]'},

    {"num": 153, "slug": "telescope_observation", "name": "Telescope Observation Quality",
     "desc": "Plackett-Burman screening of aperture, focal ratio, eyepiece focal length, tracking rate, and cooling time for image sharpness and limiting magnitude",
     "design": "plackett_burman", "category": "photography",
     "factors": [
         {"name": "aperture_mm", "levels": ["80", "300"], "type": "continuous", "unit": "mm", "description": "Primary mirror/lens aperture"},
         {"name": "focal_ratio", "levels": ["4", "12"], "type": "continuous", "unit": "f/", "description": "Focal ratio"},
         {"name": "eyepiece_mm", "levels": ["6", "25"], "type": "continuous", "unit": "mm", "description": "Eyepiece focal length"},
         {"name": "tracking_rate", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "arcsec/s", "description": "Mount tracking accuracy"},
         {"name": "cooldown_min", "levels": ["15", "90"], "type": "continuous", "unit": "min", "description": "Thermal equilibration cooldown time"},
     ],
     "fixed": {"mount_type": "equatorial", "site": "suburban"},
     "responses": [
         {"name": "sharpness", "optimize": "maximize", "unit": "pts", "description": "Image sharpness score (1-10)"},
         {"name": "limiting_mag", "optimize": "maximize", "unit": "mag", "description": "Limiting stellar magnitude"},
     ],
     "model": """
    ap = (AP - 190) / 110;
    fr = (FR - 8) / 4;
    ep = (EP - 15.5) / 9.5;
    tr = (TR - 1.25) / 0.75;
    cd = (CD - 52.5) / 37.5;
    sharp = 6.0 + 0.8*ap + 0.5*fr - 0.3*ep - 1.0*tr + 0.6*cd + 0.2*ap*cd;
    mag = 11 + 1.5*ap + 0.3*fr - 0.2*ep - 0.5*tr + 0.3*cd + 0.2*ap*fr;
    if (sharp < 1) sharp = 1; if (sharp > 10) sharp = 10;
    if (mag < 8) mag = 8;
    printf "{\\"sharpness\\": %.1f, \\"limiting_mag\\": %.1f}", sharp + n1*0.3, mag + n2*0.2;
""",
     "factor_cases": '--aperture_mm) AP="$2"; shift 2 ;;\n        --focal_ratio) FR="$2"; shift 2 ;;\n        --eyepiece_mm) EP="$2"; shift 2 ;;\n        --tracking_rate) TR="$2"; shift 2 ;;\n        --cooldown_min) CD="$2"; shift 2 ;;',
     "awk_vars": '-v AP="$AP" -v FR="$FR" -v EP="$EP" -v TR="$TR" -v CD="$CD"',
     "vars_init": 'AP=""\nFR=""\nEP=""\nTR=""\nCD=""', "validate": '[ -z "$AP" ] || [ -z "$FR" ] || [ -z "$EP" ] || [ -z "$TR" ]'},

    {"num": 154, "slug": "drone_aerial_photo", "name": "Drone Aerial Photography",
     "desc": "Full factorial of altitude, gimbal angle, flight speed, and overlap percentage to maximize ground resolution and minimize motion blur",
     "design": "full_factorial", "category": "photography",
     "factors": [
         {"name": "altitude_m", "levels": ["30", "120"], "type": "continuous", "unit": "m", "description": "Flight altitude"},
         {"name": "gimbal_angle", "levels": ["-90", "-45"], "type": "continuous", "unit": "deg", "description": "Camera gimbal pitch angle"},
         {"name": "flight_speed", "levels": ["2", "12"], "type": "continuous", "unit": "m/s", "description": "Horizontal flight speed"},
         {"name": "overlap_pct", "levels": ["60", "85"], "type": "continuous", "unit": "%", "description": "Image overlap for stitching"},
     ],
     "fixed": {"camera": "1inch_sensor", "wind": "light"},
     "responses": [
         {"name": "gsd_cm", "optimize": "minimize", "unit": "cm/px", "description": "Ground sample distance in cm per pixel"},
         {"name": "blur_score", "optimize": "minimize", "unit": "pts", "description": "Motion blur score (1-10)"},
     ],
     "model": """
    al = (AL - 75) / 45;
    ga = (GA - -67.5) / 22.5;
    fs = (FS - 7) / 5;
    op = (OP - 72.5) / 12.5;
    gsd = 2.5 + 1.5*al + 0.3*ga + 0.1*fs - 0.2*op;
    blur = 3.0 + 0.3*al - 0.5*ga + 1.5*fs - 0.2*op + 0.3*fs*fs + 0.2*al*fs;
    if (gsd < 0.5) gsd = 0.5;
    if (blur < 1) blur = 1; if (blur > 10) blur = 10;
    printf "{\\"gsd_cm\\": %.1f, \\"blur_score\\": %.1f}", gsd + n1*0.2, blur + n2*0.3;
""",
     "factor_cases": '--altitude_m) AL="$2"; shift 2 ;;\n        --gimbal_angle) GA="$2"; shift 2 ;;\n        --flight_speed) FS="$2"; shift 2 ;;\n        --overlap_pct) OP="$2"; shift 2 ;;',
     "awk_vars": '-v AL="$AL" -v GA="$GA" -v FS="$FS" -v OP="$OP"',
     "vars_init": 'AL=""\nGA=""\nFS=""\nOP=""', "validate": '[ -z "$AL" ] || [ -z "$GA" ] || [ -z "$FS" ] || [ -z "$OP" ]'},

    {"num": 155, "slug": "photo_print_color", "name": "Photo Print Color Accuracy",
     "desc": "Box-Behnken design to maximize color accuracy and minimize ink cost by tuning color profile, ink density, and paper type brightness",
     "design": "box_behnken", "category": "photography",
     "factors": [
         {"name": "profile_gamma", "levels": ["1.8", "2.4"], "type": "continuous", "unit": "gamma", "description": "ICC profile gamma value"},
         {"name": "ink_density_pct", "levels": ["80", "120"], "type": "continuous", "unit": "%", "description": "Ink density relative to default"},
         {"name": "paper_brightness", "levels": ["90", "100"], "type": "continuous", "unit": "ISO", "description": "Paper brightness ISO value"},
     ],
     "fixed": {"printer": "inkjet_8color", "resolution_dpi": "1440"},
     "responses": [
         {"name": "delta_e", "optimize": "minimize", "unit": "dE", "description": "Average Delta-E color difference"},
         {"name": "ink_ml", "optimize": "minimize", "unit": "mL/m2", "description": "Ink consumption per square meter"},
     ],
     "model": """
    pg = (PG - 2.1) / 0.3;
    id = (ID - 100) / 20;
    pb = (PB - 95) / 5;
    de = 5.0 + 1.2*pg + 0.5*id - 0.8*pb + 0.8*pg*pg + 0.3*id*id + 0.2*pg*id;
    ink = 8.0 + 0.3*pg + 2.5*id + 0.1*pb + 0.5*id*id;
    if (de < 0.5) de = 0.5;
    if (ink < 3) ink = 3;
    printf "{\\"delta_e\\": %.1f, \\"ink_ml\\": %.1f}", de + n1*0.3, ink + n2*0.4;
""",
     "factor_cases": '--profile_gamma) PG="$2"; shift 2 ;;\n        --ink_density_pct) ID="$2"; shift 2 ;;\n        --paper_brightness) PB="$2"; shift 2 ;;',
     "awk_vars": '-v PG="$PG" -v ID="$ID" -v PB="$PB"',
     "vars_init": 'PG=""\nID=""\nPB=""', "validate": '[ -z "$PG" ] || [ -z "$ID" ] || [ -z "$PB" ]'},

    {"num": 156, "slug": "video_encoding", "name": "Video Encoding Quality",
     "desc": "Central composite design to maximize visual quality and minimize file size by tuning bitrate, CRF value, and GOP length",
     "design": "central_composite", "category": "photography",
     "factors": [
         {"name": "bitrate_mbps", "levels": ["5", "50"], "type": "continuous", "unit": "Mbps", "description": "Target video bitrate"},
         {"name": "crf", "levels": ["18", "28"], "type": "continuous", "unit": "CRF", "description": "Constant rate factor (lower = better)"},
         {"name": "gop_frames", "levels": ["15", "120"], "type": "continuous", "unit": "frames", "description": "Group of pictures length"},
     ],
     "fixed": {"codec": "h265", "resolution": "4K"},
     "responses": [
         {"name": "vmaf_score", "optimize": "maximize", "unit": "VMAF", "description": "Video quality metric (0-100)"},
         {"name": "file_size_mb", "optimize": "minimize", "unit": "MB/min", "description": "File size per minute of video"},
     ],
     "model": """
    br = (BR - 27.5) / 22.5;
    cf = (CF - 23) / 5;
    gp = (GP - 67.5) / 52.5;
    vmaf = 85 + 5*br - 6*cf + 0.5*gp - 1.5*br*br - 2*cf*cf + 1*br*cf;
    fsize = 200 + 120*br - 40*cf - 10*gp + 20*br*br;
    if (vmaf < 50) vmaf = 50; if (vmaf > 100) vmaf = 100;
    if (fsize < 30) fsize = 30;
    printf "{\\"vmaf_score\\": %.0f, \\"file_size_mb\\": %.0f}", vmaf + n1*1.5, fsize + n2*10;
""",
     "factor_cases": '--bitrate_mbps) BR="$2"; shift 2 ;;\n        --crf) CF="$2"; shift 2 ;;\n        --gop_frames) GP="$2"; shift 2 ;;',
     "awk_vars": '-v BR="$BR" -v CF="$CF" -v GP="$GP"',
     "vars_init": 'BR=""\nCF=""\nGP=""', "validate": '[ -z "$BR" ] || [ -z "$CF" ] || [ -z "$GP" ]'},

    # ══════════════════════════════════════════════════
    # Music & Audio (157-166)
    # ══════════════════════════════════════════════════
    {"num": 157, "slug": "guitar_string_tone", "name": "Guitar String Tone Optimization",
     "desc": "Box-Behnken design to maximize brightness and sustain by tuning string gauge, action height, and pickup height",
     "design": "box_behnken", "category": "music",
     "factors": [
         {"name": "gauge_thou", "levels": ["9", "13"], "type": "continuous", "unit": "thou", "description": "High E string gauge in thousandths of an inch"},
         {"name": "action_mm", "levels": ["1.5", "3.0"], "type": "continuous", "unit": "mm", "description": "String action height at 12th fret"},
         {"name": "pickup_mm", "levels": ["2", "5"], "type": "continuous", "unit": "mm", "description": "Pickup distance from strings"},
     ],
     "fixed": {"guitar_type": "solid_body", "tuning": "standard"},
     "responses": [
         {"name": "brightness", "optimize": "maximize", "unit": "pts", "description": "Tonal brightness score (1-10)"},
         {"name": "sustain_sec", "optimize": "maximize", "unit": "sec", "description": "Note sustain duration"},
     ],
     "model": """
    ga = (GA - 11) / 2;
    ac = (AC - 2.25) / 0.75;
    pk = (PK - 3.5) / 1.5;
    bright = 6.5 - 1.2*ga + 0.5*ac - 0.8*pk + 0.3*ga*ga + 0.2*ac*pk;
    sust = 4.0 + 0.8*ga + 0.5*ac + 0.3*pk - 0.3*ga*ga - 0.2*ac*ac + 0.2*ga*ac;
    if (bright < 1) bright = 1; if (bright > 10) bright = 10;
    if (sust < 1) sust = 1;
    printf "{\\"brightness\\": %.1f, \\"sustain_sec\\": %.1f}", bright + n1*0.3, sust + n2*0.3;
""",
     "factor_cases": '--gauge_thou) GA="$2"; shift 2 ;;\n        --action_mm) AC="$2"; shift 2 ;;\n        --pickup_mm) PK="$2"; shift 2 ;;',
     "awk_vars": '-v GA="$GA" -v AC="$AC" -v PK="$PK"',
     "vars_init": 'GA=""\nAC=""\nPK=""', "validate": '[ -z "$GA" ] || [ -z "$AC" ] || [ -z "$PK" ]'},

    {"num": 158, "slug": "room_acoustics", "name": "Room Acoustics Treatment",
     "desc": "Central composite design to optimize RT60 reverb time and minimize flutter echo by tuning absorption panel area, diffuser coverage, and bass trap count",
     "design": "central_composite", "category": "music",
     "factors": [
         {"name": "absorption_m2", "levels": ["4", "20"], "type": "continuous", "unit": "m2", "description": "Total absorption panel area"},
         {"name": "diffuser_m2", "levels": ["2", "12"], "type": "continuous", "unit": "m2", "description": "Diffuser panel area"},
         {"name": "bass_traps", "levels": ["2", "8"], "type": "continuous", "unit": "count", "description": "Number of corner bass traps"},
     ],
     "fixed": {"room_m3": "50", "purpose": "mixing_studio"},
     "responses": [
         {"name": "rt60_ms", "optimize": "minimize", "unit": "ms", "description": "RT60 reverb time in milliseconds (target ~300ms)"},
         {"name": "flutter_echo", "optimize": "minimize", "unit": "pts", "description": "Flutter echo intensity (1-10)"},
     ],
     "model": """
    ab = (AB - 12) / 8;
    df = (DF - 7) / 5;
    bt = (BT - 5) / 3;
    rt = 500 - 100*ab - 30*df - 40*bt + 20*ab*ab + 10*df*df + 5*ab*df;
    flut = 5.0 - 1.0*ab - 1.5*df - 0.3*bt + 0.3*ab*ab + 0.5*df*df + 0.2*ab*df;
    if (rt < 100) rt = 100;
    if (flut < 1) flut = 1; if (flut > 10) flut = 10;
    printf "{\\"rt60_ms\\": %.0f, \\"flutter_echo\\": %.1f}", rt + n1*15, flut + n2*0.3;
""",
     "factor_cases": '--absorption_m2) AB="$2"; shift 2 ;;\n        --diffuser_m2) DF="$2"; shift 2 ;;\n        --bass_traps) BT="$2"; shift 2 ;;',
     "awk_vars": '-v AB="$AB" -v DF="$DF" -v BT="$BT"',
     "vars_init": 'AB=""\nDF=""\nBT=""', "validate": '[ -z "$AB" ] || [ -z "$DF" ] || [ -z "$BT" ]'},

    {"num": 159, "slug": "vinyl_playback", "name": "Vinyl Playback Optimization",
     "desc": "Box-Behnken design to maximize audio fidelity and minimize surface noise by tuning tracking force, anti-skate, and cartridge alignment",
     "design": "box_behnken", "category": "music",
     "factors": [
         {"name": "tracking_force_g", "levels": ["1.2", "2.2"], "type": "continuous", "unit": "g", "description": "Stylus tracking force"},
         {"name": "anti_skate_g", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "g", "description": "Anti-skate force"},
         {"name": "overhang_mm", "levels": ["14", "18"], "type": "continuous", "unit": "mm", "description": "Cartridge overhang distance"},
     ],
     "fixed": {"turntable": "belt_drive", "cartridge_type": "moving_magnet"},
     "responses": [
         {"name": "fidelity_score", "optimize": "maximize", "unit": "pts", "description": "Audio fidelity score (1-10)"},
         {"name": "surface_noise", "optimize": "minimize", "unit": "dB", "description": "Surface noise level in dB above floor"},
     ],
     "model": """
    tf = (TF - 1.7) / 0.5;
    as_ = (AS - 1.25) / 0.75;
    oh = (OH - 16) / 2;
    fid = 7.0 + 0.5*tf + 0.3*as_ + 0.4*oh - 0.8*tf*tf - 0.5*as_*as_ - 0.6*oh*oh + 0.2*tf*as_;
    noise = -55 + 2*tf + 1*as_ - 0.5*oh + 1*tf*tf + 0.5*oh*oh;
    if (fid < 1) fid = 1; if (fid > 10) fid = 10;
    if (noise < -65) noise = -65;
    printf "{\\"fidelity_score\\": %.1f, \\"surface_noise\\": %.0f}", fid + n1*0.3, noise + n2*1;
""",
     "factor_cases": '--tracking_force_g) TF="$2"; shift 2 ;;\n        --anti_skate_g) AS="$2"; shift 2 ;;\n        --overhang_mm) OH="$2"; shift 2 ;;',
     "awk_vars": '-v TF="$TF" -v AS="$AS" -v OH="$OH"',
     "vars_init": 'TF=""\nAS=""\nOH=""', "validate": '[ -z "$TF" ] || [ -z "$AS" ] || [ -z "$OH" ]'},

    {"num": 160, "slug": "podcast_recording", "name": "Podcast Recording Quality",
     "desc": "Full factorial of mic distance, gain level, room treatment, and noise gate threshold to maximize voice clarity and minimize background noise",
     "design": "full_factorial", "category": "music",
     "factors": [
         {"name": "mic_dist_cm", "levels": ["5", "30"], "type": "continuous", "unit": "cm", "description": "Microphone distance from mouth"},
         {"name": "gain_db", "levels": ["20", "50"], "type": "continuous", "unit": "dB", "description": "Preamp gain"},
         {"name": "treatment_pct", "levels": ["0", "80"], "type": "continuous", "unit": "%", "description": "Room acoustic treatment coverage"},
         {"name": "gate_db", "levels": ["-60", "-30"], "type": "continuous", "unit": "dB", "description": "Noise gate threshold"},
     ],
     "fixed": {"mic_type": "large_diaphragm_condenser", "sample_rate": "48000"},
     "responses": [
         {"name": "clarity_score", "optimize": "maximize", "unit": "pts", "description": "Voice clarity score (1-10)"},
         {"name": "noise_floor_db", "optimize": "minimize", "unit": "dB", "description": "Background noise floor level"},
     ],
     "model": """
    md = (MD - 17.5) / 12.5;
    gn = (GN - 35) / 15;
    tr = (TR - 40) / 40;
    gt = (GT - -45) / 15;
    clarity = 6.5 - 0.8*md + 0.5*gn + 1.0*tr + 0.3*gt - 0.3*md*md - 0.4*gn*gn + 0.2*md*gn;
    noise = -40 + 3*md + 5*gn - 8*tr + 4*gt + 2*gn*gn;
    if (clarity < 1) clarity = 1; if (clarity > 10) clarity = 10;
    if (noise < -70) noise = -70;
    printf "{\\"clarity_score\\": %.1f, \\"noise_floor_db\\": %.0f}", clarity + n1*0.3, noise + n2*2;
""",
     "factor_cases": '--mic_dist_cm) MD="$2"; shift 2 ;;\n        --gain_db) GN="$2"; shift 2 ;;\n        --treatment_pct) TR="$2"; shift 2 ;;\n        --gate_db) GT="$2"; shift 2 ;;',
     "awk_vars": '-v MD="$MD" -v GN="$GN" -v TR="$TR" -v GT="$GT"',
     "vars_init": 'MD=""\nGN=""\nTR=""\nGT=""', "validate": '[ -z "$MD" ] || [ -z "$GN" ] || [ -z "$TR" ] || [ -z "$GT" ]'},

    {"num": 161, "slug": "speaker_placement", "name": "Speaker Placement in Room",
     "desc": "Box-Behnken design to maximize stereo imaging and minimize bass nulls by tuning distance from wall, toe-in angle, and listener distance",
     "design": "box_behnken", "category": "music",
     "factors": [
         {"name": "wall_dist_cm", "levels": ["30", "150"], "type": "continuous", "unit": "cm", "description": "Distance from rear wall"},
         {"name": "toe_in_deg", "levels": ["0", "30"], "type": "continuous", "unit": "deg", "description": "Speaker toe-in angle toward listener"},
         {"name": "listener_m", "levels": ["1.5", "4.0"], "type": "continuous", "unit": "m", "description": "Listening distance"},
     ],
     "fixed": {"speaker_type": "bookshelf", "room_size": "medium"},
     "responses": [
         {"name": "imaging_score", "optimize": "maximize", "unit": "pts", "description": "Stereo imaging width and depth (1-10)"},
         {"name": "bass_evenness", "optimize": "maximize", "unit": "pts", "description": "Bass frequency response evenness (1-10)"},
     ],
     "model": """
    wd = (WD - 90) / 60;
    ti = (TI - 15) / 15;
    ld = (LD - 2.75) / 1.25;
    img = 6.0 + 0.8*wd + 1.2*ti + 0.5*ld - 0.4*wd*wd - 0.5*ti*ti - 0.3*ld*ld + 0.3*ti*ld;
    bass = 5.5 + 1.0*wd - 0.3*ti + 0.4*ld - 0.5*wd*wd - 0.2*ld*ld + 0.2*wd*ld;
    if (img < 1) img = 1; if (img > 10) img = 10;
    if (bass < 1) bass = 1; if (bass > 10) bass = 10;
    printf "{\\"imaging_score\\": %.1f, \\"bass_evenness\\": %.1f}", img + n1*0.3, bass + n2*0.3;
""",
     "factor_cases": '--wall_dist_cm) WD="$2"; shift 2 ;;\n        --toe_in_deg) TI="$2"; shift 2 ;;\n        --listener_m) LD="$2"; shift 2 ;;',
     "awk_vars": '-v WD="$WD" -v TI="$TI" -v LD="$LD"',
     "vars_init": 'WD=""\nTI=""\nLD=""', "validate": '[ -z "$WD" ] || [ -z "$TI" ] || [ -z "$LD" ]'},

    {"num": 162, "slug": "drum_tuning", "name": "Drum Head Tuning",
     "desc": "Central composite design to maximize resonance and minimize overtones by tuning batter tension, resonant tension, and muffling amount",
     "design": "central_composite", "category": "music",
     "factors": [
         {"name": "batter_torque", "levels": ["20", "80"], "type": "continuous", "unit": "in-lb", "description": "Batter head lug torque"},
         {"name": "reso_torque", "levels": ["20", "80"], "type": "continuous", "unit": "in-lb", "description": "Resonant head lug torque"},
         {"name": "muffle_pct", "levels": ["0", "50"], "type": "continuous", "unit": "%", "description": "Muffling ring coverage percentage"},
     ],
     "fixed": {"drum_size": "14x5_snare", "head_type": "coated"},
     "responses": [
         {"name": "resonance", "optimize": "maximize", "unit": "pts", "description": "Resonance and body score (1-10)"},
         {"name": "overtone_control", "optimize": "maximize", "unit": "pts", "description": "Overtone control score (1-10, 10=cleanest)"},
     ],
     "model": """
    bt = (BT - 50) / 30;
    rt = (RT - 50) / 30;
    mf = (MF - 25) / 25;
    res = 6.0 + 0.5*bt + 0.8*rt - 1.5*mf - 0.4*bt*bt - 0.3*rt*rt + 0.3*bt*rt;
    over = 5.0 - 0.3*bt - 0.2*rt + 2.0*mf + 0.2*bt*bt - 0.3*mf*mf + 0.2*bt*mf;
    if (res < 1) res = 1; if (res > 10) res = 10;
    if (over < 1) over = 1; if (over > 10) over = 10;
    printf "{\\"resonance\\": %.1f, \\"overtone_control\\": %.1f}", res + n1*0.3, over + n2*0.3;
""",
     "factor_cases": '--batter_torque) BT="$2"; shift 2 ;;\n        --reso_torque) RT="$2"; shift 2 ;;\n        --muffle_pct) MF="$2"; shift 2 ;;',
     "awk_vars": '-v BT="$BT" -v RT="$RT" -v MF="$MF"',
     "vars_init": 'BT=""\nRT=""\nMF=""', "validate": '[ -z "$BT" ] || [ -z "$RT" ] || [ -z "$MF" ]'},

    {"num": 163, "slug": "piano_voicing", "name": "Piano Voicing & Regulation",
     "desc": "Box-Behnken design to maximize tonal evenness and touch responsiveness by tuning hammer hardness, letoff distance, and aftertouch depth",
     "design": "box_behnken", "category": "music",
     "factors": [
         {"name": "hammer_hardness", "levels": ["30", "80"], "type": "continuous", "unit": "shore", "description": "Hammer felt hardness (Shore scale)"},
         {"name": "letoff_mm", "levels": ["1", "4"], "type": "continuous", "unit": "mm", "description": "Jack letoff distance from string"},
         {"name": "aftertouch_mm", "levels": ["0.5", "2.5"], "type": "continuous", "unit": "mm", "description": "Key aftertouch travel depth"},
     ],
     "fixed": {"piano_type": "grand", "action": "repetition"},
     "responses": [
         {"name": "tonal_evenness", "optimize": "maximize", "unit": "pts", "description": "Tonal evenness across range (1-10)"},
         {"name": "touch_response", "optimize": "maximize", "unit": "pts", "description": "Touch responsiveness score (1-10)"},
     ],
     "model": """
    hh = (HH - 55) / 25;
    lo = (LO - 2.5) / 1.5;
    at = (AT - 1.5) / 1;
    tone = 6.5 - 0.5*hh + 0.3*lo + 0.2*at - 0.8*hh*hh - 0.3*lo*lo + 0.2*hh*lo;
    touch = 6.0 + 0.3*hh - 0.5*lo + 0.8*at - 0.3*hh*hh + 0.2*lo*lo - 0.4*at*at + 0.2*lo*at;
    if (tone < 1) tone = 1; if (tone > 10) tone = 10;
    if (touch < 1) touch = 1; if (touch > 10) touch = 10;
    printf "{\\"tonal_evenness\\": %.1f, \\"touch_response\\": %.1f}", tone + n1*0.3, touch + n2*0.3;
""",
     "factor_cases": '--hammer_hardness) HH="$2"; shift 2 ;;\n        --letoff_mm) LO="$2"; shift 2 ;;\n        --aftertouch_mm) AT="$2"; shift 2 ;;',
     "awk_vars": '-v HH="$HH" -v LO="$LO" -v AT="$AT"',
     "vars_init": 'HH=""\nLO=""\nAT=""', "validate": '[ -z "$HH" ] || [ -z "$LO" ] || [ -z "$AT" ]'},

    {"num": 164, "slug": "headphone_eq", "name": "Headphone EQ Calibration",
     "desc": "Fractional factorial screening of bass boost, mid presence, treble roll-off, soundstage width, and crossfeed for preference score and fatigue reduction",
     "design": "fractional_factorial", "category": "music",
     "factors": [
         {"name": "bass_boost_db", "levels": ["0", "8"], "type": "continuous", "unit": "dB", "description": "Bass shelf boost at 100Hz"},
         {"name": "mid_presence_db", "levels": ["-3", "3"], "type": "continuous", "unit": "dB", "description": "Midrange presence boost at 3kHz"},
         {"name": "treble_rolloff_db", "levels": ["-6", "0"], "type": "continuous", "unit": "dB", "description": "Treble rolloff at 10kHz"},
         {"name": "soundstage_pct", "levels": ["0", "100"], "type": "continuous", "unit": "%", "description": "Virtual soundstage widening effect"},
         {"name": "crossfeed_pct", "levels": ["0", "60"], "type": "continuous", "unit": "%", "description": "Crossfeed blending percentage"},
     ],
     "fixed": {"headphone": "open_back", "source": "lossless"},
     "responses": [
         {"name": "preference_score", "optimize": "maximize", "unit": "pts", "description": "Listener preference score (1-10)"},
         {"name": "fatigue_score", "optimize": "minimize", "unit": "pts", "description": "Listening fatigue after 1 hour (1-10)"},
     ],
     "model": """
    bb = (BB - 4) / 4;
    mp = (MP - 0) / 3;
    tr = (TR - -3) / 3;
    sw = (SW - 50) / 50;
    cf = (CF - 30) / 30;
    pref = 6.0 + 0.8*bb + 0.5*mp - 0.3*tr + 0.4*sw + 0.3*cf - 0.5*bb*bb - 0.3*mp*mp;
    fat = 4.0 + 0.5*bb + 0.8*mp + 1.0*tr - 0.3*sw - 0.2*cf + 0.3*mp*tr;
    if (pref < 1) pref = 1; if (pref > 10) pref = 10;
    if (fat < 1) fat = 1; if (fat > 10) fat = 10;
    printf "{\\"preference_score\\": %.1f, \\"fatigue_score\\": %.1f}", pref + n1*0.3, fat + n2*0.3;
""",
     "factor_cases": '--bass_boost_db) BB="$2"; shift 2 ;;\n        --mid_presence_db) MP="$2"; shift 2 ;;\n        --treble_rolloff_db) TR="$2"; shift 2 ;;\n        --soundstage_pct) SW="$2"; shift 2 ;;\n        --crossfeed_pct) CF="$2"; shift 2 ;;',
     "awk_vars": '-v BB="$BB" -v MP="$MP" -v TR="$TR" -v SW="$SW" -v CF="$CF"',
     "vars_init": 'BB=""\nMP=""\nTR=""\nSW=""\nCF=""', "validate": '[ -z "$BB" ] || [ -z "$MP" ] || [ -z "$TR" ] || [ -z "$SW" ]'},

    {"num": 165, "slug": "concert_hall_design", "name": "Concert Hall Acoustic Design",
     "desc": "Plackett-Burman screening of ceiling height, width-to-length ratio, absorption coefficient, diffusion index, stage riser height, and balcony depth for clarity and warmth",
     "design": "plackett_burman", "category": "music",
     "factors": [
         {"name": "ceiling_m", "levels": ["8", "18"], "type": "continuous", "unit": "m", "description": "Ceiling height"},
         {"name": "width_ratio", "levels": ["0.5", "0.9"], "type": "continuous", "unit": "ratio", "description": "Width-to-length ratio"},
         {"name": "absorption_nrc", "levels": ["0.3", "0.7"], "type": "continuous", "unit": "NRC", "description": "Average absorption coefficient"},
         {"name": "diffusion_idx", "levels": ["0.2", "0.8"], "type": "continuous", "unit": "index", "description": "Diffusion index"},
         {"name": "stage_riser_m", "levels": ["0.3", "1.2"], "type": "continuous", "unit": "m", "description": "Stage riser height"},
     ],
     "fixed": {"seats": "800", "floor_material": "hardwood"},
     "responses": [
         {"name": "clarity_c80", "optimize": "maximize", "unit": "dB", "description": "Clarity index C80"},
         {"name": "warmth_index", "optimize": "maximize", "unit": "ratio", "description": "Bass ratio warmth index"},
     ],
     "model": """
    ch = (CH - 13) / 5;
    wr = (WR - 0.7) / 0.2;
    ab = (AB - 0.5) / 0.2;
    di = (DI - 0.5) / 0.3;
    sr = (SR - 0.75) / 0.45;
    c80 = 1.5 - 1.0*ch + 0.5*wr + 2.0*ab + 0.8*di + 0.3*sr + 0.3*ab*di;
    warm = 1.1 + 0.15*ch - 0.1*wr - 0.2*ab + 0.05*di + 0.08*sr + 0.05*ch*wr;
    if (c80 < -3) c80 = -3;
    if (warm < 0.6) warm = 0.6; if (warm > 1.6) warm = 1.6;
    printf "{\\"clarity_c80\\": %.1f, \\"warmth_index\\": %.2f}", c80 + n1*0.3, warm + n2*0.03;
""",
     "factor_cases": '--ceiling_m) CH="$2"; shift 2 ;;\n        --width_ratio) WR="$2"; shift 2 ;;\n        --absorption_nrc) AB="$2"; shift 2 ;;\n        --diffusion_idx) DI="$2"; shift 2 ;;\n        --stage_riser_m) SR="$2"; shift 2 ;;',
     "awk_vars": '-v CH="$CH" -v WR="$WR" -v AB="$AB" -v DI="$DI" -v SR="$SR"',
     "vars_init": 'CH=""\nWR=""\nAB=""\nDI=""\nSR=""', "validate": '[ -z "$CH" ] || [ -z "$WR" ] || [ -z "$AB" ] || [ -z "$DI" ]'},

    {"num": 166, "slug": "mixing_vocal_chain", "name": "Vocal Mix Processing Chain",
     "desc": "Box-Behnken design to maximize vocal presence and minimize harshness by tuning compression ratio, EQ boost frequency, and reverb send level",
     "design": "box_behnken", "category": "music",
     "factors": [
         {"name": "comp_ratio", "levels": ["2", "8"], "type": "continuous", "unit": "ratio", "description": "Compressor ratio"},
         {"name": "eq_boost_khz", "levels": ["2", "8"], "type": "continuous", "unit": "kHz", "description": "Presence EQ boost center frequency"},
         {"name": "reverb_send_db", "levels": ["-24", "-6"], "type": "continuous", "unit": "dB", "description": "Reverb send level"},
     ],
     "fixed": {"mic": "sm7b", "genre": "pop"},
     "responses": [
         {"name": "presence_score", "optimize": "maximize", "unit": "pts", "description": "Vocal presence and clarity (1-10)"},
         {"name": "harshness", "optimize": "minimize", "unit": "pts", "description": "Sibilance and harshness (1-10)"},
     ],
     "model": """
    cr = (CR - 5) / 3;
    eq = (EQ - 5) / 3;
    rv = (RV - -15) / 9;
    pres = 6.0 + 0.8*cr + 0.5*eq - 0.3*rv - 0.5*cr*cr - 0.3*eq*eq + 0.2*cr*eq;
    harsh = 3.5 + 0.5*cr + 1.2*eq + 0.2*rv + 0.3*cr*cr + 0.4*eq*eq + 0.2*cr*eq;
    if (pres < 1) pres = 1; if (pres > 10) pres = 10;
    if (harsh < 1) harsh = 1; if (harsh > 10) harsh = 10;
    printf "{\\"presence_score\\": %.1f, \\"harshness\\": %.1f}", pres + n1*0.3, harsh + n2*0.3;
""",
     "factor_cases": '--comp_ratio) CR="$2"; shift 2 ;;\n        --eq_boost_khz) EQ="$2"; shift 2 ;;\n        --reverb_send_db) RV="$2"; shift 2 ;;',
     "awk_vars": '-v CR="$CR" -v EQ="$EQ" -v RV="$RV"',
     "vars_init": 'CR=""\nEQ=""\nRV=""', "validate": '[ -z "$CR" ] || [ -z "$EQ" ] || [ -z "$RV" ]'},

    # ══════════════════════════════════════════════════
    # Pet Care & Animal Science (167-176)
    # ══════════════════════════════════════════════════
    {"num": 167, "slug": "dog_kibble_formulation", "name": "Dog Kibble Formulation",
     "desc": "Box-Behnken design to maximize palatability and coat condition by tuning protein content, fat percentage, and fiber content",
     "design": "box_behnken", "category": "petcare",
     "factors": [
         {"name": "protein_pct", "levels": ["20", "35"], "type": "continuous", "unit": "%", "description": "Crude protein percentage"},
         {"name": "fat_pct", "levels": ["8", "18"], "type": "continuous", "unit": "%", "description": "Crude fat percentage"},
         {"name": "fiber_pct", "levels": ["2", "6"], "type": "continuous", "unit": "%", "description": "Crude fiber percentage"},
     ],
     "fixed": {"breed_size": "medium", "life_stage": "adult"},
     "responses": [
         {"name": "palatability", "optimize": "maximize", "unit": "pts", "description": "Palatability taste test score (1-10)"},
         {"name": "coat_score", "optimize": "maximize", "unit": "pts", "description": "Coat condition score after 8 weeks (1-10)"},
     ],
     "model": """
    pr = (PR - 27.5) / 7.5; ft = (FT - 13) / 5; fb = (FB - 4) / 2;
    pal = 6.5 + 0.5*pr + 1.2*ft - 0.4*fb - 0.3*pr*pr - 0.4*ft*ft + 0.2*pr*ft;
    coat = 6.0 + 0.8*pr + 0.6*ft + 0.2*fb - 0.3*pr*pr - 0.2*ft*ft + 0.15*pr*fb;
    if (pal < 1) pal = 1; if (pal > 10) pal = 10;
    if (coat < 1) coat = 1; if (coat > 10) coat = 10;
    printf "{\\"palatability\\": %.1f, \\"coat_score\\": %.1f}", pal + n1*0.3, coat + n2*0.3;
""",
     "factor_cases": '--protein_pct) PR="$2"; shift 2 ;;\n        --fat_pct) FT="$2"; shift 2 ;;\n        --fiber_pct) FB="$2"; shift 2 ;;',
     "awk_vars": '-v PR="$PR" -v FT="$FT" -v FB="$FB"',
     "vars_init": 'PR=""\nFT=""\nFB=""', "validate": '[ -z "$PR" ] || [ -z "$FT" ] || [ -z "$FB" ]'},

    {"num": 168, "slug": "cat_litter_box", "name": "Cat Litter Box Management",
     "desc": "Central composite design to minimize odor and maximize cat usage by tuning litter depth, cleaning frequency, and box size",
     "design": "central_composite", "category": "petcare",
     "factors": [
         {"name": "litter_depth_cm", "levels": ["3", "10"], "type": "continuous", "unit": "cm", "description": "Litter fill depth"},
         {"name": "clean_per_day", "levels": ["1", "3"], "type": "continuous", "unit": "per_day", "description": "Scooping frequency per day"},
         {"name": "box_area_cm2", "levels": ["1500", "4000"], "type": "continuous", "unit": "cm2", "description": "Litter box floor area"},
     ],
     "fixed": {"litter_type": "clumping_clay", "cats": "2"},
     "responses": [
         {"name": "odor_control", "optimize": "maximize", "unit": "pts", "description": "Odor control score (1-10, 10=no odor)"},
         {"name": "usage_pct", "optimize": "maximize", "unit": "%", "description": "Percentage of eliminations in the box"},
     ],
     "model": """
    ld = (LD - 6.5) / 3.5; cf = (CF - 2) / 1; ba = (BA - 2750) / 1250;
    odor = 5.5 + 0.8*ld + 1.5*cf + 0.5*ba - 0.3*ld*ld - 0.4*cf*cf + 0.2*ld*cf;
    usage = 85 + 3*ld + 5*cf + 4*ba - 1.5*ld*ld - 2*cf*cf - 1*ba*ba + 1*cf*ba;
    if (odor < 1) odor = 1; if (odor > 10) odor = 10;
    if (usage < 50) usage = 50; if (usage > 100) usage = 100;
    printf "{\\"odor_control\\": %.1f, \\"usage_pct\\": %.0f}", odor + n1*0.3, usage + n2*2;
""",
     "factor_cases": '--litter_depth_cm) LD="$2"; shift 2 ;;\n        --clean_per_day) CF="$2"; shift 2 ;;\n        --box_area_cm2) BA="$2"; shift 2 ;;',
     "awk_vars": '-v LD="$LD" -v CF="$CF" -v BA="$BA"',
     "vars_init": 'LD=""\nCF=""\nBA=""', "validate": '[ -z "$LD" ] || [ -z "$CF" ] || [ -z "$BA" ]'},

    {"num": 169, "slug": "chicken_egg_production", "name": "Backyard Chicken Egg Production",
     "desc": "Full factorial of light hours, feed protein, calcium supplement, and coop ventilation to maximize egg production and shell quality",
     "design": "full_factorial", "category": "petcare",
     "factors": [
         {"name": "light_hrs", "levels": ["10", "16"], "type": "continuous", "unit": "hrs", "description": "Daily light exposure hours"},
         {"name": "feed_protein_pct", "levels": ["14", "20"], "type": "continuous", "unit": "%", "description": "Feed crude protein percentage"},
         {"name": "calcium_g", "levels": ["2", "6"], "type": "continuous", "unit": "g/day", "description": "Supplemental calcium per hen per day"},
         {"name": "ventilation", "levels": ["low", "high"], "type": "categorical", "unit": "", "description": "Coop ventilation level"},
     ],
     "fixed": {"breed": "rhode_island_red", "flock_size": "6"},
     "responses": [
         {"name": "eggs_per_week", "optimize": "maximize", "unit": "eggs/hen", "description": "Eggs per hen per week"},
         {"name": "shell_thickness", "optimize": "maximize", "unit": "mm", "description": "Average eggshell thickness"},
     ],
     "model": """
    lh = (LH - 13) / 3; fp = (FP - 17) / 3; ca = (CA - 4) / 2; vt = (VT == "high") ? 1 : -1;
    eggs = 5.0 + 0.8*lh + 0.5*fp + 0.2*ca + 0.3*vt - 0.3*lh*lh + 0.1*lh*fp;
    shell = 0.35 + 0.01*lh + 0.015*fp + 0.04*ca + 0.01*vt + 0.005*ca*ca;
    if (eggs < 2) eggs = 2; if (eggs > 7) eggs = 7;
    if (shell < 0.2) shell = 0.2; if (shell > 0.5) shell = 0.5;
    printf "{\\"eggs_per_week\\": %.1f, \\"shell_thickness\\": %.3f}", eggs + n1*0.3, shell + n2*0.01;
""",
     "factor_cases": '--light_hrs) LH="$2"; shift 2 ;;\n        --feed_protein_pct) FP="$2"; shift 2 ;;\n        --calcium_g) CA="$2"; shift 2 ;;\n        --ventilation) VT="$2"; shift 2 ;;',
     "awk_vars": '-v LH="$LH" -v FP="$FP" -v CA="$CA" -v VT="$VT"',
     "vars_init": 'LH=""\nFP=""\nCA=""\nVT=""', "validate": '[ -z "$LH" ] || [ -z "$FP" ] || [ -z "$CA" ] || [ -z "$VT" ]'},

    {"num": 170, "slug": "fish_tank_health", "name": "Tropical Fish Tank Health",
     "desc": "Box-Behnken design to maximize fish vitality and minimize algae by tuning water change frequency, feeding amount, and light duration",
     "design": "box_behnken", "category": "petcare",
     "factors": [
         {"name": "water_change_pct", "levels": ["10", "40"], "type": "continuous", "unit": "%/week", "description": "Weekly water change percentage"},
         {"name": "feed_g_day", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "g/day", "description": "Daily feeding amount"},
         {"name": "light_hrs", "levels": ["6", "12"], "type": "continuous", "unit": "hrs", "description": "Daily photoperiod"},
     ],
     "fixed": {"tank_L": "200", "fish_count": "20"},
     "responses": [
         {"name": "vitality_score", "optimize": "maximize", "unit": "pts", "description": "Fish activity and coloration (1-10)"},
         {"name": "algae_level", "optimize": "minimize", "unit": "pts", "description": "Algae growth level (1-10)"},
     ],
     "model": """
    wc = (WC - 25) / 15; fd = (FD - 1.75) / 1.25; lh = (LH - 9) / 3;
    vit = 7.0 + 0.5*wc + 0.8*fd + 0.3*lh - 0.3*wc*wc - 0.5*fd*fd + 0.2*wc*fd;
    alg = 4.0 - 0.8*wc + 1.0*fd + 1.2*lh + 0.3*fd*fd + 0.2*lh*lh + 0.3*fd*lh;
    if (vit < 1) vit = 1; if (vit > 10) vit = 10;
    if (alg < 1) alg = 1; if (alg > 10) alg = 10;
    printf "{\\"vitality_score\\": %.1f, \\"algae_level\\": %.1f}", vit + n1*0.3, alg + n2*0.3;
""",
     "factor_cases": '--water_change_pct) WC="$2"; shift 2 ;;\n        --feed_g_day) FD="$2"; shift 2 ;;\n        --light_hrs) LH="$2"; shift 2 ;;',
     "awk_vars": '-v WC="$WC" -v FD="$FD" -v LH="$LH"',
     "vars_init": 'WC=""\nFD=""\nLH=""', "validate": '[ -z "$WC" ] || [ -z "$FD" ] || [ -z "$LH" ]'},

    {"num": 171, "slug": "dog_training_protocol", "name": "Dog Training Effectiveness",
     "desc": "Central composite design to maximize command reliability and minimize training time by tuning session length, reward frequency, and difficulty progression rate",
     "design": "central_composite", "category": "petcare",
     "factors": [
         {"name": "session_min", "levels": ["5", "20"], "type": "continuous", "unit": "min", "description": "Training session duration"},
         {"name": "reward_ratio_pct", "levels": ["30", "100"], "type": "continuous", "unit": "%", "description": "Percentage of correct responses rewarded"},
         {"name": "progression_rate", "levels": ["1", "5"], "type": "continuous", "unit": "level/wk", "description": "Difficulty increase per week"},
     ],
     "fixed": {"method": "positive_reinforcement", "breed": "labrador"},
     "responses": [
         {"name": "reliability_pct", "optimize": "maximize", "unit": "%", "description": "Command reliability percentage after 6 weeks"},
         {"name": "sessions_to_learn", "optimize": "minimize", "unit": "sessions", "description": "Sessions needed to learn new command"},
     ],
     "model": """
    sm = (SM - 12.5) / 7.5; rr = (RR - 65) / 35; pr = (PR - 3) / 2;
    rel = 75 + 3*sm + 5*rr - 2*pr - 2*sm*sm - 3*rr*rr - 1*pr*pr + 1.5*sm*rr;
    sess = 12 - 1.5*sm - 2*rr + 1.5*pr + 0.5*sm*sm + 0.8*rr*rr + 0.5*sm*pr;
    if (rel < 30) rel = 30; if (rel > 100) rel = 100;
    if (sess < 3) sess = 3;
    printf "{\\"reliability_pct\\": %.0f, \\"sessions_to_learn\\": %.0f}", rel + n1*3, sess + n2*1;
""",
     "factor_cases": '--session_min) SM="$2"; shift 2 ;;\n        --reward_ratio_pct) RR="$2"; shift 2 ;;\n        --progression_rate) PR="$2"; shift 2 ;;',
     "awk_vars": '-v SM="$SM" -v RR="$RR" -v PR="$PR"',
     "vars_init": 'SM=""\nRR=""\nPR=""', "validate": '[ -z "$SM" ] || [ -z "$RR" ] || [ -z "$PR" ]'},

    {"num": 172, "slug": "beehive_management", "name": "Beehive Honey Production",
     "desc": "Box-Behnken design to maximize honey yield and colony health by tuning hive spacing, supplemental feeding, and mite treatment timing",
     "design": "box_behnken", "category": "petcare",
     "factors": [
         {"name": "hive_spacing_m", "levels": ["2", "8"], "type": "continuous", "unit": "m", "description": "Distance between hives"},
         {"name": "sugar_feed_kg", "levels": ["0", "10"], "type": "continuous", "unit": "kg", "description": "Supplemental sugar syrup per season"},
         {"name": "mite_treat_month", "levels": ["3", "9"], "type": "continuous", "unit": "month", "description": "Month of Varroa mite treatment"},
     ],
     "fixed": {"bee_species": "apis_mellifera", "frames": "10"},
     "responses": [
         {"name": "honey_kg", "optimize": "maximize", "unit": "kg", "description": "Honey harvest per hive per season"},
         {"name": "colony_health", "optimize": "maximize", "unit": "pts", "description": "Colony health score (1-10)"},
     ],
     "model": """
    hs = (HS - 5) / 3; sf = (SF - 5) / 5; mt = (MT - 6) / 3;
    honey = 25 + 3*hs + 5*sf - 2*mt - 1*hs*hs - 2*sf*sf + 0.5*hs*sf;
    health = 7.0 + 0.5*hs - 0.3*sf + 0.8*mt - 0.3*hs*hs + 0.2*sf*sf - 0.5*mt*mt + 0.2*sf*mt;
    if (honey < 5) honey = 5;
    if (health < 1) health = 1; if (health > 10) health = 10;
    printf "{\\"honey_kg\\": %.1f, \\"colony_health\\": %.1f}", honey + n1*2, health + n2*0.3;
""",
     "factor_cases": '--hive_spacing_m) HS="$2"; shift 2 ;;\n        --sugar_feed_kg) SF="$2"; shift 2 ;;\n        --mite_treat_month) MT="$2"; shift 2 ;;',
     "awk_vars": '-v HS="$HS" -v SF="$SF" -v MT="$MT"',
     "vars_init": 'HS=""\nSF=""\nMT=""', "validate": '[ -z "$HS" ] || [ -z "$SF" ] || [ -z "$MT" ]'},

    {"num": 173, "slug": "horse_feed_ration", "name": "Horse Feed Ration Balance",
     "desc": "Fractional factorial screening of hay ratio, grain amount, mineral supplement, oil supplement, and feeding frequency for weight maintenance and hoof quality",
     "design": "fractional_factorial", "category": "petcare",
     "factors": [
         {"name": "hay_kg", "levels": ["6", "12"], "type": "continuous", "unit": "kg/day", "description": "Daily hay intake"},
         {"name": "grain_kg", "levels": ["1", "5"], "type": "continuous", "unit": "kg/day", "description": "Daily grain concentrate"},
         {"name": "mineral_g", "levels": ["30", "90"], "type": "continuous", "unit": "g/day", "description": "Mineral supplement amount"},
         {"name": "oil_ml", "levels": ["0", "120"], "type": "continuous", "unit": "mL/day", "description": "Vegetable oil supplement"},
         {"name": "feed_freq", "levels": ["2", "4"], "type": "continuous", "unit": "per_day", "description": "Feeding frequency per day"},
     ],
     "fixed": {"horse_weight": "500kg", "activity": "moderate"},
     "responses": [
         {"name": "body_condition", "optimize": "maximize", "unit": "pts", "description": "Body condition score (1-9 Henneke scale)"},
         {"name": "hoof_quality", "optimize": "maximize", "unit": "pts", "description": "Hoof wall quality score (1-10)"},
     ],
     "model": """
    hy = (HY - 9) / 3; gr = (GR - 3) / 2; mn = (MN - 60) / 30; ol = (OL - 60) / 60; ff = (FF - 3) / 1;
    body = 5.5 + 0.5*hy + 0.8*gr + 0.2*mn + 0.3*ol + 0.2*ff - 0.3*gr*gr + 0.1*hy*gr;
    hoof = 6.0 + 0.2*hy + 0.1*gr + 0.6*mn + 0.4*ol + 0.15*ff + 0.1*mn*ol;
    if (body < 1) body = 1; if (body > 9) body = 9;
    if (hoof < 1) hoof = 1; if (hoof > 10) hoof = 10;
    printf "{\\"body_condition\\": %.1f, \\"hoof_quality\\": %.1f}", body + n1*0.3, hoof + n2*0.3;
""",
     "factor_cases": '--hay_kg) HY="$2"; shift 2 ;;\n        --grain_kg) GR="$2"; shift 2 ;;\n        --mineral_g) MN="$2"; shift 2 ;;\n        --oil_ml) OL="$2"; shift 2 ;;\n        --feed_freq) FF="$2"; shift 2 ;;',
     "awk_vars": '-v HY="$HY" -v GR="$GR" -v MN="$MN" -v OL="$OL" -v FF="$FF"',
     "vars_init": 'HY=""\nGR=""\nMN=""\nOL=""\nFF=""', "validate": '[ -z "$HY" ] || [ -z "$GR" ] || [ -z "$MN" ] || [ -z "$OL" ]'},

    {"num": 174, "slug": "reptile_habitat", "name": "Reptile Terrarium Setup",
     "desc": "Full factorial of basking temperature, humidity, UVB output, and substrate depth to maximize activity level and minimize stress indicators",
     "design": "full_factorial", "category": "petcare",
     "factors": [
         {"name": "basking_c", "levels": ["30", "40"], "type": "continuous", "unit": "C", "description": "Basking spot temperature"},
         {"name": "humidity_pct", "levels": ["30", "70"], "type": "continuous", "unit": "%", "description": "Enclosure humidity"},
         {"name": "uvb_pct", "levels": ["5", "14"], "type": "continuous", "unit": "%UVI", "description": "UVB output percentage"},
         {"name": "substrate_cm", "levels": ["3", "15"], "type": "continuous", "unit": "cm", "description": "Substrate depth"},
     ],
     "fixed": {"species": "bearded_dragon", "enclosure_L": "120cm"},
     "responses": [
         {"name": "activity_score", "optimize": "maximize", "unit": "pts", "description": "Activity and exploration score (1-10)"},
         {"name": "stress_indicators", "optimize": "minimize", "unit": "pts", "description": "Stress behavior count (1-10)"},
     ],
     "model": """
    bk = (BK - 35) / 5; hm = (HM - 50) / 20; uv = (UV - 9.5) / 4.5; sb = (SB - 9) / 6;
    act = 6.0 + 0.5*bk + 0.3*hm + 0.6*uv + 0.4*sb - 0.8*bk*bk - 0.3*hm*hm + 0.2*bk*uv;
    stress = 4.0 + 0.8*bk - 0.3*hm + 0.2*uv - 0.3*sb + 0.5*bk*bk + 0.2*hm*hm;
    if (act < 1) act = 1; if (act > 10) act = 10;
    if (stress < 1) stress = 1; if (stress > 10) stress = 10;
    printf "{\\"activity_score\\": %.1f, \\"stress_indicators\\": %.1f}", act + n1*0.3, stress + n2*0.3;
""",
     "factor_cases": '--basking_c) BK="$2"; shift 2 ;;\n        --humidity_pct) HM="$2"; shift 2 ;;\n        --uvb_pct) UV="$2"; shift 2 ;;\n        --substrate_cm) SB="$2"; shift 2 ;;',
     "awk_vars": '-v BK="$BK" -v HM="$HM" -v UV="$UV" -v SB="$SB"',
     "vars_init": 'BK=""\nHM=""\nUV=""\nSB=""', "validate": '[ -z "$BK" ] || [ -z "$HM" ] || [ -z "$UV" ] || [ -z "$SB" ]'},

    {"num": 175, "slug": "rabbit_hutch_design", "name": "Rabbit Hutch Enrichment",
     "desc": "Box-Behnken design to maximize rabbit activity and minimize stereotypic behavior by tuning floor area, platform levels, and toy rotation frequency",
     "design": "box_behnken", "category": "petcare",
     "factors": [
         {"name": "floor_area_m2", "levels": ["2", "6"], "type": "continuous", "unit": "m2", "description": "Total floor area"},
         {"name": "platform_levels", "levels": ["1", "4"], "type": "continuous", "unit": "levels", "description": "Number of elevated platforms"},
         {"name": "toy_rotation_days", "levels": ["1", "7"], "type": "continuous", "unit": "days", "description": "Days between toy rotation"},
     ],
     "fixed": {"rabbits": "2", "outdoor_access": "daily"},
     "responses": [
         {"name": "activity_index", "optimize": "maximize", "unit": "pts", "description": "Daily activity and play index (1-10)"},
         {"name": "stereotypy_pct", "optimize": "minimize", "unit": "%", "description": "Time spent in stereotypic behaviors"},
     ],
     "model": """
    fa = (FA - 4) / 2; pl = (PL - 2.5) / 1.5; tr = (TR - 4) / 3;
    act = 6.0 + 1.0*fa + 0.8*pl - 0.5*tr - 0.3*fa*fa - 0.2*pl*pl + 0.2*fa*pl;
    ster = 8 - 2*fa - 1.5*pl + 1*tr + 0.5*fa*fa + 0.3*tr*tr - 0.3*fa*tr;
    if (act < 1) act = 1; if (act > 10) act = 10;
    if (ster < 0) ster = 0; if (ster > 30) ster = 30;
    printf "{\\"activity_index\\": %.1f, \\"stereotypy_pct\\": %.1f}", act + n1*0.3, ster + n2*1;
""",
     "factor_cases": '--floor_area_m2) FA="$2"; shift 2 ;;\n        --platform_levels) PL="$2"; shift 2 ;;\n        --toy_rotation_days) TR="$2"; shift 2 ;;',
     "awk_vars": '-v FA="$FA" -v PL="$PL" -v TR="$TR"',
     "vars_init": 'FA=""\nPL=""\nTR=""', "validate": '[ -z "$FA" ] || [ -z "$PL" ] || [ -z "$TR" ]'},

    {"num": 176, "slug": "pond_koi_health", "name": "Koi Pond Water Management",
     "desc": "Central composite design to maximize koi coloration and growth by tuning filtration turnover, stocking density, and feeding rate",
     "design": "central_composite", "category": "petcare",
     "factors": [
         {"name": "turnover_per_hr", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "x/hr", "description": "Pond volume filtration turnover rate"},
         {"name": "fish_per_m3", "levels": ["1", "5"], "type": "continuous", "unit": "fish/m3", "description": "Stocking density"},
         {"name": "feed_pct_bw", "levels": ["1", "4"], "type": "continuous", "unit": "%BW", "description": "Daily feeding as percentage of body weight"},
     ],
     "fixed": {"pond_volume": "10m3", "filter_type": "bead"},
     "responses": [
         {"name": "color_vibrancy", "optimize": "maximize", "unit": "pts", "description": "Color vibrancy and pattern score (1-10)"},
         {"name": "growth_cm_mo", "optimize": "maximize", "unit": "cm/month", "description": "Monthly length growth"},
     ],
     "model": """
    to = (TO - 1.75) / 1.25; fd = (FD - 3) / 2; fr = (FR - 2.5) / 1.5;
    color = 6.5 + 0.5*to - 0.3*fd + 0.4*fr - 0.3*to*to + 0.2*fd*fd - 0.3*fr*fr + 0.2*to*fd;
    growth = 1.5 + 0.3*to - 0.4*fd + 0.6*fr - 0.2*to*to - 0.2*fd*fd - 0.3*fr*fr + 0.15*fd*fr;
    if (color < 1) color = 1; if (color > 10) color = 10;
    if (growth < 0.2) growth = 0.2;
    printf "{\\"color_vibrancy\\": %.1f, \\"growth_cm_mo\\": %.2f}", color + n1*0.3, growth + n2*0.1;
""",
     "factor_cases": '--turnover_per_hr) TO="$2"; shift 2 ;;\n        --fish_per_m3) FD="$2"; shift 2 ;;\n        --feed_pct_bw) FR="$2"; shift 2 ;;',
     "awk_vars": '-v TO="$TO" -v FD="$FD" -v FR="$FR"',
     "vars_init": 'TO=""\nFD=""\nFR=""', "validate": '[ -z "$TO" ] || [ -z "$FD" ] || [ -z "$FR" ]'},

    # ══════════════════════════════════════════════════
    # Textiles & Fashion (177-186)
    # ══════════════════════════════════════════════════
    {"num": 177, "slug": "fabric_dyeing", "name": "Natural Fabric Dyeing",
     "desc": "Box-Behnken design to maximize color depth and wash fastness by tuning dye concentration, bath temperature, and immersion time",
     "design": "box_behnken", "category": "textiles",
     "factors": [
         {"name": "dye_concentration_pct", "levels": ["5", "30"], "type": "continuous", "unit": "%WOF", "description": "Dye weight as % of fabric weight"},
         {"name": "bath_temp_c", "levels": ["40", "95"], "type": "continuous", "unit": "C", "description": "Dye bath temperature"},
         {"name": "immersion_min", "levels": ["30", "120"], "type": "continuous", "unit": "min", "description": "Immersion time"},
     ],
     "fixed": {"fabric": "cotton_muslin", "mordant": "alum"},
     "responses": [
         {"name": "color_depth", "optimize": "maximize", "unit": "K/S", "description": "Color depth (K/S value)"},
         {"name": "wash_fastness", "optimize": "maximize", "unit": "grade", "description": "Wash fastness grade (1-5)"},
     ],
     "model": """
    dc = (DC - 17.5) / 12.5; bt = (BT - 67.5) / 27.5; im = (IM - 75) / 45;
    depth = 3.0 + 1.5*dc + 0.8*bt + 0.5*im - 0.4*dc*dc - 0.3*bt*bt + 0.2*dc*bt;
    fast = 3.5 + 0.3*dc + 0.5*bt + 0.3*im - 0.2*dc*dc + 0.1*bt*bt - 0.15*im*im + 0.1*bt*im;
    if (depth < 0.5) depth = 0.5;
    if (fast < 1) fast = 1; if (fast > 5) fast = 5;
    printf "{\\"color_depth\\": %.1f, \\"wash_fastness\\": %.1f}", depth + n1*0.2, fast + n2*0.15;
""",
     "factor_cases": '--dye_concentration_pct) DC="$2"; shift 2 ;;\n        --bath_temp_c) BT="$2"; shift 2 ;;\n        --immersion_min) IM="$2"; shift 2 ;;',
     "awk_vars": '-v DC="$DC" -v BT="$BT" -v IM="$IM"',
     "vars_init": 'DC=""\nBT=""\nIM=""', "validate": '[ -z "$DC" ] || [ -z "$BT" ] || [ -z "$IM" ]'},

    {"num": 178, "slug": "knitting_tension", "name": "Knitting Gauge & Tension",
     "desc": "Central composite design to achieve target gauge and maximize fabric drape by tuning needle size, yarn weight, and tension setting",
     "design": "central_composite", "category": "textiles",
     "factors": [
         {"name": "needle_mm", "levels": ["3.0", "6.0"], "type": "continuous", "unit": "mm", "description": "Knitting needle diameter"},
         {"name": "yarn_weight", "levels": ["1", "5"], "type": "continuous", "unit": "category", "description": "Yarn weight category (1=fingering, 5=bulky)"},
         {"name": "tension_setting", "levels": ["3", "9"], "type": "continuous", "unit": "dial", "description": "Machine tension dial (or hand tension 1-10)"},
     ],
     "fixed": {"fiber": "merino_wool", "stitch_pattern": "stockinette"},
     "responses": [
         {"name": "gauge_sts_10cm", "optimize": "maximize", "unit": "sts/10cm", "description": "Stitch gauge per 10cm"},
         {"name": "drape_score", "optimize": "maximize", "unit": "pts", "description": "Fabric drape and hand score (1-10)"},
     ],
     "model": """
    nm = (NM - 4.5) / 1.5; yw = (YW - 3) / 2; ts = (TS - 6) / 3;
    gauge = 22 - 4*nm - 3*yw + 2*ts + 1*nm*nm + 0.5*yw*yw + 0.5*nm*yw;
    drape = 6.0 + 0.8*nm + 0.3*yw - 0.5*ts - 0.3*nm*nm + 0.2*yw*yw + 0.2*nm*ts;
    if (gauge < 8) gauge = 8; if (gauge > 36) gauge = 36;
    if (drape < 1) drape = 1; if (drape > 10) drape = 10;
    printf "{\\"gauge_sts_10cm\\": %.0f, \\"drape_score\\": %.1f}", gauge + n1*1, drape + n2*0.3;
""",
     "factor_cases": '--needle_mm) NM="$2"; shift 2 ;;\n        --yarn_weight) YW="$2"; shift 2 ;;\n        --tension_setting) TS="$2"; shift 2 ;;',
     "awk_vars": '-v NM="$NM" -v YW="$YW" -v TS="$TS"',
     "vars_init": 'NM=""\nYW=""\nTS=""', "validate": '[ -z "$NM" ] || [ -z "$YW" ] || [ -z "$TS" ]'},

    {"num": 179, "slug": "sewing_stitch_quality", "name": "Sewing Machine Stitch Quality",
     "desc": "Box-Behnken design to maximize stitch quality and minimize thread breakage by tuning upper tension, stitch length, and presser foot pressure",
     "design": "box_behnken", "category": "textiles",
     "factors": [
         {"name": "upper_tension", "levels": ["2", "7"], "type": "continuous", "unit": "dial", "description": "Upper thread tension setting"},
         {"name": "stitch_length_mm", "levels": ["1.5", "4.0"], "type": "continuous", "unit": "mm", "description": "Stitch length"},
         {"name": "foot_pressure", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "Presser foot pressure level"},
     ],
     "fixed": {"machine": "mechanical", "fabric": "cotton_twill"},
     "responses": [
         {"name": "stitch_quality", "optimize": "maximize", "unit": "pts", "description": "Stitch evenness and formation (1-10)"},
         {"name": "break_rate", "optimize": "minimize", "unit": "per_m", "description": "Thread breaks per meter of stitching"},
     ],
     "model": """
    ut = (UT - 4.5) / 2.5; sl = (SL - 2.75) / 1.25; fp = (FP - 3) / 2;
    qual = 7.0 + 0.3*ut + 0.5*sl + 0.4*fp - 0.8*ut*ut - 0.3*sl*sl - 0.3*fp*fp + 0.2*ut*fp;
    brk = 0.5 + 0.5*ut - 0.2*sl + 0.3*fp + 0.4*ut*ut + 0.1*fp*fp + 0.2*ut*fp;
    if (qual < 1) qual = 1; if (qual > 10) qual = 10;
    if (brk < 0) brk = 0;
    printf "{\\"stitch_quality\\": %.1f, \\"break_rate\\": %.2f}", qual + n1*0.3, brk + n2*0.1;
""",
     "factor_cases": '--upper_tension) UT="$2"; shift 2 ;;\n        --stitch_length_mm) SL="$2"; shift 2 ;;\n        --foot_pressure) FP="$2"; shift 2 ;;',
     "awk_vars": '-v UT="$UT" -v SL="$SL" -v FP="$FP"',
     "vars_init": 'UT=""\nSL=""\nFP=""', "validate": '[ -z "$UT" ] || [ -z "$SL" ] || [ -z "$FP" ]'},

    {"num": 180, "slug": "leather_tanning", "name": "Leather Tanning Process",
     "desc": "Full factorial of tanning agent concentration, soak time, pH, and fat liquor percentage to maximize softness and color uniformity",
     "design": "full_factorial", "category": "textiles",
     "factors": [
         {"name": "tannin_pct", "levels": ["3", "10"], "type": "continuous", "unit": "%", "description": "Tanning agent concentration"},
         {"name": "soak_hrs", "levels": ["4", "24"], "type": "continuous", "unit": "hrs", "description": "Tanning soak duration"},
         {"name": "ph", "levels": ["3", "5"], "type": "continuous", "unit": "pH", "description": "Bath pH level"},
         {"name": "fat_liquor_pct", "levels": ["3", "10"], "type": "continuous", "unit": "%", "description": "Fat liquor percentage"},
     ],
     "fixed": {"hide_type": "cowhide", "method": "vegetable"},
     "responses": [
         {"name": "softness_score", "optimize": "maximize", "unit": "pts", "description": "Leather softness and hand (1-10)"},
         {"name": "color_uniformity", "optimize": "maximize", "unit": "pts", "description": "Color uniformity score (1-10)"},
     ],
     "model": """
    tn = (TN - 6.5) / 3.5; sk = (SK - 14) / 10; ph = (PH - 4) / 1; fl = (FL - 6.5) / 3.5;
    soft = 5.5 - 0.5*tn + 0.3*sk - 0.3*ph + 1.2*fl + 0.2*tn*tn + 0.1*sk*fl;
    color = 6.0 + 0.3*tn + 0.5*sk + 0.4*ph + 0.2*fl - 0.2*tn*tn - 0.3*sk*sk + 0.15*tn*sk;
    if (soft < 1) soft = 1; if (soft > 10) soft = 10;
    if (color < 1) color = 1; if (color > 10) color = 10;
    printf "{\\"softness_score\\": %.1f, \\"color_uniformity\\": %.1f}", soft + n1*0.3, color + n2*0.3;
""",
     "factor_cases": '--tannin_pct) TN="$2"; shift 2 ;;\n        --soak_hrs) SK="$2"; shift 2 ;;\n        --ph) PH="$2"; shift 2 ;;\n        --fat_liquor_pct) FL="$2"; shift 2 ;;',
     "awk_vars": '-v TN="$TN" -v SK="$SK" -v PH="$PH" -v FL="$FL"',
     "vars_init": 'TN=""\nSK=""\nPH=""\nFL=""', "validate": '[ -z "$TN" ] || [ -z "$SK" ] || [ -z "$PH" ] || [ -z "$FL" ]'},

    {"num": 181, "slug": "embroidery_design", "name": "Machine Embroidery Settings",
     "desc": "Box-Behnken design to maximize design fidelity and minimize puckering by tuning stitch density, stabilizer weight, and hoop tension",
     "design": "box_behnken", "category": "textiles",
     "factors": [
         {"name": "density_sts_cm", "levels": ["3", "8"], "type": "continuous", "unit": "sts/cm", "description": "Fill stitch density"},
         {"name": "stabilizer_gsm", "levels": ["40", "120"], "type": "continuous", "unit": "g/m2", "description": "Stabilizer backing weight"},
         {"name": "hoop_tension", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "Hoop tension level"},
     ],
     "fixed": {"machine": "single_needle", "thread": "rayon_40wt"},
     "responses": [
         {"name": "fidelity_score", "optimize": "maximize", "unit": "pts", "description": "Design fidelity and detail (1-10)"},
         {"name": "pucker_score", "optimize": "minimize", "unit": "pts", "description": "Fabric puckering severity (1-10)"},
     ],
     "model": """
    ds = (DS - 5.5) / 2.5; st = (ST - 80) / 40; ht = (HT - 3) / 2;
    fid = 6.0 + 1.0*ds + 0.5*st + 0.3*ht - 0.5*ds*ds - 0.2*st*st + 0.2*ds*st;
    puck = 4.0 + 0.8*ds - 0.6*st + 0.3*ht + 0.3*ds*ds - 0.2*st*st + 0.2*ds*ht;
    if (fid < 1) fid = 1; if (fid > 10) fid = 10;
    if (puck < 1) puck = 1; if (puck > 10) puck = 10;
    printf "{\\"fidelity_score\\": %.1f, \\"pucker_score\\": %.1f}", fid + n1*0.3, puck + n2*0.3;
""",
     "factor_cases": '--density_sts_cm) DS="$2"; shift 2 ;;\n        --stabilizer_gsm) ST="$2"; shift 2 ;;\n        --hoop_tension) HT="$2"; shift 2 ;;',
     "awk_vars": '-v DS="$DS" -v ST="$ST" -v HT="$HT"',
     "vars_init": 'DS=""\nST=""\nHT=""', "validate": '[ -z "$DS" ] || [ -z "$ST" ] || [ -z "$HT" ]'},

    {"num": 182, "slug": "shoe_comfort", "name": "Running Shoe Comfort Design",
     "desc": "Central composite design to maximize cushioning and energy return by tuning midsole thickness, foam density, and drop height",
     "design": "central_composite", "category": "textiles",
     "factors": [
         {"name": "midsole_mm", "levels": ["20", "40"], "type": "continuous", "unit": "mm", "description": "Midsole stack height"},
         {"name": "foam_density", "levels": ["150", "300"], "type": "continuous", "unit": "kg/m3", "description": "Foam material density"},
         {"name": "drop_mm", "levels": ["0", "12"], "type": "continuous", "unit": "mm", "description": "Heel-to-toe drop"},
     ],
     "fixed": {"upper": "knit_mesh", "outsole": "rubber"},
     "responses": [
         {"name": "cushion_score", "optimize": "maximize", "unit": "pts", "description": "Impact cushioning score (1-10)"},
         {"name": "energy_return_pct", "optimize": "maximize", "unit": "%", "description": "Energy return percentage"},
     ],
     "model": """
    ms = (MS - 30) / 10; fd = (FD - 225) / 75; dr = (DR - 6) / 6;
    cush = 6.5 + 1.2*ms - 0.8*fd + 0.3*dr - 0.4*ms*ms + 0.2*fd*fd + 0.2*ms*fd;
    ret = 60 + 3*ms - 5*fd + 1*dr + 2*fd*fd - 1*ms*ms + 1*ms*fd;
    if (cush < 1) cush = 1; if (cush > 10) cush = 10;
    if (ret < 30) ret = 30; if (ret > 85) ret = 85;
    printf "{\\"cushion_score\\": %.1f, \\"energy_return_pct\\": %.0f}", cush + n1*0.3, ret + n2*2;
""",
     "factor_cases": '--midsole_mm) MS="$2"; shift 2 ;;\n        --foam_density) FD="$2"; shift 2 ;;\n        --drop_mm) DR="$2"; shift 2 ;;',
     "awk_vars": '-v MS="$MS" -v FD="$FD" -v DR="$DR"',
     "vars_init": 'MS=""\nFD=""\nDR=""', "validate": '[ -z "$MS" ] || [ -z "$FD" ] || [ -z "$DR" ]'},

    {"num": 183, "slug": "screen_printing", "name": "Screen Printing Quality",
     "desc": "Box-Behnken design to maximize print sharpness and ink adhesion by tuning mesh count, squeegee pressure, and ink viscosity",
     "design": "box_behnken", "category": "textiles",
     "factors": [
         {"name": "mesh_count", "levels": ["110", "300"], "type": "continuous", "unit": "threads/in", "description": "Screen mesh thread count"},
         {"name": "squeegee_pressure", "levels": ["2", "8"], "type": "continuous", "unit": "kg/cm", "description": "Squeegee pressure"},
         {"name": "ink_viscosity", "levels": ["2000", "8000"], "type": "continuous", "unit": "cP", "description": "Ink viscosity in centipoise"},
     ],
     "fixed": {"substrate": "cotton_tshirt", "ink_type": "plastisol"},
     "responses": [
         {"name": "sharpness", "optimize": "maximize", "unit": "pts", "description": "Print edge sharpness and detail (1-10)"},
         {"name": "adhesion_score", "optimize": "maximize", "unit": "pts", "description": "Ink adhesion after wash (1-10)"},
     ],
     "model": """
    mc = (MC - 205) / 95; sp = (SP - 5) / 3; iv = (IV - 5000) / 3000;
    sharp = 6.5 + 1.0*mc + 0.5*sp - 0.8*iv - 0.3*mc*mc - 0.2*sp*sp + 0.2*mc*sp;
    adh = 6.0 - 0.3*mc + 0.8*sp + 0.3*iv - 0.2*mc*mc - 0.3*sp*sp + 0.2*sp*iv;
    if (sharp < 1) sharp = 1; if (sharp > 10) sharp = 10;
    if (adh < 1) adh = 1; if (adh > 10) adh = 10;
    printf "{\\"sharpness\\": %.1f, \\"adhesion_score\\": %.1f}", sharp + n1*0.3, adh + n2*0.3;
""",
     "factor_cases": '--mesh_count) MC="$2"; shift 2 ;;\n        --squeegee_pressure) SP="$2"; shift 2 ;;\n        --ink_viscosity) IV="$2"; shift 2 ;;',
     "awk_vars": '-v MC="$MC" -v SP="$SP" -v IV="$IV"',
     "vars_init": 'MC=""\nSP=""\nIV=""', "validate": '[ -z "$MC" ] || [ -z "$SP" ] || [ -z "$IV" ]'},

    {"num": 184, "slug": "wool_felting", "name": "Wool Felting Process",
     "desc": "Fractional factorial screening of water temperature, agitation time, soap concentration, fiber blend, and compression cycles for shrinkage control and density",
     "design": "fractional_factorial", "category": "textiles",
     "factors": [
         {"name": "water_temp_c", "levels": ["40", "80"], "type": "continuous", "unit": "C", "description": "Water temperature"},
         {"name": "agitation_min", "levels": ["5", "30"], "type": "continuous", "unit": "min", "description": "Agitation time"},
         {"name": "soap_ml_L", "levels": ["1", "10"], "type": "continuous", "unit": "mL/L", "description": "Soap concentration"},
         {"name": "merino_pct", "levels": ["50", "100"], "type": "continuous", "unit": "%", "description": "Merino wool percentage in blend"},
         {"name": "compressions", "levels": ["10", "50"], "type": "continuous", "unit": "cycles", "description": "Manual compression cycles"},
     ],
     "fixed": {"technique": "wet_felting", "thickness": "medium"},
     "responses": [
         {"name": "shrinkage_pct", "optimize": "minimize", "unit": "%", "description": "Dimensional shrinkage percentage"},
         {"name": "density_score", "optimize": "maximize", "unit": "pts", "description": "Felt density and firmness (1-10)"},
     ],
     "model": """
    wt = (WT - 60) / 20; ag = (AG - 17.5) / 12.5; sp = (SP - 5.5) / 4.5; mp = (MP - 75) / 25; cm = (CM - 30) / 20;
    shrink = 20 + 5*wt + 6*ag + 2*sp + 3*mp + 4*cm + 1*wt*ag + 0.5*mp*cm;
    dens = 5.0 + 0.8*wt + 1.0*ag + 0.3*sp + 0.5*mp + 0.8*cm + 0.2*ag*cm;
    if (shrink < 5) shrink = 5; if (shrink > 50) shrink = 50;
    if (dens < 1) dens = 1; if (dens > 10) dens = 10;
    printf "{\\"shrinkage_pct\\": %.0f, \\"density_score\\": %.1f}", shrink + n1*2, dens + n2*0.3;
""",
     "factor_cases": '--water_temp_c) WT="$2"; shift 2 ;;\n        --agitation_min) AG="$2"; shift 2 ;;\n        --soap_ml_L) SP="$2"; shift 2 ;;\n        --merino_pct) MP="$2"; shift 2 ;;\n        --compressions) CM="$2"; shift 2 ;;',
     "awk_vars": '-v WT="$WT" -v AG="$AG" -v SP="$SP" -v MP="$MP" -v CM="$CM"',
     "vars_init": 'WT=""\nAG=""\nSP=""\nMP=""\nCM=""', "validate": '[ -z "$WT" ] || [ -z "$AG" ] || [ -z "$SP" ] || [ -z "$MP" ]'},

    {"num": 185, "slug": "tie_dye_pattern", "name": "Tie-Dye Pattern Control",
     "desc": "Box-Behnken design to maximize color vibrancy and pattern definition by tuning dye soak time, soda ash concentration, and rubber band tightness",
     "design": "box_behnken", "category": "textiles",
     "factors": [
         {"name": "soak_hrs", "levels": ["4", "24"], "type": "continuous", "unit": "hrs", "description": "Dye soak/cure time"},
         {"name": "soda_ash_g_L", "levels": ["10", "50"], "type": "continuous", "unit": "g/L", "description": "Soda ash fixative concentration"},
         {"name": "band_tightness", "levels": ["1", "5"], "type": "continuous", "unit": "level", "description": "Rubber band tightness (1=loose, 5=tight)"},
     ],
     "fixed": {"fabric": "100pct_cotton", "dye_type": "fiber_reactive"},
     "responses": [
         {"name": "vibrancy", "optimize": "maximize", "unit": "pts", "description": "Color vibrancy score (1-10)"},
         {"name": "pattern_definition", "optimize": "maximize", "unit": "pts", "description": "Pattern edge definition (1-10)"},
     ],
     "model": """
    sh = (SH - 14) / 10; sa = (SA - 30) / 20; bt = (BT - 3) / 2;
    vib = 6.0 + 1.0*sh + 0.8*sa + 0.3*bt - 0.3*sh*sh - 0.2*sa*sa + 0.2*sh*sa;
    pat = 5.5 + 0.3*sh + 0.2*sa + 1.5*bt - 0.2*sh*sh + 0.1*sa*sa - 0.4*bt*bt + 0.2*sh*bt;
    if (vib < 1) vib = 1; if (vib > 10) vib = 10;
    if (pat < 1) pat = 1; if (pat > 10) pat = 10;
    printf "{\\"vibrancy\\": %.1f, \\"pattern_definition\\": %.1f}", vib + n1*0.3, pat + n2*0.3;
""",
     "factor_cases": '--soak_hrs) SH="$2"; shift 2 ;;\n        --soda_ash_g_L) SA="$2"; shift 2 ;;\n        --band_tightness) BT="$2"; shift 2 ;;',
     "awk_vars": '-v SH="$SH" -v SA="$SA" -v BT="$BT"',
     "vars_init": 'SH=""\nSA=""\nBT=""', "validate": '[ -z "$SH" ] || [ -z "$SA" ] || [ -z "$BT" ]'},

    {"num": 186, "slug": "iron_press_settings", "name": "Garment Pressing Settings",
     "desc": "Central composite design to maximize crease sharpness and minimize fabric shine by tuning iron temperature, steam output, and pressing duration",
     "design": "central_composite", "category": "textiles",
     "factors": [
         {"name": "iron_temp_c", "levels": ["110", "200"], "type": "continuous", "unit": "C", "description": "Iron sole plate temperature"},
         {"name": "steam_g_min", "levels": ["0", "40"], "type": "continuous", "unit": "g/min", "description": "Steam output rate"},
         {"name": "press_sec", "levels": ["3", "15"], "type": "continuous", "unit": "sec", "description": "Pressing duration per area"},
     ],
     "fixed": {"fabric": "wool_blend", "press_cloth": "yes"},
     "responses": [
         {"name": "crease_sharpness", "optimize": "maximize", "unit": "pts", "description": "Crease definition score (1-10)"},
         {"name": "shine_risk", "optimize": "minimize", "unit": "pts", "description": "Fabric shine/glazing risk (1-10)"},
     ],
     "model": """
    it = (IT - 155) / 45; sg = (SG - 20) / 20; ps = (PS - 9) / 6;
    crease = 5.5 + 1.2*it + 0.8*sg + 0.6*ps - 0.3*it*it - 0.2*sg*sg + 0.2*it*sg;
    shine = 3.0 + 1.5*it + 0.3*sg + 0.8*ps + 0.5*it*it + 0.2*ps*ps + 0.3*it*ps;
    if (crease < 1) crease = 1; if (crease > 10) crease = 10;
    if (shine < 1) shine = 1; if (shine > 10) shine = 10;
    printf "{\\"crease_sharpness\\": %.1f, \\"shine_risk\\": %.1f}", crease + n1*0.3, shine + n2*0.3;
""",
     "factor_cases": '--iron_temp_c) IT="$2"; shift 2 ;;\n        --steam_g_min) SG="$2"; shift 2 ;;\n        --press_sec) PS="$2"; shift 2 ;;',
     "awk_vars": '-v IT="$IT" -v SG="$SG" -v PS="$PS"',
     "vars_init": 'IT=""\nSG=""\nPS=""', "validate": '[ -z "$IT" ] || [ -z "$SG" ] || [ -z "$PS" ]'},

    # ══════════════════════════════════════════════════
    # Chemistry & Lab Science (187-196)
    # ══════════════════════════════════════════════════
    {"num": 187, "slug": "titration_accuracy", "name": "Titration Accuracy Optimization",
     "desc": "Box-Behnken design to maximize endpoint precision and minimize reagent waste by tuning drop size, stirring speed, and indicator concentration",
     "design": "box_behnken", "category": "chemistry",
     "factors": [
         {"name": "drop_size_ul", "levels": ["10", "100"], "type": "continuous", "unit": "uL", "description": "Burette drop size near endpoint"},
         {"name": "stir_rpm", "levels": ["100", "600"], "type": "continuous", "unit": "rpm", "description": "Magnetic stirrer speed"},
         {"name": "indicator_pct", "levels": ["0.05", "0.5"], "type": "continuous", "unit": "%", "description": "Indicator solution concentration"},
     ],
     "fixed": {"analyte": "HCl", "titrant": "NaOH"},
     "responses": [
         {"name": "precision_pct", "optimize": "maximize", "unit": "%", "description": "Endpoint precision (100% - %error)"},
         {"name": "reagent_waste_ml", "optimize": "minimize", "unit": "mL", "description": "Excess titrant past endpoint"},
     ],
     "model": """
    ds = (DS - 55) / 45; sr = (SR - 350) / 250; ic = (IC - 0.275) / 0.225;
    prec = 96 - 2*ds + 0.5*sr + 1*ic + 1*ds*ds - 0.3*sr*sr - 0.5*ic*ic + 0.3*sr*ic;
    waste = 0.5 + 0.3*ds - 0.1*sr - 0.05*ic + 0.1*ds*ds;
    if (prec < 80) prec = 80; if (prec > 100) prec = 100;
    if (waste < 0.02) waste = 0.02;
    printf "{\\"precision_pct\\": %.1f, \\"reagent_waste_ml\\": %.2f}", prec + n1*0.5, waste + n2*0.03;
""",
     "factor_cases": '--drop_size_ul) DS="$2"; shift 2 ;;\n        --stir_rpm) SR="$2"; shift 2 ;;\n        --indicator_pct) IC="$2"; shift 2 ;;',
     "awk_vars": '-v DS="$DS" -v SR="$SR" -v IC="$IC"',
     "vars_init": 'DS=""\nSR=""\nIC=""', "validate": '[ -z "$DS" ] || [ -z "$SR" ] || [ -z "$IC" ]'},

    {"num": 188, "slug": "crystallization", "name": "Crystal Growth Optimization",
     "desc": "Central composite design to maximize crystal size and purity by tuning cooling rate, supersaturation, and seed crystal size",
     "design": "central_composite", "category": "chemistry",
     "factors": [
         {"name": "cool_rate_c_hr", "levels": ["0.5", "5.0"], "type": "continuous", "unit": "C/hr", "description": "Cooling rate"},
         {"name": "supersaturation", "levels": ["1.1", "1.5"], "type": "continuous", "unit": "ratio", "description": "Initial supersaturation ratio"},
         {"name": "seed_mm", "levels": ["0.1", "2.0"], "type": "continuous", "unit": "mm", "description": "Seed crystal size"},
     ],
     "fixed": {"solvent": "water", "compound": "copper_sulfate"},
     "responses": [
         {"name": "crystal_size_mm", "optimize": "maximize", "unit": "mm", "description": "Average crystal dimension"},
         {"name": "purity_pct", "optimize": "maximize", "unit": "%", "description": "Crystal purity percentage"},
     ],
     "model": """
    cr = (CR - 2.75) / 2.25; ss = (SS - 1.3) / 0.2; sd = (SD - 1.05) / 0.95;
    size = 5 - 2*cr + 1.5*ss + 1*sd + 0.5*cr*cr - 0.8*ss*ss + 0.3*sd*sd + 0.5*cr*ss;
    pur = 95 + 2*cr - 3*ss + 0.5*sd - 1*cr*cr + 1.5*ss*ss + 0.5*cr*ss;
    if (size < 0.5) size = 0.5;
    if (pur < 80) pur = 80; if (pur > 100) pur = 100;
    printf "{\\"crystal_size_mm\\": %.1f, \\"purity_pct\\": %.1f}", size + n1*0.3, pur + n2*0.5;
""",
     "factor_cases": '--cool_rate_c_hr) CR="$2"; shift 2 ;;\n        --supersaturation) SS="$2"; shift 2 ;;\n        --seed_mm) SD="$2"; shift 2 ;;',
     "awk_vars": '-v CR="$CR" -v SS="$SS" -v SD="$SD"',
     "vars_init": 'CR=""\nSS=""\nSD=""', "validate": '[ -z "$CR" ] || [ -z "$SS" ] || [ -z "$SD" ]'},

    {"num": 189, "slug": "chromatography_separation", "name": "Chromatography Separation",
     "desc": "Box-Behnken design to maximize resolution and minimize run time by tuning flow rate, mobile phase ratio, and column temperature",
     "design": "box_behnken", "category": "chemistry",
     "factors": [
         {"name": "flow_ml_min", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "mL/min", "description": "Mobile phase flow rate"},
         {"name": "organic_pct", "levels": ["30", "80"], "type": "continuous", "unit": "%", "description": "Organic solvent percentage in mobile phase"},
         {"name": "column_temp_c", "levels": ["25", "55"], "type": "continuous", "unit": "C", "description": "Column oven temperature"},
     ],
     "fixed": {"column": "C18_150mm", "detector": "UV_254nm"},
     "responses": [
         {"name": "resolution", "optimize": "maximize", "unit": "Rs", "description": "Peak resolution between critical pair"},
         {"name": "run_time_min", "optimize": "minimize", "unit": "min", "description": "Total chromatographic run time"},
     ],
     "model": """
    fl = (FL - 1.25) / 0.75; op = (OP - 55) / 25; ct = (CT - 40) / 15;
    res = 2.5 - 0.5*fl + 0.3*op + 0.2*ct + 0.3*fl*fl - 0.5*op*op - 0.2*ct*ct + 0.2*fl*op;
    run = 15 - 4*fl - 3*op - 1.5*ct + 1*fl*fl + 0.5*op*op;
    if (res < 0.5) res = 0.5;
    if (run < 3) run = 3;
    printf "{\\"resolution\\": %.2f, \\"run_time_min\\": %.1f}", res + n1*0.1, run + n2*0.5;
""",
     "factor_cases": '--flow_ml_min) FL="$2"; shift 2 ;;\n        --organic_pct) OP="$2"; shift 2 ;;\n        --column_temp_c) CT="$2"; shift 2 ;;',
     "awk_vars": '-v FL="$FL" -v OP="$OP" -v CT="$CT"',
     "vars_init": 'FL=""\nOP=""\nCT=""', "validate": '[ -z "$FL" ] || [ -z "$OP" ] || [ -z "$CT" ]'},

    {"num": 190, "slug": "pcr_amplification", "name": "PCR Amplification Efficiency",
     "desc": "Full factorial of annealing temperature, primer concentration, MgCl2 concentration, and cycle count to maximize yield and minimize non-specific bands",
     "design": "full_factorial", "category": "chemistry",
     "factors": [
         {"name": "anneal_temp_c", "levels": ["52", "65"], "type": "continuous", "unit": "C", "description": "Annealing step temperature"},
         {"name": "primer_nm", "levels": ["200", "600"], "type": "continuous", "unit": "nM", "description": "Primer concentration"},
         {"name": "mgcl2_mm", "levels": ["1.0", "3.0"], "type": "continuous", "unit": "mM", "description": "MgCl2 concentration"},
         {"name": "cycles", "levels": ["25", "40"], "type": "continuous", "unit": "cycles", "description": "Number of PCR cycles"},
     ],
     "fixed": {"polymerase": "taq", "template_ng": "50"},
     "responses": [
         {"name": "yield_score", "optimize": "maximize", "unit": "pts", "description": "Target band yield intensity (1-10)"},
         {"name": "specificity", "optimize": "maximize", "unit": "pts", "description": "Band specificity score (1-10, 10=no non-specific)"},
     ],
     "model": """
    at = (AT - 58.5) / 6.5; pn = (PN - 400) / 200; mg = (MG - 2) / 1; cy = (CY - 32.5) / 7.5;
    yld = 6.0 + 0.3*at + 0.8*pn + 0.5*mg + 1.0*cy - 0.5*at*at - 0.3*pn*pn + 0.2*pn*cy;
    spec = 7.0 + 1.0*at - 0.5*pn - 0.8*mg - 0.5*cy - 0.3*at*at + 0.2*mg*mg + 0.2*at*mg;
    if (yld < 1) yld = 1; if (yld > 10) yld = 10;
    if (spec < 1) spec = 1; if (spec > 10) spec = 10;
    printf "{\\"yield_score\\": %.1f, \\"specificity\\": %.1f}", yld + n1*0.3, spec + n2*0.3;
""",
     "factor_cases": '--anneal_temp_c) AT="$2"; shift 2 ;;\n        --primer_nm) PN="$2"; shift 2 ;;\n        --mgcl2_mm) MG="$2"; shift 2 ;;\n        --cycles) CY="$2"; shift 2 ;;',
     "awk_vars": '-v AT="$AT" -v PN="$PN" -v MG="$MG" -v CY="$CY"',
     "vars_init": 'AT=""\nPN=""\nMG=""\nCY=""', "validate": '[ -z "$AT" ] || [ -z "$PN" ] || [ -z "$MG" ] || [ -z "$CY" ]'},

    {"num": 191, "slug": "ph_buffer_prep", "name": "pH Buffer Preparation",
     "desc": "Box-Behnken design to maximize buffer capacity and minimize temperature sensitivity by tuning buffer concentration, acid-base ratio, and ionic strength",
     "design": "box_behnken", "category": "chemistry",
     "factors": [
         {"name": "concentration_mm", "levels": ["10", "100"], "type": "continuous", "unit": "mM", "description": "Total buffer concentration"},
         {"name": "acid_base_ratio", "levels": ["0.5", "2.0"], "type": "continuous", "unit": "ratio", "description": "Weak acid to conjugate base ratio"},
         {"name": "ionic_strength_mm", "levels": ["50", "300"], "type": "continuous", "unit": "mM", "description": "Total ionic strength from added salt"},
     ],
     "fixed": {"buffer_system": "phosphate", "target_ph": "7.4"},
     "responses": [
         {"name": "buffer_capacity", "optimize": "maximize", "unit": "mmol/L/pH", "description": "Buffer capacity in mmol per pH unit change"},
         {"name": "temp_sensitivity", "optimize": "minimize", "unit": "dpH/dC", "description": "pH change per degree Celsius"},
     ],
     "model": """
    cn = (CN - 55) / 45; ar = (AR - 1.25) / 0.75; is = (IS - 175) / 125;
    cap = 15 + 8*cn + 0.5*ar + 1*is - 2*cn*cn - 3*ar*ar + 0.5*cn*ar;
    temp = 0.005 + 0.001*cn + 0.002*ar + 0.001*is + 0.0005*ar*ar;
    if (cap < 1) cap = 1;
    if (temp < 0.001) temp = 0.001;
    printf "{\\"buffer_capacity\\": %.1f, \\"temp_sensitivity\\": %.4f}", cap + n1*0.5, temp + n2*0.0003;
""",
     "factor_cases": '--concentration_mm) CN="$2"; shift 2 ;;\n        --acid_base_ratio) AR="$2"; shift 2 ;;\n        --ionic_strength_mm) IS="$2"; shift 2 ;;',
     "awk_vars": '-v CN="$CN" -v AR="$AR" -v IS="$IS"',
     "vars_init": 'CN=""\nAR=""\nIS=""', "validate": '[ -z "$CN" ] || [ -z "$AR" ] || [ -z "$IS" ]'},

    {"num": 192, "slug": "distillation_purity", "name": "Lab Distillation Purity",
     "desc": "Central composite design to maximize distillate purity and recovery by tuning reflux ratio, heating rate, and column packing height",
     "design": "central_composite", "category": "chemistry",
     "factors": [
         {"name": "reflux_ratio", "levels": ["1", "5"], "type": "continuous", "unit": "ratio", "description": "Reflux ratio (return:collect)"},
         {"name": "heat_rate_c_min", "levels": ["0.5", "3.0"], "type": "continuous", "unit": "C/min", "description": "Heating mantle rate"},
         {"name": "packing_cm", "levels": ["10", "50"], "type": "continuous", "unit": "cm", "description": "Column packing height"},
     ],
     "fixed": {"mixture": "ethanol_water", "column_diam": "25mm"},
     "responses": [
         {"name": "purity_pct", "optimize": "maximize", "unit": "%", "description": "Distillate purity percentage"},
         {"name": "recovery_pct", "optimize": "maximize", "unit": "%", "description": "Product recovery percentage"},
     ],
     "model": """
    rr = (RR - 3) / 2; hr = (HR - 1.75) / 1.25; pc = (PC - 30) / 20;
    pur = 88 + 3*rr - 2*hr + 4*pc - 1*rr*rr + 0.5*hr*hr - 1*pc*pc + 0.5*rr*pc;
    rec = 75 - 5*rr + 3*hr - 2*pc + 1*rr*rr - 1*hr*hr + 0.5*rr*hr;
    if (pur < 70) pur = 70; if (pur > 99.9) pur = 99.9;
    if (rec < 40) rec = 40; if (rec > 98) rec = 98;
    printf "{\\"purity_pct\\": %.1f, \\"recovery_pct\\": %.0f}", pur + n1*0.5, rec + n2*2;
""",
     "factor_cases": '--reflux_ratio) RR="$2"; shift 2 ;;\n        --heat_rate_c_min) HR="$2"; shift 2 ;;\n        --packing_cm) PC="$2"; shift 2 ;;',
     "awk_vars": '-v RR="$RR" -v HR="$HR" -v PC="$PC"',
     "vars_init": 'RR=""\nHR=""\nPC=""', "validate": '[ -z "$RR" ] || [ -z "$HR" ] || [ -z "$PC" ]'},

    {"num": 193, "slug": "spectrophotometry", "name": "UV-Vis Spectrophotometry",
     "desc": "Box-Behnken design to maximize signal-to-noise ratio and minimize baseline drift by tuning slit width, scan speed, and sample path length",
     "design": "box_behnken", "category": "chemistry",
     "factors": [
         {"name": "slit_nm", "levels": ["0.5", "5.0"], "type": "continuous", "unit": "nm", "description": "Monochromator slit width"},
         {"name": "scan_speed", "levels": ["100", "1000"], "type": "continuous", "unit": "nm/min", "description": "Wavelength scan speed"},
         {"name": "path_cm", "levels": ["0.1", "5.0"], "type": "continuous", "unit": "cm", "description": "Cuvette path length"},
     ],
     "fixed": {"lamp": "deuterium", "wavelength": "260nm"},
     "responses": [
         {"name": "snr", "optimize": "maximize", "unit": "ratio", "description": "Signal-to-noise ratio"},
         {"name": "baseline_drift", "optimize": "minimize", "unit": "AU/hr", "description": "Baseline drift in absorbance units per hour"},
     ],
     "model": """
    sl = (SL - 2.75) / 2.25; ss = (SS - 550) / 450; pl = (PL - 2.55) / 2.45;
    snr = 200 + 50*sl - 30*ss + 40*pl - 15*sl*sl + 10*ss*ss + 5*sl*pl;
    drift = 0.005 + 0.001*sl + 0.002*ss + 0.0005*pl + 0.0003*ss*ss;
    if (snr < 20) snr = 20;
    if (drift < 0.001) drift = 0.001;
    printf "{\\"snr\\": %.0f, \\"baseline_drift\\": %.4f}", snr + n1*10, drift + n2*0.0005;
""",
     "factor_cases": '--slit_nm) SL="$2"; shift 2 ;;\n        --scan_speed) SS="$2"; shift 2 ;;\n        --path_cm) PL="$2"; shift 2 ;;',
     "awk_vars": '-v SL="$SL" -v SS="$SS" -v PL="$PL"',
     "vars_init": 'SL=""\nSS=""\nPL=""', "validate": '[ -z "$SL" ] || [ -z "$SS" ] || [ -z "$PL" ]'},

    {"num": 194, "slug": "electroplating", "name": "Electroplating Thickness Control",
     "desc": "Plackett-Burman screening of current density, bath temperature, plating time, pH, and agitation for uniform coating thickness and adhesion",
     "design": "plackett_burman", "category": "chemistry",
     "factors": [
         {"name": "current_density", "levels": ["1", "10"], "type": "continuous", "unit": "A/dm2", "description": "Cathode current density"},
         {"name": "bath_temp_c", "levels": ["20", "55"], "type": "continuous", "unit": "C", "description": "Plating bath temperature"},
         {"name": "time_min", "levels": ["5", "60"], "type": "continuous", "unit": "min", "description": "Plating duration"},
         {"name": "bath_ph", "levels": ["2", "5"], "type": "continuous", "unit": "pH", "description": "Bath pH"},
         {"name": "agitation_rpm", "levels": ["0", "200"], "type": "continuous", "unit": "rpm", "description": "Bath agitation speed"},
     ],
     "fixed": {"metal": "nickel", "substrate": "mild_steel"},
     "responses": [
         {"name": "thickness_um", "optimize": "maximize", "unit": "um", "description": "Average coating thickness"},
         {"name": "adhesion_score", "optimize": "maximize", "unit": "pts", "description": "Adhesion tape test score (1-5)"},
     ],
     "model": """
    cd = (CD - 5.5) / 4.5; bt = (BT - 37.5) / 17.5; tm = (TM - 32.5) / 27.5; ph = (PH - 3.5) / 1.5; ag = (AG - 100) / 100;
    thick = 15 + 8*cd + 2*bt + 10*tm + 1*ph + 1*ag + 2*cd*tm;
    adh = 3.5 - 0.3*cd + 0.5*bt + 0.2*tm + 0.4*ph + 0.2*ag - 0.3*cd*cd + 0.1*ph*bt;
    if (thick < 1) thick = 1;
    if (adh < 1) adh = 1; if (adh > 5) adh = 5;
    printf "{\\"thickness_um\\": %.0f, \\"adhesion_score\\": %.1f}", thick + n1*1, adh + n2*0.15;
""",
     "factor_cases": '--current_density) CD="$2"; shift 2 ;;\n        --bath_temp_c) BT="$2"; shift 2 ;;\n        --time_min) TM="$2"; shift 2 ;;\n        --bath_ph) PH="$2"; shift 2 ;;\n        --agitation_rpm) AG="$2"; shift 2 ;;',
     "awk_vars": '-v CD="$CD" -v BT="$BT" -v TM="$TM" -v PH="$PH" -v AG="$AG"',
     "vars_init": 'CD=""\nBT=""\nTM=""\nPH=""\nAG=""', "validate": '[ -z "$CD" ] || [ -z "$BT" ] || [ -z "$TM" ] || [ -z "$PH" ]'},

    {"num": 195, "slug": "enzyme_kinetics", "name": "Enzyme Kinetics Assay",
     "desc": "Full factorial of substrate concentration, enzyme amount, pH, and temperature to maximize reaction rate and minimize substrate inhibition",
     "design": "full_factorial", "category": "chemistry",
     "factors": [
         {"name": "substrate_mm", "levels": ["0.1", "10"], "type": "continuous", "unit": "mM", "description": "Substrate concentration"},
         {"name": "enzyme_ug", "levels": ["1", "20"], "type": "continuous", "unit": "ug", "description": "Enzyme amount"},
         {"name": "ph", "levels": ["5", "9"], "type": "continuous", "unit": "pH", "description": "Buffer pH"},
         {"name": "temp_c", "levels": ["20", "45"], "type": "continuous", "unit": "C", "description": "Reaction temperature"},
     ],
     "fixed": {"enzyme": "alkaline_phosphatase", "buffer": "tris"},
     "responses": [
         {"name": "reaction_rate", "optimize": "maximize", "unit": "umol/min", "description": "Initial reaction rate"},
         {"name": "inhibition_pct", "optimize": "minimize", "unit": "%", "description": "Substrate inhibition percentage"},
     ],
     "model": """
    sb = (SB - 5.05) / 4.95; en = (EN - 10.5) / 9.5; ph = (PH - 7) / 2; tp = (TP - 32.5) / 12.5;
    rate = 5 + 2*sb + 3*en + 0.5*ph + 1.5*tp - 1.5*sb*sb - 0.5*en*en - 1*ph*ph - 0.8*tp*tp + 0.5*en*tp;
    inh = 5 + 8*sb - 1*en + 1*ph + 0.5*tp + 5*sb*sb + 1*ph*ph;
    if (rate < 0.1) rate = 0.1;
    if (inh < 0) inh = 0; if (inh > 50) inh = 50;
    printf "{\\"reaction_rate\\": %.1f, \\"inhibition_pct\\": %.0f}", rate + n1*0.3, inh + n2*2;
""",
     "factor_cases": '--substrate_mm) SB="$2"; shift 2 ;;\n        --enzyme_ug) EN="$2"; shift 2 ;;\n        --ph) PH="$2"; shift 2 ;;\n        --temp_c) TP="$2"; shift 2 ;;',
     "awk_vars": '-v SB="$SB" -v EN="$EN" -v PH="$PH" -v TP="$TP"',
     "vars_init": 'SB=""\nEN=""\nPH=""\nTP=""', "validate": '[ -z "$SB" ] || [ -z "$EN" ] || [ -z "$PH" ] || [ -z "$TP" ]'},

    {"num": 196, "slug": "gel_electrophoresis", "name": "Gel Electrophoresis Resolution",
     "desc": "Box-Behnken design to maximize band resolution and minimize run time by tuning gel percentage, voltage, and loading volume",
     "design": "box_behnken", "category": "chemistry",
     "factors": [
         {"name": "gel_pct", "levels": ["0.8", "2.5"], "type": "continuous", "unit": "%", "description": "Agarose gel percentage"},
         {"name": "voltage_v_cm", "levels": ["3", "10"], "type": "continuous", "unit": "V/cm", "description": "Electric field strength"},
         {"name": "load_ul", "levels": ["5", "25"], "type": "continuous", "unit": "uL", "description": "Sample loading volume"},
     ],
     "fixed": {"buffer": "TAE_1x", "stain": "ethidium_bromide"},
     "responses": [
         {"name": "resolution", "optimize": "maximize", "unit": "pts", "description": "Band resolution score (1-10)"},
         {"name": "run_time_min", "optimize": "minimize", "unit": "min", "description": "Total electrophoresis run time"},
     ],
     "model": """
    gp = (GP - 1.65) / 0.85; vl = (VL - 6.5) / 3.5; ld = (LD - 15) / 10;
    res = 6.5 + 0.8*gp - 0.5*vl - 0.3*ld - 0.4*gp*gp + 0.2*vl*vl + 0.2*gp*vl;
    run = 45 + 10*gp - 15*vl + 2*ld + 3*gp*gp + 2*vl*vl;
    if (res < 1) res = 1; if (res > 10) res = 10;
    if (run < 10) run = 10;
    printf "{\\"resolution\\": %.1f, \\"run_time_min\\": %.0f}", res + n1*0.3, run + n2*3;
""",
     "factor_cases": '--gel_pct) GP="$2"; shift 2 ;;\n        --voltage_v_cm) VL="$2"; shift 2 ;;\n        --load_ul) LD="$2"; shift 2 ;;',
     "awk_vars": '-v GP="$GP" -v VL="$VL" -v LD="$LD"',
     "vars_init": 'GP=""\nVL=""\nLD=""', "validate": '[ -z "$GP" ] || [ -z "$VL" ] || [ -z "$LD" ]'},

    # ══════════════════════════════════════════════════
    # General (197-198) — two more general use cases
    # ══════════════════════════════════════════════════
    {"num": 197, "slug": "moving_day_logistics", "name": "Moving Day Logistics",
     "desc": "Box-Behnken design to minimize total move time and breakage by tuning box size, crew size, and truck loading strategy padding thickness",
     "design": "box_behnken", "category": "general",
     "factors": [
         {"name": "box_volume_L", "levels": ["30", "80"], "type": "continuous", "unit": "L", "description": "Average moving box volume"},
         {"name": "crew_size", "levels": ["2", "6"], "type": "continuous", "unit": "people", "description": "Moving crew size"},
         {"name": "padding_layers", "levels": ["1", "4"], "type": "continuous", "unit": "layers", "description": "Bubble wrap padding layers on fragile items"},
     ],
     "fixed": {"distance_km": "20", "apartment_floor": "3"},
     "responses": [
         {"name": "total_hours", "optimize": "minimize", "unit": "hrs", "description": "Total move duration in hours"},
         {"name": "breakage_pct", "optimize": "minimize", "unit": "%", "description": "Percentage of items damaged"},
     ],
     "model": """
    bv = (BV - 55) / 25; cs = (CS - 4) / 2; pl = (PL - 2.5) / 1.5;
    hrs = 6 + 0.5*bv - 2*cs + 0.3*pl + 0.3*bv*bv + 0.5*cs*cs + 0.2*bv*cs;
    brk = 5 + 0.8*bv + 0.3*cs - 2*pl + 0.3*bv*bv + 0.5*pl*pl - 0.3*cs*pl;
    if (hrs < 2) hrs = 2;
    if (brk < 0) brk = 0; if (brk > 20) brk = 20;
    printf "{\\"total_hours\\": %.1f, \\"breakage_pct\\": %.1f}", hrs + n1*0.3, brk + n2*0.5;
""",
     "factor_cases": '--box_volume_L) BV="$2"; shift 2 ;;\n        --crew_size) CS="$2"; shift 2 ;;\n        --padding_layers) PL="$2"; shift 2 ;;',
     "awk_vars": '-v BV="$BV" -v CS="$CS" -v PL="$PL"',
     "vars_init": 'BV=""\nCS=""\nPL=""', "validate": '[ -z "$BV" ] || [ -z "$CS" ] || [ -z "$PL" ]'},

    {"num": 198, "slug": "party_planning", "name": "Party Planning Optimization",
     "desc": "Central composite design to maximize guest satisfaction and minimize cost per person by tuning venue size, food budget ratio, and entertainment hours",
     "design": "central_composite", "category": "general",
     "factors": [
         {"name": "sqft_per_guest", "levels": ["15", "40"], "type": "continuous", "unit": "sqft", "description": "Venue square feet per guest"},
         {"name": "food_budget_pct", "levels": ["30", "60"], "type": "continuous", "unit": "%", "description": "Food as percentage of total budget"},
         {"name": "entertainment_hrs", "levels": ["1", "4"], "type": "continuous", "unit": "hrs", "description": "Scheduled entertainment duration"},
     ],
     "fixed": {"guests": "50", "event_type": "birthday"},
     "responses": [
         {"name": "satisfaction", "optimize": "maximize", "unit": "pts", "description": "Guest satisfaction score (1-10)"},
         {"name": "cost_per_person", "optimize": "minimize", "unit": "USD", "description": "Total cost per guest"},
     ],
     "model": """
    sg = (SG - 27.5) / 12.5; fb = (FB - 45) / 15; eh = (EH - 2.5) / 1.5;
    sat = 6.5 + 0.5*sg + 1.0*fb + 0.8*eh - 0.3*sg*sg - 0.4*fb*fb - 0.3*eh*eh + 0.2*fb*eh;
    cost = 40 + 5*sg + 8*fb + 6*eh + 2*sg*sg + 1*fb*fb;
    if (sat < 1) sat = 1; if (sat > 10) sat = 10;
    if (cost < 15) cost = 15;
    printf "{\\"satisfaction\\": %.1f, \\"cost_per_person\\": %.0f}", sat + n1*0.3, cost + n2*3;
""",
     "factor_cases": '--sqft_per_guest) SG="$2"; shift 2 ;;\n        --food_budget_pct) FB="$2"; shift 2 ;;\n        --entertainment_hrs) EH="$2"; shift 2 ;;',
     "awk_vars": '-v SG="$SG" -v FB="$FB" -v EH="$EH"',
     "vars_init": 'SG=""\nFB=""\nEH=""', "validate": '[ -z "$SG" ] || [ -z "$FB" ] || [ -z "$EH" ]'},
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
    import json as j
    for uc in USE_CASES:
        num, slug = uc["num"], uc["slug"]
        uc_dir = f"use_cases/{num}_{slug}"
        os.makedirs(os.path.join(uc_dir, "results"), exist_ok=True)
        with open(os.path.join(uc_dir, "config.json"), "w") as f:
            j.dump(build_config(uc), f, indent=4)
        sim_path = os.path.join(uc_dir, "sim.sh")
        with open(sim_path, "w") as f:
            f.write(build_sim_script(uc))
        os.chmod(sim_path, os.stat(sim_path).st_mode | stat.S_IEXEC)
        print(f"  [{num:03d}] {uc_dir}/")
    print(f"\n  {len(USE_CASES)} use cases created (147-198).")


if __name__ == "__main__":
    main()
