"""Smaller own-design VTOL quadplane, sized for our 0.45 kg sensor kit (2026-10-30, user: "OUR OWN DESIGN 100%" and no $8k).
Same hand-model as scout_perf.py (one formula per step). Sweeps wing area S and battery parallel count P (6S Molicel P50B).
Lift motor = T-Motor MN5008 KV340 + P18x6.1 (store.tmotor.com thrust table, read 2026-10-30 [V]).
Run: python3 analysis/mini_sizing.py  -> analysis/out/mini_sizing.md + .json
"""
import json, math
from pathlib import Path
G = 9.81
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

# ---- lift motor table [V] MN5008 KV340, P18x6.1, about 23 V: thrust g, power W (electrical)
MN5008 = [(996, 88), (1238, 120), (1541, 162), (1822, 208), (2120, 258), (2394, 311), (2675, 369), (2966, 432), (3262, 503),
          (3909, 667), (4215, 754)]
T_MAX_G, V_TEST = 4215, 22.51       # [V] 100 % throttle row
V_LOAD = 6 * 3.6                    # [A] 6S Li-ion under hover load
RHO_TEST = 1.20                     # [A] test-stand air density, not stated on the page

# ---- aero [A] (scout_perf.py values, adjusted for a smaller aircraft)
AR, E_OSW, CLMAX = 10.0, 0.80, 1.3   # CLMAX 1.3 per the 10-27 washout check
CDA_ROTOR = 0.0019 * (18 / 28) ** 2  # stopped-rotor drag area scaled from the 28 in Scout value
ETA_PUSH, P_AV = 0.55, 20.0          # pusher efficiency [A]; avionics 15 W + spot sensor/Pi 5 W [A]

# ---- masses, kg
SCOUT_STRUCT, SCOUT_S = 6.45, 0.866  # printed 4.97 [C BOM.md] + carbon tubes about 1.48 [A from the cut list x store g/m]
FIXED = {"sensor kit (thermal, colour camera, 1610 nm spot sensor, Pi)": 0.45,        # [A]
         "avionics: Pixhawk 6C 0.059, M9N, airspeed, telemetry, receiver, Dronetag 0.016, PM07": 0.22,   # [A]
         "4 x MN5008 0.135 [V]": 4 * 0.135, "8 x P18 blades 0.0315 [V]": 8 * 0.0315,
         "4 x ALPHA 40A 6S ESC (mass NOT FOUND, 0.05 each)": 4 * 0.05,
         "pusher AT3520 + prop + ESC (motor mass NOT FOUND)": 0.30,                      # [A]
         "4 wing/tail servos": 4 * 0.022, "harness, 6S (Scout 1.59 kg was 12S + long ESC feeds)": 0.40}   # [A]
CELL_KG, CELL_WH, PACK_OVH = 0.070, 5.0 * 3.6, 1.08   # P50B 70 g [S], 5 Ah [V], 8 % for strip, BMS, wrap [A]
SOC_USE, RESERVE = 0.95 - 0.10, 0.20

def rho_at(h, dT=0.0):
    p = 101325 * (1 - 2.25577e-5 * h) ** 5.25588
    return p / (287.05 * (288.15 - 0.0065 * h + dT))

def hover_power(T_g, rho):
    """Electrical power per motor from the table (linear in log-log), scaled to density by momentum theory."""
    xs = [math.log(t) for t, _ in MN5008]; ys = [math.log(p) for _, p in MN5008]
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return math.exp(my + k * (math.log(T_g) - mx)) * math.sqrt(RHO_TEST / rho)

def design(S, P, f_struct=1.0, cd0_af=0.025, h=0.0, dT=0.0):
    b = math.sqrt(AR * S)
    m_struct = SCOUT_STRUCT * S / SCOUT_S * f_struct
    m_bat = 6 * P * CELL_KG * PACK_OVH
    m = m_struct + m_bat + sum(FIXED.values())
    rho = rho_at(h, dT); W = m * G
    cd0 = cd0_af + 4 * CDA_ROTOR / S; k = 1 / (math.pi * E_OSW * AR)
    vs = math.sqrt(2 * W / (rho * S * CLMAX))
    cl_mp = math.sqrt(3 * cd0 / k); v = max(math.sqrt(2 * W / (rho * S * cl_mp)), 1.3 * vs)
    q = 0.5 * rho * v * v; CL = W / (q * S); D = q * S * (cd0 + k * CL * CL)
    P_cr = D * v / ETA_PUSH + P_AV
    P_hov = 4 * hover_power(m * 1000 / 4, rho) + P_AV
    e_use = 6 * P * CELL_WH * SOC_USE * (1 - RESERVE)
    e_vtol = P_hov * 2 * (45 + 15) / 3600
    e_climb = (P_cr + W * 3.0 / ETA_PUSH) * (120 / 3.0) / 3600
    t = (e_use - e_vtol - e_climb) / P_cr * 60
    tmax = T_MAX_G / 1000 * G * (V_LOAD / V_TEST) ** 2 * rho / RHO_TEST
    tw = 4 * tmax / W
    rho_h = rho_at(800, 20); tw_hot = 4 * T_MAX_G / 1000 * G * (V_LOAD / V_TEST) ** 2 * rho_h / RHO_TEST / W
    i_hov = hover_power(m * 1000 / 4, rho) / V_LOAD
    return dict(S=S, b=b, P=P, m=m, m_struct=m_struct, m_bat=m_bat, v_stall=vs, v_loiter=v, CL=CL, P_cruise=P_cr, P_hover=P_hov,
                t_min=t, tw_sl=tw, tw_800hot=tw_hot, i_hover_per_motor=i_hov, wh=6 * P * CELL_WH)

