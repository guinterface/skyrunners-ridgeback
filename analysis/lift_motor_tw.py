"""Lift motor candidates for hover thrust/weight 2 (team requirement, 20 Nov), from T-Motor's own test tables.

Reads saved r.jina.ai copies of store.tmotor.com product pages (folder given as argv[1]); each page has a test table
(prop, throttle, voltage, current, power, rpm, torque, thrust g, g/W). Keeps 6S rows (22-24 V) only, since the pack is 6S.
For each motor + prop: full-throttle thrust, and the electrical power per motor at the hover thrust of a given mass
(linear interpolation in the table). T/W uses the same correction as sheet 04 Lift_Hover: thrust x (V_load/V_test)^2 x rho/rho_test.
Run: python3 analysis/lift_motor_tw.py /scratch/users/gsbonfim/skyrunners/motor_pages -> analysis/out/lift_motor_tw.md/.json
"""
import json, re, sys, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V_LOAD, RHO_TEST, RHO_SL, RHO_HOT = 21.6, 1.20, 1.2250, 1.0588     # sheet 04 C27, C28; Constants C15, C24 [C]
M2 = round(json.load(open(ROOT / "analysis/out/cf_redesign.json"))["pick"]["m"], 2)
MASSES = (8.0, M2)   # team AUW; lightest carbon option meeting endurance (cf_redesign)
M_TODAY = 135                                                       # g, MN5008 KV340 incl. cable [V T-Motor page]

COLS = [("Voltage", "V"), ("Current", "A"), ("Power", "W"), ("RPM", "rpm"), ("Torque", "Nm"), ("Thrust", "g"), ("Efficiency", "eff")]

def parse(md):
    """Column order differs between pages, so it is read from each table's header line; a voltage missing from the rows
    (MN5212 pages) is taken from the block line 'KV340 24 T-MOTOR'. Each row is checked: V x A within 10 % of W."""
    txt = md.replace("  \n", " ")
    title = re.search(r"Title: (.+)", md).group(1)
    # motor mass per KV: spec blocks read "KV 340 ... Motor Weight(Incl. Cable)135g", so a weight belongs to the last
    # "KV nnn" (with a space) before it; pages with one spec block (MN5212) have no such token -> key None
    w, kvs = {}, None
    for m in re.finditer(r"KV (\d{2,3})\b|Weight\s*\(Incl\. Cable\)\s*(\d+)\s*g|Weight Including Cables\s*(\d+)\s*g", txt):
        if m.group(1): kvs = int(m.group(1))
        else: w.setdefault(kvs, int(m.group(2) or m.group(3)))
    price = re.findall(r"\$(\d+\.\d\d)", md)
    blocks, cur, kv, vblk, order, bad = [], None, None, None, None, 0
    for line in txt.splitlines():
        if "Throttle" in line and "Thrust" in line:
            pos = sorted((line.find(k), key) for k, key in COLS if line.find(k) >= 0); order = [key for _, key in pos]; continue
        if order is None: continue
        m = re.search(r"KV(\d+)(?:\s+(\d+(?:\.\d+)?)\s+T-MOTOR)?", line)
        if m and len(line) < 80: kv = int(m.group(1)); vblk = float(m.group(2)) if m.group(2) else None
        p = re.search(r"P?(\d{2}(?:\.\d)?\*\d+(?:\.\d+)?)\s*(?:\"|CF)", line)
        if p: cur = dict(kv=kv, prop=p.group(1), rows=[]); blocks.append(cur)
        for r in re.finditer(r"(\d{2,3})%\s*([\d. ]+)", line):
            nums = [float(x) for x in r.group(2).split()]
            ordr = [k for k in order if k != "V"] if vblk else order     # MN5212 rows have no V column but a trailing temperature
            row = dict(zip(ordr, nums))
            if "V" not in row: row["V"] = vblk
            if cur is None or not row.get("V") or not row.get("A") or not row.get("W"): continue
            if abs(row["V"] * row["A"] - row["W"]) / row["W"] > 0.10: bad += 1; continue
            row["thr"] = int(r.group(1)); cur["rows"].append(row)
    if bad: print(f"  {title[:40]}: {bad} rows failed the V x A = W check (skipped)")
    return title, w, price, [b for b in blocks if b["rows"] and 21 <= b["rows"][-1]["V"] <= 25.5]

