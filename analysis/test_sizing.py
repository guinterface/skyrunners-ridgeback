"""Smaller TEST version of Ridgeback Scout, to be built first (2026-11-19, user: "we really nee to consider building a smaller
version for a test version"; earlier: a hover-only rig is not a meaningful proof of concept, and "something built as soon as possible").
Same layout and construction as the Scout (4 lift motors on two booms, pusher, arch tail, printed LW-ASA/CF-PETG on carbon tubes),
same hand model as mini_sizing.py and the design workbook (one formula per step). Reused from the full build (no extra cost):
Cube Orange, GPS, airspeed, telemetry, receiver, Remote ID, PM07, servo regulator, servos, Pi + sensors. Extra = lift motors,
props, ESCs, pusher, battery, airframe.
Sweeps span, lift-motor choice and pack (Molicel P50B 6S1P..6S3P, 4S2P..4S3P), three drag cases
(old sweep 0.035 / reviewer-like 0.055 / CAD buildup scaled to the smaller aircraft).
Tags: [V date] read on the maker/store page, [C] calculated here or in the workbook, [A] assumed.
Run: python3 analysis/test_sizing.py  -> analysis/out/test_sizing.md + .json
"""
import json, math
from pathlib import Path
G = 9.80665
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

# ------------------------------------------------------------------ the full Scout, for scaling and the validation run
S0, B0 = 0.50, 2.24                          # [C] cad/design.py
STRUCT0 = dict(                              # g, CAD groups summed from the workbook Mass_CG tab [C]
    wing=938.4, tail=250.5, boom=850.6,      # printed shells and boom parts: scale with wing area (minimum-wall skins) [A]
    tubes=758.2,                             # carbon spars/booms: scale with wing area, as mini_sizing.py [A]
    epoxy_hw=350.0,                          # epoxy 200 + inserts/bolts 150 [A workbook lumps]: scale with area [A]
    fuse=599.4, mounts=299.7)                # fuselage + misc pads, mounts: hold the same Cube/sensors, so scale with span only [A]
CD0_AF0 = 0.03216                            # [C] workbook Drag_Buildup: CD0 without motors, feet, stopped props, at Re of the 2.24 m
CDA_VTOL0 = (0.06260 - 0.03216) * S0         # [C] drag area of motors + feet + stopped 18 in props = 0.0152 m²
CDA_PROPS0 = 4 * 0.000785                    # [C] of which the 4 stopped P18 props
E_OSW, AR0 = 0.7557, 10.0                    # [C] workbook (Raymer straight wing, AR 10)
CLMAX0 = 1.186                               # [C] workbook: 0.9 x SD7037 cl_max 1.318 at Re 230k
P_AV = 25.1                                  # [C] workbook: avionics 15 W + minimum sensors 10.1 W
ETA_PUSH = 0.55                              # [A] workbook
RHO_TEST = 1.20                              # [A] maker test-stand density, not stated on the pages
CELL_KG, CELL_WH, PACK_OVH, CELL_A = 0.070, 18.0, 1.08, 60.0   # P50B 70 g, 5 Ah x 3.6 V, +8 % strip/BMS/wrap [workbook], 60 A rating
SOC_USE, RESERVE = 0.85, 0.20                # [A] workbook: 95 %..10 % window, 20 % landing reserve
T_HOVER_S = 2 * (45 + 15)                    # [A] workbook: 2 x (45 s hover + 15 s transition) per flight
H_CLIMB, ROC = 120.0, 1.5                    # [A] workbook
R_SITE, T_SURVEY_SHORT = 1000.0, 10.0        # [A] 1 km to the site (workbook); a SHORT test survey = 10 min over the site [A]

# fixed masses on the test aircraft, kg (moved over from the full build)
REUSED = {"Cube Orange on carrier 75 g [A, weigh it]": 0.075, "Holybro M10 GPS 32 g": 0.032, "airspeed + pitot 17.4 g": 0.0174,
          "SiK telemetry 23.5 g": 0.0235, "RP2 receiver 1 g": 0.001, "Ruko R111S Remote ID 13.5 g": 0.0135, "PM07 25 g": 0.025,
          "servo regulator 20 g": 0.020, "4 x KST X10 servos 23 g": 0.092, "mount hardware 60 g [A]": 0.060}      # parts.toml masses
SENSORS = 0.230                              # Pi 5 50, regulator 10, Lepton 25, colour camera 60, 1610 nm spot 80, SHT45 5 g (parts.toml)


def rho_at(h, dT=0.0):
    p = 101325 * (1 - 2.25577e-5 * h) ** 5.25588
    return p / (287.05 * (288.15 - 0.0065 * h + dT))


RHO_SL, RHO_HOT = rho_at(0), rho_at(800, 20)


def fit(table):
    """least squares ln P = c + k ln T over the maker's rows (thrust g, electrical W)"""
    xs = [math.log(t) for t, _ in table]; ys = [math.log(p) for _, p in table]
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - k * mx, k


