"""Build the Ridgeback mini-VTOL design workbook (xlsx with live formulas) for Google Sheets.

Every number is an input with a source tag, or a formula on other cells. Run from the sheets/ folder:
  python3 build_sheet.py   (needs openpyxl)
Inputs: mass_rows.json (export_mass.py, CAD), sd7037_polar.json (NeuralFoil), values typed below with their sources.
"""
import json, re
from collections import OrderedDict
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
OUTF = HERE / "Ridgeback_mini_VTOL_design_2026-11-17.xlsx"
REPO = "<repo>"

wb = Workbook()
wb.remove(wb.active)
REF = {}            # key -> 'Tab'!$C$n
PENDING = []        # (ws, cell, template)

SITE = "https://guinterface.github.io/skyrunners-ridgeback/"

# Prices, links, quantities and masses of bought parts come from data/parts.toml (one place to edit).
import sys as _sys, tomllib as _toml
_sys.path.insert(0, str(HERE.parent / "tools"))
from parts import PARTS as _PARTS
PP = {p["id"]: p for p in _PARTS}
_NONE = dict(price=0, buy=[], mass=0, qty=0, where="", name="")      # a part removed on the website counts as zero
def _pp(pid): return PP.get(pid, _NONE)
def part_price(pid): return _pp(pid)["price"]                         # unit price, US$
def part_url(pid): return _pp(pid)["buy"][0][1] if _pp(pid)["buy"] else ""   # first shop link
def part_mass(pid): return _pp(pid)["mass"]                          # mass each, g
def part_qty(pid): return _pp(pid)["qty"]
def buy_qty(p): return 0 if p.get("order") == "have it" else p["qty"]   # already ours: nothing to buy
def part_store(pid): return _pp(pid)["buy"][0][0].split(" (")[0] if _pp(pid)["buy"] else _pp(pid).get("where", "")

# Typed design inputs can be changed in data/inputs.toml without touching this file.
_INF = HERE.parent / "data/inputs.toml"
INPUTS = _toml.loads(_INF.read_text()) if _INF.exists() else {}
INPUTS = {k: v for grp in INPUTS.values() for k, v in (grp.items() if isinstance(grp, dict) else [])}
USED_INPUTS = set()
TYPED = []   # every typed input: (tab, key, label, value, unit, source)
PART_KEYS = [("pixhawk", "pixhawk"), ("m9n", "gnss"), ("airspeed", "airspeed"), ("pm07", "pm07"), ("telemetry", "telemetry"), ("rc receiver", "rc_rx"),
             ("mn5008", "motor_lift"), ("p18", "prop_lift"), ("alpha 40a", "esc_lift"), ("at3520", "motor_pusher"), ("apc", "prop_pusher"),
             ("kst", "servos"), ("servo regulator", "servo_reg"), ("ruko", "remote_id"), ("p50b", "battery"), ("bms", "battery"),
             ("tubes", "booms"), ("carbon plates", "booms"), ("solid rod", "wing")]


def part_link(ws, r, c, name):
    """Hyperlink cell that opens this part on the website's 3D drone."""
    n = (name or "").lower()
    pid = next((v for k, v in PART_KEYS if k in n), None)
    if pid:
        cell = put(ws, r, c, "see on the drone")
        cell.hyperlink = SITE + "index.html#" + pid; cell.font = Font(color="1155CC", underline="single")
HDR = PatternFill("solid", fgColor="1F3A5F"); HFONT = Font(bold=True, color="FFFFFF")
INP = PatternFill("solid", fgColor="FFF4CC")   # typed input (with source)
CALC = PatternFill("solid", fgColor="E8F1FB")  # formula
KEY = PatternFill("solid", fgColor="D9F2D9")   # key result
BAD = PatternFill("solid", fgColor="F8D7DA")
SEC = Font(bold=True, size=12, color="1F3A5F")
TITLE = Font(bold=True, size=14)
thin = Side(style="thin", color="C8CCD2")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")


def q(ws):
    return "'" + ws.title + "'"


def sheet(name, widths):
    ws = wb.create_sheet(name)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.sheet_view.zoomScale = 100
    ws._r = 1
    return ws


def lit(v):
    return ("→ " + v[1:].strip()) if isinstance(v, str) and v.startswith("=") else v


def put(ws, r, c, v, fill=None, bold=False, fmt=None, wrap=True):
    cell = ws.cell(row=r, column=c)
    if isinstance(v, str) and "{" in v and v.startswith("="):
        PENDING.append((cell, v))
    else:
        cell.value = v
    if fill: cell.fill = fill
    if bold: cell.font = Font(bold=True)
    if fmt: cell.number_format = fmt
    cell.border = BOX
    if wrap: cell.alignment = WRAP
    return cell


def title(ws, text, sub=None):
    ws.cell(row=ws._r, column=1, value=text).font = TITLE; ws._r += 1
    if sub:
        c = ws.cell(row=ws._r, column=1, value=sub); c.alignment = Alignment(wrap_text=False); ws._r += 1
    ws._r += 1


def section(ws, text):
    ws._r += 1
    ws.cell(row=ws._r, column=1, value=text).font = SEC; ws._r += 1


def header(ws, cols):
    for i, h in enumerate(cols, 1):
        c = ws.cell(row=ws._r, column=i, value=h); c.fill = HDR; c.font = HFONT; c.alignment = WRAP; c.border = BOX
    ws._r += 1


PARAM_COLS = ["Quantity", "Symbol", "Value", "Unit", "Equation / how it is found", "Source [tag]", "Note"]


SUB = str.maketrans("0123456789aehiklmnoprstuvx+-=()", "₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢₖₗₘₙₒₚᵣₛₜᵤᵥₓ₊₋₌₍₎")
NAMES = {"CL_mp": "C_L at min power", "V_mp": "V at min power", "CL_max": "C_L,max", "C_L,max": "C_L,max", "P_av": "P avionics", "η_p": "η pusher",
         "E_u": "E usable", "E_h": "E hover", "E_c": "E climb", "E_f": "E per flight", "t_tr": "t transit", "t_s": "t survey", "t_h": "t hover",
         "V_test": "V test", "V_load": "V load", "ρ_test": "ρ test", "T_max": "T max", "I_ESC": "I ESC rating", "I_100": "I at 100 %",
         "m_bat": "m battery", "m_e": "m empty", "m_p": "m payload", "x_cg": "x CG", "Δx_bat": "battery shift", "S_wet,f": "S wet fuselage",
         "L_f": "L fuselage", "W_f": "W fuselage", "H_f": "H fuselage", "L_b": "L boom", "D_b": "D boom", "h_t": "h tail",
         "y_b": "y boom", "L_t": "L tail", "CDA_r": "CDA rotor", "V_ref": "V ref", "V_0": "V zero thrust", "J_0": "J zero thrust",
         "T_0": "T static", "c_r": "c root", "T(V)": "T at speed", "D / T(V)": "D ÷ T", "T/T_max": "T ÷ T max", "P_m": "P per motor",
         "P_hov": "P hover", "P_T": "P thrust", "P_cr": "P loiter", "I_m": "I per motor", "I_cell": "I per cell", "E_cell": "E per cell"}


def readable(t):
    """Engineering notation without code: subscripts, √, ², no underscores."""
    if not isinstance(t, str) or not t or t.startswith("="):
        return t
    keep = {}
    def protect(m):
        keep[f"\x00{len(keep)}\x00"] = m.group(0); return f"\x00{len(keep) - 1}\x00"
    t = re.sub(r"\b[A-Z][a-z]{2,}[A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b|\S+\.(?:py|md|json)\b|\b[A-Z0-9]{2,}(?:_[A-Z0-9]+)+\b", protect, t)
    for k in sorted(NAMES, key=len, reverse=True):
        t = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(k) + r"(?![A-Za-z0-9_])", NAMES[k], t)
    t = t.replace("sqrt", "√").replace("^2", "²").replace("^3", "³").replace("^0.5", "^½").replace(" * ", " · ").replace("*", "·")
    def sub(m):
        body = m.group(2)
        return m.group(1) + (body.translate(SUB) if all(ch in "0123456789aehiklmnoprstuvx+-=()" for ch in body) else body)
    t = re.sub(r"([A-Za-zρηΔμ])_\(([^)]*)\)", lambda m: m.group(1) + m.group(2), t)
    t = re.sub(r"([A-Za-zρηΔμ\)])_([A-Za-z0-9,]+)", sub, t)
    for k, v in keep.items():
        t = t.replace(k, v)
    return t


HISTORY = re.compile(r"\s*\((?:[^()]*(?:fixed 11-17|review|was a formula|mini_sizing|old sizing)[^()]*)\)|;?\s*(?:fixed 11-17[^;.]*|[^;.]*mini_sizing\.py[^;.]*|[^;.]*old sizing[^;.]*|type 0\.[^;.]*)", re.I)


HIST_WORDS = re.compile(r"mini_sizing|fixed 11-17|old sizing|review|type 0\.|was a formula", re.I)


def clean(t):
    """Drop note segments that only tell the history of our work; keep the ones that explain the number."""
    if not isinstance(t, str) or t.startswith("="):
        return t
    segs = [x.strip() for x in re.split(r";\s+", t)]
    return "; ".join(x for x in segs if x and not HIST_WORDS.search(x))


def p(ws, key, label, sym, val, unit, eq, src, note="", fmt="0.000", key_result=False):
    """One parameter row: value in column C. Strings starting with '=' are formulas ({key} -> cell)."""
    r = ws._r
    isf = isinstance(val, str) and val.startswith("=")
    if key in INPUTS:
        assert not isf, f"data/inputs.toml sets '{key}', but '{label}' is calculated, not typed. Remove it from inputs.toml."
        val = INPUTS[key]; USED_INPUTS.add(key)
    if key and not isf:
        TYPED.append((ws.title, key, label, val, unit, src))
    put(ws, r, 1, label); put(ws, r, 2, readable(sym))
    put(ws, r, 3, val, fill=(KEY if key_result else (CALC if isf else INP)), fmt=fmt, bold=key_result)
    put(ws, r, 4, lit(unit)); put(ws, r, 5, readable(lit(eq))); put(ws, r, 6, clean(lit(src))); put(ws, r, 7, readable(clean(lit(note))))
    if key:
        assert key not in REF, key
        REF[key] = f"{q(ws)}!$C${r}"
    ws._r += 1
    return r


def text_rows(ws, rows, widths_cols=None, fills=None):
    for row in rows:
        for i, v in enumerate(row, 1):
            put(ws, ws._r, i, v, fill=(fills.get(i) if fills else None))
        ws._r += 1


def resolve():
    for cell, tpl in PENDING:
        def rep(m):
            k = m.group(1)
            if k not in REF:
                raise KeyError(f"unknown ref {k} in {cell.parent.title}!{cell.coordinate}: {tpl}")
            return REF[k]
        cell.value = re.sub(r"\{([A-Za-z0-9_]+)\}", rep, tpl)


# =====================================================================================================
# README
ws = sheet("README", [26, 120])
title(ws, "Ridgeback Scout, our own 2.24 m VTOL: complete design workbook (2026-11-17)",
      "SkyRunners (Stanford Student Robotics). Every step from requirements to cost, with the equations live, so anyone can check and change it.")
text_rows(ws, [
    ["What this is", "The whole design chain for our own small VTOL quadplane (4 lift motors on two booms + 1 pusher, 2.24 m wing, 6S6P Li-ion): "
     "requirements -> mass and CG (from the CAD) -> airfoil -> drag buildup -> cruise aero -> hover thrust -> pusher thrust -> mission energy -> "
     "battery choice -> structure/stability checks -> electronics -> bill of materials and cost -> ways to cut cost -> decisions and why -> open checks."],
    ["Goal of the aircraft", "Fly over chaparral at dawn and at midday carrying our own sensors (thermal + a 1610 nm water-band sensor), to measure how much water "
     "shrubs lose during the day for prescribed-burn planning. Our sensor kit is light (~0.3-0.45 kg), so the aircraft can be small and cheap."],
    ["How to read a tab", "Yellow cells = typed inputs, each with its source. Blue cells = formulas on other cells (click a cell to see the formula). "
     "Green cells = key results. Change a yellow input and every result updates."],
    ["Tags", "[V] read today or on the stated date at the primary source (store page, datasheet, CAD output).  [S] secondary source or search snippet, "
     "not re-read.  [C] calculated here or by our scripts.  [A] assumption, needs a test or a better source.  NOT FOUND = we looked and found no value."],
    ["Units", "SI throughout (m, kg, N, W, Wh, m/s). Masses in the parts list are in grams. Prices in USD."],
    ["Where the numbers come from", f"CAD: {REPO}/cad/fab (build123d), exported per part with export_mass.py (161 rows, 8,478 g, CG x 94.2 mm, same as the CAD assembly). "
     f"Sizing model: {REPO}/analysis/mini_sizing.py. Structure, spar, boom, servo, wiring, duty: {REPO}/analysis/mini_*.py -> analysis/out/*.md. "
     f"Stability: AVL 3.40 ({REPO}/analysis/mini_avl_cad.py). Prices: {REPO}/docs/BEST_PRICES_2026-11-10.md and BUY_LIST_2026-11-02.md. Airfoil: NeuralFoil (large) on SD7037."],
    ["What is new in this workbook (11-17)", "1) Drag buildup part by part (the earlier sizing used an assumed CD0 0.025-0.035). "
     "2) Wing CLmax taken from the airfoil polar (0.9 x section cl_max) instead of an assumed 1.3. 3) Pusher check with T-Motor's own AT3520 test table. "
     "4) Mass from the CAD + payload instead of the sizing estimate. 5) Battery options recomputed with the same equations. Results that changed are flagged on the Decisions and Open_Checks tabs."],
    ["Honest status", "Nothing has flown. Nothing has been ordered by an agent. Masses of printed parts are CAD volume x density; the first printed test pieces will tell. "
     "Every [A] value is a place where a test or a better source would change the answer; the biggest ones are listed on Open_Checks."],
    ["Not in here (on purpose)", "How the water measurement is computed (internal until Stanford OTL). Sensor science is in the sensor doc, not here."],
    ["Website", f"{SITE} : the drone in 3D (click a part), mission and range with references, the equations, and links to all six sheets"],
    ["Tabs", "Requirements | Constants | Mass_CG | Airfoil_SD7037 | Drag_Buildup | Aero_Cruise | Lift_Hover | Pusher | Mission_Energy | Battery_Options | "
     "Structure_Stability | Electronics | Connectors_Wiring | BOM_Cost | Cost_Options | Decisions | Open_Checks | Sources"],
])

# =====================================================================================================
ws = sheet("Summary", [46, 14, 14, 12, 70])
title(ws, "Summary: does the design meet its requirements? (live: every number links to its tab)")
header(ws, ["Requirement / result", "Sea level", "800 m ISA+20", "Rule", "Status and what it means"])


def srow(label, a, b, rule, status):
    r = ws._r
    put(ws, r, 1, label); put(ws, r, 2, a, fill=CALC, fmt="0.00"); put(ws, r, 3, b, fill=CALC, fmt="0.00"); put(ws, r, 4, rule); put(ws, r, 5, status)
    ws._r += 1
    return r


