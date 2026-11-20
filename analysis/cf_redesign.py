"""Carbon-fibre redesign of the Ridgeback Scout (Sky 3), checked against the team's requirements (2026-11-20).

User (11-20): "WE NEED TO REDESIGN EVERYTHING WE SHOULD NOT PRINT MOST OF THE STUFF WE SHOULD MOSTLY USE CARBON FIBER ...
THE WING SHOULD BE MOSTLY CF ... WE CAN PRINT CONNECTORS OR THE PLATE FOR THE ELECTRONICS", then "REDESIGN EVERYTHING ON
CALCULATION AND ESTIMATIONS". Team requirements (preliminary table from the team, 11-20): mapping and drop mission,
5 km round trip, 60 min endurance, 65 km/h cruise, 1500 g payload, 8 kg all-up weight, hover thrust/weight 2:1 or more.

What this does:
  1. Mass of every structural part rebuilt in carbon (tube spar, waterjet-cut carbon ribs, carbon plate fuselage,
     carbon plate clamps), with foam only for fairings and tail surfaces; printed parts kept only for connectors,
     feet and the electronics plate. Bought parts are taken unchanged from sheet 02 (Mass_CG).
  2. The same performance equations as the sheets (03 Aero_Cruise, 04 Lift_Hover and Mission_Energy), with their
     inputs read from data/calc_values.json, swept over wing area and battery size.
  3. A pass/fail table against each team requirement, and what it would take to pass the ones that fail.
Tags: [V] read at the source, [S] from a listing or search, [C] calculated, [A] our assumption (to be measured).
Run: python3 analysis/cf_redesign.py  -> analysis/out/cf_redesign.md + .json
"""
import json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/out"; OUT.mkdir(exist_ok=True)
G = 9.81

# ------------------------------------------------------------------ sheet values (same inputs as the website)
_R = json.load(open(ROOT / "data/refs.json")); _V = json.load(open(ROOT / "data/calc_values.json"))
_FN = "RIDGEBACK_MINI_VTOL_DESIGN_2026-11-17.XLSX"
def sv(k):
    m = re.match(r"'(.+)'!\$?([A-Z]+)\$?(\d+)", _R[k]); return _V[f"'[{_FN}]{m.group(1).upper()}'!{m.group(2)}{m.group(3)}"]
def cell(sheet, ref):
    return _V[f"'[{_FN}]{sheet}'!{ref}"]
def mass_rows():
    rows = {}
    for k, x in _V.items():
        m = re.match(r"'\[.*\]MASS_CG'!([A-L])(\d+)", k)
        if m: rows.setdefault(int(m.group(2)), {})[m.group(1)] = x
    return {d["A"]: d for r, d in rows.items() if isinstance(d.get("G"), (int, float)) and r < 100 and d.get("A")}

S0, B0, AR = sv("S"), sv("b"), sv("AR")
CD0_0, K0, CLMAX = sv("CD0_build"), sv("K"), sv("CLmax")
E_OSW = 1 / (math.pi * AR * K0)
ETA, P_AV = sv("eta_push"), sv("P_av")
T_HOV, H_CLIMB, ROC = sv("t_hov"), sv("h_climb"), sv("roc_plan")
SOC, RES = sv("soc"), sv("reserve")
RHO_SL, RHO_HOT, RHO_TEST = sv("rho_sl"), sv("rho_hot"), sv("rho_test")
FIT_C, FIT_K = sv("fit_c"), sv("fit_k")
TMAX_TEST_G, V_LOAD, V_TEST = sv("Tmax_test"), sv("V_load"), sv("V_test")
MROWS = mass_rows()

# ------------------------------------------------------------------ team requirements (preliminary)
REQ = dict(range_km=5.0, endurance_min=60.0, cruise_kmh=65.0, payload_g=1500.0, auw_kg=8.0, tw_hover=2.0)
V_CR = REQ["cruise_kmh"] / 3.6