# ------------------------------------------------------------------ lift motor + prop options (filled from the store pages)
LIFT = {
    # validation only: the Scout's motor, table [V store.tmotor.com 2026-10-30] as in mini_sizing.py / workbook Lift_Hover
    "MN5008 KV340 + P18 (Scout)": dict(table=[(996, 88), (1238, 120), (1541, 162), (1822, 208), (2120, 258), (2394, 311),
        (2675, 369), (2966, 432), (3262, 503), (3909, 667), (4215, 754)], t_max_g=4215, v_test=22.51, i_max=754 / 22.51,
        m_motor=0.135, m_prop=0.0315, d_prop_in=18, d_motor_mm=55.6, price_motor=89.99, price_prop_pair=82.90, cells=6,
        push="AT3520", esc="ALPHA 40A"),
}
V19 = "[V 2026-11-19]"
TM = "store.tmotor.com"
LIFT.update({
    # 6S. Tables are the maker's rows for the P15x5 carbon prop: (thrust g, electrical W = A x test V) [V 2026-11-19 store.tmotor.com]
    "MN4010 KV370 + P15x5": dict(table=[(940, 93.24), (1300, 155.40), (1620, 206.46), (1950, 270.84), (2240, 324.12)],
        t_max_g=2240, v_test=22.2, i_max=14.6, m_motor=0.137, m_prop=0.021, d_prop_in=15, d_motor_mm=46, price_motor=86.90,
        price_prop_pair=55.90, cells=6, push="AT3520", esc="ALPHA 40A",
        src=f"{TM}/product/mn4010-kv370-motor-navigator-type.html {V19}; 137 g with cable; 20 A / 450 W max; stock not shown"),
    "MN3510 KV360 + P15x5": dict(table=[(780, 66.60), (1180, 124.32), (1460, 170.94), (1700, 235.32), (1900, 277.50)],
        t_max_g=1900, v_test=22.2, i_max=12.5, m_motor=0.117, m_prop=0.021, d_prop_in=15, d_motor_mm=42, price_motor=85.36,
        price_prop_pair=55.90, cells=6, push="AT3520", esc="ALPHA 40A",
        src=f"{TM}/product/mn3510-motor-navigator-type.html $79.90; robotshop.com $85.36 'In stock' {V19}; 117 g with cable"),
    "MN4006 KV380 + P15x5": dict(table=[(805, 74), (959, 98), (1093, 115), (1236, 139), (1561, 199), (1823, 257), (2228, 360)],
        t_max_g=2228, v_test=24.0, i_max=15.0, m_motor=0.068, m_prop=0.021, d_prop_in=15, d_motor_mm=46, price_motor=149.75 / 2,
        price_prop_pair=55.90, cells=6, push="AT3520", esc="ALPHA 40A",
        src=f"{TM}/product/mn4006-kv380-motor-antigravity-type.html; robotshop.com $149.75 per 2, 'In stock' {V19}; "
            "page gives 57 g and 68 g (68 used); tested at 24 V; page's 16x5.4 run exceeds its own 16 A limit"),
    # the Scout's own lift set, flown first on the test airframe and moved to the Scout afterwards ($0 extra but a spare prop pair)
    "MN5008 KV340 + P18 (Scout's own)": dict(table=[(996, 88), (1238, 120), (1541, 162), (1822, 208), (2120, 258), (2394, 311),
        (2675, 369), (2966, 432), (3262, 503), (3909, 667), (4215, 754)], t_max_g=4215, v_test=22.51, i_max=754 / 22.51,
        m_motor=0.135, m_prop=0.0315, d_prop_in=18, d_motor_mm=55.6, price_motor=89.99, price_prop_pair=82.90, cells=6,
        push="AT3520", esc="ALPHA 40A", reuse=True,
        src="store.tmotor.com MN5008 KV340 table [V 2026-10-30] as workbook Lift_Hover; parts.toml $89.99, P18 pair $82.90"),
    # 4S
    "MN4010 KV580 + P15x5 (4S)": dict(table=[(770, 85.84), (1190, 148.0), (1450, 198.32), (1800, 260.48), (2000, 313.76)],
        t_max_g=2000, v_test=14.8, i_max=21.2, m_motor=0.137, m_prop=0.021, d_prop_in=15, d_motor_mm=46, price_motor=86.90,
        price_prop_pair=55.90, cells=4, push="AT2826", esc="F35A",
        src=f"{TM}/product/mn4010-kv370-motor-navigator-type.html (KV580 rows, 14.8 V) {V19}"),
})
# prop blade mass 21 g, P15x5 pair $55.90 [V 2026-11-19 store.tmotor.com/product/polish-carbon-fiber-15x5-prop.html]
PUSH = {"AT3520": dict(m=0.218, m_prop=0.028, t_static_g=3575, price=79.99, price_prop=12.0,       # Scout's pusher: 13x6.5 at 22 V
                       src=f"{TM}/product/at3520-long-shaft-fixed-wing-motor.html {V19}: 3575 g at 34.9 A; 2711 g at 22.6 A"),
        "AT2826": dict(m=0.175, m_prop=0.028, t_static_g=3409, price=69.99, price_prop=12.0,
                       src=f"{TM}/product/at2826-long-shaft-fixed-wing-motor.html {V19}: KV900 13x6.5, 3409 g at 57 A, 14.35 V")}