srow("Takeoff mass (kg), CAD + payload", "={m_to}", "={m_to}", "", "=\"From 161 CAD parts + \"&TEXT({m_pay_g},\"0\")&\" g of mission sensors. Printed-part masses still to be weighed.\"")
r_ = srow("CG x (mm) vs target 94", "={cg_x}", "", "94 ± 5", "=IF(ABS({cg_x}-{cg_target})<=5,\"OK: within 5 mm, trim with the battery\",\"MOVE BATTERY\")")
srow("Hover thrust / weight", "={TW_sl}", "={TW_hot}", "≥ 1.5 hot", "=IF({TW_hot}>={req_tw},\"PASS\",\"FAIL\")&\": MN5008 + P18 maker data; matches our Python model exactly\"")
srow("Hover power (W)", "={Phov_sl}", "={Phov_hot}", "", "About 13-14 A per motor, under the 40 A ESCs; about 9 A per cell.")
srow("Stall speed (m/s), clean wing", "={Vs_sl}", "={Vs_hot}", "≤ 15 SL", "=IF({Vs_sl}<={req_stall},\"PASS\",\"FAIL by \"&TEXT({Vs_sl}-{req_stall},\"0.0\")&\" m/s\")&\": CLmax from the SD7037 polar. Flaps (already in the CAD) or relaxing the rule (VTOL lands on rotors) would fix it.\"")
srow("CD0 (drag buildup)", "={CD0_build}", "", "first sizing assumed 0.025-0.035", "An independent check put it at 0.040 to 0.090, most likely 0.060. The exposed lift motors, landing feet and stopped props are about 45 %.")
srow("Loiter speed (m/s)", "={V_sl}", "={V_hot}", "", "Set by 1.3 x stall, not by best power.")
srow("Loiter power (W)", "={Pcr_sl}", "={Pcr_hot}", "", "The first sizing assumed about 238 W, with a drag coefficient of 0.031.")
srow("Loiter time (min), 20 % reserve left", "={tloit_sl}", "={tloit_hot}", "≥ 80", "=IF({tloit_sl}>={req_loiter},\"PASS\",\"FAIL\")&\": see the levers below. Upper bound if motors, feet and props added no drag at all (CD0 \"&TEXT({CD0_clean},\"0.000\")&\"): \"&TEXT({t_clean},\"0\")&\" min (Mission_Energy sensitivity).\"")
srow("Flights per battery: 15 min over a 2 ha site, 1 km out", "={flights_pack}", "", "≥ 3 per day", "=IF({flights_pack}>={req_flights},\"PASS\",\"FAIL\")&\": the field day (pre-dawn, mid-morning, midday) on one battery, 20 % reserve kept.\"")
srow("Range on one charge (km)", "={range_km}", "", "not a driver", "We may only fly within about 1 km (line of sight, Part 107), so range is never the limit; hover thrust and time on site are.")
srow("Pusher: thrust needed / available at loiter", "={Tratio_sl}", "={Tratio_hot}", "< 1", "=\"Level loiter OK. Best winged climb ≈ \"&TEXT({ROC_hot},\"0.0\")&\"-\"&TEXT({ROC_sl},\"0.0\")&\" m/s (estimate from 13x6.5 data): plan 1.5 m/s or climb on rotors.\"")
srow("Aircraft cost (USD)", "={cost_total}", "", "≤ 3000", "=IF({cost_total}<={req_budget},\"PASS\",\"OVER\")&\" by $\"&TEXT(ABS({req_budget}-{cost_total}),\"0\")&\". Sensors and ground equipment (transmitter, charger) are counted separately.\"")
section(ws, "What to do next, cheapest first")
text_rows(ws, [
    ["1. Fair the bluff parts (cost: filament only)", "", "", "", "Teardrop TPU feet, a printed cowl/spinner over each lift motor, and park the lift props fore-aft in cruise. Together they are about 45 % of CD0 (Summary row: loiter time with them faired)."],
    ["2. Measure instead of assume", "", "", "", "Weigh the first printed parts; bench-test the 12x6E pusher; glide or fly to fit the real CD0. Each replaces an [A] on these tabs."],
    ["3. Cut cost where risk is low", "", "", "", "Cost_Options: club leftovers, hardware from stock, skip the nozzle if not needed."],
    ["4. Only then change size or battery", "", "", "", "A 7P pack adds time but drops hot-day T/W under 1.5 (Battery_Options); a larger wing lowers stall speed but adds mass. Re-run here before deciding."],
])

# =====================================================================================================
ws = sheet("Requirements", [34, 12, 12, 10, 50, 40, 60])
title(ws, "Requirements: what the aircraft must do, and why each limit")
header(ws, PARAM_COLS)
p(ws, "req_loiter", "Loiter time, with 20 % reserve left", "t_req", 80, "min", "typed", "[A] team rule (OWN_SMALL_DRONE §1)",
  "One dawn flight and one midday flight over the same plants need time to cover a hillside plot and hover for the spot sensor; 80 min kept even with a draggier airframe.", fmt="0")
p(ws, "req_tw", "Hover thrust / weight, 800 m altitude, ISA+20 (hot day)", "T/W", 1.5, "-", "typed", "[A] common VTOL control-margin rule; same rule as the 3.35 m design",
  "Below ~1.5 a quadplane cannot hold attitude in gusts while hovering at full mass. 800 m covers the hills around Stanford (Jasper Ridge < 300 m) with margin.", fmt="0.00")
p(ws, "req_stall", "Stall speed (clean wing, takeoff mass, sea level)", "V_s", 15.0, "m/s", "typed", "[A] team rule",
  "VTOL takes off and lands on rotors, so stall matters for transitions and slow turns, not landing. Lower stall = slower, safer transitions.", fmt="0.0")
p(ws, "req_payload", "Sensor payload (minimum mission kit)", "m_p", round(sum(pp_["mass"] * pp_["qty"] for pp_ in _PARTS if pp_["system"] == "payload" and pp_.get("tier") == "minimum") / 1000, 3), "kg", "Σ minimum sensors in data/parts.toml", "[A] masses from makers / estimates until weighed: computer, regulator, thermal camera, colour camera, 1610 nm spot sensor, air sensor",
  "Real units must be weighed.", fmt="0.000")
p(ws, "req_budget", "Budget for the aircraft", "$", 3000, "USD", "typed", "team budget (30 Oct): $3k cap, stretch $4–5k", "Stock parts only, real store prices.", fmt="$#,##0")
p(ws, "req_alt", "Design altitude for the hot-day case", "h", 800, "m", "typed", "[A]", "", fmt="0")
p(ws, "req_dT", "Hot-day temperature above ISA", "ΔT", 20, "K", "typed", "[A] ISA+20 = 30 °C at sea level", "", fmt="0")
section(ws, "Mission: how far and how long we fly, and why (prediction / observation flights)")
header(ws, PARAM_COLS)
p(ws, "req_radius", "Operating radius from the take-off point", "R", 1000, "m", "typed", "[A] FAA Part 107 §107.31: the pilot or a visual observer must see the aircraft; our field plan flies within ~1 km (docs/BASE_STATION.md D3)",
  "The legal limit is sight, not distance; ~1 km is what we can reliably see a 2.2 m aircraft. Flying farther needs a BVLOS waiver.", fmt="#,##0")
p(ws, "req_site", "Site surveyed per flight", "A", 2, "ha", "typed", "[A] docs/BASE_STATION.md §2.1: a 5-acre plot of chaparral plus a 50 m buffer", "", fmt="0")
p(ws, "req_survey", "Time over the site per flight", "t_s", 15, "min", "typed", "[A] BASE_STATION.md: 18 lines x 240 m ≈ 7 min at 19 m/s, plus passes and hovering for the spot sensor", "", fmt="0")
p(ws, "req_flights", "Flights per field day on one battery", "n", 3, "-", "typed", "[A] BASE_STATION.md: pre-dawn, mid-morning, midday (the water-loss curve needs at least dawn and midday)", "No field charging planned.", fmt="0")
p(ws, "req_why", "Why endurance matters more than range", "", "", "", "", "",
  "Range on one charge is tens of km (Mission_Energy), far beyond the ~1 km we may fly. So the motors and battery are sized by hover thrust and by time on site for the day's flights, not by distance.")
section(ws, "Also required (yes/no rules)")
text_rows(ws, [
    ["Own design, stock parts only", "", "", "", "We design and print the airframe; every bought part is a stock item with a real store price.", "user 10-30", ""],
    ["Fits the club printer", "", "", "", "Prusa CORE One bed 250 x 220 x 270 mm; all 82 printed files fit (CAD check).", "[C] CAD BOM §7", ""],
    ["Legal to fly in the US", "", "", "", "FAA Part 107 + an FAA-accepted Remote ID broadcast module (Ruko R111S, RID000001939).", "[V] FAA DOC list 10-31", ""],
    ["Carries the sensors looking down", "", "", "", "Space checked in CAD (payload_fit.py: no overlaps); belly windows still to draw.", "[C]", ""],
])

# =====================================================================================================
ws = sheet("Constants", [34, 10, 14, 12, 58, 40, 40])
title(ws, "Constants and atmosphere")
header(ws, PARAM_COLS)
p(ws, "g", "Gravity", "g", 9.80665, "m/s²", "typed", "standard", "", fmt="0.00000")
p(ws, "Rair", "Gas constant of air", "R", 287.05, "J/(kg K)", "typed", "standard", "", fmt="0.00")
p(ws, "T0", "Sea-level ISA temperature", "T0", 288.15, "K", "typed", "ISA", "", fmt="0.00")
p(ws, "p0", "Sea-level ISA pressure", "p0", 101325, "Pa", "typed", "ISA", "", fmt="0")
p(ws, "lapse", "Temperature lapse rate", "L", 0.0065, "K/m", "typed", "ISA", "", fmt="0.0000")
section(ws, "Case A: sea level, ISA (15 °C)")
header(ws, PARAM_COLS)
p(ws, "h_sl", "Altitude", "h", 0, "m", "typed", "", "", fmt="0")
p(ws, "dT_sl", "ISA deviation", "ΔT", 0, "K", "typed", "", "", fmt="0")
p(ws, "T_sl", "Temperature", "T", "={T0}-{lapse}*{h_sl}+{dT_sl}", "K", "T = T0 - L h + ΔT", "[C]", "", fmt="0.00")
p(ws, "rho_sl", "Air density", "ρ", "={p0}*(1-2.25577E-5*{h_sl})^5.25588/({Rair}*{T_sl})", "kg/m³", "ρ = p0 (1 - 2.25577e-5 h)^5.25588 / (R T)", "[C] ISA pressure law", "", fmt="0.0000")
p(ws, "mu_sl", "Dynamic viscosity", "μ", "=1.458E-6*{T_sl}^1.5/({T_sl}+110.4)", "Pa s", "Sutherland: μ = 1.458e-6 T^1.5 / (T + 110.4)", "[C]", "", fmt="0.000E+00")
p(ws, "a_sl", "Speed of sound", "a", "=SQRT(1.4*{Rair}*{T_sl})", "m/s", "a = √(γ R T)", "[C]", "", fmt="0.0")
section(ws, "Case B: 800 m, ISA+20 (hot day, the hover-margin case)")
header(ws, PARAM_COLS)
p(ws, "h_hot", "Altitude", "h", "={req_alt}", "m", "= Requirements", "", "", fmt="0")
p(ws, "dT_hot", "ISA deviation", "ΔT", "={req_dT}", "K", "= Requirements", "", "", fmt="0")
p(ws, "T_hot", "Temperature", "T", "={T0}-{lapse}*{h_hot}+{dT_hot}", "K", "T = T0 - L h + ΔT", "[C]", "", fmt="0.00")
p(ws, "rho_hot", "Air density", "ρ", "={p0}*(1-2.25577E-5*{h_hot})^5.25588/({Rair}*{T_hot})", "kg/m³", "same law", "[C]", "", fmt="0.0000")
p(ws, "mu_hot", "Dynamic viscosity", "μ", "=1.458E-6*{T_hot}^1.5/({T_hot}+110.4)", "Pa s", "Sutherland", "[C]", "", fmt="0.000E+00")
p(ws, "a_hot", "Speed of sound", "a", "=SQRT(1.4*{Rair}*{T_hot})", "m/s", "a = √(γ R T)", "[C]", "", fmt="0.0")

# =====================================================================================================
# Mass_CG from the CAD
mr = json.loads((HERE / "mass_rows.json").read_text())
rows = mr["rows"]


def base(n):
    n = re.sub(r"#\d+$", "", n)
    for _ in range(3):
        n2 = re.sub(r"(_(L|R|in|out))$|(_\d+(_-?1)?)$", "", n)
        if n2 == n: break
        n = n2
    return n


TAGS = [("motor_MN5008", "[S] CAD uses 150 g; store page lists 135 g [V]: conservative"),
        ("prop_P18", "[A] 31 g per blade (store mass unclear per blade or prop)"),
        ("esc_alpha40", "[S] 54.5 g with cables (uav-en.tmotor.com)"), ("esc_pusher", "[S] 54.5 g"),
        ("motor_pusher_AT3520", "[V] 218 g incl. cable (store.tmotor.com 11-17); CAD 221 g"),
        ("prop_pusher", "[A] APC 12x6E ~28 g"), ("battery", "[C] = Battery_Options chosen pack"),
        ("servo_regulator", "[A] 20 g, model not chosen"), ("pixhawk", "[A] Cube Orange on its carrier, 75 g estimate: weigh ours"),
        ("remote_id", "[S] 13.5 g listing"), ("gnss", "[A] 32 g"), ("telemetry", "[A]"), ("rc_receiver", "[A]"),
        ("power_module", "[A]"), ("airspeed", "[A]"), ("servo_", "[A] 23 g; KST X10 mass not read"),
        ("tube_", "[C] CF density 1.6 g/cm³ x tube volume"), ("rod_", "[C] CF density x volume"),
        ("wiring", "[A] mini_wiring lengths"), ("hardware", "[A]"), ("epoxy", "[A]")]


def tag_for(name, kind):
    for k, t in TAGS:
        if name.startswith(k): return t
    if kind in ("print", "cnc"): return "[C] CAD volume x material density x fill"
    return "[A]"


agg = OrderedDict()
for r in rows:
    b = base(r["name"])
    a = agg.setdefault(b, dict(group=r["group"], kind=r["kind"], material=r["material"], n=0, m=0.0, mx=0.0, my=0.0, mz=0.0))
    a["n"] += 1; a["m"] += r["mass_g"]; a["mx"] += r["mass_g"]*r["cg"][0]; a["my"] += r["mass_g"]*r["cg"][1]; a["mz"] += r["mass_g"]*r["cg"][2]
order = ["battery", "motor", "prop", "avionics", "wing", "boom", "tube", "fuselage", "tail", "lump", "misc"]
items = sorted(agg.items(), key=lambda kv: (order.index(kv[1]["group"]) if kv[1]["group"] in order else 99, -kv[1]["m"]))

ws = sheet("Mass_CG", [34, 11, 9, 11, 6, 10, 11, 9, 9, 9, 14, 44])
title(ws, "Mass and centre of gravity (CAD, all 161 parts, grouped)",
      "x forward-negative / aft-positive from the wing reference, mm. CG target x = 94 mm (15 % static margin, mini_layout.py). Battery mass links to Battery_Options.")