def cost(S, P):
    """Parts cost, $ (tags in the doc). Structure items scale with wing area from the Scout's store-priced lines."""
    c = {"4 x MN5008 KV340 $89.99 [V]": 4 * 89.99, "2 pairs P18x6.1 $82.90 [V]": 2 * 82.90,
         "5 x ALPHA 40A 6S $69.99 [V] (4 lift + pusher)": 5 * 69.99, "AT3520 KV550 $79.99 [V]": 79.99,
         "pusher prop [A]": 12.0, "4 x KST X10 servo $44.99 [V, upper bound]": 4 * 44.99,
         f"{6 * P} P50B cells $9.50 [V]": 6 * P * 9.50, "BMS, strip, wrap [A]": 50.0, "Dronetag Beacon $149 [V]": 149.0,
         "carbon tubes, scaled from $566 [C] by area": 566 * S / SCOUT_S, "filament, scaled from $390 [C] by area": 390 * S / SCOUT_S,
         "wiring 6S, half the Scout's $499 [A]": 250.0, "Sky4 FC, GPS, airspeed, PM07, telemetry": 0.0}
    return c

if __name__ == "__main__":
    rows = []
    for S in (0.40, 0.45, 0.50, 0.55, 0.60, 0.70):
        for P in (3, 4, 5, 6):
            d = design(S, P); d["t_lo"] = design(S, P, f_struct=1.0, cd0_af=0.035)["t_min"]
            d["t_light"] = design(S, P, f_struct=0.8)["t_min"]; d["cost"] = sum(cost(S, P).values()); rows.append(d)
    ok = [r for r in rows if r["tw_800hot"] >= 1.5 and r["v_stall"] <= 15.0]
    lines = ["| Wing m² | Span m | Cells 6S×P | Mass kg | Stall m/s | Loiter min (CD0 0.025 / 0.035 / 20 % lighter structure) | Hover T/W sea level / 800 m hot | Hover A per motor | Parts $ |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        flag = "" if r in ok else " (fails T/W or stall)"
        lines.append(f"| {r['S']:.2f} | {r['b']:.2f} | 6S{r['P']}P | {r['m']:.2f} | {r['v_stall']:.1f} | {r['t_min']:.0f} / {r['t_lo']:.0f} / {r['t_light']:.0f} | "
                     f"{r['tw_sl']:.2f} / {r['tw_800hot']:.2f} | {r['i_hover_per_motor']:.1f} | {r['cost']:,.0f}{flag} |")
    best = min((r for r in ok if r["t_lo"] >= 80), key=lambda r: (r["cost"], -r["t_lo"]), default=None)
    lines.append("")
    if best:
        lines.append(f"**Cheapest that passes (T/W ≥ 1.5 at 800 m hot, stall ≤ 15 m/s, ≥ 80 min even at CD0 0.035): wing {best['S']:.2f} m², span "
                     f"{best['b']:.2f} m, 6S{best['P']}P, {best['m']:.2f} kg, {best['t_lo']:.0f}–{best['t_min']:.0f} min, ${best['cost']:,.0f} [C].**")
        lines.append("\n| Cost line | $ |\n|---|---|")
        for k, v in cost(best["S"], best["P"]).items(): lines.append(f"| {k} | {v:,.0f} |")
        lines.append("\n| Mass line | kg |\n|---|---|")
        lines.append(f"| structure (printed + tubes), scaled by area from the Scout | {best['m_struct']:.2f} |")
        lines.append(f"| battery 6S{best['P']}P ({best['wh']:.0f} Wh) | {best['m_bat']:.2f} |")
        for k, v in FIXED.items(): lines.append(f"| {k} | {v:.2f} |")
    (OUT / "mini_sizing.md").write_text("\n".join(lines) + "\n")
    json.dump(dict(rows=rows, best=best), open(OUT / "mini_sizing.json", "w"), indent=1, default=float)
    print("\n".join(lines))