ESC = {"ALPHA 40A": dict(m=0.0545, i_cont=20, i_peak=40, price=69.99,     # 6S only (18-25.2 V); 20 A continuous, 40 A peak 10 s
                         src=f"{TM}/product/alpha-40a-6s-esc.html {V19}: $69.99, 20 A continuous / 40 A 10 s; parts.toml US price $92"),
       "F35A": dict(m=0.010, i_cont=35, i_peak=35, price=28.32,          # current and mass NOT FOUND on the page: 35 A from the name, 10 g [A]
                    src=f"tmotorhobby.com goods-586 {V19}: $28.32, 3-6S AM32; continuous A and mass NOT FOUND"),
       }
PUSH_ESC = {"AT3520": ("AT55A", 0.063, 29.99), "AT2826": ("AT75A", 0.070, 35.99)}   # [V 2026-11-19 store.tmotor.com]; AT75A mass [A]


def design(b, lift, s_cells, p_cells, cd0_case="cad", f_struct=1.0, payload=True, AR=AR0, push=None, esc=None, m_force=None):
    L = LIFT[lift]; Pu = PUSH[push or L["push"]]; E = ESC[esc or L["esc"]]
    S = b * b / AR; area = S / S0; lin = b / B0
    st = {k: v * (lin if k in ("fuse", "mounts") else area) for k, v in STRUCT0.items()}
    m_struct = sum(st.values()) / 1000 * f_struct
    m_bat = s_cells * p_cells * CELL_KG * PACK_OVH
    m_pesc = PUSH_ESC[push or L["push"]][1] if (push or L["push"]) in PUSH_ESC and lift in LIFT and not lift.endswith("(Scout)") else E["m"]
    m_prop = 4 * (L["m_motor"] + L["m_prop"]) + 4 * E["m"] + Pu["m"] + Pu["m_prop"] + m_pesc
    m_harn = 0.15 if s_cells == 6 else 0.18     # [A] 6S: half the Scout's 300 g (shorter feeds); 4S: thicker wire
    m = m_struct + m_bat + m_prop + m_harn + sum(REUSED.values()) + (SENSORS if payload else 0.0)
    m = m_force or m
    W = m * G; k_i = 1 / (math.pi * E_OSW * AR)
    # drag: airframe CD0 at lower Reynolds (Cf ~ Re^-0.2, Re ~ size) + VTOL hardware drag area scaled by prop/motor size
    cd0_af = CD0_AF0 * lin ** -0.2
    cda_vtol = CDA_PROPS0 * (L["d_prop_in"] / 18) ** 2 + (CDA_VTOL0 - CDA_PROPS0) * (L["d_motor_mm"] / 55.6) ** 2
    cd0 = {"old": 0.035, "mid": 0.055, "cad": cd0_af + cda_vtol / S}[cd0_case]
    clmax = CLMAX0 * min(lin, 1.0) ** 0.05     # [A] small cl_max loss at the lower Reynolds number (-2 % at 0.7 x size)
    out = dict(b=b, S=S, AR=AR, lift=lift, cells=f"{s_cells}S{p_cells}P", m=m, m_struct=m_struct, m_bat=m_bat, m_prop=m_prop,
               cd0=cd0, clmax=clmax, payload=payload)
    for tag, rho in (("sl", RHO_SL), ("hot", RHO_HOT)):
        vs = math.sqrt(2 * W / (rho * S * clmax))
        cl_mp = math.sqrt(3 * cd0 / k_i); v = max(math.sqrt(2 * W / (rho * S * cl_mp)), 1.3 * vs)
        q = 0.5 * rho * v * v; CL = W / (q * S); D = q * S * (cd0 + k_i * CL * CL)
        p_cr = D * v / ETA_PUSH + P_AV
        c, kk = fit(L["table"])
        p_mot = math.exp(c) * (m * 1000 / 4) ** kk * math.sqrt(RHO_TEST / rho)
        p_hov = 4 * p_mot + P_AV
        v_load = s_cells * 3.6
        t_max = L["t_max_g"] / 1000 * G * (v_load / L["v_test"]) ** 2 * rho / RHO_TEST     # T ~ V² (rpm ~ V), ~ rho [A]
        e_use = s_cells * p_cells * CELL_WH * SOC_USE * (1 - RESERVE)
        e_vtol = p_hov * T_HOVER_S / 3600
        e_climb = (p_cr + W * ROC / ETA_PUSH) * (H_CLIMB / ROC) / 3600
        t = (e_use - e_vtol - e_climb) / p_cr * 60
        e_flight = e_vtol + e_climb + p_cr * (T_SURVEY_SHORT * 60 + 2 * R_SITE / v) / 3600
        i_full = L["i_max"] * (v_load / L["v_test"])                       # full-throttle current ~ V [A]
        out.update({f"vs_{tag}": vs, f"v_{tag}": v, f"D_{tag}": D, f"Pcr_{tag}": p_cr, f"Phov_{tag}": p_hov, f"t_{tag}": t,
                    f"tw_{tag}": 4 * t_max / W, f"flights_{tag}": e_use / e_flight, f"ihov_{tag}": p_mot / v_load,
                    f"icell_full_{tag}": 4 * i_full / p_cells,
                    # cell current when the motors give the T/W 1.5 thrust (the control-margin case), capped at full throttle
                    f"icell_tw15_{tag}": min(4 * math.exp(c) * min(1.5 * m * 1000 / 4, t_max / G * 1000) ** kk
                                             * math.sqrt(RHO_TEST / rho) / v_load, 4 * i_full) / p_cells, f"thr_{tag}": (m / 4) / (t_max / G)})
    out["i_full_motor"] = L["i_max"] * (s_cells * 3.6 / L["v_test"])
    out["esc_ok"] = out["ihov_hot"] <= E["i_cont"] and out["i_full_motor"] <= E["i_peak"]   # hover continuous, full throttle peak
    out["push_static_over_W"] = Pu["t_static_g"] / 1000 * G / W
    out["passes"] = (out["tw_hot"] >= 1.5 and out["vs_sl"] <= 15.0 and out["t_sl"] >= 25 and out["esc_ok"]
                     and out["icell_tw15_hot"] <= CELL_A)
    return out