header(ws, ["Item", "Group", "Kind", "Material", "Qty", "g each", "g total", "x mm", "y mm", "z mm", "x · m (g mm)", "Source [tag]"])
r0 = ws._r
for name, a in items:
    r = ws._r
    each = a["m"]/a["n"]
    put(ws, r, 1, name); put(ws, r, 2, a["group"]); put(ws, r, 3, a["kind"]); put(ws, r, 4, a["material"] or "")
    put(ws, r, 5, a["n"], fill=INP, fmt="0")
    if name.startswith("battery"):
        put(ws, r, 6, "={bat_pack_g}", fill=CALC, fmt="0.0")
    else:
        put(ws, r, 6, round(each, 2), fill=INP, fmt="0.0")
    put(ws, r, 7, f"=E{r}*F{r}", fill=CALC, fmt="0.0")
    put(ws, r, 8, round(a["mx"]/a["m"], 1), fill=INP, fmt="0.0"); put(ws, r, 9, round(a["my"]/a["m"], 1), fill=INP, fmt="0.0")
    put(ws, r, 10, round(a["mz"]/a["m"], 1), fill=INP, fmt="0.0")
    put(ws, r, 11, f"=G{r}*H{r}", fill=CALC, fmt="#,##0")
    put(ws, r, 12, tag_for(name, a["kind"]))
    ws._r += 1
r1 = ws._r - 1
section(ws, "Payload (not in the CAD mass). Include = 1 / 0")
header(ws, ["Item", "Group", "Kind", "Include (1/0)", "Qty", "g each", "g total", "x mm", "y mm", "z mm", "x · m (g mm)", "Source [tag]"])
PAY = [p for p in _PARTS if p["system"] == "payload"]   # mission sensors, from data/parts.toml
p0r = ws._r
for pp_ in PAY:
    r = ws._r
    inc = 1 if pp_.get("tier", "minimum") == "minimum" else 0
    put(ws, r, 1, pp_["name"]); put(ws, r, 2, "payload"); put(ws, r, 3, pp_["status"]); put(ws, r, 4, inc, fill=INP, fmt="0")
    put(ws, r, 5, pp_["qty"], fill=INP, fmt="0"); put(ws, r, 6, pp_["mass"], fill=INP, fmt="0.0"); put(ws, r, 7, f"=D{r}*E{r}*F{r}", fill=CALC, fmt="0.0")
    c_ = pp_["box"]["c"]
    put(ws, r, 8, c_[0], fill=INP, fmt="0.0"); put(ws, r, 9, c_[1], fill=INP, fmt="0.0"); put(ws, r, 10, c_[2], fill=INP, fmt="0.0")
    put(ws, r, 11, f"=G{r}*H{r}", fill=CALC, fmt="#,##0"); put(ws, r, 12, "data/parts.toml; mass [A] until weighed")
    ws._r += 1
p1r = ws._r - 1
section(ws, "Totals")
header(ws, PARAM_COLS)
p(ws, "m_cad_g", "Aircraft mass from the CAD (no payload)", "m_e", f"=SUM(G{r0}:G{r1})", "g", "Σ g total (parts list above)", "[C]", "CAD assembly says 8,478 g with the 6S6P pack", fmt="#,##0")
p(ws, "m_pay_g", "Payload included", "m_p", f"=SUM(G{p0r}:G{p1r})", "g", "Σ payload rows with Include = 1", "[C]", "", fmt="#,##0")
_added = [p_ for p_ in _PARTS if p_["system"] in ("power", "lift", "cruise", "control", "surfaces", "airframe") and not p_["nodes"] and not p_.get("box")]
p(ws, "m_add_g", "Parts added on the website, not in the CAD yet", "m_a", round(sum(p_["mass"] * p_["qty"] for p_ in _added), 1), "g",
  "Σ mass × qty: " + (", ".join(p_["name"] for p_ in _added) or "none"), "[A]", "add them to the CAD to place them", fmt="#,##0")
p(ws, "m_to_g", "Takeoff mass", "m", "={m_cad_g}+{m_pay_g}+{m_add_g}", "g", "m = m_e + m_p + m_a", "[C]", "", fmt="#,##0", key_result=True)
p(ws, "m_to", "Takeoff mass", "m", "={m_to_g}/1000", "kg", "", "[C]", "", fmt="0.000", key_result=True)
p(ws, "m_nobat_g", "Takeoff mass without the battery", "m - m_bat", "={m_to_g}-{bat_pack_g}", "g", "used by Battery_Options", "[C]", "", fmt="#,##0")
p(ws, "cg_x", "CG x", "x_cg", f"=(SUM(K{r0}:K{r1})+SUM(K{p0r}:K{p1r}))/{{m_to_g}}", "mm", "x_cg = Σ(m x) / Σ m", "[C]", "target 94 mm; move the battery to trim", fmt="0.0", key_result=True)
p(ws, "cg_target", "CG target", "", 94, "mm", "typed", "[C] mini_layout.py, 15 % static margin", "", fmt="0.0")
p(ws, "bat_shift", "Battery shift to put the CG on target", "Δx_bat", "=({cg_target}-{cg_x})*{m_to_g}/{bat_pack_g}", "mm", "Δx = (x_target - x_cg) m / m_bat", "[C]", "+ = move aft. The tray has room for about ±30 mm [A].", fmt="0.0")

# =====================================================================================================
pol = json.loads((HERE / "sd7037_polar.json").read_text())
ws = sheet("Airfoil_SD7037", [10, 10, 11, 11, 10, 12, 4, 10, 10, 11, 11, 10, 12])
title(ws, "Wing airfoil SD7037 (9.2 % thick): polar from NeuralFoil (large model), Mach 0.05",
      "Re 230,000 ≈ MAC at stall speed; Re 300,000 ≈ MAC at loiter. Confidence = NeuralFoil's own analysis confidence (0-1).")
ws.cell(row=ws._r, column=1, value="Re = 230,000").font = SEC; ws.cell(row=ws._r, column=8, value="Re = 300,000").font = SEC; ws._r += 1
hdr = ["α deg", "cl", "cd", "cm", "cl/cd", "confidence"]
for i, h in enumerate(hdr):
    for off in (1, 8):
        c = ws.cell(row=ws._r, column=off + i, value=h); c.fill = HDR; c.font = HFONT; c.border = BOX
ws._r += 1
a0 = ws._r
for k, rr in enumerate(pol["polars"]["230000"]):
    r = ws._r
    for off, key in ((1, "230000"), (8, "300000")):
        row = pol["polars"][key][k]
        put(ws, r, off, row[0], fill=INP, fmt="0.0"); put(ws, r, off + 1, round(row[1], 4), fill=INP, fmt="0.000")
        put(ws, r, off + 2, round(row[2], 5), fill=INP, fmt="0.00000"); put(ws, r, off + 3, round(row[3], 4), fill=INP, fmt="0.000")
        L = get_column_letter(off + 1); D = get_column_letter(off + 2)
        put(ws, r, off + 4, f"={L}{r}/{D}{r}", fill=CALC, fmt="0.0"); put(ws, r, off + 5, round(row[4], 2), fill=INP, fmt="0.00")
    ws._r += 1
a1 = ws._r - 1
section(ws, "Summary")
header(ws, PARAM_COLS)
p(ws, "tc", "Thickness / chord", "t/c", round(pol["tc"], 4), "-", "AeroSandbox Airfoil('sd7037').max_thickness()", "[C]", "", fmt="0.000")
p(ws, "clmax230", "Section cl_max at Re 230k", "cl_max", f"=MAX(B{a0}:B{a1})", "-", "max of the cl column", "[C] NeuralFoil", "at α ≈ 13°", fmt="0.000")
p(ws, "clmax300", "Section cl_max at Re 300k", "cl_max", f"=MAX(I{a0}:I{a1})", "-", "", "[C] NeuralFoil", "", fmt="0.000")
p(ws, "ldmax300", "Section (L/D)max at Re 300k", "(cl/cd)max", f"=MAX(L{a0}:L{a1})", "-", "", "[C]", "section only; the aircraft's L/D is far lower (drag buildup)", fmt="0.0")
p(ws, "cdmin300", "Section cd_min at Re 300k", "cd_min", f"=MIN(J{a0}:J{a1})", "-", "", "[C]", "NeuralFoil assumes a smooth surface with free transition; printed skins are rougher", fmt="0.00000")

# =====================================================================================================
ws = sheet("Drag_Buildup", [30, 5, 9, 9, 10, 9, 11, 9, 8, 6, 8, 9, 10, 10, 9, 46])
title(ws, "Parasite drag buildup, part by part (Raymer, Aircraft Design 6th ed., ch. 12 component method)",
      "Friction parts: CDA = Cf · FF · Q · S_wet, Cf = 0.455 / ((log10 Re)^2.58 (1 + 0.144 M²)^0.65) (fully turbulent). Bluff parts: CDA = Cd · A_front. CD0 = Σ CDA / S_ref.")
header(ws, PARAM_COLS)
p(ws, "Vref", "Reference airspeed for Reynolds numbers", "V_ref", 19.0, "m/s", "typed (≈ loiter speed, Aero_Cruise)", "[A]",
  "Re changes Cf only weakly (±10 % speed ≈ ∓2 % drag); kept typed to avoid a circular reference. Check against Aero_Cruise V_loiter.", fmt="0.0")
p(ws, "Mref", "Mach number", "M", "={Vref}/{a_sl}", "-", "M = V / a", "[C]", "", fmt="0.000")
p(ws, "fuse_L", "Fuselage length", "L_f", 0.94, "m", "CAD FUSE_X0 -380 to FUSE_X1 560 mm", "[C] cad/design.py", "", fmt="0.000")
p(ws, "fuse_W", "Fuselage width", "W_f", 0.170, "m", "CAD FUSE_W", "[C]", "", fmt="0.000")
p(ws, "fuse_H", "Fuselage height", "H_f", 0.165, "m", "CAD FUSE_H", "[C]", "", fmt="0.000")
p(ws, "fuse_Swet", "Fuselage wetted area", "S_wet,f", 0.45, "m²", "CAD: half of the 4 shell meshes = 0.437 m² (trimesh); station integration of f_fuse.py = 0.464 m²", "[C] CAD, 2 methods", "fixed 11-17 after review (was a formula giving 0.38)", fmt="0.000")
p(ws, "boom_len", "Boom tube length", "L_b", 1.358, "m", "CAD BOOM_FRONT_X -390 to BOOM_REAR_X 968 mm", "[C]", "", fmt="0.000")
p(ws, "boom_D", "Boom tube diameter", "D_b", 0.030, "m", "CAD BOOM_TUBE 30/28", "[C]", "", fmt="0.000")
p(ws, "tail_c", "Arch tail chord", "c_tail", 0.12, "m", "mini_layout pick 0.12 x 0.36", "[C]", "", fmt="0.000")
p(ws, "tail_h", "Arch tail apex height", "h_t", 0.36, "m", "", "[C]", "", fmt="0.000")
p(ws, "boom_y", "Boom lateral position", "y_b", 0.39, "m", "CAD BOOM_Y", "[C]", "", fmt="0.000")
p(ws, "tail_len", "Arch tail length (two straight halves, boom end to apex)", "L_t", "=2*SQRT({boom_y}^2+{tail_h}^2)", "m", "L = 2 √(y_b² + h_t²)", "[C]", "", fmt="0.000")
p(ws, "nac_L", "Nacelle (ESC fairing) length", "", 0.220, "m", "f_boom.py NAC len", "[C]", "", fmt="0.000")
p(ws, "nac_W", "Nacelle width", "", 0.064, "m", "NAC w", "[C]", "", fmt="0.000")
p(ws, "nac_H", "Nacelle height", "", 0.095, "m", "NAC z -85 to 10", "[C]", "", fmt="0.000")
p(ws, "leg_c", "Leg fairing chord (NACA 0025)", "", 0.048, "m", "f_boom.py LEG chord (mini)", "[C]", "", fmt="0.000")
p(ws, "leg_h", "Leg fairing height", "", 0.148, "m", "LEG z -67 to -215", "[C]", "", fmt="0.000")
p(ws, "foot_D", "Foot diameter (TPU)", "", 0.036, "m", "FOOT r 18", "[C]", "", fmt="0.000")
p(ws, "foot_H", "Foot height", "", 0.045, "m", "FOOT z -260 to -215", "[C]", "", fmt="0.000")
p(ws, "mot_D", "Lift motor diameter", "", 0.0556, "m", "CAD LIFT_MOTOR d (MN5008)", "[C]", "", fmt="0.0000")
p(ws, "mot_H", "Lift motor height", "", 0.031, "m", "CAD LIFT_MOTOR h", "[C]", "", fmt="0.000")
p(ws, "Cd_bluff", "Cd of short bluff cylinders (motors, feet)", "Cd", 0.8, "-", "typed", "[A] Hoerner: short cylinder in cross-flow, L/D ≈ 0.5-1.3 → 0.6-0.9",
  "The biggest single assumption on this tab. A wind-tunnel or flight value would replace it.", fmt="0.00")
p(ws, "CDA_rotor", "Drag area of one stopped 18 in 2-blade prop", "CDA_r", "=0.0019*(18/28)^2", "m²", "0.0019 m² for a 28 in prop (Scout model) x (18/28)²", "[A] analysis/scout_perf.py CDA_ROTOR, scaled by area", "Not measured. Plausible range 0.0003 (blades lined up with the flow) to 0.003 m² (crosswise). The props stop at random angles unless PX4 parks them.", fmt="0.000000")
p(ws, "misc_frac", "Extra for gaps, hinges, antennas, GNSS pads, rough print", "", 0.10, "-", "typed", "[A] Raymer: 5-10 % (leakage + protuberance)", "", fmt="0%")
section(ws, "Components")
header(ws, ["Component", "n", "L_ref m", "S_wet each m²", "t/c or fineness", "Re", "Cf", "FF", "Q", "Cd", "A_front m²", "CDA each m²", "CDA total m²", "ΔCD0", "% of CD0", "How / source"])
comp_rows = []


def comp(name, n, L, Swet, tcf, ff_formula, Q, cd=None, af=None, how=""):
    r = ws._r
    put(ws, r, 1, name); put(ws, r, 2, n, fill=INP, fmt="0")
    if cd is None:
        put(ws, r, 3, L, fill=CALC if str(L).startswith("=") else INP, fmt="0.000")
        put(ws, r, 4, Swet, fill=CALC, fmt="0.0000"); put(ws, r, 5, tcf, fill=CALC if str(tcf).startswith("=") else INP, fmt="0.000")
        put(ws, r, 6, f"={{rho_sl}}*{{Vref}}*C{r}/{{mu_sl}}", fill=CALC, fmt="#,##0")
        put(ws, r, 7, f"=0.455/(LOG10(F{r})^2.58*(1+0.144*{{Mref}}^2)^0.65)", fill=CALC, fmt="0.00000")
        put(ws, r, 8, ff_formula.replace("TC", f"E{r}"), fill=CALC, fmt="0.000"); put(ws, r, 9, Q, fill=INP, fmt="0.00")
        put(ws, r, 10, "", ); put(ws, r, 11, "")
        put(ws, r, 12, f"=G{r}*H{r}*I{r}*D{r}", fill=CALC, fmt="0.000000")
    else:
        for c_ in (3, 4, 5, 6, 7, 8, 9): put(ws, r, c_, "")
        put(ws, r, 10, cd, fill=CALC if str(cd).startswith("=") else INP, fmt="0.00"); put(ws, r, 11, af, fill=CALC, fmt="0.000000")
        put(ws, r, 12, f"=J{r}*K{r}" if not str(cd).startswith("CDA") else cd, fill=CALC, fmt="0.000000")
    put(ws, r, 13, f"=B{r}*L{r}", fill=CALC, fmt="0.000000")
    put(ws, r, 14, f"=M{r}/{{S}}", fill=CALC, fmt="0.0000")
    put(ws, r, 16, how)
    comp_rows.append(r); ws._r += 1
    return r