def p_at(rows, g):
    rows = sorted(rows, key=lambda r: r["g"])
    for a, b in zip(rows, rows[1:]):
        if a["g"] <= g <= b["g"]:
            f = (g - a["g"]) / (b["g"] - a["g"]); return a["W"] + f * (b["W"] - a["W"]), a["A"] + f * (b["A"] - a["A"])
    return None, None

out = []
for f in sorted(Path(sys.argv[1]).glob("*.md")):
    md = f.read_text()
    if "404 Page" in md or "%" not in md: continue
    title, w, price, blocks = parse(md)
    for b in blocks:
        top = max(b["rows"], key=lambda r: r["thr"])
        corr = (V_LOAD / top["V"]) ** 2
        r = dict(page=f.stem, title=title, kv=b["kv"], prop=b["prop"], motor_g=w.get(b["kv"], w.get(None)), V=top["V"], A=top["A"],
                 W=top["W"], tmax_g=top["g"], tw_sl={}, tw_hot={}, hover_W={}, hover_A={})
        dm = 4 * ((r["motor_g"] or M_TODAY) - M_TODAY) / 1000          # kg, own motor mass against today's MN5008 KV340
        r["tw_own"] = 4 * top["g"] / 1000 * corr * RHO_SL / RHO_TEST / (M2 + dm)
        for m in MASSES:
            r["tw_sl"][m] = 4 * top["g"] / 1000 * corr * RHO_SL / RHO_TEST / m
            r["tw_hot"][m] = 4 * top["g"] / 1000 * corr * RHO_HOT / RHO_TEST / m
            pw, pa = p_at(b["rows"], m * 1000 / 4)                     # sheet 04 method: P(T) at test air x sqrt(rho_test/rho)
            f_ = math.sqrt(RHO_TEST / RHO_SL)
            r["hover_W"][m], r["hover_A"][m] = (pw * f_ if pw else None), (pa * f_ if pa else None)
        out.append(r)
L = ["# Lift motors for hover thrust/weight 2 [C from T-Motor test tables]\n",
     "6S rows only. T/W corrected to our 21.6 V loaded pack and air density as in sheet 04. Hover power = one motor at the "
     "hover thrust (mass/4), from the maker's table, at sea level (sheet 04 method: table power x sqrt(rho_test/rho)); four motors hover at 4x this. "
     f"Motor masses include cable, per KV. The two T/W columns at 8.0 and {M2} kg hold the take-off mass FIXED; the last T/W column adds each motor's own "
     "mass change against today's MN5008 (135 g), so heavy motors are not flattered (props and ESCs not included there).\n",
     f"| Motor | Prop | Motor g | Full throttle (V, A) | Thrust g | T/W at 8.0 kg SL / hot | T/W at {M2} kg SL / hot | T/W {M2} kg + motor mass change, SL | Hover W per motor at 8.0 / {M2} kg, SL |",
     "|---|---|---|---|---|---|---|---|---|"]
seen = set()
for r in sorted(out, key=lambda r: -r["tmax_g"]):
    key = (r["page"].split("-")[0], r["kv"], r["prop"])          # two pages of the same motor family repeat the same table
    if key in seen: continue
    seen.add(key)
    hw = " / ".join(f"{r['hover_W'][m]:.0f}" if r["hover_W"][m] else "-" for m in MASSES)
    L.append(f"| {r['page'].split('-')[0].upper()} KV{r['kv']} | {r['prop']} in | {r['motor_g']} | {r['V']:.1f} V, {r['A']:.1f} A | {r['tmax_g']:,.0f} | "
             f"{r['tw_sl'][8.0]:.2f} / {r['tw_hot'][8.0]:.2f} | {r['tw_sl'][M2]:.2f} / {r['tw_hot'][M2]:.2f} | {r['tw_own']:.2f} | {hw} |")