def validate():
    """The Scout itself through this model, at the workbook mass (8.92 kg) and its own CD0 buildup -> compare with the workbook."""
    d = design(B0, "MN5008 KV340 + P18 (Scout)", 6, 6, cd0_case="cad", m_force=8.9186)
    return d


PRINT_H0 = 299        # [C] full Scout print list (cad BOM.md, mini_1120): 100 prints, ~299 printer-hours


def printed_ratio(b, AR=AR0):
    area, lin = b * b / AR / S0, b / B0
    p0 = STRUCT0["wing"] + STRUCT0["tail"] + STRUCT0["boom"] + STRUCT0["fuse"] + STRUCT0["mounts"]
    return ((STRUCT0["wing"] + STRUCT0["tail"] + STRUCT0["boom"]) * area + (STRUCT0["fuse"] + STRUCT0["mounts"]) * lin) / p0


def cost(d, shared=False):
    """Extra $ for the test aircraft only (avionics, servos, Pi and sensors are moved over from the full build: $0).
    shared=True: the Scout's 4 ALPHA ESCs and AT3520 pusher are used first on the test aircraft (6S only)."""
    L = LIFT[d["lift"]]; s_c, p_c = int(d["cells"][0]), int(d["cells"][2]); push = L["push"]
    area = d["S"] / S0
    reuse = L.get("reuse", False)
    share = (shared or reuse) and s_c == 6
    prop = f"P{L['d_prop_in']}"
    c = {f"4 x {d['lift'].split(' +')[0]} ${L['price_motor']:.2f} [V]" + (" (Scout's, moved over)" if reuse else ""):
             0.0 if reuse else 4 * L["price_motor"],
         (f"1 spare pair {prop} ${L['price_prop_pair']:.2f} [V] (the 2 Scout pairs moved over)" if reuse else
          f"3 pairs {prop} (2 + 1 spare) ${L['price_prop_pair']:.2f} [V]"): (1 if reuse else 3) * L["price_prop_pair"],
         f"4 x {L['esc']} lift ESC ${ESC[L['esc']]['price']:.2f} [V]" + (" (Scout's, moved over)" if share else ""):
             0.0 if share else 4 * ESC[L["esc"]]["price"],
         f"pusher {push} ${PUSH[push]['price']:.2f} [V] + 13 in prop $12 [A]" + (" (Scout's, moved over)" if share else ""):
             0.0 if share else PUSH[push]["price"] + PUSH[push]["price_prop"],
         f"pusher ESC {PUSH_ESC[push][0]} ${PUSH_ESC[push][2]:.2f} [V]": PUSH_ESC[push][2],
         f"{s_c * p_c} P50B cells $8.99 [parts.toml] + strip/BMS $30 [A]": s_c * p_c * 8.99 + 30,
         "carbon tubes, Scout $293 x wing-area ratio [A]": 293 * area,
         "filament, Scout $297 (PETG-CF, small spools, LW-ASA) x printed-mass ratio [A]": 297 * printed_ratio(d["b"], d["AR"]),
         "wire, connectors, heat shrink (Scout $156) [A]": 90.0, "epoxy, inserts, bolts [A]": 50.0}
    return c


def sweep():
    rows = []
    packs = {6: [(6, 1), (6, 2), (6, 3)], 4: [(4, 2), (4, 3), (4, 4)]}
    for lift, L in LIFT.items():
        if lift.endswith("(Scout)"): continue
        for b in (1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9):
            for s_c, p_c in packs[L["cells"]]:
                d = design(b, lift, s_c, p_c, "cad")
                d["t_old"] = design(b, lift, s_c, p_c, "old")["t_sl"]
                d["t_mid"] = design(b, lift, s_c, p_c, "mid")["t_sl"]
                hv = design(b, lift, s_c, p_c, "cad", f_struct=1.25)
                d["t_heavy"], d["tw_hot_heavy"], d["vs_heavy"] = hv["t_sl"], hv["tw_hot"], hv["vs_sl"]
                d["cost"] = sum(cost(d).values()); d["cost_shared"] = sum(cost(d, shared=True).values())
                d["print_h"] = PRINT_H0 * printed_ratio(b)
                d["tw_hot_nopay"] = design(b, lift, s_c, p_c, "cad", payload=False)["tw_hot"]
                rows.append(d)
    # AR 8 variants (same layout, wider chord: more wing area at the same span, lower stall)
    for lift, b, p_c in [(l, b, p) for l in ("MN4010 KV370 + P15x5", "MN5008 KV340 + P18 (Scout's own)")
                         for b in (1.4, 1.5, 1.6, 1.7) for p in (2, 3)]:
            d = design(b, lift, 6, p_c, "cad", AR=8.0)
            d["t_old"] = design(b, lift, 6, p_c, "old", AR=8.0)["t_sl"]
            d["t_mid"] = design(b, lift, 6, p_c, "mid", AR=8.0)["t_sl"]
            hv = design(b, lift, 6, p_c, "cad", f_struct=1.25, AR=8.0)
            d["t_heavy"], d["tw_hot_heavy"], d["vs_heavy"] = hv["t_sl"], hv["tw_hot"], hv["vs_sl"]
            d["cost"] = sum(cost(d).values()); d["cost_shared"] = sum(cost(d, shared=True).values())
            d["print_h"] = PRINT_H0 * printed_ratio(b, 8.0)
            d["tw_hot_nopay"] = design(b, lift, 6, p_c, "cad", AR=8.0, payload=False)["tw_hot"]
            rows.append(d)
    return rows