FF_WING = "=(1+0.6/0.3*TC+100*TC^4)*MAX(1,1.34*{Mref}^0.18)"
FF_BODY = "=1+60/TC^3+TC/400"
FF_NAC = "=1+0.35/TC"
comp("Wing (exposed)", 1, "={MAC}", "=({S}-{c_root}*{fuse_W})*(1.977+0.52*{tc})", "={tc}", FF_WING, 1.0,
     how="S_wet = (S - c_root W_f)(1.977 + 0.52 t/c); FF = [1 + 0.6/(x/c)_m t/c + 100 (t/c)^4] · max(1, 1.34 M^0.18), (x/c)_m = 0.3 [A]; Raymer's Mach factor goes to 0 at low speed, so it is held at 1 (fixed 11-17 after review); Q = 1")
comp("Arch tail (both halves)", 1, "={tail_c}", "={tail_c}*{tail_len}*(1.977+0.52*0.10)", 0.10, FF_WING, 1.08,
     how="NACA 0010; S_wet = c_t L_t (1.977 + 0.52 t/c); Q = 1.08 (Raymer, tail surfaces)")
comp("Fuselage", 1, "={fuse_L}", "={fuse_Swet}",
     "={fuse_L}/SQRT({fuse_W}*{fuse_H})", FF_BODY, 1.0,
     how="S_wet from the CAD (see input above; the Torenbeek formula gives 0.38 m², too low for this boxy shape); fineness f = L / √(W H); FF = 1 + 60/f³ + f/400 (Raymer)")
comp("Boom tubes (outside the nacelles)", 2, "={boom_len}-2*{nac_L}", "=PI()*{boom_D}*({boom_len}-2*{nac_L})", "=({boom_len}-2*{nac_L})/{boom_D}", FF_BODY, 1.1,
     how="booms hang under the wing (z -20 mm), so only the 2 nacelle lengths per boom are covered; Q = 1.1 [A]; saddle junction drag is in the 10 % extra (fixed 11-17)")
comp("Nacelles (ESC fairings)", 4, "={nac_L}", "=PI()*SQRT({nac_W}*{nac_H})*{nac_L}", "={nac_L}/SQRT({nac_W}*{nac_H})", FF_NAC, 1.3,
     how="FF = 1 + 0.35/f (Raymer, nacelles); Q = 1.3 (nacelle on a boom/wing, Raymer upper value) [S]")
comp("Leg fairings (NACA 0025)", 4, "={leg_c}", "={leg_c}*{leg_h}*(1.977+0.52*0.25)", 0.25, FF_WING, 1.0,
     how="strut treated as a wing section, t/c 0.25")
comp("Lift motors (exposed cylinders)", 4, None, None, None, None, None, cd="={Cd_bluff}", af="={mot_D}*{mot_H}",
     how="A_front = d h; Cd [A]")
comp("Feet (TPU, bluff)", 4, None, None, None, None, None, cd="={Cd_bluff}", af="={foot_D}*{foot_H}", how="A_front = d h; Cd [A]")
r = ws._r
put(ws, r, 1, "Stopped lift props"); put(ws, r, 2, 4, fill=INP, fmt="0")
for c_ in range(3, 12): put(ws, r, c_, "")
put(ws, r, 12, "={CDA_rotor}", fill=CALC, fmt="0.000000"); put(ws, r, 13, f"=B{r}*L{r}", fill=CALC, fmt="0.000000")
put(ws, r, 14, f"=M{r}/{{S}}", fill=CALC, fmt="0.0000"); put(ws, r, 16, "CDA per prop [A], see above"); comp_rows.append(r); ws._r += 1
rS = ws._r
put(ws, rS, 1, "Sum of parts", bold=True); put(ws, rS, 13, f"=SUM(M{comp_rows[0]}:M{comp_rows[-1]})", fill=CALC, fmt="0.000000")
ws._r += 1
rM = ws._r
put(ws, rM, 1, "Gaps, hinges, antennas, roughness"); put(ws, rM, 13, f"={{misc_frac}}*M{rS}", fill=CALC, fmt="0.000000")
put(ws, rM, 14, f"=M{rM}/{{S}}", fill=CALC, fmt="0.0000"); comp_rows.append(rM); ws._r += 1
for rr in comp_rows:
    put(ws, rr, 15, f"=N{rr}/{{CD0_build}}", fill=CALC, fmt="0%")
section(ws, "Result")
header(ws, PARAM_COLS)
p(ws, "CD0_rev_lo", "Independent review: CD0 low", "", 0.040, "-", "own component estimate, same geometry", "[C from A] independent reviewer 11-17", "", fmt="0.000")
p(ws, "CD0_rev_mid", "Independent review: CD0 likely", "", 0.060, "-", "", "[C from A]", "motors + feet + props ≈ 45 % of it", fmt="0.000")
p(ws, "CD0_rev_hi", "Independent review: CD0 high", "", 0.090, "-", "", "[C from A]", "", fmt="0.000")
p(ws, "CDA_tot", "Total drag area", "CDA", f"=M{rS}+M{rM}", "m²", "Σ parts + extra", "[C]", "", fmt="0.00000")
p(ws, "CD0_build", "Zero-lift drag coefficient from the buildup", "CD0", "={CDA_tot}/{S}", "-", "CD0 = CDA / S_ref", "[C]",
  "Earlier sizing assumed 0.025 (base) to 0.035 (draggy); AVL used CDp 0.0313.", fmt="0.0000", key_result=True)
p(ws, "CD0_clean", "Same, without motors, feet and stopped props", "", f"=({{CDA_tot}}-(M{comp_rows[6]}+M{comp_rows[7]}+M{comp_rows[8]})*(1+{{misc_frac}}))/{{S}}", "-",
  "shows how much the VTOL hardware costs in cruise", "[C]", "", fmt="0.0000")

# =====================================================================================================
ws = sheet("Aero_Cruise", [36, 12, 13, 13, 56, 34, 44])
title(ws, "Wing geometry and cruise aerodynamics (steady level flight)")
header(ws, PARAM_COLS)
p(ws, "S", "Wing area", "S", 0.50, "m²", "chosen in the size sweep (Battery_Options / mini_sizing.py)", "[C] cad/design.py WING_AREA_M2", "", fmt="0.000")
p(ws, "b", "Span", "b", 2.24, "m", "CAD SPAN", "[C]", "", fmt="0.000")
p(ws, "c_root", "Root chord", "c_r", 0.2706, "m", "CAD ROOT_CHORD", "[C]", "", fmt="0.0000")
p(ws, "c_tip", "Tip chord", "c_tip", 0.1759, "m", "CAD TIP_CHORD (taper 0.65)", "[C]", "", fmt="0.0000")
p(ws, "AR", "Aspect ratio", "AR", "={b}^2/{S}", "-", "AR = b² / S", "[C]", "", fmt="0.00")
p(ws, "taper", "Taper ratio", "λ", "={c_tip}/{c_root}", "-", "λ = c_tip / c_root", "[C]", "", fmt="0.000")
p(ws, "MAC", "Mean aerodynamic chord", "MAC", "=2/3*{c_root}*(1+{taper}+{taper}^2)/(1+{taper})", "m", "MAC = 2/3 c_root (1 + λ + λ²)/(1 + λ)", "[C]",
  "mini_layout.py gives 0.2266 m", fmt="0.0000")
p(ws, "e_raymer", "Oswald factor, Raymer straight-wing estimate", "e", "=1.78*(1-0.045*{AR}^0.68)-0.64", "-", "e = 1.78 (1 - 0.045 AR^0.68) - 0.64", "[S] Raymer eq. 12.48", "", fmt="0.000")
p(ws, "e_used", "Oswald factor used", "e", "={e_raymer}", "-", "= Raymer estimate above", "[C]", "mini_sizing.py used 0.80 [A]", fmt="0.000")
p(ws, "K", "Induced drag factor", "K", "=1/(PI()*{AR}*{e_used})", "-", "K = 1 / (π AR e)", "[C]", "", fmt="0.0000")
p(ws, "CLmax", "Wing CLmax (clean)", "CL_max", "=0.9*{clmax230}", "-", "CL_max ≈ 0.9 cl_max (Raymer, unswept wing)", "[C] Airfoil_SD7037", "mini_sizing.py assumed 1.3 [A]; flaps are not counted", fmt="0.000")
p(ws, "CD0", "CD0 used", "CD0", "={CD0_build}", "-", "= result of Drag_Buildup", "[C]", "", fmt="0.0000", key_result=True)
p(ws, "eta_push", "Pusher efficiency (electrical → thrust power)", "η_p", 0.55, "-", "typed", "[A] motor ~0.80 x prop ~0.70 at cruise", "Not measured. See Pusher tab.", fmt="0.00")
p(ws, "P_avionics", "Flight avionics power", "", 15, "W", "typed", "[A] flight controller, GPS, radios, servos at rest", "", fmt="0")
p(ws, "P_payload", "Mission sensor power", "", sum(pp_.get("power_w", 0) for pp_ in _PARTS if pp_["system"] == "payload" and pp_.get("tier") == "minimum"), "W", "Σ power_w of the minimum sensors in data/parts.toml", "[A] makers' typical figures", "", fmt="0.0")
p(ws, "P_av", "Avionics + sensor power", "P_av", "={P_avionics}+{P_payload}", "W", "P_av = P avionics + P sensors", "[C]", "", fmt="0.0")
section(ws, "Loiter speed = max(minimum-power speed, 1.3 x stall). Here CL_mp > CL_max, so loiter is always set by 1.3 x stall.")
header(ws, ["Quantity", "Symbol", "Sea level ISA", "800 m ISA+20", "Equation", "Source [tag]", "Note"])


def two(key, label, sym, f_sl, f_hot, unit, eq, src="[C]", note="", fmt="0.000", key_result=False):
    r = ws._r
    put(ws, r, 1, label + (f" ({unit})" if unit else "")); put(ws, r, 2, readable(sym))
    put(ws, r, 3, f_sl, fill=KEY if key_result else CALC, fmt=fmt, bold=key_result)
    put(ws, r, 4, f_hot, fill=KEY if key_result else CALC, fmt=fmt, bold=key_result)
    put(ws, r, 5, readable(lit(eq))); put(ws, r, 6, clean(lit(src))); put(ws, r, 7, readable(clean(lit(note))))
    assert key + "_sl" not in REF and key + "_hot" not in REF, key
    REF[key + "_sl"] = f"{q(ws)}!$C${r}"; REF[key + "_hot"] = f"{q(ws)}!$D${r}"
    ws._r += 1


two("rhoA", "Air density", "ρ", "={rho_sl}", "={rho_hot}", "kg/m³", "Constants", fmt="0.0000")
two("W", "Weight", "W", "={m_to}*{g}", "={m_to}*{g}", "N", "W = m g (Mass_CG)", fmt="0.00")
two("WS", "Wing loading", "W/S", "={W_sl}/{S}", "={W_hot}/{S}", "N/m²", "", fmt="0.0")
two("Vs", "Stall speed", "V_s", "=SQRT(2*{W_sl}/({rho_sl}*{S}*{CLmax}))", "=SQRT(2*{W_hot}/({rho_hot}*{S}*{CLmax}))", "m/s", "V_s = √(2W / (ρ S CL_max))", fmt="0.00", key_result=True)
two("CLmp", "CL for minimum power", "CL_mp", "=SQRT(3*{CD0}/{K})", "=SQRT(3*{CD0}/{K})", "", "CL_mp = √(3 CD0 / K)", fmt="0.000")
two("Vmp", "Minimum-power speed", "V_mp", "=SQRT(2*{W_sl}/({rho_sl}*{S}*{CLmp_sl}))", "=SQRT(2*{W_hot}/({rho_hot}*{S}*{CLmp_hot}))", "m/s", "V = √(2W / (ρ S CL))", fmt="0.00")
two("V", "Loiter speed used", "V", "=MAX({Vmp_sl},1.3*{Vs_sl})", "=MAX({Vmp_hot},1.3*{Vs_hot})", "m/s", "V = max(V_mp, 1.3 V_s)", note="1.3 V_s keeps a stall margin in turns and gusts", fmt="0.00", key_result=True)
two("qd", "Dynamic pressure", "q", "=0.5*{rho_sl}*{V_sl}^2", "=0.5*{rho_hot}*{V_hot}^2", "Pa", "q = ½ ρ V²", fmt="0.0")
two("CL", "Lift coefficient", "CL", "={W_sl}/({qd_sl}*{S})", "={W_hot}/({qd_hot}*{S})", "", "CL = W / (q S)", fmt="0.000")
two("CD", "Drag coefficient", "CD", "={CD0}+{K}*{CL_sl}^2", "={CD0}+{K}*{CL_hot}^2", "", "CD = CD0 + K CL²", fmt="0.0000")
two("LD", "Lift / drag", "L/D", "={CL_sl}/{CD_sl}", "={CL_hot}/{CD_hot}", "", "", fmt="0.0", key_result=True)
two("D", "Drag = thrust needed", "D", "={qd_sl}*{S}*{CD_sl}", "={qd_hot}*{S}*{CD_hot}", "N", "D = q S CD", fmt="0.00", key_result=True)
two("Psh", "Thrust power", "P_T", "={D_sl}*{V_sl}", "={D_hot}*{V_hot}", "W", "P_T = D V", fmt="0.0")
two("Pcr", "Electrical power in loiter", "P_cr", "={Psh_sl}/{eta_push}+{P_av}", "={Psh_hot}/{eta_push}+{P_av}", "W", "P = P_T / η_p + P_av", fmt="0.0", key_result=True)
two("Re", "Reynolds number at the MAC", "Re", "={rho_sl}*{V_sl}*{MAC}/{mu_sl}", "={rho_hot}*{V_hot}*{MAC}/{mu_hot}", "", "Re = ρ V MAC / μ", note="Drag_Buildup uses V_ref; keep V_ref ≈ V here", fmt="#,##0")

# =====================================================================================================
ws = sheet("Lift_Hover", [36, 12, 13, 13, 56, 38, 40])
title(ws, "Hover: lift motor T-Motor MN5008 KV340 + P18x6.1 (4 motors)")
for txt, url in ((f"Buy the motor: {part_store('motor_lift')}, ${part_price('motor_lift'):.2f}", part_url("motor_lift")),
                 ("Maker's test table (thrust and power)", "https://store.tmotor.com/product/mn5008-kv340-motor-antigravity-type.html"),
                 ("This motor on the website's 3D drone", SITE + "index.html#motor_lift")):
    c = ws.cell(row=ws._r, column=1, value=txt); c.hyperlink = url; c.font = Font(color="1155CC", underline="single"); ws._r += 1