(ROOT / "analysis/out").mkdir(exist_ok=True)
(ROOT / "analysis/out/lift_motor_tw.md").write_text("\n".join(L) + "\n")
print("\n".join(L))

# ------------------------------------------------------------------ whole aircraft with the swap (same model as cf_redesign.py)
import importlib.util, math as _m
spec = importlib.util.spec_from_file_location("cf", ROOT / "analysis/cf_redesign.py"); cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
def fit(rows):
    xs = [_m.log(r["g"]) for r in rows if r["thr"] < 100]; ys = [_m.log(r["W"]) for r in rows if r["thr"] < 100]
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); return my - k * mx, k
pages = {f.stem: f.read_text() for f in Path(sys.argv[1]).glob("*.md")}
_, _, _, blk = parse(pages["mn6007-kv320-motor-antigravity-type"])
new = [b for b in blk if b["kv"] == 320 and b["prop"].startswith("22")][0]
_, _, _, blk0 = parse(pages["mn5008-kv400-motor-antigravity-type"])
old = [b for b in blk0 if b["kv"] == 340 and b["prop"].startswith("18")][0]
c0, k0 = fit(old["rows"]); c1, k1 = fit(new["rows"])
# swap masses [V T-Motor store pages, 20 Nov]: motor 135 -> 161 g, prop 31.5 -> 45 g, ESC ALPHA 40A 6S 54.5 -> ALPHA 60A 6S 62.8 g
DM = 4 * ((161 - 135) + (45 - 31.5) + (62.8 - 54.5))
L2 = ["\n## Whole aircraft: MN5008 KV340 + P18x6.1 vs MN6007II KV320 + P22x6.6 [C, model of analysis/cf_redesign.py]\n",
      f"Hover fits from the maker tables (P = exp(c + k ln T), W and g per motor): today c {c0:.3f} k {k0:.3f} (sheet 04 uses {cf.FIT_C:.3f} / {cf.FIT_K:.3f}); "
      f"MN6007II c {c1:.3f} k {k1:.3f}. The 'today' rows use the sheet fit, our own fit of the same table gives under 1 % less hover power, so the comparison holds. "
      f"Endurance hardly changes because hover is only {cf.T_HOV:.0f} s of the flight; the gain is less current and heat in hover. Swap adds {DM:.0f} g (4 motors +26 g, 4 props +13.5 g, 4 ESCs +8.3 g).\n",
      "| Case | Lift set | Mass kg | T/W sea level / hot | Hover W (4 motors + avionics) | Endurance at 65 km/h min | Stall m/s |", "|---|---|---|---|---|---|---|"]
MX8 = json.load(open(ROOT / "analysis/out/cf_redesign.json"))["max8"]           # largest payload at 8.00 kg with today's motors
CASE8 = f"8 kg case: {MX8['payload_g']/1000:.2f} kg payload, {MX8['S']:.2f} m², 6S{MX8['P']}P"
res = {}
top_new = max(new["rows"], key=lambda r: r["thr"])
for name, S, P, pay in (("Team 1.5 kg, 0.50 m², 6S6P", 0.50, 6, 1500.0), ("Team 1.5 kg, 0.65 m², 6S6P", 0.65, 6, 1500.0),
                        (CASE8, MX8["S"], MX8["P"], MX8["payload_g"]), ("Today's sensors, 0.50 m², 6S6P", 0.50, 6, 230.0)):
    for lab, c, k, tmax, vt, dm in (("MN5008 + P18 (today)", cf.sv("fit_c"), cf.sv("fit_k"), cf.TMAX_TEST_G, cf.sv("V_test"), 0.0),
                                    ("MN6007II + P22", c1, k1, top_new["g"], top_new["V"], DM)):
        cf.FIT_C, cf.FIT_K, cf.V_TEST = c, k, vt
        r = cf.perf(S, P, pay + dm, tmax_g=tmax)
        res[(name, lab)] = r
        L2.append(f"| {name} | {lab} | {r['m']:.2f} | {r['tw_sl']:.2f} / {r['tw_hot']:.2f} | {r['p_hov']:,.0f} | {r['t_cr']:.0f} | {r['vs']:.1f} |")
    cf.FIT_C, cf.FIT_K, cf.V_TEST = cf.sv("fit_c"), cf.sv("fit_k"), cf.sv("V_test")   # back to the sheet values