# ------------------------------------------------------------------ materials [A unless tagged]
RHO_CF = 1.55        # g/cm3, carbon laminate (sheet, rod, strip), typical 1.5-1.6 [A]
FILM_GM2 = 45.0      # g/m2, light iron-on covering film [A: the Horizon UltraCote Lite page (read 20 Nov) gives no weight; weigh a sample]
FOAM = 0.030         # g/cm3, EPS/XPS foam for fairings and tail cores [A]
TC = 0.092           # SD7037 thickness/chord [A, airfoil library value, not re-read]
RIB_T, RIB_PITCH, RIB_LIGHT = 1.0, 0.10, 0.50   # mm (SendCutSend 0.040 in), m between ribs, fraction removed by holes [A]
def _ribs_cad():
    """Masses from the drawn ribs (cad/cf/ribs.py -> cad/out/cf_ribs/ribs.json) for the 0.50 m2 wing, without aileron ribs."""
    f = ROOT / "cad/out/cf_ribs/ribs.json"
    if not f.exists():                         # fail loudly: the site's wing mass (462 g) comes from the drawn ribs
        raise SystemExit("cad/out/cf_ribs/ribs.json missing: run cad/cf/ribs.py first (cadenv python)")
    j = json.load(open(f)); rows = [r for r in j["rows"] if not r["part"].startswith("aileron")]
    return dict(S=0.50, wing_ribs_g=sum(r["mass_g"] * r["qty"] for r in rows), n=j["n_wing_ribs"],
                te_w_mm=j["te_strip"]["w_mm"], te_t_mm=j["te_strip"]["t_mm"], removed=j["removed_mean"])
RIBS_CAD = _ribs_cad()
GLUE = 0.15          # epoxy and fillets as a fraction of the bonded carbon [A]
TAPER = 0.65         # cad/design.py

def wing_cf(S, m_kg):
    """Built-up carbon wing: tube spar + 1 mm carbon ribs + carbon LE rod + TE strip + rear false spar + film. g per part."""
    b = math.sqrt(AR * S); cr = 2 * S / (b * (1 + TAPER)); ct = cr * TAPER
    # spar: same tubes as today (analysis/mini_spar.py, sized for 9.04 kg); wall fixed, diameter ~ sqrt(moment) -> mass ~ b*sqrt(W*b)
    spar0 = sum(MROWS[n]["G"] for n in ("tube_spar_outer", "tube_spar_centre_21x19", "tube_spar_tip_inner", "tube_spar_tip"))
    # never lighter than today's tubes: a smaller wing keeps them (stiffness, joints); a bigger one needs re-sized tubes [A]
    spar = max(spar0, spar0 * (b / B0) * math.sqrt((m_kg * b) / (9.04 * B0)))
    n_ribs = 2 * math.ceil((b / 2) / RIB_PITCH) + 1
    ys = [i / (n_ribs - 1) for i in range(n_ribs)]                # 0..1 across the span
    rib_area = sum(0.68 * TC * (cr + (ct - cr) * abs(2 * y - 1)) ** 2 for y in ys)   # m2, airfoil area ~ 0.68 t c
    ribs = rib_area * 1e4 * RIB_T / 10 * RHO_CF * (1 - RIB_LIGHT)
    te = b * 100 * (1.0 * 0.1) * RHO_CF                            # 10 x 1 mm strip (old assumption)
    ail = 0.0
    if RIBS_CAD:                                                   # drawn ribs (cad/cf/ribs.py, reviewed 11-20) replace the estimate
        k = S / RIBS_CAD["S"]                                      # same AR: chord^2 ~ S, rib count ~ span ~ S^0.5
        ribs = RIBS_CAD["wing_ribs_g"] * k ** 1.5
        n_ribs = round(RIBS_CAD["n"] * k ** 0.5)
        te = b * 100 * (RIBS_CAD["te_w_mm"] / 10 * RIBS_CAD["te_t_mm"] / 10) * RHO_CF   # flush strip, about 26 x 0.5 mm
        # ailerons are foam-core panels (decision 11-20): 2 x span 0.365 m x 25 % chord, mean core 5 mm [A], film counted with the wing
        ail = 2 * 0.365 * (b / B0) * 0.25 * (S / b) * 1e4 * 0.5 * FOAM
    le = b * 100 * (math.pi / 4 * 0.3 ** 2) * RHO_CF               # 3 mm rod
    false_spar = (MROWS["rod_rear_outer"]["G"] + MROWS["rod_rear_centre"]["G"]) * b / B0   # 6/4 tubes kept (aileron hinge line)
    film = 2.04 * S * FILM_GM2
    glue = GLUE * (ribs + le + te)
    return dict(spar=spar, ribs=ribs, le_rod=le, te_strip=te, false_spar=false_spar, film=film, glue=glue, aileron_foam=ail,
                _n_ribs=n_ribs, _b=b, _cr=cr)