section(ws, "Maker's test table [V] store.tmotor.com, read 2026-10-30 (about 22.5 V)")
header(ws, ["Thrust g", "Power W", "ln T", "ln P", "", "", ""])
MN = [(996, 88), (1238, 120), (1541, 162), (1822, 208), (2120, 258), (2394, 311), (2675, 369), (2966, 432), (3262, 503), (3909, 667), (4215, 754)]
t0 = ws._r
for T, P in MN:
    r = ws._r
    put(ws, r, 1, T, fill=INP, fmt="0"); put(ws, r, 2, P, fill=INP, fmt="0")
    put(ws, r, 3, f"=LN(A{r})", fill=CALC, fmt="0.0000"); put(ws, r, 4, f"=LN(B{r})", fill=CALC, fmt="0.0000"); ws._r += 1
t1 = ws._r - 1
section(ws, "Inputs and fit")
header(ws, PARAM_COLS)
p(ws, "fit_k", "Power-law exponent (P = e^c T^k)", "k", f"=SLOPE(D{t0}:D{t1},C{t0}:C{t1})", "-", "least squares on ln P vs ln T", "[C]", "", fmt="0.0000")
p(ws, "fit_c", "Power-law constant", "c", f"=INTERCEPT(D{t0}:D{t1},C{t0}:C{t1})", "-", "", "[C]", "", fmt="0.0000")
p(ws, "Tmax_test", "Max thrust per motor in the test (100 %)", "T_max", 4215, "g", "last row of the table", "[V]", "", fmt="0")
p(ws, "V_test", "Test voltage at 100 %", "V_test", 22.51, "V", "", "[V]", "", fmt="0.00")
p(ws, "V_load", "Our pack voltage under hover load", "V_load", "=6*3.6", "V", "6 cells x 3.6 V", "[A] Li-ion mid-discharge under load", "", fmt="0.00")
p(ws, "rho_test", "Air density during the maker's test", "ρ_test", 1.20, "kg/m³", "typed", "[A] not stated on the page", "", fmt="0.00")
p(ws, "I_esc", "ESC continuous rating (ALPHA 40A 6S)", "I_ESC", 40, "A", "", "[V] product name / page", "", fmt="0")
p(ws, "I_full", "Motor current at 100 % (table)", "I_100", f"=B{t1}/{{V_test}}", "A", "P / V", "[C]", "must stay under the ESC rating", fmt="0.0")
section(ws, "Hover results")
header(ws, ["Quantity", "Symbol", "Sea level ISA", "800 m ISA+20", "Equation", "Source [tag]", "Note"])
two("Thov", "Thrust per motor needed", "T", "={m_to_g}/4", "={m_to_g}/4", "g", "T = m / 4")
two("Pmot", "Electrical power per motor", "P_m", "=EXP({fit_c}+{fit_k}*LN({Thov_sl}))*SQRT({rho_test}/{rho_sl})", "=EXP({fit_c}+{fit_k}*LN({Thov_hot}))*SQRT({rho_test}/{rho_hot})", "W",
    "P = e^c T^k √(ρ_test / ρ)", note="momentum theory: same thrust needs √(ρ0/ρ) more power in thin air", fmt="0.0")
two("Phov", "Hover power, all motors + avionics", "P_hov", "=4*{Pmot_sl}+{P_av}", "=4*{Pmot_hot}+{P_av}", "W", "P = 4 P_m + P_av", fmt="0", key_result=True)
two("Imot", "Current per motor", "I_m", "={Pmot_sl}/{V_load}", "={Pmot_hot}/{V_load}", "A", "I = P / V", fmt="0.0")
two("Ipack", "Pack current", "I", "={Phov_sl}/{V_load}", "={Phov_hot}/{V_load}", "A", "", fmt="0.0")
two("Icell", "Current per cell", "I_cell", "={Ipack_sl}/{bat_P}", "={Ipack_hot}/{bat_P}", "A", "I / P (parallel cells)", note="P50B rated 60 A [S]", fmt="0.0")
two("Tmax", "Max thrust per motor at our voltage and density", "T_max", "={Tmax_test}/1000*{g}*({V_load}/{V_test})^2*{rho_sl}/{rho_test}", "={Tmax_test}/1000*{g}*({V_load}/{V_test})^2*{rho_hot}/{rho_test}", "N",
    "T ∝ V² (rpm ∝ V) and ∝ ρ", src="[C] / [A] scaling", fmt="0.00")
two("TW", "Thrust / weight", "T/W", "=4*{Tmax_sl}/{W_sl}", "=4*{Tmax_hot}/{W_hot}", "", "T/W = 4 T_max / W", note="rule: ≥ 1.5 in the hot case", fmt="0.00", key_result=True)
r = ws._r
put(ws, r, 1, "Hot-day rule met?"); put(ws, r, 4, '=IF({TW_hot}>={req_tw},"YES","NO")', fill=KEY, bold=True); put(ws, r, 5, "T/W (800 m ISA+20) ≥ Requirements"); ws._r += 1
two("throttle", "Hover throttle (thrust share of max)", "T/T_max", "={Thov_sl}/1000*{g}/{Tmax_sl}", "={Thov_hot}/1000*{g}/{Tmax_hot}", "", "", fmt="0%")

# =====================================================================================================
ws = sheet("Pusher", [36, 12, 13, 13, 56, 38, 44])
title(ws, "Cruise thrust: pusher T-Motor AT3520 KV550")
for txt, url in ((f"Buy the motor: {part_store('motor_pusher')}, ${part_price('motor_pusher'):.2f}", part_url("motor_pusher")),
                 ("Maker's spec and test table", "https://store.tmotor.com/product/at3520-long-shaft-fixed-wing-motor.html"),
                 ("This motor on the website's 3D drone", SITE + "index.html#motor_pusher")):
    c = ws.cell(row=ws._r, column=1, value=txt); c.hyperlink = url; c.font = Font(color="1155CC", underline="single"); ws._r += 1
section(ws, "Maker's test table [V] store.tmotor.com, AT3520 Long Shaft KV550 + APC 13x6.5, read 2026-11-17")
header(ws, ["Throttle", "Voltage V", "Current A", "Power W", "rpm", "Thrust g", "g/W"])
AT = [(0.40, 22.49, 4.96, 111.61, 4834, 912, 8.18), (0.45, 22.47, 6.00, 134.81, 5181, 1053, 7.81), (0.50, 22.45, 7.26, 163.08, 5558, 1208, 7.41),
      (0.55, 22.43, 8.88, 199.17, 5990, 1396, 7.01), (0.60, 22.39, 10.87, 243.44, 6404, 1619, 6.65), (0.65, 22.35, 13.47, 300.90, 6895, 1890, 6.28),
      (0.70, 22.30, 16.12, 359.46, 7313, 2140, 5.95), (0.75, 22.25, 19.27, 428.67, 7732, 2412, 5.63), (0.80, 22.19, 22.60, 501.48, 8119, 2711, 5.41),
      (0.90, 22.06, 30.77, 678.62, 8940, 3289, 4.85), (1.00, 21.99, 34.89, 767.14, 9252, 3575, 4.66)]
a0r = ws._r
for row in AT:
    for i, v in enumerate(row, 1):
        put(ws, ws._r, i, v, fill=INP, fmt=("0%" if i == 1 else "0.00" if i in (2, 3) else "0"))
    ws._r += 1
a1r = ws._r - 1
section(ws, "Static numbers and an in-flight estimate")
header(ws, PARAM_COLS)
p(ws, "T0_push", "Static thrust at 100 % (13x6.5)", "T_0", f"=F{a1r}/1000*{{g}}", "N", "table, g → N", "[V]", "", fmt="0.00")
p(ws, "I_push", "Current at 100 %", "I", f"=C{a1r}", "A", "table", "[V]", "under the 40 A ALPHA ESC → the 13x6.5 is allowed (the buy-list note said it might exceed 40 A [A]; the maker's table says 34.9 A)", fmt="0.0")
p(ws, "n_push", "Prop speed at 100 %", "n", f"=E{a1r}/60", "rev/s", "rpm / 60", "[V]", "", fmt="0.0")
p(ws, "D_push", "Prop diameter of the test data (13 in)", "D", "=13*0.0254", "m", "", "[V]", "our CAD/BOM prop is 12 in (305 mm): 13 in would leave ~15 mm ground clearance", fmt="0.000")
p(ws, "J0", "Advance ratio where thrust reaches zero", "J_0", 0.66, "-", "typed", "[A] APC thin-electric props, pitch/diameter ≈ 0.5: zero thrust at J ≈ 0.62-0.70 (independent review, from UIUC/APC data; APC file blocked HTTP 403)", "", fmt="0.00")
p(ws, "V0_push", "Airspeed where thrust reaches zero at 100 % (static rpm)", "V_0", "={J0}*{n_push}*{D_push}", "m/s", "V_0 = J_0 n D", "[C]", "", fmt="0.0")
section(ws, "Thrust needed vs available")
header(ws, ["Quantity", "Symbol", "Sea level ISA", "800 m ISA+20", "Equation", "Source [tag]", "Note"])
two("Tav", "Max thrust at loiter speed (estimate)", "T(V)", "={T0_push}*(1-({V_sl}/{V0_push})^1.5)*{rho_sl}/{rho_test}", "={T0_push}*(1-({V_hot}/{V0_push})^1.5)*{rho_hot}/{rho_test}", "N",
    "T(V) ≈ T_0 (1 - (J/J_0)^1.5) ρ/ρ_test, J = V/(nD): zero at J_0, ≈ 0.54 T_0 at J 0.4", src="[A] fits CT/CT0 ≈ 0.5-0.6 at J 0.4 (review); rpm rise ignored (conservative); measure", fmt="0.00")
two("Tratio", "Thrust needed / available", "D / T(V)", "={D_sl}/{Tav_sl}", "={D_hot}/{Tav_hot}", "", "", note="< 1 means level loiter is possible", fmt="0%", key_result=True)
two("ROC", "Best winged climb rate at loiter speed (100 % pusher)", "RC", "=({Tav_sl}-{D_sl})*{V_sl}/{W_sl}", "=({Tav_hot}-{D_hot})*{V_hot}/{W_hot}", "m/s", "RC = (T - D) V / W", fmt="0.00", key_result=True)
r = ws._r
put(ws, r, 1, "What it means"); put(ws, r, 5, "Data is for the maker's 13x6.5 test prop (the only data found). The CAD and BOM use a 12x6E: a 13 in prop leaves only ~15 mm to the ground, so we keep 12 in "
    "unless the legs get longer; a 12 in gives somewhat less thrust (no data). Level loiter is within reach; a winged climb is limited to ~1.5-2 m/s, so Mission_Energy plans 1.5 m/s. Bench-test the 12x6E (current + thrust) before the first transition.")
ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7); ws.row_dimensions[r].height = 60; ws._r += 1

# =====================================================================================================
ws = sheet("Mission_Energy", [40, 12, 13, 13, 56, 36, 40])
title(ws, "Mission energy and loiter time (chosen battery)")
header(ws, PARAM_COLS)
p(ws, "bat_S", "Cells in series", "s", 6, "-", "6S: our motors and ESCs are 6S parts", "[V] parts", "", fmt="0")
p(ws, "bat_P", "Cells in parallel (chosen)", "P", "={chosen_P}", "-", "= Battery_Options chosen row", "[C]", "", fmt="0")
p(ws, "cell_Wh", "Energy per cell", "E_cell", "={chosen_Wh}", "Wh", "= Battery_Options", "", "", fmt="0.00")
p(ws, "E_tot", "Pack energy (nominal)", "E", "={bat_S}*{bat_P}*{cell_Wh}", "Wh", "E = s P E_cell", "[C]", "", fmt="0", key_result=True)
p(ws, "soc", "Usable charge window", "", "=0.95-0.10", "-", "use 95 % → 10 % state of charge", "[A] protects the cells", "", fmt="0.00")
p(ws, "reserve", "Landing reserve kept", "", 0.20, "-", "typed", "[A] same as the 3.35 m design", "", fmt="0%")
p(ws, "E_use", "Energy for the mission", "E_u", "={E_tot}*{soc}*(1-{reserve})", "Wh", "E_u = E · window · (1 - reserve)", "[C]", "", fmt="0")
p(ws, "t_hov", "Hover time per flight (takeoff + landing, incl. transitions)", "t_h", "=2*(45+15)", "s", "2 x (45 s hover + 15 s transition)", "[A] mini_sizing.py", "", fmt="0")
p(ws, "h_climb", "Winged climb height", "Δh", 120, "m", "typed", "[A] to 120 m (Part 107 limit)", "", fmt="0")
p(ws, "roc_plan", "Planned winged climb rate", "RC", 1.5, "m/s", "typed", "[A] Pusher tab: best winged climb ≈ 1.5-2 m/s", "was 3 m/s in mini_sizing.py (not reachable with this pusher)", fmt="0.0")
header(ws, ["Quantity", "Symbol", "Sea level ISA", "800 m ISA+20", "Equation", "Source [tag]", "Note"])
two("Evtol", "Hover energy", "E_h", "={Phov_sl}*{t_hov}/3600", "={Phov_hot}*{t_hov}/3600", "Wh", "E = P_hov t_h", fmt="0.0")
two("Eclimb", "Climb energy", "E_c", "=({Pcr_sl}+{W_sl}*{roc_plan}/{eta_push})*({h_climb}/{roc_plan})/3600", "=({Pcr_hot}+{W_hot}*{roc_plan}/{eta_push})*({h_climb}/{roc_plan})/3600", "Wh",
    "E = (P_cr + W RC / η_p) (Δh / RC)", fmt="0.0")
two("tloit", "Loiter time with reserve left", "t", "=({E_use}-{Evtol_sl}-{Eclimb_sl})/{Pcr_sl}*60", "=({E_use}-{Evtol_hot}-{Eclimb_hot})/{Pcr_hot}*60", "min", "t = (E_u - E_h - E_c) / P_cr", fmt="0", key_result=True)
r = ws._r
put(ws, r, 1, "Loiter rule met?"); put(ws, r, 3, '=IF({tloit_sl}>={req_loiter},"YES","NO")', fill=KEY, bold=True); put(ws, r, 4, '=IF({tloit_hot}>={req_loiter},"YES","NO")', fill=KEY, bold=True)
put(ws, r, 5, "t ≥ Requirements loiter time"); ws._r += 1
section(ws, "One field day: flights per battery, and range")
header(ws, PARAM_COLS)
p(ws, "t_transit", "Transit out and back per flight", "t_tr", "=2*{req_radius}/{V_sl}", "s", "t = 2 R / V", "[C]", "", fmt="0")
p(ws, "E_flight", "Energy per flight (sea level)", "E_f", "={Evtol_sl}+{Eclimb_sl}+{Pcr_sl}*({req_survey}*60+{t_transit})/3600", "Wh", "E = E_hover + E_climb + P_cr (t_s + t_tr)", "[C]", "", fmt="0")
p(ws, "flights_pack", "Flights per battery, reserve kept", "n", "={E_use}/{E_flight}", "-", "n = E_u / E_f", "[C]", "", fmt="0.0", key_result=True)
r = ws._r
put(ws, r, 1, "Field-day rule met?"); put(ws, r, 3, '=IF({flights_pack}>={req_flights},"YES","NO")', fill=KEY, bold=True); put(ws, r, 5, "n ≥ flights per day (Requirements)"); ws._r += 1
p(ws, "range_km", "Still-air range on one charge, reserve kept", "range", "={V_sl}*{tloit_sl}*60/1000", "km", "range ≈ V t_loiter", "[C]", "Not a design driver: we fly within the operating radius.", fmt="0")
p(ws, "endur_min", "Endurance (loiter time, reserve kept)", "t", "={tloit_sl}", "min", "= loiter time above", "[C]", "", fmt="0")
section(ws, "Levers to close the gap: same mass, speed and battery; each row changes one thing (website: Requirements)")
header(ws, PARAM_COLS)
p(ws, "fair_frac", "Share of the motor, foot and stopped-prop drag removed by printed fairings", "", 0.5, "-", "typed",
  "[A] not measured; fairings (teardrop feet, motor cowls, props parked fore-aft) typically halve a bluff body's drag", "", fmt="0%")