def staged_scout(p_cells=3):
    """Option (a): the Scout itself, first flights on a 6S3P half pack (workbook mass minus the cells not fitted)."""
    m = 8.9186 - 36 * CELL_KG * PACK_OVH + 6 * p_cells * CELL_KG * PACK_OVH
    d = design(B0, "MN5008 KV340 + P18 (Scout)", 6, p_cells, "cad", m_force=m)
    d["t_old"] = design(B0, "MN5008 KV340 + P18 (Scout)", 6, p_cells, "old", m_force=m)["t_sl"]
    d["t_mid"] = design(B0, "MN5008 KV340 + P18 (Scout)", 6, p_cells, "mid", m_force=m)["t_sl"]
    return d


def row(name, d, cost_s, ph, note=""):
    return (f"| {name} | {d['b']:.2f} | {d['AR']:.0f} | {d['S']:.3f} | {d['cells']} | {d['m']:.2f} | {d['cd0']:.3f} | {d['vs_sl']:.1f} | "
            f"{d['t_old'] if 't_old' in d else float('nan'):.0f} / {d['t_mid'] if 't_mid' in d else float('nan'):.0f} / **{d['t_sl']:.0f}** | "
            f"{d['flights_sl']:.1f} | {d['tw_hot']:.2f} | {d['thr_hot']:.2f} | {cost_s} | {ph} | {note} |")


HDR = ("| Option | Span m | AR | Wing m² | Pack | Mass kg | CD0 (CAD-scaled) | Stall m/s | Loiter min, CD0 0.035 / 0.055 / **CAD-scaled** "
       "| Short flights per charge | T/W 800 m ISA+20 | Hover throttle (thrust share), hot | Extra $ | Printer-h | Fails |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")


def fails(d):
    f = []
    if d["tw_hot"] < 1.5: f.append("T/W")
    if d["vs_sl"] > 15.0: f.append(f"stall {d['vs_sl']:.1f}")
    if d["t_sl"] < 25: f.append("loiter")
    if not d["esc_ok"]: f.append("ESC")
    if d["icell_tw15_hot"] > CELL_A: f.append("cell A")
    return ", ".join(f) or "none"


ALBA = 549.90 + 12 + 30 + 18 * 8.99 + 30   # Albabird-XL PNP + UBEC + landing gear [V finwinghobby 2026-11-19] + our 6S3P P50B pack [C]