def fuselage_cf():
    """Carbon frame fuselage: four carbon tube rails, 1 mm carbon bulkheads (60 % cut out), a 1.5 mm carbon floor only under
    the battery and payload, carbon-rimmed hatches, and a foam + film skin (non-structural). Size kept: 0.94 x 0.17 x 0.165 m.
    A closed carbon plate box was tried first: about 1.6 kg, three times the printed fuselage, so carbon goes only where loads are."""
    L, W, H = 0.94, 0.17, 0.165
    rails = 4 * L * 100 * (math.pi / 4 * (0.8 ** 2 - 0.6 ** 2)) * RHO_CF   # 8/6 tubes
    bulkheads = 5 * W * H * 1e4 * 0.10 * RHO_CF * 0.40
    floor = 0.40 * 0.15 * 1e4 * 0.15 * RHO_CF                        # battery + payload bay, 1.5 mm
    skin_area = 2 * (L * H + L * W)
    skin = skin_area * 1e4 * 0.3 * FOAM + skin_area * FILM_GM2       # 3 mm foam sheet, filmed
    hatches = 2 * 2 * (0.16 + 0.11) * 100 * 0.1 * 0.8 * RHO_CF + 0.6 * L * W * 1e4 * 0.3 * FOAM   # carbon rims 8 x 1 mm, foam lids
    fairings = 0.12 * 1e4 * 0.5 * FOAM + 0.12 * FILM_GM2             # 5 mm foam nose + tail cone, filmed
    connectors = 120.0                                               # printed rail joints, bulkhead clips, hatch frames [A]
    glue = GLUE * (rails + bulkheads + floor)
    return dict(rails=rails, bulkheads=bulkheads, floor=floor, foam_film_skin=skin, hatches=hatches,
                fairings_foam=fairings, printed_connectors=connectors, glue=glue)

def tail_cf(S):
    """Arch tail: carbon tubes kept, foam-core panels with a carbon strip spar, printed sockets and apex kept (connectors)."""
    k = S / S0
    arc = 2 * math.hypot(0.39, 0.36); A = arc * 0.12 * k             # m, m2 (arch chord 120 mm, apex 360 mm)
    core = A * 1e4 * 0.6 * FOAM; film = 2 * A * FILM_GM2; strip = arc * 100 * 0.1 * RHO_CF
    keep = sum(MROWS[n]["G"] for n in ("tail_socket", "tail_apex", "tube_tail_spar"))
    return dict(foam_panels=core, film=film, cf_strip_spar=strip, printed_sockets_apex_and_tubes=keep)

def booms_cf():
    """Booms, legs and motor plates already carbon; printed pylons/saddles become carbon-plate clamps with printed spacers."""
    keep = sum(MROWS[n]["G"] for n in ("tube_boom", "tube_boom_sleeve", "rod_leg", "boom_motor_plate", "boom_foot"))
    old_clamps = sum(MROWS[n]["G"] for n in ("boom_pylon_lower", "boom_pylon_upper", "boom_saddle_aft", "boom_saddle_fwd"))
    clamps = 0.75 * old_clamps                                      # [A] 3 mm carbon plate pairs + printed spacers
    nacelles = 60.0                                                 # [A] foam + film fairing around motor and ESC (was 123 g printed)
    return dict(tubes_legs_plates_feet=keep, cf_plate_clamps=clamps, nacelle_fairings=nacelles)

def other_fixed():
    keep = ["gnss_M9N", "misc_gnss_pad", "misc_control_horn", "wiring_harness", "hardware_inserts_bolts"]
    d = {n: MROWS[n]["G"] for n in keep if n in MROWS}
    d["epoxy (non-structure bonds)"] = 100.0                        # [A] the structure glue is counted per part above
    d["mounts (printed electronics plate + carbon battery sled)"] = sum(v["G"] for n, v in MROWS.items() if n.startswith("mount_"))
    d["mount hardware (website part)"] = 60.0
    return d

def bought():
    groups = ("motor", "prop", "avionics")
    return {n: v["G"] for n, v in MROWS.items() if v.get("B") in groups and n != "gnss_M9N"}

def hover_p(m_kg, rho):
    return 4 * math.exp(FIT_C + FIT_K * math.log(m_kg * 1000 / 4)) * math.sqrt(RHO_TEST / rho) + P_AV