def lever(key, label, cd0, survey="{req_survey}"):
    p(ws, f"Pcr_{key}", f"{label}: loiter power", "", f"=0.5*{{rho_sl}}*{{V_sl}}^3*{{S}}*({cd0}+{{K}}*{{CL_sl}}^2)/{{eta_push}}+{{P_av}}", "W",
      "P = ½ ρ V³ S (CD0 + K CL²) / η_p + P_av", "[C]", "", fmt="0")
    p(ws, f"Eclimb_{key}", f"{label}: climb energy", "", f"=({{Pcr_{key}}}+{{W_sl}}*{{roc_plan}}/{{eta_push}})*({{h_climb}}/{{roc_plan}})/3600", "Wh", "as Eclimb", "[C]", "", fmt="0.0")
    p(ws, f"tloit_{key}", f"{label}: loiter time", "", f"=({{E_use}}-{{Evtol_sl}}-{{Eclimb_{key}}})/{{Pcr_{key}}}*60", "min", "as tloit", "[C]", "", fmt="0", key_result=True)
    p(ws, f"flights_{key}", f"{label}: flights per charge", "", f"={{E_use}}/({{Evtol_sl}}+{{Eclimb_{key}}}+{{Pcr_{key}}}*({survey}*60+{{t_transit}})/3600)", "-",
      "as flights_pack", "[C]", "", fmt="0.00", key_result=True)


lever("fair", "Fairings", "{CD0}-{fair_frac}*({CD0_build}-{CD0_clean})")
lever("clean", "Upper bound: no motor, foot or prop drag", "{CD0_clean}")
lever("s12", "Survey 12 min instead of 15", "{CD0}", "12")
lever("fair12", "Fairings and a 12 min survey", "{CD0}-{fair_frac}*({CD0_build}-{CD0_clean})", "12")
section(ws, "Sensitivity: loiter time (sea level) vs CD0 and Oswald e, same mass and battery")
header(ws, ["CD0", "e", "V m/s", "P_cr W", "Loiter min", "Note", ""])
for cd0, e, note in ((0.025, 0.80, "first sizing, low drag"), (0.035, 0.80, "first sizing, high drag"), (0.025, "={e_raymer}", ""), (0.035, "={e_raymer}", ""),
                     (0.045, "={e_raymer}", ""), ("={CD0_clean}", "={e_raymer}", "SENSCLEAN buildup without motors/feet/props (what fairings could win)"),
                     ("={CD0_build}", "={e_raymer}", "buildup, as designed")):
    r = ws._r
    put(ws, r, 1, cd0, fill=INP if not str(cd0).startswith("=") else CALC, fmt="0.0000"); put(ws, r, 2, e, fill=INP if not str(e).startswith("=") else CALC, fmt="0.000")
    Kx = f"(1/(PI()*{{AR}}*B{r}))"
    put(ws, r, 3, f"=MAX(SQRT(2*{{W_sl}}/({{rho_sl}}*{{S}}*SQRT(3*A{r}/{Kx}))),1.3*{{Vs_sl}})", fill=CALC, fmt="0.00")
    cl = f"({{W_sl}}/(0.5*{{rho_sl}}*C{r}^2*{{S}}))"
    put(ws, r, 4, f"=0.5*{{rho_sl}}*C{r}^3*{{S}}*(A{r}+{Kx}*{cl}^2)/{{eta_push}}+{{P_av}}", fill=CALC, fmt="0.0")
    put(ws, r, 5, f"=({{E_use}}-{{Evtol_sl}}-(D{r}+{{W_sl}}*{{roc_plan}}/{{eta_push}})*({{h_climb}}/{{roc_plan}})/3600)/D{r}*60", fill=KEY, fmt="0")
    if note.startswith("SENSCLEAN"):
        note = note.replace("SENSCLEAN ", ""); REF["t_clean"] = f"{q(ws)}!$E${r}"
    put(ws, r, 6, note); ws._r += 1

# =====================================================================================================
ws = sheet("Battery_Options", [24, 6, 7, 7, 7, 8, 8, 9, 8, 9, 8, 8, 8, 9, 8, 8, 8, 9, 9, 40])
title(ws, "Battery choice: same equations as Aero_Cruise / Lift_Hover / Mission_Energy, one row per pack",
      "Pack mass = cells x cell mass x 1.08 (strip, BMS, wrap [A]); pack $ = loose cells + $50 to build it. The chosen row is the ready-made pack: its mass and price come from data/parts.toml. Mass of everything else = Mass_CG takeoff mass without the battery. CG shift not recomputed per row.")
header(ws, ["Option", "P", "Ah/cell", "Wh/cell", "g/cell", "A rating", "$/cell", "Pack g", "Pack Wh", "Mass kg", "V_s m/s", "V m/s", "P_cr W", "P_hov W (SL)",
            "Loiter min (SL)", "T/W hot", "A/cell hot hover", "Pack $", "Passes all?", "Source / note"])
OPTS = [("Molicel P50B 6S4P", 4, 5.0, 70, 60, 8.99, "[V] liionwholesale.com 10-31 ($8.99 a loose cell); 70 g [S]; 60 A [S]"),
        ("Molicel P50B 6S5P", 5, 5.0, 70, 60, 8.99, "same cell"),
        ("Molicel P50B 6S6P (chosen)", 6, 5.0, 70, 60, 8.99, "same cell; chosen 11-02. Bought ready-made (11-19): pack $ and pack g come from the battery row of data/parts.toml"),
        ("Molicel P50B 6S7P", 7, 5.0, 70, 60, 8.99, "same cell"),
        ("Samsung 50S 6S6P", 6, 5.0, 70, 25, 6.99, "[V] imrbatteries $6.99 10-31; 25 A rated, ~20 A continuous per Mooch [S]; voltage sag vs P50B NOT FOUND → bench test"),
        ("Samsung 50E 6S6P", 6, 4.9, 69, 9.8, 6.99, "[S] 9.8 A rating: too low for hover (rejected)")]
b0 = ws._r
chosen_row = None
for name, P, ah, g_, amp, usd, src in OPTS:
    r = ws._r
    put(ws, r, 1, name); put(ws, r, 2, P, fill=INP, fmt="0"); put(ws, r, 3, ah, fill=INP, fmt="0.0")
    put(ws, r, 4, f"=C{r}*3.6", fill=CALC, fmt="0.0"); put(ws, r, 5, g_, fill=INP, fmt="0"); put(ws, r, 6, amp, fill=INP, fmt="0.0"); put(ws, r, 7, usd, fill=INP, fmt="$0.00")
    if "chosen" in name: put(ws, r, 8, part_mass("battery"), fill=INP, fmt="#,##0")   # ready-made pack mass, data/parts.toml
    else: put(ws, r, 8, f"=6*B{r}*E{r}*1.08", fill=CALC, fmt="#,##0")
    put(ws, r, 9, f"=6*B{r}*D{r}", fill=CALC, fmt="0")
    put(ws, r, 10, f"=({{m_nobat_g}}+H{r})/1000", fill=CALC, fmt="0.000")
    W = f"(J{r}*{{g}})"
    put(ws, r, 11, f"=SQRT(2*{W}/({{rho_sl}}*{{S}}*{{CLmax}}))", fill=CALC, fmt="0.00")
    put(ws, r, 12, f"=MAX(SQRT(2*{W}/({{rho_sl}}*{{S}}*SQRT(3*{{CD0}}/{{K}}))),1.3*K{r})", fill=CALC, fmt="0.00")
    cl = f"({W}/(0.5*{{rho_sl}}*L{r}^2*{{S}}))"
    put(ws, r, 13, f"=0.5*{{rho_sl}}*L{r}^3*{{S}}*({{CD0}}+{{K}}*{cl}^2)/{{eta_push}}+{{P_av}}", fill=CALC, fmt="0")
    put(ws, r, 14, f"=4*EXP({{fit_c}}+{{fit_k}}*LN(J{r}*1000/4))*SQRT({{rho_test}}/{{rho_sl}})+{{P_av}}", fill=CALC, fmt="0")
    put(ws, r, 15, f"=(I{r}*{{soc}}*(1-{{reserve}})-N{r}*{{t_hov}}/3600-(M{r}+{W}*{{roc_plan}}/{{eta_push}})*({{h_climb}}/{{roc_plan}})/3600)/M{r}*60", fill=KEY, fmt="0")
    put(ws, r, 16, f"=4*{{Tmax_test}}/1000*{{g}}*({{V_load}}/{{V_test}})^2*{{rho_hot}}/{{rho_test}}/{W}", fill=CALC, fmt="0.00")
    put(ws, r, 17, f"=(4*EXP({{fit_c}}+{{fit_k}}*LN(J{r}*1000/4))*SQRT({{rho_test}}/{{rho_hot}})+{{P_av}})/{{V_load}}/B{r}", fill=CALC, fmt="0.0")
    if "chosen" in name: put(ws, r, 18, part_price("battery"), fill=INP, fmt="$#,##0")   # ready-made pack price, data/parts.toml
    else: put(ws, r, 18, f"=6*B{r}*G{r}+50", fill=CALC, fmt="$#,##0")   # loose cells + about $50 BMS, strip, wrap [A]
    put(ws, r, 19, f'=IF(AND(O{r}>={{req_loiter}},P{r}>={{req_tw}},K{r}<={{req_stall}},Q{r}<=F{r}),"YES","NO")', fill=KEY, bold=True)
    put(ws, r, 20, src)
    bl = "https://liionwholesale.com/products/molicel-npe-inr-21700-p50b-60a-5000mah-flat-top-21700-battery-authorized-distributor" if "P50B" in name else "https://imrbatteries.com/"
    ws.cell(row=r, column=1).hyperlink = bl; ws.cell(row=r, column=1).font = Font(color="1155CC", underline="single")
    part_link(ws, r, 21, "p50b")
    if "chosen" in name: chosen_row = r
    ws._r += 1
section(ws, "Chosen pack (links into Mass_CG and Mission_Energy)")
header(ws, PARAM_COLS)
p(ws, "chosen_P", "Parallel count", "P", f"=B{chosen_row}", "-", "row marked (chosen)", "", "", fmt="0")
p(ws, "chosen_Wh", "Wh per cell", "", f"=D{chosen_row}", "Wh", "", "", "", fmt="0.00")
p(ws, "bat_pack_g", "Pack mass", "m_bat", f"=H{chosen_row}", "g", "", "[C]", "CAD battery block: 2,720 g", fmt="#,##0")
section(ws, "Why 21700 Li-ion and not LiPo")
text_rows(ws, [["Energy per mass", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
                "P50B: 5.0 Ah x 3.6 V / 70 g ≈ 257 Wh/kg cell level [C from S]. Typical 6S LiPo packs ≈ 150-190 Wh/kg [S]. Loiter time scales with Wh carried, and our hover current per cell (~10-13 A) is well inside a high-drain 21700's rating, so Li-ion wins for a long-endurance quadplane."]])

# =====================================================================================================
ws = sheet("Structure_Stability", [34, 22, 16, 16, 60, 40])
title(ws, "Structure and stability checks (results of our scripts; open the script to re-run)")
header(ws, ["Check", "Result", "Margin / value", "Pass rule", "Method", "Source [tag]"])
text_rows(ws, [
    ["Wing spar, root (21/19 CF tube)", "pass", 1.52, "≥ 1.4", "beam bending at 3.8 g limit x 1.5, both lift motors at full thrust, 9.04 kg", "[C] analysis/mini_spar.py → out/mini_spar.md"],
    ["Wing spar at the boom (17/15)", "pass", 2.13, "≥ 1.4", "same", "[C] same"],
    ["Wing spar, outer tube end (13/11)", "pass", 18.7, "≥ 1.4", "same", "[C] same"],
    ["Boom tube 30/28, jointed (HaoZhong 1 m x 2)", "pass", 1.97, "≥ 1.4 at 400 MPa; 1st bending ≥ 15 Hz", "design moment 129.6 N m (hard landing on 2 legs x 1.5); 1st bending 18 / 23 Hz (E 70 / 110 GPa)", "[C] analysis/mini_boom.py"],
    ["Boom joint (bonded sleeve 27/25)", "TO TEST", "", "bench test", "bonded-joint test before flight", "[A] doc §4f"],
    ["Aileron servo torque", "pass", 1.60, "≥ 1 (x2 already in the need)", "need 4.7 kg cm at 33.8 m/s dive; KST X10 7.5 kg cm", "[C] analysis/mini_servo.py, torque [S]"],
    ["Ruddervator servo torque", "pass", 2.27, "", "need 3.3 kg cm", "[C] same"],
    ["Static margin", "set", "15 %", "10-20 % typical", "CG placed for 15 % by the VLM (wing + tail only)", "[C] analysis/mini_layout.py"],
    ["Roll stability (Cl_β)", "pass with 10° tips", -0.031, "< 0", "flat wing +0.015 → 10° polyhedral tips at y 0.87 m", "[C] mini_polyhedral.py"],
    ["Short period (AVL, CAD masses)", "stable", "5.28 rad/s, ζ 0.63", "ζ > 0.35", "AVL 3.40 eigenmodes", "[C] analysis/mini_avl_cad.py"],
    ["Dutch roll", "stable", "4.67 rad/s, ζ 0.157", "ζ > 0.08", "same", "[C]"],
    ["Spiral", "slowly unstable", "doubles in 6.7 s (10.2 s with 10° tips)", "> 4 s doubling OK with autopilot", "same", "[C]"],
    ["Phugoid", "lightly damped", "7.9 s period, ζ 0.002", "autopilot holds speed", "same", "[C]"],
    ["Wiring voltage drop, hover", "pass", "1.0 %", "< 3 %", "14 AWG ESC feeds 1.0 m", "[C] analysis/mini_wiring.py"],
    ["Printer bed fit", "pass", "82/82 files", "fits 240 x 210 x 260", "CAD check", "[C] CAD BOM §7"],
    ["Interference in CAD", "pass", "0 pairs > 20 mm³", "0", "bought parts vs airframe", "[C] CAD BOM §7"],
    ["Printed-part mass", "TO TEST", "", "within 20 % of CAD", "weigh the first wing test pieces (CAD 31 / 29 g)", "[A]"],
])