L2.append(f"\nWith the swap the 8 kg case is {res[(CASE8, 'MN6007II + P22')]['m']:.2f} kg; to stay at 8.00 kg its payload "
          f"drops from {MX8['payload_g']:.0f} g to about {MX8['payload_g'] - DM:.0f} g.")

# ---- full team point with the swap: smallest wing (0.01 m2 steps) that keeps stall <= cruise / 1.3 with 1.5 kg payload
VS_MAX = cf.REQ["cruise_kmh"] / 3.6 / 1.3
cf.FIT_C, cf.FIT_K, cf.V_TEST = c1, k1, top_new["V"]
full = None
for S100 in range(50, 81):
    r = cf.perf(S100 / 100, 6, 1500.0 + DM, tmax_g=top_new["g"])
    if r["vs"] <= VS_MAX and r["t_cr"] >= cf.REQ["endurance_min"]:
        full = (S100 / 100, r); break
cf.FIT_C, cf.FIT_K, cf.V_TEST = cf.sv("fit_c"), cf.sv("fit_k"), cf.sv("V_test")
if full:
    S_, r = full
    L2.append(f"\nFull team point with the swap (1.5 kg payload, 6S6P, every requirement except the 8 kg limit): smallest wing that keeps stall at or "
              f"below {VS_MAX:.1f} m/s is {S_:.2f} m² ({r['b']:.2f} m span): {r['m']:.2f} kg, stall {r['vs']:.2f} m/s, {r['t_cr']:.0f} min at 65 km/h, "
              f"T/W {r['tw_sl']:.2f} sea level / {r['tw_hot']:.2f} hot.")

# ---- ESC current (I ~ V^2 for a fixed prop, from the table's full-throttle row)
i_load = top_new["A"] * (V_LOAD / top_new["V"]) ** 2; i_full = top_new["A"] * (25.2 / top_new["V"]) ** 2
i_hov = res[("Team 1.5 kg, 0.50 m², 6S6P", "MN6007II + P22")]["i_hov"] / 4
L2.append(f"\nESC current per lift motor, MN6007II + P22 (ALPHA 60A 6S: 40 A continuous, 60 A for 10 s [V T-Motor page]): full throttle "
          f"{top_new['A']:.1f} A in the maker's test at {top_new['V']:.1f} V, about {i_load:.0f} A on our loaded pack (21.6 V) and about {i_full:.0f} A on a fresh "
          f"pack (25.2 V); hover about {i_hov:.0f} A. Full throttle is therefore above the continuous rating and allowed only as a burst under 10 s "
          "(climb-out, gust recovery); hover is far below it. Today's ALPHA 40A 6S is 20 A continuous / 40 A for 10 s [V saved page alpha-40a-6s-esc.esc]; inputs.toml I_esc is now 20.")

# ---- cost, duty as the buy list charges it (data/buy_list.json: motors 149.38 on 359.96, props 62.18 on 165.80; ESC from US stock, no duty)
bl = {r["id"]: r for r in json.load(open(ROOT / "data/buy_list.json")) if "id" in r}
dm_rate = bl["motor_lift"]["duty"] / bl["motor_lift"]["line"]; dp_rate = bl["prop_lift"]["duty"] / bl["prop_lift"]["line"]
old_cost = sum(bl[k]["line"] + bl[k]["duty"] for k in ("motor_lift", "prop_lift", "esc_lift"))
new_cost = 4 * 129.99 * (1 + dm_rate) + 2 * 140.90 * (1 + dp_rate) + 4 * 69.99 * 1.375
L2.append(f"\nPrices [V T-Motor store, 20 Nov]: MN6007II KV320 $129.99 (MN5008 $89.99), P22x6.6 pair $140.90 (P18x6.1 $82.90), ALPHA 60A 6S $69.99. "
          f"With duty as the buy list charges it (motors {dm_rate:.1%}, props {dp_rate:.1%}, ESCs 37.5 % from China): new set ${new_cost:,.0f} against "
          f"${old_cost:,.0f} in the buy list today, so about ${new_cost - old_cost:,.0f} more.")