def tw(m_kg, rho, tmax_g=TMAX_TEST_G):
    return 4 * tmax_g / 1000 * G * (V_LOAD / V_TEST) ** 2 * (rho / RHO_TEST) / (m_kg * G)

WING_CDA0 = cell("DRAG_BUILDUP", "M32")    # m2, wing drag area n Cf FF Q Swet at S0 [C sheet 03 Drag_Buildup row 32]
FUSE_CDA0 = cell("DRAG_BUILDUP", "M34")    # m2, fuselage drag area (printed, rounded shape) [C sheet 03 row 34]
FILM_SAG, FUSE_BOX = 1.10, 1.25            # film sags between ribs; a flat-sided foam box drags more than the rounded print [A]
def cd0(S):
    """Drag area from the sheet's buildup: the wing part scales with S and gets +10 % for film sag, the fuselage +25 % for its
    box shape, everything else unchanged."""
    return (CD0_0 * S0 - WING_CDA0 - FUSE_CDA0 + WING_CDA0 * S / S0 * FILM_SAG + FUSE_CDA0 * FUSE_BOX) / S

def perf(S, P, payload_g, tmax_g=TMAX_TEST_G):
    w = wing_cf(S, 8.5); f = fuselage_cf(); t = tail_cf(S); bm = booms_cf(); o = other_fixed(); bo = bought()
    struct = sum(v for k, v in w.items() if not k.startswith("_")) + sum(f.values()) + sum(t.values()) + sum(bm.values())
    for _ in range(3):                                              # spar depends on mass: iterate
        bat = 6 * P * 70 * 1.08
        m = (struct + sum(o.values()) + sum(bo.values()) + bat + payload_g) / 1000
        w = wing_cf(S, m)
        struct = sum(v for k, v in w.items() if not k.startswith("_")) + sum(f.values()) + sum(t.values()) + sum(bm.values())
    W = m * G; b = math.sqrt(AR * S); K = 1 / (math.pi * E_OSW * AR); c0 = cd0(S)
    vs = math.sqrt(2 * W / (RHO_SL * S * CLMAX))
    def p_at(v):
        q = 0.5 * RHO_SL * v * v; cl = W / (q * S); return q * S * v * (c0 + K * cl * cl) / ETA + P_AV, cl
    p_cr, cl_cr = p_at(V_CR)
    e_use = 6 * P * 18.0 * SOC * (1 - RES)
    p_h = hover_p(m, RHO_SL); e_h = p_h * T_HOV / 3600
    e_cl = (p_cr + W * ROC / ETA) * (H_CLIMB / ROC) / 3600
    t_cr = (e_use - e_h - e_cl) / p_cr * 60
    vbest = max(math.sqrt(2 * W / (RHO_SL * S * math.sqrt(3 * c0 / K))), 1.3 * vs); p_b, _ = p_at(vbest)
    t_best = (e_use - e_h - e_cl) / p_b * 60
    return dict(S=S, b=b, P=P, m=m, struct_g=struct, bat_g=6 * P * 70 * 1.08, vs=vs, cl_cr=cl_cr, p_cr=p_cr, t_cr=t_cr,
                v_best=vbest, t_best=t_best, p_hov=p_h, i_hov=(p_h - P_AV) / V_LOAD, tw_sl=tw(m, RHO_SL, tmax_g),
                tw_hot=tw(m, RHO_HOT, tmax_g), wh=6 * P * 18.0, range_km=t_cr / 60 * REQ["cruise_kmh"], cd0=c0,
                parts=dict(wing=w, fuselage=f, tail=t, booms=bm, other=o, bought=bo))

def wing_twist(G_pa, v, cm=-0.10, S=None):
    """Tip twist of the tube spar alone (no D-box) under the airfoil's pitching moment. Spar tubes as built today
    (mini_spar.py): 21/19 to |y| 0.30, 17/15 to 0.87, 13/11 to the tip. cm about -0.1 for a cambered section [A]."""
    S = S or S0; b = math.sqrt(AR * S); cr = 2 * S / (b * (1 + TAPER)); ct = cr * TAPER
    q = 0.5 * RHO_SL * v * v; n = 400; dy = (b / 2) / n
    def c(y): return cr + (ct - cr) * y / (b / 2)
    def J(y):
        D, d = (0.021, 0.019) if y <= 0.30 else (0.017, 0.015) if y <= 0.87 else (0.013, 0.011)
        return math.pi / 32 * (D ** 4 - d ** 4)
    ys = [(i + 0.5) * dy for i in range(n)]
    T = [0.0] * n; acc = 0.0
    for i in reversed(range(n)):
        acc += q * c(ys[i]) ** 2 * abs(cm) * dy; T[i] = acc
    return math.degrees(sum(T[i] / (G_pa * J(ys[i])) * dy for i in range(n)))