# =====================================================================================================
ws = sheet("Electronics", [30, 26, 5, 16, 10, 12, 44, 10, 46, 46, 18])
title(ws, "Electronics: what each part does, reuse vs buy, and why this part")
header(ws, ["Part", "Job", "Qty", "Status", "Unit $", "Line $", "Buy", "Mass g (each)", "Why this one", "Alternatives considered", "On the website"])
EL = [
    ("CubePilot Cube Orange on its carrier (ours)", "flight controller (PX4 VTOL)", part_qty("pixhawk"), "OWN", part_price("pixhawk"), part_url("pixhawk"), part_mass("pixhawk"),
     "club already owns it (user 11-19); 3 IMUs, 2 heated + isolated; ADS-B in if on the ADS-B carrier; PX4 cubepilot_cubeorange. Mass 75 g [A]: weigh it", "Pixhawk 6C plastic + PM07 $242.99 [V Holybro 11-19]; Cube Orange+ Standard Set $451 [V IRLock 11-19]"),
    ("Holybro PM07 power module", "power to the ESCs + battery voltage/current", part_qty("pm07"), "BUY", part_price("pm07"), part_url("pm07"), part_mass("pm07"),
     "90 A continuous [V Holybro 11-19] vs hot hover current [C Lift_Hover]; check its power cable fits the Cube carrier", "the Cube's Power Brick Mini (too small for our current)"),
    ("Holybro M10 GPS", "position, heading", part_qty("gnss"), "BUY", part_price("gnss"), part_url("gnss"), part_mass("gnss"), "plugs into the flight controller GPS port (check the cable for the Cube carrier)", "M9N $54.99"),
    ("Holybro MS5525DSO airspeed + PT40", "airspeed for transitions and stall protection", part_qty("airspeed"), "BUY", part_price("airspeed"), part_url("airspeed"), part_mass("airspeed"), "PX4 I2C driver", "MS4525DO sold out"),
    ("Holybro SiK V3 915 MHz (pair)", "ground link", part_qty("telemetry"), "BUY", part_price("telemetry"), part_url("telemetry"), part_mass("telemetry"), "pair = drone + laptop radio", "1 W pair $175"),
    ("RadioMaster RP2 V2 ELRS receiver", "manual control", part_qty("rc_rx"), "BUY", part_price("rc_rx"), part_url("rc_rx"), part_mass("rc_rx"), "CRSF into PX4", ""),
    ("T-Motor MN5008 KV340", "lift motor", part_qty("motor_lift"), "BUY", part_price("motor_lift"), part_url("motor_lift"), part_mass("motor_lift"),
     "maker's thrust table [V] gives T/W 1.5+ at 800 m hot on 6S with P18 (Lift_Hover)", "SunnySky V4014 KV330: T/W 1.20 hot [C] → rejected"),
    ("T-Motor P18x6.1 prop pair", "lift props", part_qty("prop_lift"), "BUY", part_price("prop_lift"), part_url("prop_lift"), part_mass("prop_lift"), "matched to MN5008 in the maker's test", ""),
    ("T-Motor ALPHA 40A 6S ESC", "motor drive (4 lift + 1 pusher)", part_qty("esc_lift") + part_qty("esc_pusher"), "BUY", part_price("esc_lift"), part_url("esc_lift"), part_mass("esc_lift"),
     "FOC, 6S; 40 A > 33.5 A motor full-throttle current [C Lift_Hover]; US stock = no import duty", "UnmannedRC $69.99 + 37.5 % duty = $96.24 [C]"),
    ("T-Motor AT3520 KV550 long shaft", "pusher motor", part_qty("motor_pusher"), "BUY", part_price("motor_pusher"), part_url("motor_pusher"), part_mass("motor_pusher"),
     "maker recommends 6S + 13x6.5; table [V] 3.58 kg static at 34.9 A", "V4014 too slow (330 KV)"),
    ("APC 12x6E pusher prop", "pusher prop", part_qty("prop_pusher"), "BUY", part_price("prop_pusher"), part_url("prop_pusher"), part_mass("prop_pusher"), "fits the CAD (305 mm disc, ground clearance); price [A]", "13x6.5 (maker's test prop, 34.9 A < 40 A [V]) leaves ~15 mm ground clearance → only with longer legs"),
    ("KST X10 V2 wing servo", "ailerons + ruddervators", part_qty("servos"), "BUY", part_price("servos"), part_url("servos"), part_mass("servos"),
     "10 mm thin-wing servo; 7.5 kg cm vs 4.7 needed [C]", "KST DS145MG $34.99 (5.2 kg cm, ships from China) → Cost_Options"),
    ("Servo regulator 5-6 V ≥ 5 A", "servo power", part_qty("servo_reg"), "BUY", part_price("servo_reg"), part_url("servo_reg"), part_mass("servo_reg"),
     "ALPHA ESCs have no BEC [S]", "another ≥ 5 A regulator if out of stock"),
    ("Ruko R111S Remote ID", "FAA broadcast Remote ID", part_qty("remote_id"), "BUY", part_price("remote_id"), part_url("remote_id"), part_mass("remote_id"),
     "on the FAA accepted list (RID000001939) [V 10-31], cheapest found", "Dronetag Beacon $149"),
    ("Ready-made 6S6P Molicel P50B pack", "battery (Battery_Options)", part_qty("battery"), "BUY", part_price("battery"),
     part_url("battery"), part_mass("battery"),
     "best loiter per $ that passes every rule; ready-made so no first-time pack build", "build it from 36 loose cells ($324 + about $50 BMS/strip/wrap + spot welder)"),
]
e0 = ws._r
for row in EL:
    r = ws._r
    name, job, qty, st, usd, link, g_, why, alt = row
    put(ws, r, 1, name); put(ws, r, 2, job); put(ws, r, 3, qty, fill=INP, fmt="0"); put(ws, r, 4, st, fill=(KEY if st.startswith("REUSE") else None))
    put(ws, r, 5, usd, fill=INP, fmt="$#,##0.00"); put(ws, r, 6, f"=C{r}*E{r}", fill=CALC, fmt="$#,##0.00")
    c = put(ws, r, 7, link)
    if link: c.hyperlink = link; c.font = Font(color="1155CC", underline="single")
    put(ws, r, 8, g_, fill=INP, fmt="0.0"); put(ws, r, 9, why); put(ws, r, 10, alt); part_link(ws, r, 11, name); ws._r += 1
r = ws._r
put(ws, r, 1, "Electronics to buy", bold=True); put(ws, r, 6, f"=SUM(F{e0}:F{r-1})", fill=KEY, fmt="$#,##0.00", bold=True)
put(ws, r, 9, "Excludes wiring/connectors (BOM_Cost), shipping and duty."); ws._r += 1
section(ws, "Nothing is reused from Sky4 (user, 19 Nov: the Sky4 parts are not available); every part above is bought")

# =====================================================================================================
ws = sheet("Connectors_Wiring", [34, 26, 6, 26, 12, 12, 10, 9, 10, 40])
title(ws, "Connectors, wire and soldering: every joint, the current through it, and whether the connector is big enough",
      "Currents link to Lift_Hover and Pusher. Ratings are the makers' continuous ratings [S]; check the exact part page before buying.")
header(ws, ["Joint", "Connector / method", "Qty", "Wire", "Current A", "Rating A", "OK?", "Unit $", "Line $", "Source [tag] / note"])
CONN = [
    ("Battery pack → power module", "XT90H pair (pack side female)", 2, "2 x 14 AWG per pole", "={Ipack_hot}", 90, 1.49 * 2, "[V] XT90H $1.49 each; current = hot-day hover; full-throttle bursts ≈ 4 x 33.5 + 34.9 A for seconds"),
    ("Power module input", "replace the PM07's XT60 with an XT90H", 0, "", "={Ipack_hot}", 90, 0, "counted in the row above (mini_wiring.md)"),
    ("Power module → each lift ESC", "solder at the PM07 pads; XT60 pair at the wing root if the wing comes off", 4, "14 AWG, 1.0 m", "={Imot_hot}", 30, 1.80, "[A] XT60 ~$9 for 5 pairs; 30 A continuous / 60 A burst [S]; full throttle 33.5 A only for seconds"),
    ("Power module → pusher ESC", "solder", 1, "14 AWG, 0.4 m", "={I_push}", 60, 0, "[C] I_push = 100 % pusher current"),
    ("Lift ESC → motor (3 phases)", "3.5 mm gold bullets", 12, "motor leads", "={I_full}", 40, 0.66, "[V 10-30] $1.99 per 3-pack; store guide up to 40 A"),
    ("Pusher ESC → motor (3 phases)", "3.5 mm gold bullets", 3, "motor leads", "={I_push}", 40, 0.66, "same"),
    ("Servo regulator input", "XT30 pair", 1, "20 AWG", 5, 15, 1.40, "[A] XT30 ~$7 for 5 pairs; 15 A continuous [S]"),
    ("Servos and ESC signals → Pixhawk", "60 cm servo extensions (JR)", 16, "22 AWG", 2, 3, 1.59, "[S] RMRC $1.59"),
    ("Sensors → Pixhawk (GPS, airspeed, telemetry, receiver)", "JST-GH cables (come with the Holybro parts) + spare set", 1, "", "", "", 16.99, "[S] spare JST-GH set"),
    ("Battery balance lead (charging)", "JST-XH 7-pin (6S) balance lead", 1, "22 AWG", 1, 3, 3.00, "[A] for the charger and a cell checker"),
    ("Pack cells (36 x 21700)", "spot-welded nickel strip + BMS", 1, "", "", "", 0, "in the battery row of BOM_Cost; needs a spot welder (club or lab?) or a pack built by the seller"),
    ("Every soldered joint", "solder, flux, heat shrink, 80 W+ iron for 14 AWG", 1, "", "", "", 25.0, "[A] heat shrink $9.99 [V] + solder/flux; check club stock"),
]
w0 = ws._r
for row in CONN:
    r = ws._r
    joint, how, qty, wire, cur, rat, unit, src = row
    put(ws, r, 1, joint); put(ws, r, 2, how); put(ws, r, 3, qty, fill=INP, fmt="0"); put(ws, r, 4, wire)
    put(ws, r, 5, cur, fill=(CALC if str(cur).startswith("=") else INP), fmt="0.0"); put(ws, r, 6, rat, fill=INP, fmt="0")
    put(ws, r, 7, f'=IF(OR(E{r}="",F{r}=""),"",IF(E{r}<=F{r},"OK","TOO SMALL"))', fill=CALC)
    put(ws, r, 8, unit, fill=INP, fmt="$0.00"); put(ws, r, 9, f"=C{r}*H{r}", fill=CALC, fmt="$#,##0.00"); put(ws, r, 10, src)
    ws._r += 1
r = ws._r
put(ws, r, 1, "Connectors and soldering total", bold=True); put(ws, r, 9, f"=SUM(I{w0}:I{r-1})", fill=KEY, fmt="$#,##0.00", bold=True)
put(ws, r, 10, "Already in BOM_Cost: XT90H, bullets, extensions, heat shrink, JST-GH, solder. New there: XT60 pairs, XT30 pairs, balance lead."); ws._r += 1

ws = sheet("BOM_Cost", [40, 6, 10, 11, 16, 9, 9, 11, 46, 40, 18])
title(ws, "Bill of materials and cost (aircraft for first flights; sensors separate)",
      "Duty applies to China-origin goods (HTS 2026 Rev 22, read 10-30: normal + Section 301 25 % + 12.5 %). Tariffs change: 25 % on drone parts from 2027-02-09 [S].")
header(ws, ["Item", "Qty", "Unit $", "Line $", "Store", "China? 1/0", "Duty rate", "Duty $", "Buy", "Source [tag] / note", "On the website"])
# Every aircraft part with a price, straight from data/parts.toml (add or remove a part there or on the website).
FLY = ("power", "lift", "cruise", "control", "surfaces", "airframe", "materials")
BOM = []
for pp_ in sorted((p_ for p_ in _PARTS if p_["system"] in FLY and p_["price"] > 0), key=lambda p_: FLY.index(p_["system"])):
    qty = 0 if pp_.get("order") == "have it" else pp_["qty"]
    BOM.append((pp_["name"], qty, pp_["price"], part_store(pp_["id"]), pp_["china"], pp_["duty"], part_url(pp_["id"]),
                pp_["source"] + ("; already ours (order: have it)" if pp_.get("order") == "have it" else ""), pp_["id"]))
BUY = []   # everything to buy, for the website's buy list (data/buy_list.json)
c0 = ws._r
for name, qty, usd, store, china, rate, link, src, pid_ in BOM:
    r = ws._r
    put(ws, r, 1, name); put(ws, r, 2, qty, fill=(CALC if str(qty).startswith("=") else INP), fmt="0"); put(ws, r, 3, usd, fill=INP, fmt="$#,##0.00")
    put(ws, r, 4, f"=B{r}*C{r}", fill=CALC, fmt="$#,##0.00"); put(ws, r, 5, store); put(ws, r, 6, china, fill=INP, fmt="0"); put(ws, r, 7, rate, fill=INP, fmt="0.0%")
    put(ws, r, 8, f"=D{r}*F{r}*G{r}", fill=CALC, fmt="$#,##0.00")
    c = put(ws, r, 9, link)
    if link: c.hyperlink = link; c.font = Font(color="1155CC", underline="single")
    put(ws, r, 10, src); part_link(ws, r, 11, name); ws._r += 1
    qn = part_qty("battery") if str(qty).startswith("=") else qty
    BUY.append(dict(group="Aircraft", name=name, qty=qn, unit=usd, line=qn * usd, duty=round(qn * usd * china * rate, 2), store=store, link=link, note=src, id=pid_))
c1 = ws._r - 1
section(ws, "Shipping and fees")
s0 = ws._r
for name, usd, src in (("UnmannedRC express", 29.80, "[V 10-30]"), ("HaoZhong expedited", 45.00, "[V 10-30] ($30 standard)"), ("Liion Wholesale UPS Ground", 11.03, "[V 10-31]"), ("Holybro (flight electronics, from China)", 30.00, "[A] shipping not read; check at checkout"),
                       ("Other US stores (about 6 orders)", 45.00, "[A]"), ("Customs clearance fees (2 China parcels)", 40.00, "[A] $20-60")):
    r = ws._r
    put(ws, r, 1, name); put(ws, r, 2, 1, fill=INP, fmt="0"); put(ws, r, 3, usd, fill=INP, fmt="$#,##0.00"); put(ws, r, 4, f"=B{r}*C{r}", fill=CALC, fmt="$#,##0.00")
    put(ws, r, 10, src); ws._r += 1
    BUY.append(dict(group="Shipping and fees", name=name, qty=1, unit=usd, line=usd, duty=0, store="", link="", note=src))
s1 = ws._r - 1
section(ws, "Totals")
header(ws, PARAM_COLS)
p(ws, "cost_parts", "Parts", "", f"=SUM(D{c0}:D{c1})", "USD", "Σ lines", "[C]", "", fmt="$#,##0")
p(ws, "cost_duty", "Import duty", "", f"=SUM(H{c0}:H{c1})", "USD", "Σ duty", "[C]", "", fmt="$#,##0")
p(ws, "cost_ship", "Shipping and fees", "", f"=SUM(D{s0}:D{s1})", "USD", "", "[C]", "", fmt="$#,##0")
p(ws, "cost_total", "Aircraft total", "", "={cost_parts}+{cost_duty}+{cost_ship}", "USD", "", "[C]", "", fmt="$#,##0", key_result=True)
p(ws, "cost_left", "Left of the budget", "", "={req_budget}-{cost_total}", "USD", "", "[C]", "", fmt="$#,##0", key_result=True)
section(ws, "Not included yet (decide or confirm)")
text_rows(ws, [["Spot welder for the 21700 pack (or a lab's)", "", "", "", "", "", "", "", "", "borrow first (Stanford PRL / a lab); price not checked"],
               ["Ground station laptop", "", "", "", "", "", "", "", "", "a team member's laptop with QGroundControl (free)"],
               ])