# ---- geometry (cad/design.py mini block; pusher prop plane at PUSHER_X + motor h + 15, cad/fab/assemble_mini.py:80)
BOOM_Y, REAR_X, TAIL_LE, PUSH_R = 390.0, 549.0, 828.0, 305.0 / 2
PUSH_PLANE_X = 560.0 + 52.0 + 15.0
L2.append(f"\nPlan-view clearances (rear motor x {REAR_X:.0f}, booms y {BOOM_Y:.0f}, pusher prop plane x {PUSH_PLANE_X:.0f}, arch tail leading edge x {TAIL_LE:.0f}). "
          "These are plan-view rules: in 3D the lift prop plane is about 44 mm above the pusher axis, so the real blade gap is larger (about 25-30 mm at 22 in, "
          "reviewer); the issue at small plan-view gaps is the lift wake hitting the pusher disc, not a blade strike.\n")
for d_in in (18, 21, 22):
    r = d_in * 25.4 / 2
    half = math.sqrt(max(0.0, r * r - (PUSH_PLANE_X - REAR_X) ** 2))      # disc half-width in y at the pusher plane
    gap = BOOM_Y - half - PUSH_R
    tail = TAIL_LE - (REAR_X + r)
    L2.append(f"- {d_in} in: at x {PUSH_PLANE_X:.0f} the rear disc reaches y {BOOM_Y - half:.0f}, pusher disc to y {PUSH_R:.0f}: gap {gap:+.0f} mm "
              f"(booms at y {PUSH_R + half + 20:.0f} give 20 mm). Disc aft edge x {REAR_X + r:.0f} vs tail leading edge {TAIL_LE:.0f}: {tail:+.0f} mm "
              + (f"(tail {25 - tail:.0f} mm aft gives 25 mm)." if tail < 25 else "(fine)."))
r22 = 22 * 25.4 / 2
L2.append(f"\nOpen with the 22 in swap: (1) the arch tail must move about {25 - (TAIL_LE - REAR_X - r22):.0f} mm aft (boom 1358 -> about 1385 mm, still two 1 m pieces) "
          "or the rear motor forward (costs the 35 mm wing trailing-edge clearance); re-check static margin. (2) booms to about y "
          f"{PUSH_R + math.sqrt(r22**2 - (PUSH_PLANE_X - REAR_X)**2) + 20:.0f}: CENTER_HALF (= BOOM_Y, the wing centre-section joint and washout start) and the arch "
          f"tail width move with them. (3) at that boom y the disc reaches y {PUSH_R + math.sqrt(r22**2 - (PUSH_PLANE_X - REAR_X)**2) + 20 + r22:.0f}, so most of the "
          "aileron span (y 500 to that point, of 500-865) sits in the lift wake in hover and transition. (4) mass not yet counted: the MN6007II is 67.2 mm across against the 64 mm motor "
          "plate (new plate and bolt pattern), the ALPHA 60A is 71.3 x 32.5 x 15.9 mm against 64.5 x 29.4 x 14.7 (new ESC cradle). "
          "A milder option is the same motor with 21 in props: T/W just under 2 with its own motor mass (table above), booms to about y 428 and the tail about 13 mm aft.")
(ROOT / "analysis/out/lift_motor_tw.md").write_text((ROOT / "analysis/out/lift_motor_tw.md").read_text() + "\n".join(L2) + "\n")
json.dump(dict(rows=out, swap=dict(dm_g=DM, cost_new=new_cost, cost_old=old_cost, i_load=i_load, i_fresh=i_full, i_hover=i_hov,
               cases={f"{a} | {b}": {k: v for k, v in r.items() if k != "parts"} for (a, b), r in res.items()})),
          open(ROOT / "analysis/out/lift_motor_tw.json", "w"), indent=1)
print("\n".join(L2))