def narrative(r, a, opts):
    t1 = opts[0][1]
    return f"""# Ridgeback test version: sizing and the alternatives (2026-11-19)

[C] = `analysis/test_sizing.py` (run `python3 analysis/test_sizing.py`), [V date] = read on the maker/store page, [A] = assumed.
Every option carries the 230 g sensors and the moved-over avionics (Cube Orange, GPS, airspeed, telemetry, receiver,
Remote ID, PM07, servo regulator, 4 servos) at $0. Drag uses the CAD buildup (Scout CD0 0.063) scaled to the smaller size.
The model reproduces the workbook for the Scout itself (57.5 vs 57.4 min, T/W 1.536, stall 15.49 vs 15.52 m/s).

## Answer

1. **A same-layout test version that carries the sensors does not come out small.** About 2 kg does not shrink with the
   wing: avionics 0.36 kg, sensors 0.23 kg, a fuselage that must still hold the 40 mm-tall Cube and the sensor bay, the pusher,
   and the harness. The VTOL hardware also grows relative to a smaller wing, so CD0 rises from 0.063 to {r['cd0']:.3f}-0.11 [C].
   With new 15 in motors (MN4010/MN3510/MN4006, all with real T-Motor tables), **no span in 1.2-1.9 m meets T/W 1.5 on a
   hot day, a 15 m/s stall and 25 min together** (e.g. T1: {t1['b']:.1f} m, {t1['m']:.2f} kg, stall {t1['vs_sl']:.1f} m/s, {t1['t_sl']:.0f} min) [C].
2. **The best test version (T6) flies the Scout's own motors, props, ESCs and pusher.** Then they move to the Scout. The
   MN5008 + P18 set weighs 166 g per corner against 158 g for an MN4010 + P15, with nearly twice the thrust [V]. Span
   {r['b']:.2f} m, AR 8, wing {r['S']:.3f} m² (chord about 0.21 m, close to the Scout's 0.23 m, so the printed wing sections
   are nearly Scout-size), 6S3P, **{r['m']:.2f} kg, stall {r['vs_sl']:.1f} m/s (just over 15), {r['t_sl']:.0f} min loiter at CAD drag
   ({r['t_mid']:.0f} at CD0 0.055, {r['t_old']:.0f} at 0.035), {r['flights_sl']:.1f} short survey flights per charge, T/W {r['tw_hot']:.2f}
   at 800 m ISA+20, extra ${sum(cost(r).values()):,.0f}, about {r['print_h']:.0f} printer-hours** [C]. 15 m/s needs about 1.8 m at AR 8
   (6.57 kg, 14.9 m/s) [C]; leaving the sensors off gives 15.1 m/s.
3. **The Scout itself flown first on half its pack (6S3P) matches that envelope at no extra cost.** {a['m']:.2f} kg, stall
   {a['vs_sl']:.1f} m/s, {a['t_sl']:.0f} min, {a['flights_sl']:.1f} short flights, T/W {a['tw_hot']:.2f} [C]. The CAD and print pack
   already exist. T6 saves only about {299 - r['print_h']:.0f} of 299 printer-hours, and it needs new CAD plus new spar, CG and
   stability checks first.
4. **Recommendation: (a), build the Scout and fly it in stages on a 6S3P first pack. Do not build T6.** If the team wants
   something flying while the Scout prints, (b) the XUWING Albabird-XL 4+1 (1.5 m, $549.90, "Quantity: 6" [V]) beats T6
   on cost and time (about ${ALBA:,.0f} with our pack, no CAD, no printing). Its maker states 400 g of extra payload [V manual],
   so it can carry the sensors. It proves our PX4 VTOL setup and the first measurement, but not our airframe.
   Choosing between (a) alone and (a)+(b) is the user's call (direction and spending).

## What each option proves about the Scout

| | T6 test version | (a) Scout in stages | (b) Albabird-XL |
|---|---|---|---|
| VTOL takeoff/landing, PX4 hover tune | yes, Scout motors/ESCs, but at {r['thr_hot']:.2f} thrust share (Scout {0.65:.2f}) on a lighter, smaller airframe, so the PX4 gains will not carry over directly | yes, the real aircraft | PX4 setup only; other motors and frame |
| Hover-to-wing transition and back | yes, similar stall ({r['vs_sl']:.1f} vs 15.5 m/s) and same pusher | yes, at 14.3 m/s first, then the full pack (half-weight pack: re-check the CG and move the pack or add ballast [A]) | the logic and procedure only; ArduPilot-documented, PX4 as a generic standard VTOL [V docs.px4.io] |
| Printed LW-ASA/CF-PETG wing method | yes, near-Scout chord; spar loads lower, so wing strength is NOT proved | yes, at the real loads | no (foam) |
| Hatch / mount / cassette concept | yes, if the fuselage cross-section is kept | yes | no |
| First flying measurement (230 g sensors) | yes | yes | yes, if the bay fits (bay size NOT FOUND) |
| Scout endurance / drag (CD0 0.063, 57 min) | no; its own CD0 is {r['cd0']:.3f} | partly (drag measured in loiter); 6S6P later | no |
| Scout structure, flutter, 8.9 kg handling | no | yes | no |
| Extra cost | ${sum(cost(r).values()):,.0f} | $0 (a separate 6S3P is $192) | about ${ALBA:,.0f} |
| Time to first flight | new CAD + checks + ~{r['print_h']:.0f} printer-h | ~299 printer-h, CAD done | shipping + setup; 95 % pre-glued [V] |

Crash exposure is nearly the same in all three. Motors, ESCs, Cube and sensors ride along every time; only the airframe
differs (Scout tubes + filament about $590 [C, workbook lines] against T6's about $480). Fly a 230 g dummy until transitions work.

## Rules check

- T/W ≥ 1.5 at 800 m ISA+20: T6 {r['tw_hot']:.2f}, (a) {a['tw_hot']:.2f} [C]. With the new 15 in motors the rule caps the mass near 4.8 kg.
- Stall ≤ 15 m/s: **not met by T6 ({r['vs_sl']:.1f})**; met by (a) on 6S3P ({a['vs_sl']:.1f}). The Scout as designed is 15.5 [C workbook].
- Loiter ≥ 25-30 min with 20 % reserve: T6 {r['t_sl']:.0f}, (a) {a['t_sl']:.0f} [C] at CAD drag. With 20 % heavier structure, T6 drops to {r['t_heavy']:.0f}.
- 2 short survey flights per charge (10 min over the site [A], 1 km out and back, 2 min of VTOL each): T6 {r['flights_sl']:.1f}, (a) {a['flights_sl']:.1f} [C].
- 6S1P fails everywhere: 50-57 A per cell at full throttle and about 10 min of loiter.

## Found on the way

- **ALPHA 40A 6S is rated 20 A continuous, 40 A for 10 s** [V store.tmotor.com 2026-11-19, re-read]. Fixed 11-20: inputs.toml `I_esc = 20`
  and the parts.toml texts now say 20 A continuous / 40 A for 10 s. The Scout's hot-day hover is
  14.0 A per motor (fine), but full throttle is 33.5 A, which is a 10 s peak only. Fix the workbook check, or limit PX4 thrust.
- Shrinking the aircraft makes drag worse, not better: the motors, feet and stopped props are a fixed drag area [C].

## Assumptions that move the answer most

Structure mass: printed parts, tubes and epoxy are scaled with wing area; fuselage and mounts with span only [A]. A 20 % heavier
case is given. Wing CLmax is 1.186 x size^0.05 [A]. Pusher efficiency is 0.55 [A]. T/W uses thrust proportional to V² and to
density [A]. The test-stand density is not stated [A]. Motor tables were measured at 22.2-24 V; we fly at 21.6 V (included).
Stock status is NOT FOUND on store.tmotor.com. RobotShop shows the MN3510 and MN4006 "In stock".

"""


