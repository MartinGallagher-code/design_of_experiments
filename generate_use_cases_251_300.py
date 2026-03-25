#!/usr/bin/env python3
"""Generate 50 new use cases (251-300)."""
import json, os, stat, textwrap

USE_CASES = [
    # ══════ Marine & Aquatic Science (251-260) ══════
    {"num":251,"slug":"coral_reef_restoration","name":"Coral Reef Fragment Restoration","desc":"Box-Behnken design to maximize coral growth rate and survival by tuning fragment size, depth placement, and spacing","design":"box_behnken","category":"marine",
     "factors":[{"name":"fragment_cm","levels":["3","10"],"type":"continuous","unit":"cm","description":"Coral fragment length"},{"name":"depth_m","levels":["3","15"],"type":"continuous","unit":"m","description":"Planting depth"},{"name":"spacing_cm","levels":["10","40"],"type":"continuous","unit":"cm","description":"Inter-fragment spacing"}],
     "fixed":{"species":"acropora","substrate":"ceramic_disc"},
     "responses":[{"name":"growth_cm_yr","optimize":"maximize","unit":"cm/yr","description":"Annual linear growth"},{"name":"survival_pct","optimize":"maximize","unit":"%","description":"6-month survival rate"}],
     "model":'\n    f=(F-6.5)/3.5;d=(D-9)/6;s=(S-25)/15;\n    g=3.5+0.8*f-0.5*d+0.3*s-0.3*f*f-0.2*d*d+0.2*f*s;\n    sv=75+5*f-3*d+2*s-2*f*f-1.5*d*d+1*f*d;\n    if(g<0.5)g=0.5;if(sv<30)sv=30;if(sv>100)sv=100;\n    printf "{\\"growth_cm_yr\\": %.1f, \\"survival_pct\\": %.0f}",g+n1*0.2,sv+n2*3;\n',
     "factor_cases":'--fragment_cm) F="$2"; shift 2 ;;\n        --depth_m) D="$2"; shift 2 ;;\n        --spacing_cm) S="$2"; shift 2 ;;',
     "awk_vars":'-v F="$F" -v D="$D" -v S="$S"',"vars_init":'F=""\nD=""\nS=""',"validate":'[ -z "$F" ] || [ -z "$D" ] || [ -z "$S" ]'},

    {"num":252,"slug":"seawater_desalination","name":"Seawater Desalination Efficiency","desc":"Central composite design to maximize freshwater recovery and minimize energy use by tuning membrane pressure, feed temperature, and recovery ratio","design":"central_composite","category":"marine",
     "factors":[{"name":"pressure_bar","levels":["50","70"],"type":"continuous","unit":"bar","description":"Feed pressure"},{"name":"feed_temp_c","levels":["15","30"],"type":"continuous","unit":"C","description":"Feed water temperature"},{"name":"recovery_pct","levels":["35","55"],"type":"continuous","unit":"%","description":"Target water recovery percentage"}],
     "fixed":{"membrane":"RO_polyamide","salinity":"35000ppm"},
     "responses":[{"name":"permeate_lmh","optimize":"maximize","unit":"L/m2/hr","description":"Permeate flux"},{"name":"sec_kwh_m3","optimize":"minimize","unit":"kWh/m3","description":"Specific energy consumption"}],
     "model":'\n    p=(P-60)/10;t=(T-22.5)/7.5;r=(R-45)/10;\n    flux=25+5*p+3*t-4*r-2*p*p-1*t*t-1.5*r*r+1*p*t;\n    sec=3.5+0.5*p-0.3*t+0.8*r+0.2*p*p+0.3*r*r+0.2*p*r;\n    if(flux<5)flux=5;if(sec<2)sec=2;\n    printf "{\\"permeate_lmh\\": %.1f, \\"sec_kwh_m3\\": %.2f}",flux+n1*1,sec+n2*0.1;\n',
     "factor_cases":'--pressure_bar) P="$2"; shift 2 ;;\n        --feed_temp_c) T="$2"; shift 2 ;;\n        --recovery_pct) R="$2"; shift 2 ;;',
     "awk_vars":'-v P="$P" -v T="$T" -v R="$R"',"vars_init":'P=""\nT=""\nR=""',"validate":'[ -z "$P" ] || [ -z "$T" ] || [ -z "$R" ]'},

    {"num":253,"slug":"tidal_energy","name":"Tidal Turbine Placement","desc":"Box-Behnken design to maximize power output and minimize marine life impact by tuning turbine depth, rotor diameter, and cut-in speed","design":"box_behnken","category":"marine",
     "factors":[{"name":"depth_m","levels":["5","25"],"type":"continuous","unit":"m","description":"Turbine hub depth"},{"name":"rotor_m","levels":["5","20"],"type":"continuous","unit":"m","description":"Rotor diameter"},{"name":"cutin_ms","levels":["0.5","2.0"],"type":"continuous","unit":"m/s","description":"Cut-in current speed"}],
     "fixed":{"site":"tidal_channel","tidal_range":"4m"},
     "responses":[{"name":"annual_mwh","optimize":"maximize","unit":"MWh","description":"Annual energy production"},{"name":"impact_score","optimize":"minimize","unit":"pts","description":"Marine ecosystem impact score (1-10)"}],
     "model":'\n    d=(D-15)/10;r=(R-12.5)/7.5;c=(C-1.25)/0.75;\n    mwh=500+100*d+200*r-50*c-30*d*d-40*r*r+20*d*r;\n    imp=4+0.5*d+1.2*r-0.8*c+0.3*r*r+0.2*d*r;\n    if(mwh<50)mwh=50;if(imp<1)imp=1;if(imp>10)imp=10;\n    printf "{\\"annual_mwh\\": %.0f, \\"impact_score\\": %.1f}",mwh+n1*20,imp+n2*0.3;\n',
     "factor_cases":'--depth_m) D="$2"; shift 2 ;;\n        --rotor_m) R="$2"; shift 2 ;;\n        --cutin_ms) C="$2"; shift 2 ;;',
     "awk_vars":'-v D="$D" -v R="$R" -v C="$C"',"vars_init":'D=""\nR=""\nC=""',"validate":'[ -z "$D" ] || [ -z "$R" ] || [ -z "$C" ]'},

    {"num":254,"slug":"fish_farm_stocking","name":"Fish Farm Stocking Density","desc":"Full factorial of stocking density, feeding rate, water exchange, and aeration to maximize growth and minimize mortality","design":"full_factorial","category":"marine",
     "factors":[{"name":"density_kg_m3","levels":["10","40"],"type":"continuous","unit":"kg/m3","description":"Stocking density"},{"name":"feed_pct_bw","levels":["1","4"],"type":"continuous","unit":"%BW","description":"Daily feeding rate"},{"name":"exchange_pct","levels":["10","50"],"type":"continuous","unit":"%/day","description":"Daily water exchange"},{"name":"aeration","levels":["low","high"],"type":"categorical","unit":"","description":"Aeration level"}],
     "fixed":{"species":"atlantic_salmon","cage":"10m_pen"},
     "responses":[{"name":"growth_g_day","optimize":"maximize","unit":"g/day","description":"Average daily weight gain"},{"name":"mortality_pct","optimize":"minimize","unit":"%","description":"Monthly mortality rate"}],
     "model":'\n    dk=(DK-25)/15;fp=(FP-2.5)/1.5;ex=(EX-30)/20;ae=(AE=="high")?1:-1;\n    gr=8+1*dk+2*fp+1*ex+0.5*ae-0.8*dk*dk-0.5*fp*fp+0.3*dk*fp;\n    mort=3+1.5*dk+0.5*fp-1*ex-0.5*ae+0.5*dk*dk+0.3*dk*fp;\n    if(gr<1)gr=1;if(mort<0.5)mort=0.5;if(mort>15)mort=15;\n    printf "{\\"growth_g_day\\": %.1f, \\"mortality_pct\\": %.1f}",gr+n1*0.5,mort+n2*0.3;\n',
     "factor_cases":'--density_kg_m3) DK="$2"; shift 2 ;;\n        --feed_pct_bw) FP="$2"; shift 2 ;;\n        --exchange_pct) EX="$2"; shift 2 ;;\n        --aeration) AE="$2"; shift 2 ;;',
     "awk_vars":'-v DK="$DK" -v FP="$FP" -v EX="$EX" -v AE="$AE"',"vars_init":'DK=""\nFP=""\nEX=""\nAE=""',"validate":'[ -z "$DK" ] || [ -z "$FP" ] || [ -z "$EX" ] || [ -z "$AE" ]'},

    {"num":255,"slug":"wave_energy_buoy","name":"Wave Energy Converter Tuning","desc":"Box-Behnken design to maximize power capture and minimize mechanical stress by tuning buoy diameter, draft depth, and PTO damping","design":"box_behnken","category":"marine",
     "factors":[{"name":"buoy_diam_m","levels":["3","8"],"type":"continuous","unit":"m","description":"Buoy diameter"},{"name":"draft_m","levels":["2","6"],"type":"continuous","unit":"m","description":"Draft depth below waterline"},{"name":"pto_damping","levels":["1000","5000"],"type":"continuous","unit":"Ns/m","description":"Power take-off damping coefficient"}],
     "fixed":{"wave_height":"1.5m","wave_period":"8s"},
     "responses":[{"name":"power_kw","optimize":"maximize","unit":"kW","description":"Average power output"},{"name":"stress_mpa","optimize":"minimize","unit":"MPa","description":"Peak mooring stress"}],
     "model":'\n    bd=(BD-5.5)/2.5;dr=(DR-4)/2;pt=(PT-3000)/2000;\n    pwr=30+12*bd+5*dr+8*pt-3*bd*bd-2*dr*dr-3*pt*pt+2*bd*pt;\n    str_=15+4*bd+2*dr+3*pt+1*bd*bd+0.5*dr*dr+0.5*bd*dr;\n    if(pwr<2)pwr=2;if(str_<5)str_=5;\n    printf "{\\"power_kw\\": %.1f, \\"stress_mpa\\": %.0f}",pwr+n1*2,str_+n2*1;\n',
     "factor_cases":'--buoy_diam_m) BD="$2"; shift 2 ;;\n        --draft_m) DR="$2"; shift 2 ;;\n        --pto_damping) PT="$2"; shift 2 ;;',
     "awk_vars":'-v BD="$BD" -v DR="$DR" -v PT="$PT"',"vars_init":'BD=""\nDR=""\nPT=""',"validate":'[ -z "$BD" ] || [ -z "$DR" ] || [ -z "$PT" ]'},

    {"num":256,"slug":"mangrove_restoration","name":"Mangrove Restoration Planting","desc":"Central composite design to maximize seedling survival and growth by tuning planting density, tidal zone position, and sediment amendment","design":"central_composite","category":"marine",
     "factors":[{"name":"density_per_m2","levels":["1","6"],"type":"continuous","unit":"plants/m2","description":"Planting density"},{"name":"tidal_zone","levels":["1","3"],"type":"continuous","unit":"zone","description":"Tidal zone (1=low,3=high)"},{"name":"amendment_kg_m2","levels":["0","3"],"type":"continuous","unit":"kg/m2","description":"Sediment nutrient amendment"}],
     "fixed":{"species":"rhizophora","site":"estuary"},
     "responses":[{"name":"survival_1yr_pct","optimize":"maximize","unit":"%","description":"One-year survival percentage"},{"name":"height_gain_cm","optimize":"maximize","unit":"cm","description":"Height growth in first year"}],
     "model":'\n    dp=(DP-3.5)/2.5;tz=(TZ-2)/1;am=(AM-1.5)/1.5;\n    surv=65+5*dp-3*tz+8*am-3*dp*dp+2*tz*tz-2*am*am+2*dp*am;\n    ht=25+3*dp-5*tz+6*am-1.5*dp*dp+1*tz*tz-2*am*am+1.5*tz*am;\n    if(surv<20)surv=20;if(surv>98)surv=98;if(ht<5)ht=5;\n    printf "{\\"survival_1yr_pct\\": %.0f, \\"height_gain_cm\\": %.0f}",surv+n1*3,ht+n2*2;\n',
     "factor_cases":'--density_per_m2) DP="$2"; shift 2 ;;\n        --tidal_zone) TZ="$2"; shift 2 ;;\n        --amendment_kg_m2) AM="$2"; shift 2 ;;',
     "awk_vars":'-v DP="$DP" -v TZ="$TZ" -v AM="$AM"',"vars_init":'DP=""\nTZ=""\nAM=""',"validate":'[ -z "$DP" ] || [ -z "$TZ" ] || [ -z "$AM" ]'},

    {"num":257,"slug":"oyster_reef","name":"Oyster Reef Substrate Design","desc":"Box-Behnken design to maximize oyster settlement and reef height by tuning substrate rugosity, shell depth, and placement elevation","design":"box_behnken","category":"marine",
     "factors":[{"name":"rugosity_cm","levels":["2","10"],"type":"continuous","unit":"cm","description":"Surface rugosity relief"},{"name":"shell_depth_cm","levels":["10","40"],"type":"continuous","unit":"cm","description":"Recycled shell layer depth"},{"name":"elevation_m","levels":["-1","1"],"type":"continuous","unit":"m_MSL","description":"Placement elevation relative to mean sea level"}],
     "fixed":{"species":"crassostrea_virginica","site":"estuary_channel"},
     "responses":[{"name":"settlement_per_m2","optimize":"maximize","unit":"spat/m2","description":"Oyster spat settlement density"},{"name":"reef_height_cm","optimize":"maximize","unit":"cm/yr","description":"Vertical reef accretion rate"}],
     "model":'\n    rg=(RG-6)/4;sd=(SD-25)/15;el=(EL-0)/1;\n    set_=150+40*rg+30*sd-20*el-15*rg*rg-10*sd*sd-10*el*el+8*rg*sd;\n    ht=5+1.5*rg+1*sd-0.8*el-0.5*rg*rg-0.3*sd*sd+0.3*rg*el;\n    if(set_<20)set_=20;if(ht<0.5)ht=0.5;\n    printf "{\\"settlement_per_m2\\": %.0f, \\"reef_height_cm\\": %.1f}",set_+n1*15,ht+n2*0.3;\n',
     "factor_cases":'--rugosity_cm) RG="$2"; shift 2 ;;\n        --shell_depth_cm) SD="$2"; shift 2 ;;\n        --elevation_m) EL="$2"; shift 2 ;;',
     "awk_vars":'-v RG="$RG" -v SD="$SD" -v EL="$EL"',"vars_init":'RG=""\nSD=""\nEL=""',"validate":'[ -z "$RG" ] || [ -z "$SD" ] || [ -z "$EL" ]'},

    {"num":258,"slug":"beach_nourishment","name":"Beach Nourishment Longevity","desc":"Plackett-Burman screening of sand grain size, berm width, dune height, groin spacing, and nourishment volume for retention and storm resilience","design":"plackett_burman","category":"marine",
     "factors":[{"name":"grain_mm","levels":["0.3","1.0"],"type":"continuous","unit":"mm","description":"Median sand grain size"},{"name":"berm_width_m","levels":["20","60"],"type":"continuous","unit":"m","description":"Design berm width"},{"name":"dune_height_m","levels":["2","5"],"type":"continuous","unit":"m","description":"Constructed dune crest height"},{"name":"groin_spacing_m","levels":["100","400"],"type":"continuous","unit":"m","description":"Groin structure spacing"},{"name":"volume_m3_m","levels":["30","100"],"type":"continuous","unit":"m3/m","description":"Sand volume per meter of shoreline"}],
     "fixed":{"wave_climate":"moderate","longshore_drift":"southward"},
     "responses":[{"name":"retention_yrs","optimize":"maximize","unit":"yrs","description":"Years before re-nourishment needed"},{"name":"storm_resilience","optimize":"maximize","unit":"pts","description":"Storm damage resilience score (1-10)"}],
     "model":'\n    gn=(GN-0.65)/0.35;bw=(BW-40)/20;dh=(DH-3.5)/1.5;gs=(GS-250)/150;vl=(VL-65)/35;\n    ret=5+1*gn+1.5*bw+1*dh-0.5*gs+2*vl+0.3*gn*bw+0.2*bw*vl;\n    res=6+0.5*gn+0.8*bw+1.2*dh-0.3*gs+0.5*vl+0.2*dh*vl;\n    if(ret<1)ret=1;if(res<1)res=1;if(res>10)res=10;\n    printf "{\\"retention_yrs\\": %.1f, \\"storm_resilience\\": %.1f}",ret+n1*0.3,res+n2*0.3;\n',
     "factor_cases":'--grain_mm) GN="$2"; shift 2 ;;\n        --berm_width_m) BW="$2"; shift 2 ;;\n        --dune_height_m) DH="$2"; shift 2 ;;\n        --groin_spacing_m) GS="$2"; shift 2 ;;\n        --volume_m3_m) VL="$2"; shift 2 ;;',
     "awk_vars":'-v GN="$GN" -v BW="$BW" -v DH="$DH" -v GS="$GS" -v VL="$VL"',"vars_init":'GN=""\nBW=""\nDH=""\nGS=""\nVL=""',"validate":'[ -z "$GN" ] || [ -z "$BW" ] || [ -z "$DH" ] || [ -z "$GS" ]'},

    {"num":259,"slug":"underwater_camera","name":"Underwater Camera Settings","desc":"Box-Behnken design to maximize image sharpness and color accuracy by tuning white balance shift, strobe power, and lens port distance","design":"box_behnken","category":"marine",
     "factors":[{"name":"wb_shift_k","levels":["5000","10000"],"type":"continuous","unit":"K","description":"White balance color temperature"},{"name":"strobe_power_pct","levels":["25","100"],"type":"continuous","unit":"%","description":"Strobe power percentage"},{"name":"port_dist_cm","levels":["5","30"],"type":"continuous","unit":"cm","description":"Lens-to-subject distance through port"}],
     "fixed":{"depth":"10m","housing":"polycarbonate"},
     "responses":[{"name":"sharpness","optimize":"maximize","unit":"pts","description":"Image sharpness score (1-10)"},{"name":"color_accuracy","optimize":"maximize","unit":"pts","description":"Color accuracy score (1-10)"}],
     "model":'\n    wb=(WB-7500)/2500;sp=(SP-62.5)/37.5;pd=(PD-17.5)/12.5;\n    shrp=6.5+0.3*wb+0.8*sp-0.5*pd-0.2*wb*wb-0.3*sp*sp-0.3*pd*pd+0.2*sp*pd;\n    col=6+1.0*wb+0.5*sp-0.3*pd-0.8*wb*wb-0.2*sp*sp+0.2*wb*sp;\n    if(shrp<1)shrp=1;if(shrp>10)shrp=10;if(col<1)col=1;if(col>10)col=10;\n    printf "{\\"sharpness\\": %.1f, \\"color_accuracy\\": %.1f}",shrp+n1*0.3,col+n2*0.3;\n',
     "factor_cases":'--wb_shift_k) WB="$2"; shift 2 ;;\n        --strobe_power_pct) SP="$2"; shift 2 ;;\n        --port_dist_cm) PD="$2"; shift 2 ;;',
     "awk_vars":'-v WB="$WB" -v SP="$SP" -v PD="$PD"',"vars_init":'WB=""\nSP=""\nPD=""',"validate":'[ -z "$WB" ] || [ -z "$SP" ] || [ -z "$PD" ]'},

    {"num":260,"slug":"ballast_water","name":"Ballast Water Treatment","desc":"Central composite design to maximize organism removal and minimize treatment time by tuning UV dose, filtration pore size, and flow rate","design":"central_composite","category":"marine",
     "factors":[{"name":"uv_dose_mj_cm2","levels":["40","120"],"type":"continuous","unit":"mJ/cm2","description":"UV irradiation dose"},{"name":"filter_um","levels":["25","75"],"type":"continuous","unit":"um","description":"Pre-filter pore size"},{"name":"flow_m3_hr","levels":["50","300"],"type":"continuous","unit":"m3/hr","description":"Treatment flow rate"}],
     "fixed":{"vessel":"bulk_carrier","regulation":"IMO_D2"},
     "responses":[{"name":"removal_pct","optimize":"maximize","unit":"%","description":"Organism removal efficiency"},{"name":"treatment_min","optimize":"minimize","unit":"min/100m3","description":"Treatment time per 100m3"}],
     "model":'\n    uv=(UV-80)/40;fl=(FL-50)/25;fr=(FR-175)/125;\n    rem=92+4*uv-3*fl-2*fr-1.5*uv*uv+1*fl*fl+0.5*fr*fr+1*uv*fl;\n    tm=15-2*uv+1*fl-5*fr+0.5*uv*uv+0.3*fl*fl+1*fr*fr;\n    if(rem<70)rem=70;if(rem>99.9)rem=99.9;if(tm<3)tm=3;\n    printf "{\\"removal_pct\\": %.1f, \\"treatment_min\\": %.1f}",rem+n1*1,tm+n2*0.5;\n',
     "factor_cases":'--uv_dose_mj_cm2) UV="$2"; shift 2 ;;\n        --filter_um) FL="$2"; shift 2 ;;\n        --flow_m3_hr) FR="$2"; shift 2 ;;',
     "awk_vars":'-v UV="$UV" -v FL="$FL" -v FR="$FR"',"vars_init":'UV=""\nFL=""\nFR=""',"validate":'[ -z "$UV" ] || [ -z "$FL" ] || [ -z "$FR" ]'},

    # ══════ Aviation & Aerospace (261-270) ══════
    {"num":261,"slug":"model_rocket_flight","name":"Model Rocket Flight Optimization","desc":"Box-Behnken design to maximize apogee altitude and minimize drift by tuning motor impulse, fin area, and nose cone shape factor","design":"box_behnken","category":"aviation",
     "factors":[{"name":"impulse_ns","levels":["5","40"],"type":"continuous","unit":"Ns","description":"Motor total impulse"},{"name":"fin_area_cm2","levels":["20","80"],"type":"continuous","unit":"cm2","description":"Total fin planform area"},{"name":"nose_fineness","levels":["3","7"],"type":"continuous","unit":"ratio","description":"Nose cone fineness ratio (L/D)"}],
     "fixed":{"body_diam":"25mm","recovery":"parachute"},
     "responses":[{"name":"apogee_m","optimize":"maximize","unit":"m","description":"Peak altitude"},{"name":"drift_m","optimize":"minimize","unit":"m","description":"Landing drift from pad"}],
     "model":'\n    im=(IM-22.5)/17.5;fa=(FA-50)/30;nf=(NF-5)/2;\n    apo=150+80*im-15*fa+10*nf-10*im*im+5*fa*fa+3*nf*nf+5*im*nf;\n    dft=50+20*im+10*fa-5*nf+5*im*im+3*im*fa;\n    if(apo<20)apo=20;if(dft<5)dft=5;\n    printf "{\\"apogee_m\\": %.0f, \\"drift_m\\": %.0f}",apo+n1*8,dft+n2*3;\n',
     "factor_cases":'--impulse_ns) IM="$2"; shift 2 ;;\n        --fin_area_cm2) FA="$2"; shift 2 ;;\n        --nose_fineness) NF="$2"; shift 2 ;;',
     "awk_vars":'-v IM="$IM" -v FA="$FA" -v NF="$NF"',"vars_init":'IM=""\nFA=""\nNF=""',"validate":'[ -z "$IM" ] || [ -z "$FA" ] || [ -z "$NF" ]'},

    {"num":262,"slug":"paper_airplane","name":"Paper Airplane Distance","desc":"Central composite design to maximize flight distance and stability by tuning wing span, nose weight, and dihedral angle","design":"central_composite","category":"aviation",
     "factors":[{"name":"wingspan_cm","levels":["15","30"],"type":"continuous","unit":"cm","description":"Wingspan"},{"name":"nose_weight_g","levels":["0","3"],"type":"continuous","unit":"g","description":"Paper clip nose ballast"},{"name":"dihedral_deg","levels":["0","15"],"type":"continuous","unit":"deg","description":"Wing dihedral angle"}],
     "fixed":{"paper":"A4_80gsm","fold":"dart"},
     "responses":[{"name":"distance_m","optimize":"maximize","unit":"m","description":"Straight-line flight distance"},{"name":"stability_score","optimize":"maximize","unit":"pts","description":"Flight stability score (1-10)"}],
     "model":'\n    ws=(WS-22.5)/7.5;nw=(NW-1.5)/1.5;dh=(DH-7.5)/7.5;\n    dist=8+2*ws+1.5*nw+0.5*dh-1*ws*ws-0.8*nw*nw-0.3*dh*dh+0.5*ws*nw;\n    stab=6+0.3*ws+0.5*nw+1.0*dh-0.4*ws*ws-0.3*nw*nw-0.3*dh*dh+0.2*nw*dh;\n    if(dist<1)dist=1;if(stab<1)stab=1;if(stab>10)stab=10;\n    printf "{\\"distance_m\\": %.1f, \\"stability_score\\": %.1f}",dist+n1*0.5,stab+n2*0.3;\n',
     "factor_cases":'--wingspan_cm) WS="$2"; shift 2 ;;\n        --nose_weight_g) NW="$2"; shift 2 ;;\n        --dihedral_deg) DH="$2"; shift 2 ;;',
     "awk_vars":'-v WS="$WS" -v NW="$NW" -v DH="$DH"',"vars_init":'WS=""\nNW=""\nDH=""',"validate":'[ -z "$WS" ] || [ -z "$NW" ] || [ -z "$DH" ]'},

    {"num":263,"slug":"rc_plane_trim","name":"RC Plane Trim Settings","desc":"Full factorial of elevator trim, aileron differential, throttle curve, and CG position to maximize flight time and handling score","design":"full_factorial","category":"aviation",
     "factors":[{"name":"elevator_pct","levels":["-5","5"],"type":"continuous","unit":"%","description":"Elevator trim percentage"},{"name":"aileron_diff_pct","levels":["0","40"],"type":"continuous","unit":"%","description":"Aileron differential percentage"},{"name":"throttle_curve","levels":["50","100"],"type":"continuous","unit":"%","description":"Mid-stick throttle curve point"},{"name":"cg_pct_mac","levels":["25","35"],"type":"continuous","unit":"%MAC","description":"CG position as % of mean aerodynamic chord"}],
     "fixed":{"model":"trainer","wingspan":"1200mm"},
     "responses":[{"name":"flight_time_min","optimize":"maximize","unit":"min","description":"Flight time per battery"},{"name":"handling_score","optimize":"maximize","unit":"pts","description":"Pilot handling score (1-10)"}],
     "model":'\n    el=(EL-0)/5;ad=(AD-20)/20;tc=(TC-75)/25;cg=(CG-30)/5;\n    ft=12-0.5*el+0.2*ad-2*tc+0.3*cg-0.3*el*el+0.2*tc*tc;\n    hs=6.5+0.3*el+0.5*ad+0.2*tc-0.8*cg-0.5*el*el-0.3*ad*ad-0.5*cg*cg+0.2*el*cg;\n    if(ft<4)ft=4;if(hs<1)hs=1;if(hs>10)hs=10;\n    printf "{\\"flight_time_min\\": %.1f, \\"handling_score\\": %.1f}",ft+n1*0.5,hs+n2*0.3;\n',
     "factor_cases":'--elevator_pct) EL="$2"; shift 2 ;;\n        --aileron_diff_pct) AD="$2"; shift 2 ;;\n        --throttle_curve) TC="$2"; shift 2 ;;\n        --cg_pct_mac) CG="$2"; shift 2 ;;',
     "awk_vars":'-v EL="$EL" -v AD="$AD" -v TC="$TC" -v CG="$CG"',"vars_init":'EL=""\nAD=""\nTC=""\nCG=""',"validate":'[ -z "$EL" ] || [ -z "$AD" ] || [ -z "$TC" ] || [ -z "$CG" ]'},

    {"num":264,"slug":"weather_balloon","name":"Weather Balloon Launch Parameters","desc":"Box-Behnken design to maximize burst altitude and minimize payload swing by tuning helium fill volume, balloon mass, and payload weight","design":"box_behnken","category":"aviation",
     "factors":[{"name":"fill_m3","levels":["0.8","2.0"],"type":"continuous","unit":"m3","description":"Helium fill volume at ground"},{"name":"balloon_g","levels":["300","1200"],"type":"continuous","unit":"g","description":"Balloon mass"},{"name":"payload_g","levels":["100","500"],"type":"continuous","unit":"g","description":"Instrument payload weight"}],
     "fixed":{"gas":"helium","radiosonde":"RS41"},
     "responses":[{"name":"burst_alt_km","optimize":"maximize","unit":"km","description":"Burst altitude"},{"name":"swing_deg","optimize":"minimize","unit":"deg","description":"Maximum payload pendulum swing"}],
     "model":'\n    fv=(FV-1.4)/0.6;bm=(BM-750)/450;pw=(PW-300)/200;\n    alt=28+3*fv+5*bm-2*pw-1*fv*fv-1.5*bm*bm+0.5*fv*bm;\n    sw=15-3*fv+2*bm+4*pw+1*fv*fv+0.5*pw*pw+1*bm*pw;\n    if(alt<15)alt=15;if(sw<3)sw=3;\n    printf "{\\"burst_alt_km\\": %.1f, \\"swing_deg\\": %.0f}",alt+n1*1,sw+n2*1;\n',
     "factor_cases":'--fill_m3) FV="$2"; shift 2 ;;\n        --balloon_g) BM="$2"; shift 2 ;;\n        --payload_g) PW="$2"; shift 2 ;;',
     "awk_vars":'-v FV="$FV" -v BM="$BM" -v PW="$PW"',"vars_init":'FV=""\nBM=""\nPW=""',"validate":'[ -z "$FV" ] || [ -z "$BM" ] || [ -z "$PW" ]'},

    {"num":265,"slug":"kite_design","name":"Kite Aerodynamic Design","desc":"Central composite design to maximize lift and stability by tuning aspect ratio, bridle angle, and sail tension","design":"central_composite","category":"aviation",
     "factors":[{"name":"aspect_ratio","levels":["1.5","4.0"],"type":"continuous","unit":"ratio","description":"Wing aspect ratio"},{"name":"bridle_angle_deg","levels":["20","45"],"type":"continuous","unit":"deg","description":"Bridle attachment angle"},{"name":"sail_tension","levels":["1","5"],"type":"continuous","unit":"level","description":"Sail tension level (1=slack, 5=taut)"}],
     "fixed":{"material":"ripstop_nylon","area":"2m2"},
     "responses":[{"name":"lift_n","optimize":"maximize","unit":"N","description":"Lift force in 15kph wind"},{"name":"stability_score","optimize":"maximize","unit":"pts","description":"Gusty wind stability (1-10)"}],
     "model":'\n    ar=(AR-2.75)/1.25;ba=(BA-32.5)/12.5;st=(ST-3)/2;\n    lift=20+5*ar+3*ba+2*st-2*ar*ar-1.5*ba*ba-1*st*st+1*ar*ba;\n    stab=6+0.3*ar-0.5*ba+1.0*st-0.3*ar*ar+0.2*ba*ba-0.3*st*st+0.2*ba*st;\n    if(lift<5)lift=5;if(stab<1)stab=1;if(stab>10)stab=10;\n    printf "{\\"lift_n\\": %.1f, \\"stability_score\\": %.1f}",lift+n1*1,stab+n2*0.3;\n',
     "factor_cases":'--aspect_ratio) AR="$2"; shift 2 ;;\n        --bridle_angle_deg) BA="$2"; shift 2 ;;\n        --sail_tension) ST="$2"; shift 2 ;;',
     "awk_vars":'-v AR="$AR" -v BA="$BA" -v ST="$ST"',"vars_init":'AR=""\nBA=""\nST=""',"validate":'[ -z "$AR" ] || [ -z "$BA" ] || [ -z "$ST" ]'},

    {"num":266,"slug":"propeller_pitch","name":"Propeller Pitch Optimization","desc":"Box-Behnken design to maximize thrust efficiency and minimize vibration by tuning blade pitch, diameter, and RPM","design":"box_behnken","category":"aviation",
     "factors":[{"name":"pitch_deg","levels":["8","18"],"type":"continuous","unit":"deg","description":"Blade pitch angle"},{"name":"diameter_in","levels":["8","14"],"type":"continuous","unit":"in","description":"Propeller diameter"},{"name":"rpm","levels":["4000","9000"],"type":"continuous","unit":"rpm","description":"Operating RPM"}],
     "fixed":{"blades":"2","material":"carbon_fiber"},
     "responses":[{"name":"thrust_efficiency_pct","optimize":"maximize","unit":"%","description":"Thrust efficiency (thrust/power)"},{"name":"vibration_score","optimize":"minimize","unit":"pts","description":"Vibration severity (1-10)"}],
     "model":'\n    pt=(PT-13)/5;dm=(DM-11)/3;rp=(RP-6500)/2500;\n    eff=75+3*pt+5*dm-2*rp-3*pt*pt-2*dm*dm-1*rp*rp+1.5*pt*dm;\n    vib=4+0.5*pt+0.3*dm+1.2*rp+0.3*pt*pt+0.2*rp*rp+0.3*dm*rp;\n    if(eff<40)eff=40;if(eff>95)eff=95;if(vib<1)vib=1;if(vib>10)vib=10;\n    printf "{\\"thrust_efficiency_pct\\": %.0f, \\"vibration_score\\": %.1f}",eff+n1*2,vib+n2*0.3;\n',
     "factor_cases":'--pitch_deg) PT="$2"; shift 2 ;;\n        --diameter_in) DM="$2"; shift 2 ;;\n        --rpm) RP="$2"; shift 2 ;;',
     "awk_vars":'-v PT="$PT" -v DM="$DM" -v RP="$RP"',"vars_init":'PT=""\nDM=""\nRP=""',"validate":'[ -z "$PT" ] || [ -z "$DM" ] || [ -z "$RP" ]'},

    {"num":267,"slug":"wind_tunnel_setup","name":"Wind Tunnel Test Setup","desc":"Plackett-Burman screening of tunnel speed, model scale, turbulence grid, sting angle, and measurement rake position for data accuracy and repeatability","design":"plackett_burman","category":"aviation",
     "factors":[{"name":"speed_ms","levels":["10","50"],"type":"continuous","unit":"m/s","description":"Tunnel freestream velocity"},{"name":"model_scale","levels":["0.1","0.3"],"type":"continuous","unit":"ratio","description":"Model-to-full scale ratio"},{"name":"turb_grid","levels":["0","1"],"type":"continuous","unit":"bool","description":"Turbulence grid installed"},{"name":"sting_deg","levels":["-5","15"],"type":"continuous","unit":"deg","description":"Sting mount angle of attack"},{"name":"rake_pct","levels":["50","150"],"type":"continuous","unit":"%chord","description":"Wake rake position as % of chord"}],
     "fixed":{"tunnel":"closed_return","test_section":"1x1m"},
     "responses":[{"name":"data_accuracy","optimize":"maximize","unit":"pts","description":"Data accuracy vs CFD benchmark (1-10)"},{"name":"repeatability_pct","optimize":"maximize","unit":"%","description":"Run-to-run repeatability"}],
     "model":'\n    sp=(SP-30)/20;ms=(MS-0.2)/0.1;tg=(TG-0.5)/0.5;sa=(SA-5)/10;rk=(RK-100)/50;\n    acc=7+0.5*sp+0.8*ms+0.3*tg-0.2*sa-0.3*rk+0.2*sp*ms;\n    rep=92+2*sp+1*ms-1*tg+0.5*sa-0.5*rk+0.3*sp*tg;\n    if(acc<1)acc=1;if(acc>10)acc=10;if(rep<75)rep=75;if(rep>100)rep=100;\n    printf "{\\"data_accuracy\\": %.1f, \\"repeatability_pct\\": %.0f}",acc+n1*0.3,rep+n2*1;\n',
     "factor_cases":'--speed_ms) SP="$2"; shift 2 ;;\n        --model_scale) MS="$2"; shift 2 ;;\n        --turb_grid) TG="$2"; shift 2 ;;\n        --sting_deg) SA="$2"; shift 2 ;;\n        --rake_pct) RK="$2"; shift 2 ;;',
     "awk_vars":'-v SP="$SP" -v MS="$MS" -v TG="$TG" -v SA="$SA" -v RK="$RK"',"vars_init":'SP=""\nMS=""\nTG=""\nSA=""\nRK=""',"validate":'[ -z "$SP" ] || [ -z "$MS" ] || [ -z "$TG" ] || [ -z "$SA" ]'},

    {"num":268,"slug":"glider_thermal","name":"Glider Thermal Soaring Strategy","desc":"Box-Behnken design to maximize altitude gain and minimize circle time by tuning bank angle, entry speed, and thermal centering offset","design":"box_behnken","category":"aviation",
     "factors":[{"name":"bank_deg","levels":["20","45"],"type":"continuous","unit":"deg","description":"Circling bank angle"},{"name":"entry_kts","levels":["45","65"],"type":"continuous","unit":"kts","description":"Thermal entry airspeed"},{"name":"offset_m","levels":["0","50"],"type":"continuous","unit":"m","description":"Thermal center offset distance"}],
     "fixed":{"glider":"standard_class","thermal_strength":"3m/s"},
     "responses":[{"name":"climb_rate_ms","optimize":"maximize","unit":"m/s","description":"Average climb rate in thermal"},{"name":"circle_time_sec","optimize":"minimize","unit":"sec","description":"Time per 360° circle"}],
     "model":'\n    bk=(BK-32.5)/12.5;en=(EN-55)/10;of=(OF-25)/25;\n    clmb=2.5+0.3*bk-0.2*en-0.8*of-0.3*bk*bk+0.1*en*en-0.2*of*of+0.15*bk*en;\n    circ=25-3*bk+1*en+0.5*of+1*bk*bk+0.5*en*en;\n    if(clmb<0.2)clmb=0.2;if(circ<12)circ=12;\n    printf "{\\"climb_rate_ms\\": %.2f, \\"circle_time_sec\\": %.0f}",clmb+n1*0.1,circ+n2*1;\n',
     "factor_cases":'--bank_deg) BK="$2"; shift 2 ;;\n        --entry_kts) EN="$2"; shift 2 ;;\n        --offset_m) OF="$2"; shift 2 ;;',
     "awk_vars":'-v BK="$BK" -v EN="$EN" -v OF="$OF"',"vars_init":'BK=""\nEN=""\nOF=""',"validate":'[ -z "$BK" ] || [ -z "$EN" ] || [ -z "$OF" ]'},

    {"num":269,"slug":"parachute_deployment","name":"Parachute Deployment Dynamics","desc":"Central composite design to maximize opening reliability and minimize opening shock by tuning deployment altitude, reefing ratio, and slider size","design":"central_composite","category":"aviation",
     "factors":[{"name":"deploy_alt_m","levels":["300","1500"],"type":"continuous","unit":"m","description":"Deployment altitude AGL"},{"name":"reefing_pct","levels":["0","50"],"type":"continuous","unit":"%","description":"Reefing line restriction percentage"},{"name":"slider_pct","levels":["60","100"],"type":"continuous","unit":"%","description":"Slider opening percentage"}],
     "fixed":{"canopy":"ram_air","load":"90kg"},
     "responses":[{"name":"reliability_pct","optimize":"maximize","unit":"%","description":"Successful deployment percentage"},{"name":"opening_shock_g","optimize":"minimize","unit":"g","description":"Peak opening force in g"}],
     "model":'\n    da=(DA-900)/600;rr=(RR-25)/25;sl=(SL-80)/20;\n    rel=95+2*da-1*rr+1*sl-1.5*da*da+0.5*rr*rr-0.5*sl*sl+0.5*da*sl;\n    shk=3-0.3*da-1*rr-0.5*sl+0.3*da*da+0.5*rr*rr+0.2*da*rr;\n    if(rel<75)rel=75;if(rel>100)rel=100;if(shk<0.5)shk=0.5;\n    printf "{\\"reliability_pct\\": %.1f, \\"opening_shock_g\\": %.1f}",rel+n1*1,shk+n2*0.2;\n',
     "factor_cases":'--deploy_alt_m) DA="$2"; shift 2 ;;\n        --reefing_pct) RR="$2"; shift 2 ;;\n        --slider_pct) SL="$2"; shift 2 ;;',
     "awk_vars":'-v DA="$DA" -v RR="$RR" -v SL="$SL"',"vars_init":'DA=""\nRR=""\nSL=""',"validate":'[ -z "$DA" ] || [ -z "$RR" ] || [ -z "$SL" ]'},

    {"num":270,"slug":"hot_air_balloon","name":"Hot Air Balloon Flight Planning","desc":"Box-Behnken design to maximize flight duration and altitude ceiling by tuning burner output, envelope volume, and passenger count","design":"box_behnken","category":"aviation",
     "factors":[{"name":"burner_btu","levels":["6000000","12000000"],"type":"continuous","unit":"BTU/hr","description":"Burner heat output"},{"name":"envelope_m3","levels":["2000","4000"],"type":"continuous","unit":"m3","description":"Envelope volume"},{"name":"passengers","levels":["2","8"],"type":"continuous","unit":"count","description":"Number of passengers"}],
     "fixed":{"fuel_kg":"100","ambient_temp":"15C"},
     "responses":[{"name":"flight_hrs","optimize":"maximize","unit":"hrs","description":"Maximum flight duration"},{"name":"ceiling_m","optimize":"maximize","unit":"m","description":"Maximum altitude AGL"}],
     "model":'\n    bb=(BB-9000000)/3000000;ev=(EV-3000)/1000;ps=(PS-5)/3;\n    flt=1.5+0.3*bb+0.5*ev-0.8*ps-0.2*bb*bb-0.1*ev*ev+0.1*bb*ev;\n    ceil=500+100*bb+150*ev-120*ps-30*bb*bb-20*ev*ev+20*bb*ev;\n    if(flt<0.3)flt=0.3;if(ceil<100)ceil=100;\n    printf "{\\"flight_hrs\\": %.1f, \\"ceiling_m\\": %.0f}",flt+n1*0.1,ceil+n2*30;\n',
     "factor_cases":'--burner_btu) BB="$2"; shift 2 ;;\n        --envelope_m3) EV="$2"; shift 2 ;;\n        --passengers) PS="$2"; shift 2 ;;',
     "awk_vars":'-v BB="$BB" -v EV="$EV" -v PS="$PS"',"vars_init":'BB=""\nEV=""\nPS=""',"validate":'[ -z "$BB" ] || [ -z "$EV" ] || [ -z "$PS" ]'},

    # ══════ Electrical & Electronics DIY (271-280) ══════
    {"num":271,"slug":"led_strip_install","name":"LED Strip Installation","desc":"Box-Behnken design to maximize brightness uniformity and minimize hot spots by tuning strip density, power supply headroom, and diffuser distance","design":"box_behnken","category":"electronics",
     "factors":[{"name":"leds_per_m","levels":["30","120"],"type":"continuous","unit":"LEDs/m","description":"LED density per meter"},{"name":"psu_headroom_pct","levels":["10","40"],"type":"continuous","unit":"%","description":"Power supply overhead above rated load"},{"name":"diffuser_mm","levels":["5","30"],"type":"continuous","unit":"mm","description":"Diffuser distance from LEDs"}],
     "fixed":{"voltage":"12V","color":"warm_white"},
     "responses":[{"name":"uniformity_pct","optimize":"maximize","unit":"%","description":"Brightness uniformity across length"},{"name":"hotspot_temp_c","optimize":"minimize","unit":"C","description":"Maximum LED junction temperature rise"}],
     "model":'\n    ld=(LD-75)/45;ph=(PH-25)/15;df=(DF-17.5)/12.5;\n    unif=80+8*ld+3*ph+5*df-3*ld*ld-1*ph*ph-2*df*df+1*ld*df;\n    hot=35+8*ld-3*ph-2*df+2*ld*ld+1*ph*ph+1*ld*ph;\n    if(unif<50)unif=50;if(unif>100)unif=100;if(hot<15)hot=15;\n    printf "{\\"uniformity_pct\\": %.0f, \\"hotspot_temp_c\\": %.0f}",unif+n1*2,hot+n2*2;\n',
     "factor_cases":'--leds_per_m) LD="$2"; shift 2 ;;\n        --psu_headroom_pct) PH="$2"; shift 2 ;;\n        --diffuser_mm) DF="$2"; shift 2 ;;',
     "awk_vars":'-v LD="$LD" -v PH="$PH" -v DF="$DF"',"vars_init":'LD=""\nPH=""\nDF=""',"validate":'[ -z "$LD" ] || [ -z "$PH" ] || [ -z "$DF" ]'},

    {"num":272,"slug":"pcb_soldering","name":"PCB Soldering Parameters","desc":"Central composite design to maximize joint quality and minimize bridging by tuning iron temperature, contact time, and solder wire diameter","design":"central_composite","category":"electronics",
     "factors":[{"name":"iron_temp_c","levels":["280","380"],"type":"continuous","unit":"C","description":"Soldering iron tip temperature"},{"name":"contact_sec","levels":["1","5"],"type":"continuous","unit":"sec","description":"Iron contact duration"},{"name":"solder_mm","levels":["0.5","1.2"],"type":"continuous","unit":"mm","description":"Solder wire diameter"}],
     "fixed":{"flux":"rosin","tip":"chisel_2mm"},
     "responses":[{"name":"joint_quality","optimize":"maximize","unit":"pts","description":"Joint quality score (1-10)"},{"name":"bridge_rate","optimize":"minimize","unit":"per_100","description":"Solder bridges per 100 joints"}],
     "model":'\n    it=(IT-330)/50;ct=(CT-3)/2;sd=(SD-0.85)/0.35;\n    jq=7+0.5*it+0.8*ct+0.3*sd-0.8*it*it-0.4*ct*ct-0.3*sd*sd+0.2*it*ct;\n    br=3+0.3*it+0.5*ct+0.8*sd+0.2*it*it+0.3*ct*ct+0.3*ct*sd;\n    if(jq<1)jq=1;if(jq>10)jq=10;if(br<0)br=0;\n    printf "{\\"joint_quality\\": %.1f, \\"bridge_rate\\": %.1f}",jq+n1*0.3,br+n2*0.3;\n',
     "factor_cases":'--iron_temp_c) IT="$2"; shift 2 ;;\n        --contact_sec) CT="$2"; shift 2 ;;\n        --solder_mm) SD="$2"; shift 2 ;;',
     "awk_vars":'-v IT="$IT" -v CT="$CT" -v SD="$SD"',"vars_init":'IT=""\nCT=""\nSD=""',"validate":'[ -z "$IT" ] || [ -z "$CT" ] || [ -z "$SD" ]'},

    {"num":273,"slug":"antenna_tuning","name":"DIY Antenna Tuning","desc":"Box-Behnken design to maximize signal strength and minimize SWR by tuning element length, height above ground, and feed point impedance","design":"box_behnken","category":"electronics",
     "factors":[{"name":"element_pct","levels":["90","110"],"type":"continuous","unit":"%","description":"Element length as % of calculated quarter-wave"},{"name":"height_m","levels":["3","10"],"type":"continuous","unit":"m","description":"Antenna height above ground"},{"name":"feedpoint_ohm","levels":["25","75"],"type":"continuous","unit":"ohm","description":"Feed point impedance matching"}],
     "fixed":{"band":"2m_VHF","type":"ground_plane"},
     "responses":[{"name":"gain_dbi","optimize":"maximize","unit":"dBi","description":"Antenna gain"},{"name":"swr","optimize":"minimize","unit":"ratio","description":"Standing wave ratio"}],
     "model":'\n    el=(EL-100)/10;ht=(HT-6.5)/3.5;fp=(FP-50)/25;\n    gain=5+0.3*el+0.8*ht-0.2*fp-1*el*el-0.3*ht*ht-0.2*fp*fp+0.2*el*ht;\n    swr=1.5+0.8*el+0.2*ht+0.5*fp+0.5*el*el+0.2*fp*fp+0.2*el*fp;\n    if(gain<0)gain=0;if(swr<1)swr=1;\n    printf "{\\"gain_dbi\\": %.1f, \\"swr\\": %.2f}",gain+n1*0.2,swr+n2*0.1;\n',
     "factor_cases":'--element_pct) EL="$2"; shift 2 ;;\n        --height_m) HT="$2"; shift 2 ;;\n        --feedpoint_ohm) FP="$2"; shift 2 ;;',
     "awk_vars":'-v EL="$EL" -v HT="$HT" -v FP="$FP"',"vars_init":'EL=""\nHT=""\nFP=""',"validate":'[ -z "$EL" ] || [ -z "$HT" ] || [ -z "$FP" ]'},

    {"num":274,"slug":"battery_charger","name":"Battery Charger Settings","desc":"Full factorial of charge current, voltage cutoff, trickle threshold, and temperature limit to maximize capacity and cycle life","design":"full_factorial","category":"electronics",
     "factors":[{"name":"charge_c","levels":["0.5","2.0"],"type":"continuous","unit":"C","description":"Charge current rate (C-rate)"},{"name":"cutoff_v","levels":["4.15","4.25"],"type":"continuous","unit":"V","description":"Charge voltage cutoff per cell"},{"name":"trickle_pct","levels":["3","10"],"type":"continuous","unit":"%","description":"Trickle charge current as % of rated"},{"name":"temp_limit_c","levels":["35","50"],"type":"continuous","unit":"C","description":"Charge temperature cutoff"}],
     "fixed":{"chemistry":"LiPo","cells":"3S"},
     "responses":[{"name":"capacity_pct","optimize":"maximize","unit":"%","description":"Achieved capacity as % of rated"},{"name":"cycle_life","optimize":"maximize","unit":"cycles","description":"Estimated cycle life to 80% capacity"}],
     "model":'\n    cc=(CC-1.25)/0.75;cv=(CV-4.2)/0.05;tr=(TR-6.5)/3.5;tl=(TL-42.5)/7.5;\n    cap=92+3*cc+5*cv-0.5*tr-1*tl-1*cc*cc-2*cv*cv+0.5*cc*cv;\n    cyc=500-80*cc-100*cv+10*tr+20*tl+20*cc*cc+30*cv*cv-10*cc*cv;\n    if(cap<80)cap=80;if(cap>100)cap=100;if(cyc<100)cyc=100;\n    printf "{\\"capacity_pct\\": %.0f, \\"cycle_life\\": %.0f}",cap+n1*1,cyc+n2*20;\n',
     "factor_cases":'--charge_c) CC="$2"; shift 2 ;;\n        --cutoff_v) CV="$2"; shift 2 ;;\n        --trickle_pct) TR="$2"; shift 2 ;;\n        --temp_limit_c) TL="$2"; shift 2 ;;',
     "awk_vars":'-v CC="$CC" -v CV="$CV" -v TR="$TR" -v TL="$TL"',"vars_init":'CC=""\nCV=""\nTR=""\nTL=""',"validate":'[ -z "$CC" ] || [ -z "$CV" ] || [ -z "$TR" ] || [ -z "$TL" ]'},

    {"num":275,"slug":"audio_amplifier","name":"Audio Amplifier Biasing","desc":"Box-Behnken design to maximize THD+N and headroom by tuning bias current, supply voltage, and feedback ratio","design":"box_behnken","category":"electronics",
     "factors":[{"name":"bias_ma","levels":["10","100"],"type":"continuous","unit":"mA","description":"Output stage quiescent bias current"},{"name":"supply_v","levels":["15","35"],"type":"continuous","unit":"V","description":"Power supply voltage (per rail)"},{"name":"feedback_db","levels":["10","30"],"type":"continuous","unit":"dB","description":"Negative feedback amount"}],
     "fixed":{"topology":"class_AB","load":"8ohm"},
     "responses":[{"name":"thd_pct","optimize":"minimize","unit":"%","description":"Total harmonic distortion + noise"},{"name":"headroom_db","optimize":"maximize","unit":"dB","description":"Dynamic headroom above rated power"}],
     "model":'\n    bi=(BI-55)/45;sv=(SV-25)/10;fb=(FB-20)/10;\n    thd=0.1-0.03*bi+0.01*sv-0.05*fb+0.02*bi*bi+0.01*sv*sv+0.01*fb*fb-0.01*bi*fb;\n    hr=6+1*bi+3*sv-0.5*fb-0.5*bi*bi-0.5*sv*sv+0.3*sv*fb;\n    if(thd<0.001)thd=0.001;if(hr<1)hr=1;\n    printf "{\\"thd_pct\\": %.3f, \\"headroom_db\\": %.1f}",thd+n1*0.005,hr+n2*0.3;\n',
     "factor_cases":'--bias_ma) BI="$2"; shift 2 ;;\n        --supply_v) SV="$2"; shift 2 ;;\n        --feedback_db) FB="$2"; shift 2 ;;',
     "awk_vars":'-v BI="$BI" -v SV="$SV" -v FB="$FB"',"vars_init":'BI=""\nSV=""\nFB=""',"validate":'[ -z "$BI" ] || [ -z "$SV" ] || [ -z "$FB" ]'},

    {"num":276,"slug":"solar_charge_controller","name":"Solar Charge Controller Setup","desc":"Central composite design to maximize battery charge efficiency and minimize overcharge risk by tuning absorption voltage, float voltage, and MPPT sweep interval","design":"central_composite","category":"electronics",
     "factors":[{"name":"absorb_v","levels":["14.0","14.8"],"type":"continuous","unit":"V","description":"Absorption charge voltage"},{"name":"float_v","levels":["13.2","13.8"],"type":"continuous","unit":"V","description":"Float maintenance voltage"},{"name":"mppt_interval_sec","levels":["5","60"],"type":"continuous","unit":"sec","description":"MPPT tracking sweep interval"}],
     "fixed":{"panel_wp":"300","battery":"12V_100Ah"},
     "responses":[{"name":"charge_efficiency_pct","optimize":"maximize","unit":"%","description":"Daily charge efficiency"},{"name":"overcharge_risk","optimize":"minimize","unit":"pts","description":"Overcharge risk score (1-10)"}],
     "model":'\n    av=(AV-14.4)/0.4;fv=(FV-13.5)/0.3;mi=(MI-32.5)/27.5;\n    eff=88+3*av+1*fv-2*mi-2*av*av-1*fv*fv-0.5*mi*mi+0.5*av*fv;\n    ovr=3+2*av+0.5*fv+0.3*mi+1*av*av+0.3*fv*fv+0.2*av*fv;\n    if(eff<70)eff=70;if(eff>98)eff=98;if(ovr<1)ovr=1;if(ovr>10)ovr=10;\n    printf "{\\"charge_efficiency_pct\\": %.0f, \\"overcharge_risk\\": %.1f}",eff+n1*1,ovr+n2*0.3;\n',
     "factor_cases":'--absorb_v) AV="$2"; shift 2 ;;\n        --float_v) FV="$2"; shift 2 ;;\n        --mppt_interval_sec) MI="$2"; shift 2 ;;',
     "awk_vars":'-v AV="$AV" -v FV="$FV" -v MI="$MI"',"vars_init":'AV=""\nFV=""\nMI=""',"validate":'[ -z "$AV" ] || [ -z "$FV" ] || [ -z "$MI" ]'},

    {"num":277,"slug":"wire_gauge_selection","name":"Wire Gauge & Run Length","desc":"Box-Behnken design to minimize voltage drop and maximize cost efficiency by tuning wire gauge, run length, and conduit fill ratio","design":"box_behnken","category":"electronics",
     "factors":[{"name":"awg","levels":["10","18"],"type":"continuous","unit":"AWG","description":"Wire gauge (smaller = thicker)"},{"name":"run_m","levels":["5","30"],"type":"continuous","unit":"m","description":"Wire run length one-way"},{"name":"fill_pct","levels":["20","60"],"type":"continuous","unit":"%","description":"Conduit fill percentage"}],
     "fixed":{"circuit":"20A_120V","conductor":"copper"},
     "responses":[{"name":"voltage_drop_pct","optimize":"minimize","unit":"%","description":"Voltage drop as percentage"},{"name":"cost_per_m","optimize":"minimize","unit":"USD/m","description":"Wire cost per meter"}],
     "model":'\n    aw=(AW-14)/4;rl=(RL-17.5)/12.5;fl=(FL-40)/20;\n    vd=3+1.5*aw+1.2*rl+0.3*fl+0.3*aw*aw+0.2*rl*rl+0.3*aw*rl;\n    cost=2-0.8*aw+0.1*rl+0.05*fl+0.3*aw*aw;\n    if(vd<0.5)vd=0.5;if(cost<0.5)cost=0.5;\n    printf "{\\"voltage_drop_pct\\": %.1f, \\"cost_per_m\\": %.2f}",vd+n1*0.2,cost+n2*0.1;\n',
     "factor_cases":'--awg) AW="$2"; shift 2 ;;\n        --run_m) RL="$2"; shift 2 ;;\n        --fill_pct) FL="$2"; shift 2 ;;',
     "awk_vars":'-v AW="$AW" -v RL="$RL" -v FL="$FL"',"vars_init":'AW=""\nRL=""\nFL=""',"validate":'[ -z "$AW" ] || [ -z "$RL" ] || [ -z "$FL" ]'},

    {"num":278,"slug":"motor_speed_control","name":"DC Motor Speed Control","desc":"Fractional factorial screening of PWM frequency, duty cycle, voltage, load inertia, and PID gain for speed accuracy and efficiency","design":"fractional_factorial","category":"electronics",
     "factors":[{"name":"pwm_khz","levels":["1","25"],"type":"continuous","unit":"kHz","description":"PWM switching frequency"},{"name":"duty_pct","levels":["20","80"],"type":"continuous","unit":"%","description":"PWM duty cycle"},{"name":"voltage_v","levels":["6","24"],"type":"continuous","unit":"V","description":"Supply voltage"},{"name":"load_kg_cm2","levels":["1","10"],"type":"continuous","unit":"kg*cm2","description":"Load moment of inertia"},{"name":"pid_kp","levels":["0.5","5.0"],"type":"continuous","unit":"gain","description":"PID proportional gain"}],
     "fixed":{"motor":"brushed_DC","encoder":"100ppr"},
     "responses":[{"name":"speed_accuracy_pct","optimize":"maximize","unit":"%","description":"Steady-state speed accuracy"},{"name":"efficiency_pct","optimize":"maximize","unit":"%","description":"Electrical-to-mechanical efficiency"}],
     "model":'\n    pw=(PW-13)/12;dc=(DC-50)/30;vt=(VT-15)/9;li=(LI-5.5)/4.5;kp=(KP-2.75)/2.25;\n    acc=92+2*pw+1*dc+1*vt-1*li+3*kp-1*pw*pw+0.5*kp*kp+0.3*pw*kp;\n    eff=75+3*pw+2*dc+1*vt-2*li+0.5*kp-1*pw*pw-0.5*dc*dc+0.3*pw*dc;\n    if(acc<70)acc=70;if(acc>100)acc=100;if(eff<50)eff=50;if(eff>95)eff=95;\n    printf "{\\"speed_accuracy_pct\\": %.0f, \\"efficiency_pct\\": %.0f}",acc+n1*1,eff+n2*1;\n',
     "factor_cases":'--pwm_khz) PW="$2"; shift 2 ;;\n        --duty_pct) DC="$2"; shift 2 ;;\n        --voltage_v) VT="$2"; shift 2 ;;\n        --load_kg_cm2) LI="$2"; shift 2 ;;\n        --pid_kp) KP="$2"; shift 2 ;;',
     "awk_vars":'-v PW="$PW" -v DC="$DC" -v VT="$VT" -v LI="$LI" -v KP="$KP"',"vars_init":'PW=""\nDC=""\nVT=""\nLI=""\nKP=""',"validate":'[ -z "$PW" ] || [ -z "$DC" ] || [ -z "$VT" ] || [ -z "$LI" ]'},

    {"num":279,"slug":"oscilloscope_measurement","name":"Oscilloscope Measurement Setup","desc":"Box-Behnken design to maximize measurement accuracy and minimize noise floor by tuning vertical scale, bandwidth limit, and sample rate","design":"box_behnken","category":"electronics",
     "factors":[{"name":"v_div_mv","levels":["10","500"],"type":"continuous","unit":"mV/div","description":"Vertical scale setting"},{"name":"bw_mhz","levels":["20","200"],"type":"continuous","unit":"MHz","description":"Bandwidth limit setting"},{"name":"sample_msa","levels":["100","2000"],"type":"continuous","unit":"MSa/s","description":"Sample rate"}],
     "fixed":{"probe":"10x","coupling":"DC"},
     "responses":[{"name":"accuracy_pct","optimize":"maximize","unit":"%","description":"Measurement accuracy vs reference"},{"name":"noise_floor_mv","optimize":"minimize","unit":"mV_rms","description":"Noise floor in mV RMS"}],
     "model":'\n    vd=(VD-255)/245;bw=(BW-110)/90;sr=(SR-1050)/950;\n    acc=95+1*vd+2*bw+1.5*sr-1*vd*vd-0.5*bw*bw-0.5*sr*sr+0.3*bw*sr;\n    nf=5-1*vd+2*bw+0.5*sr+0.5*vd*vd+0.5*bw*bw+0.2*bw*sr;\n    if(acc<80)acc=80;if(acc>100)acc=100;if(nf<0.5)nf=0.5;\n    printf "{\\"accuracy_pct\\": %.1f, \\"noise_floor_mv\\": %.1f}",acc+n1*0.5,nf+n2*0.3;\n',
     "factor_cases":'--v_div_mv) VD="$2"; shift 2 ;;\n        --bw_mhz) BW="$2"; shift 2 ;;\n        --sample_msa) SR="$2"; shift 2 ;;',
     "awk_vars":'-v VD="$VD" -v BW="$BW" -v SR="$SR"',"vars_init":'VD=""\nBW=""\nSR=""',"validate":'[ -z "$VD" ] || [ -z "$BW" ] || [ -z "$SR" ]'},

    {"num":280,"slug":"power_supply_design","name":"Linear Power Supply Regulation","desc":"Central composite design to maximize load regulation and minimize ripple by tuning transformer tap, filter capacitance, and regulator dropout","design":"central_composite","category":"electronics",
     "factors":[{"name":"transformer_v","levels":["12","24"],"type":"continuous","unit":"V","description":"Transformer secondary voltage"},{"name":"filter_uf","levels":["1000","10000"],"type":"continuous","unit":"uF","description":"Filter capacitor value"},{"name":"dropout_v","levels":["1","4"],"type":"continuous","unit":"V","description":"Regulator minimum dropout voltage"}],
     "fixed":{"regulator":"LM317","output":"12V"},
     "responses":[{"name":"load_reg_pct","optimize":"minimize","unit":"%","description":"Load regulation percentage"},{"name":"ripple_mv","optimize":"minimize","unit":"mV_pp","description":"Output ripple voltage peak-to-peak"}],
     "model":'\n    tv=(TV-18)/6;fc=(FC-5500)/4500;dv=(DV-2.5)/1.5;\n    lr=0.5-0.1*tv-0.05*fc+0.2*dv+0.05*tv*tv+0.02*fc*fc+0.05*dv*dv;\n    rip=50-5*tv-15*fc+3*dv+2*tv*tv+3*fc*fc+1*dv*dv+1*tv*dv;\n    if(lr<0.01)lr=0.01;if(rip<1)rip=1;\n    printf "{\\"load_reg_pct\\": %.2f, \\"ripple_mv\\": %.0f}",lr+n1*0.02,rip+n2*2;\n',
     "factor_cases":'--transformer_v) TV="$2"; shift 2 ;;\n        --filter_uf) FC="$2"; shift 2 ;;\n        --dropout_v) DV="$2"; shift 2 ;;',
     "awk_vars":'-v TV="$TV" -v FC="$FC" -v DV="$DV"',"vars_init":'TV=""\nFC=""\nDV=""',"validate":'[ -z "$TV" ] || [ -z "$FC" ] || [ -z "$DV" ]'},

    # ══════ Painting & Fine Art (281-290) ══════
    {"num":281,"slug":"watercolor_wash","name":"Watercolor Wash Technique","desc":"Box-Behnken design to maximize color evenness and minimize blooming by tuning water-to-pigment ratio, paper wetness, and brush angle","design":"box_behnken","category":"painting",
     "factors":[{"name":"water_ratio","levels":["2","8"],"type":"continuous","unit":"ratio","description":"Water-to-pigment volume ratio"},{"name":"paper_wetness","levels":["1","5"],"type":"continuous","unit":"level","description":"Paper pre-wetting level (1=dry, 5=saturated)"},{"name":"brush_angle_deg","levels":["15","60"],"type":"continuous","unit":"deg","description":"Brush angle to paper surface"}],
     "fixed":{"paper":"300gsm_cold_press","pigment":"ultramarine"},
     "responses":[{"name":"evenness","optimize":"maximize","unit":"pts","description":"Color evenness across wash (1-10)"},{"name":"blooming","optimize":"minimize","unit":"pts","description":"Unwanted bloom/backrun severity (1-10)"}],
     "model":'\n    wr=(WR-5)/3;pw=(PW-3)/2;ba=(BA-37.5)/22.5;\n    even=6+0.5*wr+1.0*pw+0.3*ba-0.4*wr*wr-0.5*pw*pw+0.2*wr*pw;\n    bloom=4+0.5*wr+1.5*pw-0.3*ba+0.3*wr*wr+0.4*pw*pw+0.3*wr*pw;\n    if(even<1)even=1;if(even>10)even=10;if(bloom<1)bloom=1;if(bloom>10)bloom=10;\n    printf "{\\"evenness\\": %.1f, \\"blooming\\": %.1f}",even+n1*0.3,bloom+n2*0.3;\n',
     "factor_cases":'--water_ratio) WR="$2"; shift 2 ;;\n        --paper_wetness) PW="$2"; shift 2 ;;\n        --brush_angle_deg) BA="$2"; shift 2 ;;',
     "awk_vars":'-v WR="$WR" -v PW="$PW" -v BA="$BA"',"vars_init":'WR=""\nPW=""\nBA=""',"validate":'[ -z "$WR" ] || [ -z "$PW" ] || [ -z "$BA" ]'},

    {"num":282,"slug":"oil_paint_drying","name":"Oil Paint Drying Medium","desc":"Central composite design to maximize gloss and minimize yellowing by tuning linseed oil ratio, drying medium percentage, and layer thickness","design":"central_composite","category":"painting",
     "factors":[{"name":"linseed_pct","levels":["10","50"],"type":"continuous","unit":"%","description":"Linseed oil as % of medium"},{"name":"medium_pct","levels":["5","25"],"type":"continuous","unit":"%","description":"Alkyd medium percentage"},{"name":"thickness_mm","levels":["0.5","3.0"],"type":"continuous","unit":"mm","description":"Paint layer thickness"}],
     "fixed":{"pigment":"titanium_white","support":"linen_canvas"},
     "responses":[{"name":"gloss_score","optimize":"maximize","unit":"pts","description":"Surface gloss after cure (1-10)"},{"name":"yellowing_de","optimize":"minimize","unit":"dE","description":"Color shift (Delta-E) after 6 months"}],
     "model":'\n    lo=(LO-30)/20;mp=(MP-15)/10;th=(TH-1.75)/1.25;\n    gloss=6+0.8*lo+0.5*mp-0.3*th-0.3*lo*lo-0.2*mp*mp+0.2*lo*mp;\n    yel=3+1.5*lo+0.3*mp+0.5*th+0.5*lo*lo+0.2*th*th+0.3*lo*th;\n    if(gloss<1)gloss=1;if(gloss>10)gloss=10;if(yel<0.5)yel=0.5;\n    printf "{\\"gloss_score\\": %.1f, \\"yellowing_de\\": %.1f}",gloss+n1*0.3,yel+n2*0.3;\n',
     "factor_cases":'--linseed_pct) LO="$2"; shift 2 ;;\n        --medium_pct) MP="$2"; shift 2 ;;\n        --thickness_mm) TH="$2"; shift 2 ;;',
     "awk_vars":'-v LO="$LO" -v MP="$MP" -v TH="$TH"',"vars_init":'LO=""\nMP=""\nTH=""',"validate":'[ -z "$LO" ] || [ -z "$MP" ] || [ -z "$TH" ]'},

    {"num":283,"slug":"acrylic_pour","name":"Acrylic Pour Technique","desc":"Box-Behnken design to maximize cell formation and color separation by tuning silicone amount, paint consistency, and tilt angle","design":"box_behnken","category":"painting",
     "factors":[{"name":"silicone_drops","levels":["1","8"],"type":"continuous","unit":"drops","description":"Silicone oil drops per cup"},{"name":"consistency","levels":["1","5"],"type":"continuous","unit":"level","description":"Paint consistency (1=thick, 5=thin)"},{"name":"tilt_deg","levels":["5","30"],"type":"continuous","unit":"deg","description":"Canvas tilt angle during pour"}],
     "fixed":{"medium":"floetrol","base":"titanium_white"},
     "responses":[{"name":"cell_count","optimize":"maximize","unit":"per_100cm2","description":"Cell formations per 100 sq cm"},{"name":"color_separation","optimize":"maximize","unit":"pts","description":"Color layer separation score (1-10)"}],
     "model":'\n    sd=(SD-4.5)/3.5;cn=(CN-3)/2;ta=(TA-17.5)/12.5;\n    cells=15+8*sd+3*cn+2*ta-2*sd*sd-1*cn*cn+1*sd*cn;\n    sep=6+0.5*sd-0.3*cn+0.8*ta-0.3*sd*sd+0.2*cn*cn-0.2*ta*ta+0.2*cn*ta;\n    if(cells<0)cells=0;if(sep<1)sep=1;if(sep>10)sep=10;\n    printf "{\\"cell_count\\": %.0f, \\"color_separation\\": %.1f}",cells+n1*2,sep+n2*0.3;\n',
     "factor_cases":'--silicone_drops) SD="$2"; shift 2 ;;\n        --consistency) CN="$2"; shift 2 ;;\n        --tilt_deg) TA="$2"; shift 2 ;;',
     "awk_vars":'-v SD="$SD" -v CN="$CN" -v TA="$TA"',"vars_init":'SD=""\nCN=""\nTA=""',"validate":'[ -z "$SD" ] || [ -z "$CN" ] || [ -z "$TA" ]'},

    {"num":284,"slug":"canvas_stretching","name":"Canvas Stretching Tension","desc":"Full factorial of staple spacing, stretcher bar thickness, canvas weight, and pre-priming to maximize surface flatness and minimize warping","design":"full_factorial","category":"painting",
     "factors":[{"name":"staple_spacing_cm","levels":["3","8"],"type":"continuous","unit":"cm","description":"Staple spacing along edge"},{"name":"bar_mm","levels":["18","40"],"type":"continuous","unit":"mm","description":"Stretcher bar profile thickness"},{"name":"canvas_gsm","levels":["200","400"],"type":"continuous","unit":"g/m2","description":"Canvas weight"},{"name":"pre_prime","levels":["none","gesso"],"type":"categorical","unit":"","description":"Pre-priming treatment"}],
     "fixed":{"size":"60x80cm","canvas":"cotton_duck"},
     "responses":[{"name":"flatness","optimize":"maximize","unit":"pts","description":"Surface flatness score (1-10)"},{"name":"warp_mm","optimize":"minimize","unit":"mm","description":"Maximum bar warping"}],
     "model":'\n    ss=(SS-5.5)/2.5;bt=(BT-29)/11;cg=(CG-300)/100;pp=(PP=="gesso")?1:-1;\n    flat=7-0.8*ss+0.5*bt+0.3*cg+0.3*pp-0.3*ss*ss-0.2*bt*bt+0.2*ss*bt;\n    warp=3+0.5*ss-0.8*bt+0.3*cg-0.2*pp+0.2*ss*ss+0.3*bt*bt-0.1*bt*cg;\n    if(flat<1)flat=1;if(flat>10)flat=10;if(warp<0.5)warp=0.5;\n    printf "{\\"flatness\\": %.1f, \\"warp_mm\\": %.1f}",flat+n1*0.3,warp+n2*0.2;\n',
     "factor_cases":'--staple_spacing_cm) SS="$2"; shift 2 ;;\n        --bar_mm) BT="$2"; shift 2 ;;\n        --canvas_gsm) CG="$2"; shift 2 ;;\n        --pre_prime) PP="$2"; shift 2 ;;',
     "awk_vars":'-v SS="$SS" -v BT="$BT" -v CG="$CG" -v PP="$PP"',"vars_init":'SS=""\nBT=""\nCG=""\nPP=""',"validate":'[ -z "$SS" ] || [ -z "$BT" ] || [ -z "$CG" ] || [ -z "$PP" ]'},

    {"num":285,"slug":"framing_glass","name":"Art Framing UV Protection","desc":"Box-Behnken design to maximize UV protection and minimize glare by tuning glass type UV cutoff, anti-reflective coating layers, and spacer depth","design":"box_behnken","category":"painting",
     "factors":[{"name":"uv_cutoff_nm","levels":["380","420"],"type":"continuous","unit":"nm","description":"UV cutoff wavelength"},{"name":"ar_layers","levels":["0","4"],"type":"continuous","unit":"layers","description":"Anti-reflective coating layers"},{"name":"spacer_mm","levels":["2","8"],"type":"continuous","unit":"mm","description":"Glass-to-art spacer depth"}],
     "fixed":{"frame":"wood","mat":"acid_free"},
     "responses":[{"name":"uv_block_pct","optimize":"maximize","unit":"%","description":"UV radiation blocked"},{"name":"glare_score","optimize":"minimize","unit":"pts","description":"Visible glare score (1-10)"}],
     "model":'\n    uc=(UC-400)/20;al=(AL-2)/2;sp=(SP-5)/3;\n    uv=92+4*uc+1*al+0.5*sp-1*uc*uc+0.3*al*al+0.2*uc*al;\n    glare=5-0.2*uc-2*al+0.3*sp+0.1*uc*uc+0.5*al*al+0.2*al*sp;\n    if(uv<70)uv=70;if(uv>99.9)uv=99.9;if(glare<1)glare=1;if(glare>10)glare=10;\n    printf "{\\"uv_block_pct\\": %.1f, \\"glare_score\\": %.1f}",uv+n1*0.5,glare+n2*0.3;\n',
     "factor_cases":'--uv_cutoff_nm) UC="$2"; shift 2 ;;\n        --ar_layers) AL="$2"; shift 2 ;;\n        --spacer_mm) SP="$2"; shift 2 ;;',
     "awk_vars":'-v UC="$UC" -v AL="$AL" -v SP="$SP"',"vars_init":'UC=""\nAL=""\nSP=""',"validate":'[ -z "$UC" ] || [ -z "$AL" ] || [ -z "$SP" ]'},

    {"num":286,"slug":"pastel_fixative","name":"Pastel Fixative Application","desc":"Central composite design to maximize color preservation and minimize texture loss by tuning spray distance, number of coats, and drying interval","design":"central_composite","category":"painting",
     "factors":[{"name":"spray_dist_cm","levels":["20","50"],"type":"continuous","unit":"cm","description":"Spray can distance from surface"},{"name":"coats","levels":["1","4"],"type":"continuous","unit":"coats","description":"Number of fixative coats"},{"name":"dry_min","levels":["5","30"],"type":"continuous","unit":"min","description":"Drying time between coats"}],
     "fixed":{"fixative":"workable","brand":"krylon"},
     "responses":[{"name":"color_preservation","optimize":"maximize","unit":"pts","description":"Color vibrancy retention (1-10)"},{"name":"texture_loss","optimize":"minimize","unit":"pts","description":"Pastel tooth/texture reduction (1-10)"}],
     "model":'\n    sd=(SD-35)/15;ct=(CT-2.5)/1.5;dm=(DM-17.5)/12.5;\n    col=7-0.3*sd-0.5*ct+0.2*dm+0.2*sd*sd+0.3*ct*ct+0.1*sd*ct;\n    tex=3-0.2*sd+1.5*ct-0.3*dm+0.1*sd*sd+0.3*ct*ct+0.1*ct*dm;\n    if(col<1)col=1;if(col>10)col=10;if(tex<1)tex=1;if(tex>10)tex=10;\n    printf "{\\"color_preservation\\": %.1f, \\"texture_loss\\": %.1f}",col+n1*0.3,tex+n2*0.3;\n',
     "factor_cases":'--spray_dist_cm) SD="$2"; shift 2 ;;\n        --coats) CT="$2"; shift 2 ;;\n        --dry_min) DM="$2"; shift 2 ;;',
     "awk_vars":'-v SD="$SD" -v CT="$CT" -v DM="$DM"',"vars_init":'SD=""\nCT=""\nDM=""',"validate":'[ -z "$SD" ] || [ -z "$CT" ] || [ -z "$DM" ]'},

    {"num":287,"slug":"ceramic_glaze","name":"Ceramic Glaze Firing","desc":"Box-Behnken design to maximize glaze surface quality and color accuracy by tuning peak temperature, hold time, and cooling rate","design":"box_behnken","category":"painting",
     "factors":[{"name":"peak_temp_c","levels":["1200","1300"],"type":"continuous","unit":"C","description":"Kiln peak temperature"},{"name":"hold_min","levels":["10","60"],"type":"continuous","unit":"min","description":"Soak time at peak temperature"},{"name":"cool_rate_c_hr","levels":["50","200"],"type":"continuous","unit":"C/hr","description":"Controlled cooling rate"}],
     "fixed":{"kiln":"electric","atmosphere":"oxidation"},
     "responses":[{"name":"surface_quality","optimize":"maximize","unit":"pts","description":"Glaze surface smoothness (1-10)"},{"name":"color_match","optimize":"maximize","unit":"pts","description":"Color accuracy vs test tile (1-10)"}],
     "model":'\n    pt=(PT-1250)/50;hm=(HM-35)/25;cr=(CR-125)/75;\n    surf=7+0.5*pt+0.8*hm-0.5*cr-0.5*pt*pt-0.3*hm*hm+0.2*pt*hm;\n    col=6.5+0.3*pt+0.5*hm+0.4*cr-0.8*pt*pt-0.2*hm*hm-0.3*cr*cr+0.2*pt*cr;\n    if(surf<1)surf=1;if(surf>10)surf=10;if(col<1)col=1;if(col>10)col=10;\n    printf "{\\"surface_quality\\": %.1f, \\"color_match\\": %.1f}",surf+n1*0.3,col+n2*0.3;\n',
     "factor_cases":'--peak_temp_c) PT="$2"; shift 2 ;;\n        --hold_min) HM="$2"; shift 2 ;;\n        --cool_rate_c_hr) CR="$2"; shift 2 ;;',
     "awk_vars":'-v PT="$PT" -v HM="$HM" -v CR="$CR"',"vars_init":'PT=""\nHM=""\nCR=""',"validate":'[ -z "$PT" ] || [ -z "$HM" ] || [ -z "$CR" ]'},

    {"num":288,"slug":"printmaking_ink","name":"Printmaking Ink Viscosity","desc":"Plackett-Burman screening of ink tack, oil percentage, pigment load, modifier amount, and roller pressure for print quality and ink transfer","design":"plackett_burman","category":"painting",
     "factors":[{"name":"tack_level","levels":["2","8"],"type":"continuous","unit":"level","description":"Ink tack rating"},{"name":"oil_pct","levels":["20","50"],"type":"continuous","unit":"%","description":"Linseed oil percentage"},{"name":"pigment_pct","levels":["15","35"],"type":"continuous","unit":"%","description":"Pigment concentration"},{"name":"modifier_pct","levels":["0","10"],"type":"continuous","unit":"%","description":"Viscosity modifier"},{"name":"roller_pressure","levels":["1","5"],"type":"continuous","unit":"level","description":"Roller pressure setting"}],
     "fixed":{"method":"relief","paper":"BFK_rives"},
     "responses":[{"name":"print_quality","optimize":"maximize","unit":"pts","description":"Image clarity and detail (1-10)"},{"name":"transfer_pct","optimize":"maximize","unit":"%","description":"Ink transfer efficiency"}],
     "model":'\n    tk=(TK-5)/3;ol=(OL-35)/15;pg=(PG-25)/10;md=(MD-5)/5;rp=(RP-3)/2;\n    pq=6+0.5*tk-0.3*ol+0.8*pg-0.2*md+0.5*rp+0.2*tk*pg;\n    tr=70+5*tk+3*ol+2*pg+1*md+5*rp+1*tk*rp;\n    if(pq<1)pq=1;if(pq>10)pq=10;if(tr<40)tr=40;if(tr>100)tr=100;\n    printf "{\\"print_quality\\": %.1f, \\"transfer_pct\\": %.0f}",pq+n1*0.3,tr+n2*2;\n',
     "factor_cases":'--tack_level) TK="$2"; shift 2 ;;\n        --oil_pct) OL="$2"; shift 2 ;;\n        --pigment_pct) PG="$2"; shift 2 ;;\n        --modifier_pct) MD="$2"; shift 2 ;;\n        --roller_pressure) RP="$2"; shift 2 ;;',
     "awk_vars":'-v TK="$TK" -v OL="$OL" -v PG="$PG" -v MD="$MD" -v RP="$RP"',"vars_init":'TK=""\nOL=""\nPG=""\nMD=""\nRP=""',"validate":'[ -z "$TK" ] || [ -z "$OL" ] || [ -z "$PG" ] || [ -z "$MD" ]'},

    {"num":289,"slug":"sculpture_patina","name":"Bronze Sculpture Patina","desc":"Box-Behnken design to maximize color richness and uniformity by tuning chemical concentration, application temperature, and number of coats","design":"box_behnken","category":"painting",
     "factors":[{"name":"chemical_pct","levels":["5","30"],"type":"continuous","unit":"%","description":"Patina solution concentration"},{"name":"temp_c","levels":["20","80"],"type":"continuous","unit":"C","description":"Surface temperature during application"},{"name":"coats","levels":["1","5"],"type":"continuous","unit":"coats","description":"Number of application coats"}],
     "fixed":{"chemical":"liver_of_sulfur","metal":"bronze"},
     "responses":[{"name":"color_richness","optimize":"maximize","unit":"pts","description":"Color depth and richness (1-10)"},{"name":"uniformity","optimize":"maximize","unit":"pts","description":"Color uniformity across surface (1-10)"}],
     "model":'\n    ch=(CH-17.5)/12.5;tp=(TP-50)/30;ct=(CT-3)/2;\n    rich=6+1.0*ch+0.5*tp+0.8*ct-0.4*ch*ch-0.3*tp*tp-0.3*ct*ct+0.2*ch*tp;\n    unif=6.5-0.3*ch+0.3*tp+0.5*ct-0.2*ch*ch-0.4*tp*tp-0.2*ct*ct+0.2*tp*ct;\n    if(rich<1)rich=1;if(rich>10)rich=10;if(unif<1)unif=1;if(unif>10)unif=10;\n    printf "{\\"color_richness\\": %.1f, \\"uniformity\\": %.1f}",rich+n1*0.3,unif+n2*0.3;\n',
     "factor_cases":'--chemical_pct) CH="$2"; shift 2 ;;\n        --temp_c) TP="$2"; shift 2 ;;\n        --coats) CT="$2"; shift 2 ;;',
     "awk_vars":'-v CH="$CH" -v TP="$TP" -v CT="$CT"',"vars_init":'CH=""\nTP=""\nCT=""',"validate":'[ -z "$CH" ] || [ -z "$TP" ] || [ -z "$CT" ]'},

    {"num":290,"slug":"encaustic_wax","name":"Encaustic Wax Painting","desc":"Central composite design to maximize adhesion and minimize cracking by tuning wax temperature, damar resin ratio, and fuse heat gun distance","design":"central_composite","category":"painting",
     "factors":[{"name":"wax_temp_c","levels":["80","120"],"type":"continuous","unit":"C","description":"Melted wax working temperature"},{"name":"damar_pct","levels":["5","25"],"type":"continuous","unit":"%","description":"Damar resin percentage in medium"},{"name":"fuse_dist_cm","levels":["5","20"],"type":"continuous","unit":"cm","description":"Heat gun fusing distance"}],
     "fixed":{"wax":"purified_beeswax","support":"birch_panel"},
     "responses":[{"name":"adhesion_score","optimize":"maximize","unit":"pts","description":"Layer adhesion strength (1-10)"},{"name":"cracking_score","optimize":"minimize","unit":"pts","description":"Surface cracking severity (1-10)"}],
     "model":'\n    wt=(WT-100)/20;dr=(DR-15)/10;fd=(FD-12.5)/7.5;\n    adh=7+0.5*wt+0.8*dr-0.3*fd-0.5*wt*wt-0.3*dr*dr+0.2*wt*dr;\n    crk=3+0.8*wt-0.5*dr+0.3*fd+0.4*wt*wt+0.2*dr*dr+0.2*wt*fd;\n    if(adh<1)adh=1;if(adh>10)adh=10;if(crk<1)crk=1;if(crk>10)crk=10;\n    printf "{\\"adhesion_score\\": %.1f, \\"cracking_score\\": %.1f}",adh+n1*0.3,crk+n2*0.3;\n',
     "factor_cases":'--wax_temp_c) WT="$2"; shift 2 ;;\n        --damar_pct) DR="$2"; shift 2 ;;\n        --fuse_dist_cm) FD="$2"; shift 2 ;;',
     "awk_vars":'-v WT="$WT" -v DR="$DR" -v FD="$FD"',"vars_init":'WT=""\nDR=""\nFD=""',"validate":'[ -z "$WT" ] || [ -z "$DR" ] || [ -z "$FD" ]'},

    # ══════ Veterinary & Livestock (291-300) ══════
    {"num":291,"slug":"dairy_cow_nutrition","name":"Dairy Cow Feed Ration","desc":"Box-Behnken design to maximize milk yield and minimize feed cost by tuning forage-to-concentrate ratio, protein supplement, and energy density","design":"box_behnken","category":"veterinary",
     "factors":[{"name":"forage_pct","levels":["40","70"],"type":"continuous","unit":"%","description":"Forage as percentage of total DMI"},{"name":"protein_pct","levels":["14","20"],"type":"continuous","unit":"%CP","description":"Crude protein percentage"},{"name":"energy_mcal","levels":["1.5","1.8"],"type":"continuous","unit":"Mcal/kg","description":"Net energy for lactation"}],
     "fixed":{"breed":"holstein","lactation_stage":"mid"},
     "responses":[{"name":"milk_kg_day","optimize":"maximize","unit":"kg/day","description":"Daily milk production"},{"name":"feed_cost_day","optimize":"minimize","unit":"USD/day","description":"Daily feed cost per cow"}],
     "model":'\n    fp=(FP-55)/15;pp=(PP-17)/3;en=(EN-1.65)/0.15;\n    milk=30-3*fp+2*pp+5*en-1*fp*fp-0.5*pp*pp-2*en*en+1*pp*en;\n    cost=8-1*fp+1*pp+2*en+0.3*fp*fp+0.2*pp*en;\n    if(milk<15)milk=15;if(cost<4)cost=4;\n    printf "{\\"milk_kg_day\\": %.1f, \\"feed_cost_day\\": %.2f}",milk+n1*1,cost+n2*0.3;\n',
     "factor_cases":'--forage_pct) FP="$2"; shift 2 ;;\n        --protein_pct) PP="$2"; shift 2 ;;\n        --energy_mcal) EN="$2"; shift 2 ;;',
     "awk_vars":'-v FP="$FP" -v PP="$PP" -v EN="$EN"',"vars_init":'FP=""\nPP=""\nEN=""',"validate":'[ -z "$FP" ] || [ -z "$PP" ] || [ -z "$EN" ]'},

    {"num":292,"slug":"sheep_shearing","name":"Sheep Shearing Technique","desc":"Central composite design to maximize wool quality and minimize nicks by tuning comb tooth count, cutter speed, and blow angle","design":"central_composite","category":"veterinary",
     "factors":[{"name":"comb_teeth","levels":["9","17"],"type":"continuous","unit":"teeth","description":"Shearing comb tooth count"},{"name":"cutter_rpm","levels":["2000","3500"],"type":"continuous","unit":"rpm","description":"Cutter speed"},{"name":"blow_angle_deg","levels":["10","40"],"type":"continuous","unit":"deg","description":"Handpiece blow angle to skin"}],
     "fixed":{"breed":"merino","season":"spring"},
     "responses":[{"name":"staple_length_cm","optimize":"maximize","unit":"cm","description":"Average wool staple length preserved"},{"name":"nick_count","optimize":"minimize","unit":"per_sheep","description":"Skin nicks per animal"}],
     "model":'\n    ct=(CT-13)/4;cr=(CR-2750)/750;ba=(BA-25)/15;\n    sl=8+0.5*ct-0.3*cr+0.4*ba-0.3*ct*ct+0.2*cr*cr-0.2*ba*ba+0.15*ct*ba;\n    nk=3-0.3*ct+0.5*cr+0.3*ba+0.2*ct*ct+0.3*cr*cr+0.2*cr*ba;\n    if(sl<4)sl=4;if(nk<0)nk=0;\n    printf "{\\"staple_length_cm\\": %.1f, \\"nick_count\\": %.1f}",sl+n1*0.3,nk+n2*0.3;\n',
     "factor_cases":'--comb_teeth) CT="$2"; shift 2 ;;\n        --cutter_rpm) CR="$2"; shift 2 ;;\n        --blow_angle_deg) BA="$2"; shift 2 ;;',
     "awk_vars":'-v CT="$CT" -v CR="$CR" -v BA="$BA"',"vars_init":'CT=""\nCR=""\nBA=""',"validate":'[ -z "$CT" ] || [ -z "$CR" ] || [ -z "$BA" ]'},

    {"num":293,"slug":"poultry_house_ventilation","name":"Poultry House Ventilation","desc":"Full factorial of fan rate, inlet opening, fogging interval, and lighting schedule to maximize weight gain and minimize heat stress mortality","design":"full_factorial","category":"veterinary",
     "factors":[{"name":"fan_rate_m3_s","levels":["2","8"],"type":"continuous","unit":"m3/s","description":"Ventilation fan rate"},{"name":"inlet_pct","levels":["20","80"],"type":"continuous","unit":"%","description":"Inlet baffle opening percentage"},{"name":"fog_interval_min","levels":["5","30"],"type":"continuous","unit":"min","description":"Fogging system cycle interval"},{"name":"light_hrs","levels":["16","23"],"type":"continuous","unit":"hrs","description":"Daily lighting hours"}],
     "fixed":{"birds":"20000","house_m2":"1200"},
     "responses":[{"name":"weight_gain_g_day","optimize":"maximize","unit":"g/day","description":"Average daily weight gain"},{"name":"mortality_pct","optimize":"minimize","unit":"%","description":"Heat stress mortality percentage"}],
     "model":'\n    fr=(FR-5)/3;ip=(IP-50)/30;fi=(FI-17.5)/12.5;lh=(LH-19.5)/3.5;\n    wg=55+5*fr+2*ip-3*fi+3*lh-2*fr*fr-1*ip*ip+1*fr*ip;\n    mort=2-0.8*fr-0.3*ip+0.5*fi-0.2*lh+0.3*fr*fr+0.2*fi*fi+0.2*fi*lh;\n    if(wg<30)wg=30;if(mort<0.1)mort=0.1;if(mort>8)mort=8;\n    printf "{\\"weight_gain_g_day\\": %.0f, \\"mortality_pct\\": %.1f}",wg+n1*2,mort+n2*0.2;\n',
     "factor_cases":'--fan_rate_m3_s) FR="$2"; shift 2 ;;\n        --inlet_pct) IP="$2"; shift 2 ;;\n        --fog_interval_min) FI="$2"; shift 2 ;;\n        --light_hrs) LH="$2"; shift 2 ;;',
     "awk_vars":'-v FR="$FR" -v IP="$IP" -v FI="$FI" -v LH="$LH"',"vars_init":'FR=""\nIP=""\nFI=""\nLH=""',"validate":'[ -z "$FR" ] || [ -z "$IP" ] || [ -z "$FI" ] || [ -z "$LH" ]'},

    {"num":294,"slug":"cattle_grazing","name":"Rotational Grazing Pattern","desc":"Box-Behnken design to maximize pasture recovery and animal weight gain by tuning paddock rest days, stocking density, and grazing duration","design":"box_behnken","category":"veterinary",
     "factors":[{"name":"rest_days","levels":["21","60"],"type":"continuous","unit":"days","description":"Paddock rest period between grazing"},{"name":"stock_density_au_ha","levels":["50","200"],"type":"continuous","unit":"AU/ha","description":"Instantaneous stocking density"},{"name":"graze_days","levels":["1","5"],"type":"continuous","unit":"days","description":"Days of grazing per paddock"}],
     "fixed":{"cattle":"beef","paddock_count":"10"},
     "responses":[{"name":"pasture_recovery_pct","optimize":"maximize","unit":"%","description":"Pasture biomass recovery at end of rest"},{"name":"adg_kg","optimize":"maximize","unit":"kg/day","description":"Average daily weight gain per head"}],
     "model":'\n    rd=(RD-40.5)/19.5;sd=(SD-125)/75;gd=(GD-3)/2;\n    rec=75+8*rd-5*sd-3*gd-3*rd*rd+2*sd*sd+1*gd*gd+2*rd*sd;\n    adg=0.8+0.1*rd+0.05*sd-0.1*gd-0.05*rd*rd-0.03*sd*sd+0.02*rd*gd;\n    if(rec<30)rec=30;if(rec>100)rec=100;if(adg<0.2)adg=0.2;\n    printf "{\\"pasture_recovery_pct\\": %.0f, \\"adg_kg\\": %.2f}",rec+n1*3,adg+n2*0.05;\n',
     "factor_cases":'--rest_days) RD="$2"; shift 2 ;;\n        --stock_density_au_ha) SD="$2"; shift 2 ;;\n        --graze_days) GD="$2"; shift 2 ;;',
     "awk_vars":'-v RD="$RD" -v SD="$SD" -v GD="$GD"',"vars_init":'RD=""\nSD=""\nGD=""',"validate":'[ -z "$RD" ] || [ -z "$SD" ] || [ -z "$GD" ]'},

    {"num":295,"slug":"pig_farrowing","name":"Pig Farrowing Pen Design","desc":"Central composite design to maximize piglet survival and sow comfort by tuning creep area temperature, pen floor type heating, and space allowance","design":"central_composite","category":"veterinary",
     "factors":[{"name":"creep_temp_c","levels":["28","35"],"type":"continuous","unit":"C","description":"Creep area temperature"},{"name":"heat_mat_pct","levels":["0","100"],"type":"continuous","unit":"%","description":"Heated floor mat coverage"},{"name":"space_m2","levels":["4","7"],"type":"continuous","unit":"m2","description":"Total pen space per sow"}],
     "fixed":{"breed":"large_white","litter_size":"12"},
     "responses":[{"name":"piglet_survival_pct","optimize":"maximize","unit":"%","description":"Pre-weaning piglet survival"},{"name":"sow_comfort","optimize":"maximize","unit":"pts","description":"Sow comfort and behavior score (1-10)"}],
     "model":'\n    ct=(CT-31.5)/3.5;hm=(HM-50)/50;sp=(SP-5.5)/1.5;\n    surv=85+3*ct+4*hm+2*sp-3*ct*ct-1.5*hm*hm-1*sp*sp+1*ct*hm;\n    comf=6+0.3*ct+0.5*hm+1.2*sp-0.5*ct*ct-0.2*hm*hm-0.3*sp*sp+0.2*hm*sp;\n    if(surv<60)surv=60;if(surv>98)surv=98;if(comf<1)comf=1;if(comf>10)comf=10;\n    printf "{\\"piglet_survival_pct\\": %.0f, \\"sow_comfort\\": %.1f}",surv+n1*2,comf+n2*0.3;\n',
     "factor_cases":'--creep_temp_c) CT="$2"; shift 2 ;;\n        --heat_mat_pct) HM="$2"; shift 2 ;;\n        --space_m2) SP="$2"; shift 2 ;;',
     "awk_vars":'-v CT="$CT" -v HM="$HM" -v SP="$SP"',"vars_init":'CT=""\nHM=""\nSP=""',"validate":'[ -z "$CT" ] || [ -z "$HM" ] || [ -z "$SP" ]'},

    {"num":296,"slug":"goat_milk_quality","name":"Goat Milk Quality Factors","desc":"Box-Behnken design to maximize butterfat content and minimize somatic cell count by tuning concentrate supplementation, milking frequency, and pasture access hours","design":"box_behnken","category":"veterinary",
     "factors":[{"name":"concentrate_g","levels":["200","800"],"type":"continuous","unit":"g/day","description":"Concentrate supplement amount"},{"name":"milking_freq","levels":["1","3"],"type":"continuous","unit":"per_day","description":"Milking frequency per day"},{"name":"pasture_hrs","levels":["4","12"],"type":"continuous","unit":"hrs","description":"Daily pasture access hours"}],
     "fixed":{"breed":"saanen","lactation_week":"12"},
     "responses":[{"name":"butterfat_pct","optimize":"maximize","unit":"%","description":"Milk butterfat percentage"},{"name":"scc_k_ml","optimize":"minimize","unit":"k/mL","description":"Somatic cell count (thousands per mL)"}],
     "model":'\n    cg=(CG-500)/300;mf=(MF-2)/1;ph=(PH-8)/4;\n    bf=3.5+0.3*cg+0.2*mf+0.1*ph-0.2*cg*cg-0.1*mf*mf+0.1*cg*ph;\n    scc=200-30*cg-50*mf+20*ph+10*cg*cg+15*mf*mf+5*cg*mf;\n    if(bf<2)bf=2;if(bf>6)bf=6;if(scc<50)scc=50;\n    printf "{\\"butterfat_pct\\": %.1f, \\"scc_k_ml\\": %.0f}",bf+n1*0.1,scc+n2*15;\n',
     "factor_cases":'--concentrate_g) CG="$2"; shift 2 ;;\n        --milking_freq) MF="$2"; shift 2 ;;\n        --pasture_hrs) PH="$2"; shift 2 ;;',
     "awk_vars":'-v CG="$CG" -v MF="$MF" -v PH="$PH"',"vars_init":'CG=""\nMF=""\nPH=""',"validate":'[ -z "$CG" ] || [ -z "$MF" ] || [ -z "$PH" ]'},

    {"num":297,"slug":"hoof_trimming","name":"Hoof Trimming Schedule","desc":"Fractional factorial screening of trim interval, heel height, toe angle, weight distribution, and exercise hours for lameness prevention and hoof health","design":"fractional_factorial","category":"veterinary",
     "factors":[{"name":"trim_weeks","levels":["6","16"],"type":"continuous","unit":"weeks","description":"Trimming interval"},{"name":"heel_height_mm","levels":["20","40"],"type":"continuous","unit":"mm","description":"Target heel height after trim"},{"name":"toe_angle_deg","levels":["45","55"],"type":"continuous","unit":"deg","description":"Target dorsal toe angle"},{"name":"balance_pct","levels":["45","55"],"type":"continuous","unit":"%","description":"Weight on front feet percentage"},{"name":"exercise_hrs","levels":["2","8"],"type":"continuous","unit":"hrs","description":"Daily exercise/movement hours"}],
     "fixed":{"animal":"dairy_cow","surface":"concrete_rubber"},
     "responses":[{"name":"lameness_score","optimize":"minimize","unit":"pts","description":"Locomotion lameness score (1-5, 1=sound)"},{"name":"hoof_health","optimize":"maximize","unit":"pts","description":"Hoof wall quality score (1-10)"}],
     "model":'\n    tw=(TW-11)/5;hh=(HH-30)/10;ta=(TA-50)/5;bp=(BP-50)/5;ex=(EX-5)/3;\n    lame=2.5+0.5*tw-0.3*hh+0.2*ta+0.2*bp-0.3*ex+0.2*tw*tw+0.1*tw*hh;\n    hf=6-0.5*tw+0.3*hh+0.2*ta-0.1*bp+0.4*ex+0.1*hh*ex;\n    if(lame<1)lame=1;if(lame>5)lame=5;if(hf<1)hf=1;if(hf>10)hf=10;\n    printf "{\\"lameness_score\\": %.1f, \\"hoof_health\\": %.1f}",lame+n1*0.15,hf+n2*0.3;\n',
     "factor_cases":'--trim_weeks) TW="$2"; shift 2 ;;\n        --heel_height_mm) HH="$2"; shift 2 ;;\n        --toe_angle_deg) TA="$2"; shift 2 ;;\n        --balance_pct) BP="$2"; shift 2 ;;\n        --exercise_hrs) EX="$2"; shift 2 ;;',
     "awk_vars":'-v TW="$TW" -v HH="$HH" -v TA="$TA" -v BP="$BP" -v EX="$EX"',"vars_init":'TW=""\nHH=""\nTA=""\nBP=""\nEX=""',"validate":'[ -z "$TW" ] || [ -z "$HH" ] || [ -z "$TA" ] || [ -z "$BP" ]'},

    {"num":298,"slug":"silage_fermentation","name":"Silage Fermentation Quality","desc":"Box-Behnken design to maximize lactic acid and minimize dry matter loss by tuning chop length, packing density, and inoculant dose","design":"box_behnken","category":"veterinary",
     "factors":[{"name":"chop_mm","levels":["6","25"],"type":"continuous","unit":"mm","description":"Theoretical chop length"},{"name":"pack_kg_m3","levels":["150","300"],"type":"continuous","unit":"kg/m3","description":"Packing density"},{"name":"inoculant_cfu_g","levels":["0","1000000"],"type":"continuous","unit":"CFU/g","description":"Lactic acid bacteria inoculant dose"}],
     "fixed":{"crop":"corn","moisture":"65pct"},
     "responses":[{"name":"lactic_acid_pct","optimize":"maximize","unit":"%DM","description":"Lactic acid as % of dry matter"},{"name":"dm_loss_pct","optimize":"minimize","unit":"%","description":"Dry matter loss during ensiling"}],
     "model":'\n    cl=(CL-15.5)/9.5;pd=(PD-225)/75;in_=(IN-500000)/500000;\n    la=5+0.5*cl+1.0*pd+0.8*in_-0.3*cl*cl-0.3*pd*pd-0.2*in_*in_+0.2*pd*in_;\n    dml=8-1*cl-2*pd-0.5*in_+0.5*cl*cl+0.5*pd*pd+0.3*cl*pd;\n    if(la<2)la=2;if(la>8)la=8;if(dml<2)dml=2;if(dml>20)dml=20;\n    printf "{\\"lactic_acid_pct\\": %.1f, \\"dm_loss_pct\\": %.1f}",la+n1*0.2,dml+n2*0.5;\n',
     "factor_cases":'--chop_mm) CL="$2"; shift 2 ;;\n        --pack_kg_m3) PD="$2"; shift 2 ;;\n        --inoculant_cfu_g) IN="$2"; shift 2 ;;',
     "awk_vars":'-v CL="$CL" -v PD="$PD" -v IN="$IN"',"vars_init":'CL=""\nPD=""\nIN=""',"validate":'[ -z "$CL" ] || [ -z "$PD" ] || [ -z "$IN" ]'},

    {"num":299,"slug":"aquaculture_shrimp","name":"Shrimp Pond Management","desc":"Central composite design to maximize growth rate and survival by tuning water salinity, stocking density, and biofloc carbon source","design":"central_composite","category":"veterinary",
     "factors":[{"name":"salinity_ppt","levels":["10","30"],"type":"continuous","unit":"ppt","description":"Water salinity"},{"name":"density_per_m2","levels":["30","120"],"type":"continuous","unit":"PL/m2","description":"Post-larvae stocking density"},{"name":"carbon_g_m3","levels":["5","20"],"type":"continuous","unit":"g/m3/day","description":"Biofloc carbon source addition rate"}],
     "fixed":{"species":"L_vannamei","pond":"0.5ha"},
     "responses":[{"name":"growth_g_wk","optimize":"maximize","unit":"g/wk","description":"Weekly weight gain per shrimp"},{"name":"survival_pct","optimize":"maximize","unit":"%","description":"Harvest survival percentage"}],
     "model":'\n    sl=(SL-20)/10;dn=(DN-75)/45;cb=(CB-12.5)/7.5;\n    gr=2.0+0.3*sl-0.5*dn+0.3*cb-0.2*sl*sl-0.3*dn*dn-0.15*cb*cb+0.1*sl*cb;\n    surv=80+3*sl-5*dn+2*cb-2*sl*sl-3*dn*dn-1*cb*cb+1*sl*dn;\n    if(gr<0.5)gr=0.5;if(surv<40)surv=40;if(surv>98)surv=98;\n    printf "{\\"growth_g_wk\\": %.2f, \\"survival_pct\\": %.0f}",gr+n1*0.1,surv+n2*2;\n',
     "factor_cases":'--salinity_ppt) SL="$2"; shift 2 ;;\n        --density_per_m2) DN="$2"; shift 2 ;;\n        --carbon_g_m3) CB="$2"; shift 2 ;;',
     "awk_vars":'-v SL="$SL" -v DN="$DN" -v CB="$CB"',"vars_init":'SL=""\nDN=""\nCB=""',"validate":'[ -z "$SL" ] || [ -z "$DN" ] || [ -z "$CB" ]'},

    {"num":300,"slug":"barn_climate_control","name":"Livestock Barn Climate Control","desc":"Box-Behnken design to maximize animal comfort index and minimize energy cost by tuning ventilation rate, radiant heater coverage, and misting frequency","design":"box_behnken","category":"veterinary",
     "factors":[{"name":"vent_ach","levels":["4","20"],"type":"continuous","unit":"ACH","description":"Air changes per hour"},{"name":"heater_pct","levels":["0","50"],"type":"continuous","unit":"%","description":"Radiant heater floor coverage"},{"name":"mist_freq","levels":["0","6"],"type":"continuous","unit":"per_hr","description":"Misting cycles per hour in summer"}],
     "fixed":{"barn":"dairy_freestall","capacity":"200"},
     "responses":[{"name":"comfort_index","optimize":"maximize","unit":"pts","description":"Animal thermal comfort index (1-10)"},{"name":"energy_kwh_day","optimize":"minimize","unit":"kWh/day","description":"Daily energy consumption"}],
     "model":'\n    va=(VA-12)/8;hp=(HP-25)/25;mf=(MF-3)/3;\n    ci=6+0.5*va+0.8*hp+0.5*mf-0.4*va*va-0.3*hp*hp-0.3*mf*mf+0.2*va*mf;\n    eng=100+15*va+20*hp+5*mf+3*va*va+2*hp*hp+1*va*hp;\n    if(ci<1)ci=1;if(ci>10)ci=10;if(eng<30)eng=30;\n    printf "{\\"comfort_index\\": %.1f, \\"energy_kwh_day\\": %.0f}",ci+n1*0.3,eng+n2*5;\n',
     "factor_cases":'--vent_ach) VA="$2"; shift 2 ;;\n        --heater_pct) HP="$2"; shift 2 ;;\n        --mist_freq) MF="$2"; shift 2 ;;',
     "awk_vars":'-v VA="$VA" -v HP="$HP" -v MF="$MF"',"vars_init":'VA=""\nHP=""\nMF=""',"validate":'[ -z "$VA" ] || [ -z "$HP" ] || [ -z "$MF" ]'},
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
    echo "Missing required factors" >&2; exit 1
fi
RESULT=$(awk {uc['awk_vars']} -v seed="$RANDOM" '
BEGIN {{
    srand(seed); n1=(rand()-0.5)*2; n2=(rand()-0.5)*2;{uc['model']}}}')
mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
""")

def build_config(uc):
    return {"metadata":{"name":uc["name"],"description":uc["desc"]},"factors":uc["factors"],"fixed_factors":uc.get("fixed",{}),"responses":uc["responses"],"runner":{"arg_style":"double-dash"},"settings":{"block_count":1,"test_script":f"use_cases/{uc['num']}_{uc['slug']}/sim.sh","operation":uc["design"],"processed_directory":f"use_cases/{uc['num']}_{uc['slug']}/results/analysis","out_directory":f"use_cases/{uc['num']}_{uc['slug']}/results"}}

def main():
    for uc in USE_CASES:
        num,slug=uc["num"],uc["slug"]
        uc_dir=f"use_cases/{num}_{slug}"
        os.makedirs(os.path.join(uc_dir,"results"),exist_ok=True)
        with open(os.path.join(uc_dir,"config.json"),"w") as f: json.dump(build_config(uc),f,indent=4)
        sim_path=os.path.join(uc_dir,"sim.sh")
        with open(sim_path,"w") as f: f.write(build_sim_script(uc))
        os.chmod(sim_path,os.stat(sim_path).st_mode|stat.S_IEXEC)
        print(f"  [{num:03d}] {uc_dir}/")
    print(f"\n  {len(USE_CASES)} use cases created (251-300).")

if __name__=="__main__": main()