section(ws, "Ground equipment (from data/parts.toml, system ground)")
header(ws, ["Item", "Qty", "Unit $", "Line $", "Store", "", "", "", "Buy", "Why it is needed", "On the website"])
g0 = ws._r
for gp_ in [p_ for p_ in _PARTS if p_["system"] == "ground"]:
    r = ws._r
    put(ws, r, 1, gp_["name"]); put(ws, r, 2, buy_qty(gp_), fill=INP, fmt="0"); put(ws, r, 3, gp_["price"], fill=INP, fmt="$#,##0.00")
    put(ws, r, 4, f"=B{r}*C{r}", fill=CALC, fmt="$#,##0.00"); put(ws, r, 5, gp_["buy"][0][0] if gp_["buy"] else "")
    c = put(ws, r, 9, gp_["buy"][0][1] if gp_["buy"] else "")
    if gp_["buy"]: c.hyperlink = gp_["buy"][0][1]; c.font = Font(color="1155CC", underline="single")
    put(ws, r, 10, gp_["job"]); part_link(ws, r, 11, gp_["name"]); ws._r += 1
    BUY.append(dict(group="Ground equipment", name=gp_["name"], qty=buy_qty(gp_), unit=gp_["price"], line=buy_qty(gp_) * gp_["price"], duty=0, store=gp_["buy"][0][0] if gp_["buy"] else "", link=gp_["buy"][0][1] if gp_["buy"] else "", note=gp_["source"], id=gp_["id"]))
g1 = ws._r - 1
header(ws, PARAM_COLS)
p(ws, "cost_ground", "Ground equipment", "", f"=SUM(D{g0}:D{g1})", "USD", "Σ lines", "[C]", "US stores; shipping in the row above", fmt="$#,##0", key_result=True)
section(ws, "Mission sensors (minimum kit, from data/parts.toml; not in the aircraft total above)")
header(ws, ["Item", "Qty", "Unit $", "Line $", "Status", "", "", "", "Buy", "Why it is needed", "On the website"])
m0 = ws._r
for pp_ in PAY:
    if pp_.get("tier") != "minimum": continue
    r = ws._r
    put(ws, r, 1, pp_["name"]); put(ws, r, 2, buy_qty(pp_), fill=INP, fmt="0"); put(ws, r, 3, pp_["price"], fill=INP, fmt="$#,##0.00")
    put(ws, r, 4, f"=B{r}*C{r}", fill=CALC, fmt="$#,##0.00"); put(ws, r, 5, pp_["status"])
    c = put(ws, r, 9, part_url(pp_["id"]))
    if part_url(pp_["id"]): c.hyperlink = part_url(pp_["id"]); c.font = Font(color="1155CC", underline="single")
    put(ws, r, 10, pp_["job"])
    cell = put(ws, r, 11, "see on the drone"); cell.hyperlink = SITE + "index.html#" + pp_["id"]; cell.font = Font(color="1155CC", underline="single")
    ws._r += 1
m1 = ws._r - 1
header(ws, PARAM_COLS)
p(ws, "cost_sensors", "Mission sensors", "", f"=SUM(D{m0}:D{m1})", "USD", "Σ lines", "[C]", "small parts and shipping not included", fmt="$#,##0", key_result=True)
p(ws, "cost_all", "Aircraft + mission sensors", "", "={cost_total}+{cost_sensors}", "USD", "", "[C]", "budget: $3,000 cap, stretch $4,000–5,000 (user, 30 Oct)", fmt="$#,##0", key_result=True)
p(ws, "cost_every", "Everything to buy: aircraft, mission sensors and ground equipment", "", "={cost_all}+{cost_ground}", "USD", "", "[C]", "", fmt="$#,##0", key_result=True)

# =====================================================================================================
ws = sheet("Cost_Options", [44, 12, 14, 50, 34, 16])
title(ws, "Ways to cut cost, with the risk of each (nothing decided here unless marked)")
header(ws, ["Option", "Saves $", "Status", "Risk / what has to be true", "How to check", "Source [tag]"])
text_rows(ws, [
    ["Use owned LW-ASA (user owns it)", 150.00, "APPLIED (Qty 0)", "none", "", "user 11-10"],
    ["Club leftovers for ASA / TPU / PETG", 83.00, "OPEN", "need < 100 g of each", "ask in #officers or the CHIP shelf", "[A]"],
    ["Hardware and epoxy from club / lab stock", 120.00, "OPEN", "", "check the bins before ordering", "[A]"],
    ["Skip the hardened nozzle", 52.90, "OPEN", "only if the CORE One already has one (PETG-CF wears brass)", "look at the nozzle marking", "[V] price"],
    ["Build the pack from 36 Samsung 50S cells instead of buying it ready-made", f"={part_price('battery')}-(36*6.99+50)", "OPEN, TEST", "voltage sag under 12 A per cell must be within 0.2 V of the P50B (else hot-day T/W drops below 1.5)", "bench: one 6S pack at hover current, log voltage + temperature", "[C] doc §4l"],
    ["KST DS145MG servos instead of KST X10", f"={part_qty('servos')}*({part_price('servos')}-34.99)", "NOT RECOMMENDED", "margin 1.11 over need (X10 1.60); ships from China (+duty, 10-20 days)", "", "[C] mini_servo.md"],
    ["Buy motors + props in the US (no duty)", f"=ROUND({part_qty('motor_lift')}*{part_price('motor_lift')}*0.415+{part_qty('prop_lift')}*{part_price('prop_lift')}*0.375+{part_price('motor_pusher')}*0.415,0)", "OPEN", "only IR-LOCK found; out of stock since 10-30", "check IR-LOCK / United UAV stock", "[C] mini_duty.md"],
    ["Bambu PETG-CF from the Bambu US store", "=2*(31.99-19.99)", "UNVERIFIED", "$19.99 seen in a snippet, maybe a sale", "open the page", "[S]"],
    ["HaoZhong standard shipping instead of expedited", 15.00, "OPEN", "+1-2 weeks", "", "[V]"],
    ["Fewer cells (6S5P)", f"=6*{part_price('battery')}", "NOT RECOMMENDED", "loiter falls below the 80 min rule (Battery_Options)", "", "[C]"],
])

# =====================================================================================================
ws = sheet("Decisions", [36, 34, 40, 56, 30, 14])
title(ws, "Decisions and why (the reasoning a reviewer should check)")
header(ws, ["Decision", "Chosen", "Alternatives", "Why", "Evidence (tab / file)", "Date / status"])
text_rows(ws, [
    ["Aircraft type", "VTOL quadplane: 4 lift + 1 pusher", "multirotor; fixed wing; tilt-rotor", "A multirotor hovers the whole flight (~1.2 kW vs ~0.25 kW winged loiter [C Lift_Hover vs Aero_Cruise]) → about 5x less time; fixed wing needs a runway on hillsides; tilt-rotor adds servos and failure modes. Quadplane = simplest long-endurance VTOL.", "Mission_Energy; OWN_SMALL_DRONE", "10-15 / done"],
    ["Our own design, small", "2.24 m, 0.50 m² wing", "3.35 m SR-3; buy a DeltaQuad", "Our sensor kit is ~0.3-0.45 kg, so the 3.35 m design (sized for a 2.5 kg camera) is oversized; bought VTOLs cost $8k+.", "Battery_Options; size sweep in analysis/mini_sizing.py", "10-30 / done"],
    ["Wing area and battery", "0.50 m² + 6S6P P50B", "0.40-0.70 m², 6S3P-7P", "Cheapest size that met T/W ≥ 1.5 hot, stall ≤ 15 m/s and ≥ 80 min in the sweep (CD0 0.025-0.035 assumed). RE-CHECK with the drag buildup (this workbook).", "Battery_Options, Mission_Energy", "10-30 / re-check 11-17"],
    ["6S voltage", "6S", "12S", "Smaller aircraft draws ~1.1-1.5 kW in hover: 6S keeps currents ≤ 13 A per motor; cheaper ESCs and connectors; same cells.", "Lift_Hover", "10-30 / done"],
    ["Lift motor", "T-Motor MN5008 KV340 + P18x6.1", "Sky4 SunnySky V4014 (owned)", "V4014: T/W 1.20 at 800 m hot (rule 1.5). MN5008 table gives the margin.", "Lift_Hover; SunnySky V4014 maker table", "11-10 / done"],
    ["Pusher", "AT3520 KV550 + APC 12x6E", "APC 13x6.5 (maker's test prop)", "13x6.5 draws only 34.9 A at 100 % [V] (fine for the 40 A ESC) but leaves ~15 mm ground clearance, so 12 in stays. Winged climb limited to ~1.5-2 m/s: climb gently or on rotors.", "Pusher", "11-02 / kept 11-17"],
    ["ESC", "ALPHA 40A 6S from US stock", "same from China; Sky4 Tekko32", "US $92 vs China $69.99 + 37.5 % duty = $96.24, and no customs wait.", "BOM_Cost; Electronics", "11-10 / done"],
    ["Cells", "Molicel P50B", "Samsung 50S, 50E", "P50B rated 60 A, in US stock, tested by others; 50S cheaper but sag untested; 50E rating too low.", "Battery_Options", "11-02 / done"],
    ["Airfoil", "SD7037", "others not compared here", "Low-Re sailplane airfoil, 9.2 % thick: good L/D at Re 2-3 x 10⁵; thick enough for the spar tubes.", "Airfoil_SD7037", "10 / done"],
    ["Tail", "arch tail 0.12 x 0.36 m", "0.10 x 0.30, 0.14 x 0.40", "Middle size: yaw stability Cn_β 0.139, trims at -0.1°.", "Structure_Stability; mini_layout", "10-30 / done"],
    ["Tip polyhedral", "10° tips at y 0.87 m", "flat wing", "Flat wing slightly roll-unstable; 10° makes Cl_β -0.031.", "Structure_Stability", "10-30 / done"],
    ["Booms", "30/28 CF, two 1 m tubes bonded with a sleeve", "one-piece 2 m 25/22 ($288.60)", "$97 vs $289; margin 1.97; needs a bonded-joint test.", "Structure_Stability; mini_boom.md", "10-31 / done"],
    ["Servos", "KST X10 V2", "DS145MG, X10 Mini", "Margin 1.60 over need, US stock.", "Electronics; mini_servo.md", "10-30 / done"],
    ["Remote ID", "Ruko R111S", "Dronetag Beacon $149", "On the FAA accepted list; cheapest found.", "Electronics", "10-31 / done"],
    ["Flight electronics", "Reuse our Cube Orange (user 11-19); buy PM07, M10, MS5525DSO, SiK V3, RP2, Pocket", "Pixhawk 6C + PM07 new ($242.99); Sky4 parts (not available)", "Prices read on the stores 11-19 (Electronics tab); the Pocket transmitter and charger are in BOM_Cost, Ground equipment.", "Electronics; BOM_Cost", "11-19 / done"],
])

# =====================================================================================================
ws = sheet("Open_Checks", [48, 16, 56, 30])
title(ws, "Open checks: what would change the answer, and how to settle it")
header(ws, ["Check", "Changes", "How", "Who / when"])
text_rows(ws, [
    ["Drag buildup vs the old CD0 0.025-0.035", "loiter time, battery size", "This workbook's buildup is higher mainly because of the exposed lift motors, TPU feet and stopped props (bluff-body Cd [A]). "
     "Get a second check (Crab reviewer) and, later, a glide or flight log fit of CD0. Cheap fixes if it holds: teardrop feet, motor spinner/cowls.", "next"],
    ["Wing CLmax 1.19 (airfoil) vs 1.3 (old assumption)", "stall speed, loiter speed", "If the 15 m/s stall rule fails, options: use the flaps already in the CAD (150-900 mm), relax the rule (VTOL lands on rotors), or a bit more area.", "next"],
    ["Printed part masses", "everything mass-driven", "Weigh the wing test pieces (CAD 31 / 29 g); stop if > 20 % heavier.", "first print"],
    ["Pusher thrust at speed", "climb plan", "Thrust stand with airflow, or a car-top test; or plan rotor climbs.", "before first transition"],
    ["Pusher 12x6E thrust and current", "climb plan", "Thrust stand; no maker data for 12x6E on the AT3520.", "before first transition"],
    ["Samsung 50S sag", "-$72", "Bench test (Cost_Options).", "optional"],
    ["Bonded boom joint", "safety", "Bench bending test of the sleeve joint to 1.5 x design moment.", "before flight"],
    ["Motor and pusher bolt patterns", "CNC plates", "Calipers on the real motors before cutting.", "on delivery"],
    ["Real payload masses", "CG, T/W", "Weigh Jetson, cameras, spot sensor.", "on delivery"],
])

# =====================================================================================================
ws = sheet("Sources", [40, 100])
title(ws, "Sources")
text_rows(ws, [
    ["Raymer, Aircraft Design: A Conceptual Approach, 6th ed.", "Component drag buildup (Cf, FF, Q), Oswald estimate, CLmax ≈ 0.9 cl_max."],
    ["Torenbeek, Synthesis of Subsonic Airplane Design", "Fuselage wetted area formula."],
    ["Hoerner, Fluid-Dynamic Drag", "Bluff-body drag coefficients (short cylinders)."],
    ["NeuralFoil (Sharpe), via AeroSandbox", "SD7037 polars (large model)."],
    ["store.tmotor.com", "MN5008 KV340 thrust table (10-30); AT3520 KV550 spec and test table (11-17)."],
    ["Our CAD", f"{REPO}/cad/fab, outputs $SKY_BUILD/sr3_mini_out (BOM.md, meta/*.json); per-part export export_mass.py."],
    ["Our scripts", f"{REPO}/analysis/mini_sizing.py, mini_spar.py, mini_boom.py, mini_servo.py, mini_wiring.py, mini_filament.py, mini_duty.py, mini_layout.py, mini_polyhedral.py, mini_avl_cad.py."],
    ["Prices", f"{REPO}/docs/BEST_PRICES_2026-11-10.md, BUY_LIST_2026-11-02.md (store links in each row)."],
    ["Duty", "hts.usitc.gov HTS 2026 Revision 22 (read 10-30), mini_duty.md."],
    ["FAA Remote ID", "FAA accepted declarations of compliance list (read 10-31)."],
])

resolve()
for w in wb.worksheets:
    w.freeze_panes = None
wb.save(OUTF)
json.dump(REF, open(HERE / "refs.json", "w"))
_unused = sorted(set(INPUTS) - USED_INPUTS)
assert not _unused, f"data/inputs.toml has names the workbook does not know (typo?): {_unused}"
json.dump(TYPED, open(HERE / "typed_inputs.json", "w"), ensure_ascii=False, indent=0)
for pp_ in PAY:                                  # mission sensors: first-flight kit, then the options
    BUY.append(dict(group="Mission sensors" if pp_.get("tier") == "minimum" else "Mission sensors: worth adding", name=pp_["name"], qty=buy_qty(pp_), unit=pp_["price"],
                    line=buy_qty(pp_) * pp_["price"], duty=0, store=pp_["buy"][0][0] if pp_["buy"] else "", link=pp_["buy"][0][1] if pp_["buy"] else "", note=pp_["source"], id=pp_["id"]))
json.dump(BUY, open(HERE / "buy_list.json", "w"), ensure_ascii=False, indent=0)
print("saved", OUTF, len(REF), "named cells")