SOURCES = """
## Sources (read 2026-11-19 unless noted)

- MN4010 KV370/KV580 + P15x5 tables, 137 g, $86.90: https://store.tmotor.com/product/mn4010-kv370-motor-navigator-type.html
- MN3510 KV360 + P15x5 table, 117 g, $79.90: https://store.tmotor.com/product/mn3510-motor-navigator-type.html ; $85.36 "In stock": https://www.robotshop.com/products/t-motor-navigator-mn3510-360kv-brushless-motor
- MN4006 KV380 + 15x5 table (24 V), 68 g: https://store.tmotor.com/product/mn4006-kv380-motor-antigravity-type.html ; $149.75 per 2 "In stock": https://www.robotshop.com/products/tmotor-uav-brushless-motor-antigravity-mn4006-kv380-2x
- P15x5 pair $55.90, 21 g per blade: https://store.tmotor.com/product/polish-carbon-fiber-15x5-prop.html
- MN5008 KV340 + P18 table [V 2026-10-30], $89.99, P18 pair $82.90: workbook Lift_Hover and parts.toml
- AT3520 KV550 13x6.5 table, 218 g, $79.99: https://store.tmotor.com/product/at3520-long-shaft-fixed-wing-motor.html
- AT2826 KV900 table, 175 g, $69.99: https://store.tmotor.com/product/at2826-long-shaft-fixed-wing-motor.html
- ALPHA 40A 6S: 20 A cont., 40 A 10 s, 54.5 g, $69.99: https://store.tmotor.com/product/alpha-40a-6s-esc.html
- AT55A $29.99, 63 g; AT75A $35.99: https://store.tmotor.com/product/at-55a-6s-fixed-wing-esc.html , https://store.tmotor.com/categorys/at-series-fixed-wing-esc
- F35A $28.32 (current and mass NOT FOUND): https://tmotorhobby.com/goods-586-T-MOTOR+F35A+3-6S+AM32+Single+ESC.html
- Albabird-XL 4+1 PNP $549.90, UBEC +$12, gear +$30, "Quantity: 6", no FC/battery: https://www.finwinghobby.com/goods.php?id=186 ; 400 g extra payload, max AUW 4.5 kg, 115 min at 4.1 kg (maker): manual PDF https://www.finwinghobby.com/images/upload/File/Albabird%20XL%20VTOL%204+1%20User%20Manual20240527.pdf
- Makeflyeasy Striver Mini 2.1 m 4+1, $2,150 PNP, 1 kg payload, bay 180x150x110: https://www.aeroflyhobbies.com/airframe-accessories/315-makeflyeasy-striver-mini-2100mm-41-vtol-uav-pnp.html
- PX4 VTOL complete vehicles (none of the above listed): https://docs.px4.io/main/en/complete_vehicles_vtol/index
- Scout numbers: data/calc_values.json (workbook 2026-11-17 tabs Mass_CG, Drag_Buildup, Aero_Cruise, Lift_Hover, Mission_Energy); print hours: mini_1120 BOM.md (~299 printer-h)
"""