def passes(r):
    return dict(auw=r["m"] <= REQ["auw_kg"], endurance=r["t_cr"] >= REQ["endurance_min"], range=r["range_km"] >= REQ["range_km"],
                tw=r["tw_sl"] >= REQ["tw_hover"], cruise=V_CR >= 1.3 * r["vs"])

if __name__ == "__main__":
    pay = REQ["payload_g"]
    rows = [perf(S, P, pay) for S in (0.45, 0.50, 0.55, 0.60, 0.65, 0.70) for P in (3, 4, 5, 6, 7, 8)]
    base = perf(S0, 6, 230.0)                                       # today's payload, carbon structure
    team = perf(S0, 6, pay)
    old_struct = sum(v["G"] for n, v in MROWS.items() if v.get("C") in ("print", "cnc") or v.get("B") == "tube") \
        + sum(MROWS[n]["G"] for n in ("epoxy_bond_lines",))
    # like for like: the old total also holds the printed mounts, misc pads/horns and the bond lines, so add the same
    # categories to the carbon structure (mounts unchanged, misc unchanged, non-structure epoxy for the bond lines)
    o = base["parts"]["other"]
    same = {"mounts": o["mounts (printed electronics plate + carbon battery sled)"],
            "misc pads and horns": o["misc_gnss_pad"] + o["misc_control_horn"], "other epoxy": o["epoxy (non-structure bonds)"]}
    new_like = base["struct_g"] + sum(same.values())
    L = []
    L.append("# Carbon redesign against the team's requirements [C]\n")
    L.append("Script: `analysis/cf_redesign.py`. Inputs: sheet values in `data/calc_values.json` (same equations as sheets 03 and 04), "
             "bought-part masses from sheet 02 Mass_CG, carbon part sizes drawn from `cad/design.py`. Every carbon mass is an estimate [A] until parts are weighed.\n")
    L.append("## 1. Structure: printed today, carbon now\n")
    L.append(f"Like for like (both include the electronics mounts {same['mounts']:.0f} g, misc pads and horns {same['misc pads and horns']:.0f} g and glue): "
             f"printed + tube today (sheet 02, print/cnc/tube rows + bond lines) **{old_struct/1000:.2f} kg**, carbon at the same 0.50 m² wing "
             f"**{new_like/1000:.2f} kg** ({(new_like - old_struct)/1000:+.2f} kg). The carbon structure alone (table below, with its own glue) is "
             f"{base['struct_g']/1000:.2f} kg.\n")
    L.append("| Group | Part | g |\n|---|---|---|")
    for grp, d in base["parts"].items():
        if grp in ("other", "bought"): continue
        for k, v in d.items():
            if not k.startswith("_"): L.append(f"| {grp} | {k.replace('_', ' ')} | {v:.0f} |")
    w = base["parts"]["wing"]
    if RIBS_CAD:
        L.append(f"\nWing: {w['_n_ribs']} ribs drawn in cad/cf/ribs.py (1.0 mm carbon, split front/rear at the spar, {RIBS_CAD['removed']:.0%} cut out, "
                 f"hard ribs at the bolts, boom, aileron ends, servo and tip break), flush {RIBS_CAD['te_w_mm']:.0f} x {RIBS_CAD['te_t_mm']} mm trailing-edge strip, "
                 f"foam-core ailerons; root chord {w['_cr']*1000:.0f} mm, span {w['_b']:.2f} m.\n")
    else:
        L.append(f"\nWing: {w['_n_ribs']} ribs (1.0 mm carbon, every {RIB_PITCH*1000:.0f} mm, {RIB_LIGHT:.0%} cut out), root chord {w['_cr']*1000:.0f} mm, span {w['_b']:.2f} m.\n")
    L.append("## 2. The team's requirements, at today's size (0.50 m² wing, 6S6P)\n")
    L.append("| Requirement | Team | With 1.5 kg payload | With today's 0.23 kg sensors | Pass? |\n|---|---|---|---|---|")
    p = passes(team)
    L.append(f"| All-up weight | ≤ {REQ['auw_kg']:.0f} kg | {team['m']:.2f} kg | {base['m']:.2f} kg | {'yes' if p['auw'] else 'NO'} |")
    L.append(f"| Endurance at 65 km/h | ≥ 60 min | {team['t_cr']:.0f} min | {base['t_cr']:.0f} min | {'yes' if p['endurance'] else 'NO'} |")
    L.append(f"| Range (round trip) | ≥ 5 km | {team['range_km']:.0f} km | {base['range_km']:.0f} km | {'yes' if p['range'] else 'NO'} |")
    L.append(f"| Hover thrust / weight (sea level) | ≥ 2.0 | {team['tw_sl']:.2f} (hot day {team['tw_hot']:.2f}) | {base['tw_sl']:.2f} (hot day {base['tw_hot']:.2f}) | {'yes' if p['tw'] else 'NO'} |")
    L.append(f"| Cruise 65 km/h above 1.3 × stall (derived by us, not in the team table) | stall ≤ {V_CR/1.3:.1f} m/s | stall {team['vs']:.1f} m/s | {base['vs']:.1f} m/s | {'yes' if p['cruise'] else 'NO'} |")
    L.append(f"\nEndurance = minutes of level flight at 65 km/h on the usable energy (pack Wh × {SOC:.0%} usable × (1 − {RES:.0%} reserve)) "
             f"after {T_HOV:.0f} s of hover and the climb to {H_CLIMB:.0f} m, the same definition as sheet 04 Mission_Energy.\n")
    L.append(f"\nHover power with 1.5 kg payload: {team['p_hov']:.0f} W ({team['i_hov']:.0f} A); cruise power at 65 km/h: {team['p_cr']:.0f} W; CD0 {team['cd0']:.4f}.\n")
    L.append("## 3. Sweep with the 1.5 kg payload (MN5008 KV340 + 18 in props)\n")
    L.append("| Wing m² | Span m | Pack | Mass kg | Stall m/s | Endurance at 65 km/h min | Best-speed endurance min | T/W sea level / hot | Fails |\n|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        f = [k for k, v in passes(r).items() if not v]
        L.append(f"| {r['S']:.2f} | {r['b']:.2f} | 6S{r['P']}P {r['wh']:.0f} Wh | {r['m']:.2f} | {r['vs']:.1f} | {r['t_cr']:.0f} | {r['t_best']:.0f} | {r['tw_sl']:.2f} / {r['tw_hot']:.2f} | {', '.join(f) or 'none'} |")
    ok = [r for r in rows if all(passes(r).values())]
    no_tw = [r for r in rows if all(v for k, v in passes(r).items() if k != "tw")]
    L.append("")
    L.append(f"Options passing everything: **{len(ok)}**. Passing everything except thrust/weight: **{len(no_tw)}**.\n")
    e_c = [r for r in rows if passes(r)["endurance"] and passes(r)["range"] and passes(r)["cruise"]]
    pick = min(e_c, key=lambda r: r["m"]) if e_c else min(rows, key=lambda r: (sum(not v for v in passes(r).values()), r["m"]))
    need_g = REQ["tw_hover"] * pick["m"] * 1000 / 4 / ((V_LOAD / V_TEST) ** 2 * RHO_SL / RHO_TEST)
    need_hot = REQ["tw_hover"] * pick["m"] * 1000 / 4 / ((V_LOAD / V_TEST) ** 2 * RHO_HOT / RHO_TEST)
    L.append(f"## 4. What it takes\n")
    L.append(f"- Lightest option that meets endurance, range and cruise speed (weight and T/W still fail): wing {pick['S']:.2f} m², span {pick['b']:.2f} m, 6S{pick['P']}P, {pick['m']:.2f} kg, "
             f"{pick['t_cr']:.0f} min at 65 km/h, T/W {pick['tw_sl']:.2f}."
             + (" Its spar mass is scaled from today's tubes; a wing this long needs the tubes re-sized (analysis/mini_spar.py) before the mass is firm." if pick["b"] > B0 + 0.01 else ""))
    L.append(f"- T/W 2.0 at that mass needs each lift motor to give **{need_g:,.0f} g** at full throttle on the test stand "
             f"({need_hot:,.0f} g for a hot day at 800 m). The MN5008 KV340 with 18 in props gives {TMAX_TEST_G:,.0f} g [V T-Motor table]. "
             f"So the lift motors and props must change (bigger motor or prop, or 12S), which adds motor mass: re-run with the new motor's table.")
    L.append("\n## 4b. Does a tube spar alone stop the wing twisting? [C]\n")
    L.append("| Speed | Tip twist if the tube is wrapped with ±45° plies (G about 20 GPa [A]) | Tip twist if it is a 0/90 woven wrap or pultruded (G about 5 GPa [A]) |\n|---|---|---|")
    for v in (V_CR, 25.0, 30.0):
        L.append(f"| {v:.0f} m/s | {wing_twist(20e9, v):.2f}° | {wing_twist(5e9, v):.2f}° |")
    L.append("\nUnder about 1° the tube alone is enough; above about 2° the wing needs a molded carbon leading edge (D-box). "
             "HaoZhong lists its spar tubes as roll-wrapped, but roll-wrapped does not tell the twist stiffness: a 0/90 woven wrap is "
             "nearer G 4-6 GPa (the right column) and only ±45° plies reach about 20 GPa. **So the D-box question stays open** until "
             "the layup is known (ask HaoZhong) or one wing panel is twist-tested by hand.\n")
    L.append("\n## 5. The requirements cannot all hold together: what each relaxation gives\n")
    L.append("| If we keep... | ...then | Numbers [C] |\n|---|---|---|")
    best_e = [r for r in rows if r["t_cr"] >= 60 and V_CR >= 1.3 * r["vs"]]
    if best_e:
        r = min(best_e, key=lambda r: r["m"])
        L.append(f"| 1.5 kg payload, 60 min, 65 km/h | all-up weight rises above 8 kg | {r['m']:.2f} kg (wing {r['S']:.2f} m², 6S{r['P']}P); T/W {r['tw_sl']:.2f} with today's motors |")
    cands = []
    for S in (0.50, 0.55, 0.60, 0.65, 0.70):
        for P in (5, 6, 7):
            lo, hi = 0.0, 3000.0
            for _ in range(30):
                mid = (lo + hi) / 2
                if perf(S, P, mid)["m"] <= REQ["auw_kg"]: lo = mid
                else: hi = mid
            r = perf(S, P, lo)
            if r["t_cr"] >= 60 and V_CR >= 1.3 * r["vs"]: cands.append((lo, r))
    if cands:
        lo, r = max(cands, key=lambda c: c[0])
        L.append(f"| 8 kg, 60 min, 65 km/h | payload must shrink | at most {lo:,.0f} g (wing {r['S']:.2f} m², 6S{r['P']}P), T/W {r['tw_sl']:.2f}{' (still short of 2.0)' if r['tw_sl'] < 2 else ''} |")
        max8 = dict(payload_g=lo, S=r["S"], P=r["P"], tw_sl=r["tw_sl"], m=r["m"])
    else:
        L.append("| 8 kg, 60 min, 65 km/h | no payload fits | none of the swept sizes |")
    r8 = [rr for rr in rows if rr["m"] <= REQ["auw_kg"] and V_CR >= 1.3 * rr["vs"]]
    L.append(f"| 8 kg and 1.5 kg payload | endurance must drop | {'best ' + format(max(r8, key=lambda q: q['t_cr'])['t_cr'], '.0f') + ' min' if r8 else 'no swept size stays under 8 kg with 1.5 kg'} |")
    L.append(f"| T/W 2.0 | bigger lift motors or props | need about {need_g:,.0f} g of thrust per motor at the chosen mass; adds motor mass not counted here |")
    tw_tab = [dict(v=v, g20=wing_twist(20e9, v), g5=wing_twist(5e9, v)) for v in (V_CR, 25.0, 30.0)]
    json.dump(dict(req=REQ, base=base, team=team, rows=rows, pick=pick, need_tmax_g=need_g, need_tmax_hot_g=need_hot, old_struct_g=old_struct,
                   new_like_g=new_like, same_g=same, max8=max8 if cands else None, twist=tw_tab,
                   endurance_def=dict(soc=SOC, reserve=RES, t_hov=T_HOV, h_climb=H_CLIMB)),
              open(OUT / "cf_redesign.json", "w"), indent=1, default=float)
    (OUT / "cf_redesign.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