if __name__ == "__main__":
    v = validate()
    rows = sweep()
    print(f"validation (Scout, 8.92 kg, CD0 {v['cd0']:.4f}): loiter {v['t_sl']:.1f} min (workbook 57.4), hot {v['t_hot']:.1f} (53.1), "
          f"T/W hot {v['tw_hot']:.3f} (1.536), stall {v['vs_sl']:.2f} (15.52), hover {v['Phov_sl']:.0f} W (1152)")
    for r in rows:
        print(f"{r['lift'][:22]:22s} b{r['b']:.1f} AR{r['AR']:.0f} {r['cells']} m{r['m']:.2f} S{r['S']:.3f} cd0 {r['cd0']:.3f} "
              f"Vs{r['vs_sl']:.1f} t {r['t_old']:.0f}/{r['t_mid']:.0f}/{r['t_sl']:.0f} hvy{r['t_heavy']:.0f} "
              f"TWhot {r['tw_hot']:.2f}/{r['tw_hot_heavy']:.2f} fl{r['flights_sl']:.1f} Icell{r['icell_tw15_hot']:.0f} "
              f"Ihov{r['ihov_sl']:.1f} thr{r['thr_hot']:.2f} ${r['cost']:.0f}/{r['cost_shared']:.0f} {'PASS' if r['passes'] else ''}")
    pick = lambda lift, b, cells, AR=10.0: next(r for r in rows if r["lift"] == lift and abs(r["b"] - b) < 1e-9
                                              and r["cells"] == cells and r["AR"] == AR)
    SC = "MN5008 KV340 + P18 (Scout's own)"
    opts = [("T1 new MN4010 KV370, smallest with T/W 1.5", pick("MN4010 KV370 + P15x5", 1.5, "6S2P")),
            ("T2 new MN4006 KV380 (lightest motor)", pick("MN4006 KV380 + P15x5", 1.4, "6S2P")),
            ("T3 new MN4010 KV580 on 4S", pick("MN4010 KV580 + P15x5 (4S)", 1.4, "4S3P")),
            ("T4 Scout's motors, 1.5 m", pick(SC, 1.5, "6S3P", 8.0)),
            ("T5 Scout's motors, 1.8 m AR 10", pick(SC, 1.8, "6S3P")),
            ("**T6 Scout's motors, 1.7 m AR 8 (best test version)**", pick(SC, 1.7, "6S3P", 8.0))]
    a = staged_scout(3); full = staged_scout(6)
    L = ["## Options (all carry the 230 g sensors and the reused avionics) [C, analysis/test_sizing.py]", "", HDR]
    for n, d in opts:
        L.append(row(n, d, f"{d['cost']:,.0f}" + (f" ({d['cost_shared']:,.0f} with the Scout's ESCs + pusher)" if d["cost_shared"] < d["cost"] - 1 else ""),
                     f"{d['print_h']:.0f}", fails(d)))
    L.append(row("(a) the Scout itself, first flights on a 6S3P half pack", a, "0 (pack $192 if a separate 6S3P is built)", "299 (needed anyway)", fails(a)))
    L.append(row("Scout as designed, 6S6P (reference)", full, "-", "299", fails(full)))
    rec = opts[-1][1]
    L += ["", "### T6 cost lines (extra parts only) [C]", "", "| Line | $ |", "|---|---|"]
    L += [f"| {k} | {v:,.2f} |" for k, v in cost(rec).items()] + [f"| **Total** | **{sum(cost(rec).values()):,.2f}** |"]
    st = {k: vv * ((rec['b'] / B0) if k in ("fuse", "mounts") else rec['S'] / S0) for k, vv in STRUCT0.items()}
    L += ["", "### T6 mass lines [C from A scaling]", "", "| Line | kg |", "|---|---|"]
    L += [f"| structure: {k} (Scout {STRUCT0[k]:.0f} g, scaled by {'span' if k in ('fuse', 'mounts') else 'wing area'}) | {vv / 1000:.3f} |" for k, vv in st.items()]
    L += [f"| battery 6S3P P50B | {rec['m_bat']:.3f} |", f"| lift motors, props, ESCs, pusher, pusher ESC | {rec['m_prop']:.3f} |",
          "| harness 6S [A] | 0.150 |"] + [f"| {k} | {vv:.3f} |" for k, vv in REUSED.items()] + [f"| sensors (6 items, parts.toml) | {SENSORS:.3f} |",
          f"| **Takeoff** | **{rec['m']:.2f}** |"]
    L += ["", f"T6 detail [C]: loiter {rec['v_sl']:.1f} m/s, drag {rec['D_sl']:.1f} N, loiter power {rec['Pcr_sl']:.0f} W, hover {rec['Phov_sl']:.0f} W, "
          f"hover current {rec['ihov_hot']:.1f} A per motor (hot) against the ALPHA's 20 A continuous [V], full throttle {rec['i_full_motor']:.1f} A against 40 A for 10 s [V], "
          f"cell current at the T/W 1.5 thrust {rec['icell_tw15_hot']:.0f} A against 60 A, pusher static thrust / weight {rec['push_static_over_W']:.2f}, "
          f"wing CLmax {rec['clmax']:.3f}, 20 % heavier structure: loiter {rec['t_heavy']:.0f} min, T/W {rec['tw_hot_heavy']:.2f}, stall {rec['vs_heavy']:.1f} m/s; "
          f"without the sensors T/W {rec['tw_hot_nopay']:.2f}."]
    L += ["", "## Full sweep [C] (CAD-scaled CD0; 6S1P rows dropped: 50-57 A per cell at full throttle and ~10 min loiter)", "", HDR]
    for r in rows:
        if r["cells"] in ("6S1P",): continue
        L.append(row(r["lift"], r, f"{r['cost']:,.0f}", f"{r['print_h']:.0f}", fails(r)))
    L += ["", f"Validation [C]: the Scout through this model at 8.92 kg gives loiter {v['t_sl']:.1f} min (workbook 57.4), hot day {v['t_hot']:.1f} (53.1), "
          f"T/W {v['tw_hot']:.3f} (1.536), stall {v['vs_sl']:.2f} m/s (15.52), hover {v['Phov_sl']:.0f} W (1152)."]
    (OUT / "test_sizing.md").write_text(narrative(rec, a, opts) + "\n".join(L) + "\n" + SOURCES)
    json.dump(dict(validation=v, rows=rows, staged=a), open(OUT / "test_sizing.json", "w"), indent=1, default=float)
