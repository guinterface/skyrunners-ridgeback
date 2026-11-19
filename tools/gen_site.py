"""Build the static site in docs/ (served by GitHub Pages).

Inputs: tools/parts.py (every part), data/calc_values.json + data/refs.json (results of the calculation sheets),
data/sheet_links.json (Google Sheets links), docs/assets/ridgeback.glb (from tools/export_model.py).
Run: python3 tools/gen_site.py
"""
import json, re, html, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from parts import PARTS, SYSTEMS, PART_LINE, RAW
GH = "https://github.com/guinterface/skyrunners-ridgeback"

E = html.escape
VALS = json.load(open(ROOT / "data/calc_values.json"))
R = json.load(open(ROOT / "data/refs.json"))
LINKS = json.load(open(ROOT / "data/sheet_links.json")) if (ROOT / "data/sheet_links.json").exists() else {}
FN = "RIDGEBACK_MINI_VTOL_DESIGN_2026-11-17.XLSX"


def val(key):
    m = re.match(r"'(.+)'!\$?([A-Z]+)\$?(\d+)", R[key])
    return VALS[f"'[{FN}]{m.group(1).upper()}'!{m.group(2)}{m.group(3)}"]


FMT = {"Icell_hot": "{:.1f}", "tloit_sl": "{:.0f}", "tloit_hot": "{:.0f}", "flights_pack": "{:.1f}", "Ipack_hot": "{:.0f}", "Ipack_sl": "{:.0f}",
       "m_to": "{:.1f}", "Thov_sl": "{:,.0f}", "throttle_sl": "{:.0%}", "throttle_hot": "{:.0%}", "TW_hot": "{:.2f}", "TW_sl": "{:.2f}",
       "Imot_hot": "{:.1f}", "I_full": "{:.1f}", "I_push": "{:.1f}", "D_sl": "{:.1f}", "V_sl": "{:.0f}", "Tav_sl": "{:.0f}",
       "range_km": "{:.0f}", "Vs_sl": "{:.1f}", "CD0_build": "{:.3f}", "cost_total": "${:,.0f}", "E_use": "{:.0f}", "E_flight": "{:.0f}",
       "Pcr_sl": "{:.0f}", "Phov_sl": "{:,.0f}", "Phov_hot": "{:,.0f}"}


def fill(text):
    return re.sub(r"\{(\w+)\}", lambda m: FMT.get(m.group(1), "{:.3g}").format(val(m.group(1))), text)


def sheet(name, tab=None):
    u = LINKS.get(name)
    label = f"Sheet {name[:2]}" + (f", tab {tab}" if tab else "")
    return f'<a href="{u}" target="_blank" rel="noopener">{E(label)}</a>' if u else E(label)


# ------------------------------------------------------------------ parts data for the browser
g0 = 9.80665
CALCS = {
    "battery": dict(step="step-8", sheet=("04_Propulsion_Battery_Energy", "Mission_Energy"),
        lines=[(r"E_{flight} = E_{hover} + E_{climb} + P\,(t_{survey} + t_{transit}) = %.0f\ \text{Wh}" % val("E_flight"), "energy for one 15-minute survey, 1 km out and back"),
               (r"E_{pack,\,needed} = \dfrac{3 \times %.0f}{0.85 \times 0.8} = %.0f\ \text{Wh}" % (val("E_flight"), 3 * val("E_flight") / 0.68), "three flights, keeping the cells between 95 % and 10 % and 20 % in reserve"),
               (r"%.0f\ \text{Wh needed} \;>\; 648\ \text{Wh in 6S6P}" % (3 * val("E_flight") / 0.68), "so the pack covers %.1f flights, not 3; a 7P pack would fail the hover-thrust rule (Battery_Options)" % val("flights_pack"))]),
    "motor_lift": dict(step="step-7", sheet=("04_Propulsion_Battery_Energy", "Lift_Hover"),
        lines=[(r"T_{hover} = \dfrac{m g}{4} = \dfrac{%.2f \times 9.81}{4} = %.1f\ \text{N per motor}" % (val("m_to"), val("m_to") * g0 / 4), "thrust each motor holds in a hover"),
               (r"\dfrac{T}{W} = \dfrac{4\,T_{max}}{m g} = \dfrac{4 \times %.1f}{%.1f} = %.2f \;\geq\; 1.5" % (val("Tmax_hot"), val("m_to") * g0, val("TW_hot")), "hot day at 800 m, from T-Motor's test table")]),
    "prop_lift": dict(step="step-7", sheet=("04_Propulsion_Battery_Energy", "Lift_Hover"),
        lines=[(r"\dfrac{T}{W} = %.2f \;\text{on a hot day}" % val("TW_hot"), "the maker's thrust figures are for this exact propeller")]),
    "esc_lift": dict(step="step-6", sheet=("04_Propulsion_Battery_Energy", "Lift_Hover"),
        lines=[(r"I_{max} = \dfrac{P_{100\%%}}{V} = \dfrac{754\ \text{W}}{22.5\ \text{V}} = %.1f\ \text{A} \;<\; 40\ \text{A}" % val("I_full"), "full throttle, from the motor test table"),
               (r"I_{hover} = %.1f\ \text{A}" % val("Imot_hot"), "hot-day hover, per motor")]),
    "pm07": dict(step="step-6", sheet=("04_Propulsion_Battery_Energy", "Lift_Hover"),
        lines=[(r"I_{pack} = \dfrac{P_{hover}}{V} = \dfrac{%.0f\ \text{W}}{21.6\ \text{V}} = %.0f\ \text{A} \;<\; 90\ \text{A}" % (val("Phov_hot"), val("Ipack_hot")), "hot-day hover through the power module")]),
    "motor_pusher": dict(step="step-4", sheet=("04_Propulsion_Battery_Energy", "Pusher"),
        lines=[(r"D = \tfrac12 \rho V^2 S\, C_D = %.1f\ \text{N}" % val("D_sl"), "drag at the loiter speed of %.0f m/s" % val("V_sl")),
               (r"\dfrac{D}{T(V)} = \dfrac{%.1f}{%.0f} = %.2f" % (val("D_sl"), val("Tav_sl"), val("Tratio_sl")), "share of the pusher's thrust used in level flight (estimate)")]),
    "wing": dict(step="step-2", sheet=("03_Aerodynamics", "Aero_Cruise"),
        lines=[(r"V_s = \sqrt{\dfrac{2W}{\rho S C_{L,\max}}} = %.1f\ \text{m/s}" % val("Vs_sl"), "stall speed with 0.50 m² and the SD7037 airfoil"),
               (r"V_{loiter} = 1.3\,V_s = %.1f\ \text{m/s}" % val("V_sl"), "loiter speed, kept above stall for turns and gusts")]),
    "servos": dict(step=None, sheet=("05_Structure_and_Stability", "Structure_Stability"),
        lines=[(r"\tau_{needed} = 2 \times M_{hinge} = 2 \times 2.34 = 4.7\ \text{kg·cm} \;<\; 7.5", "aileron at a 34 m/s dive, with a factor of 2")]),
}
pj = []
for p in PARTS:
    q = dict(p)
    q["why"] = fill(p["why"]); q["job"] = fill(p["job"])
    q["systemName"], q["color"] = SYSTEMS[p["system"]]
    q["edit"] = f"{GH}/edit/main/data/parts.toml"; q["editLine"] = PART_LINE[p["id"]]; q["raw"] = RAW[p["id"]]
    if p["id"] in CALCS:
        c = CALCS[p["id"]]
        q["calc"] = [list(x) for x in c["lines"]]
        q["calcStep"] = c["step"]; q["calcSheet"] = LINKS.get(c["sheet"][0]); q["calcSheetName"] = f"Sheet {c['sheet'][0][:2]}, tab {c['sheet'][1]}"
    pj.append(q)
(ROOT / "docs/assets/parts.json").write_text(json.dumps(dict(parts=pj, systems={k: {"name": a, "color": b} for k, (a, b) in SYSTEMS.items()}), indent=1))

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,400..700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">')


def page(title, slug, body, extra_head="", body_class=""):
    nav = [("index.html", "Drone"), ("mission.html", "Mission and range"), ("calculations.html", "Calculations"), ("buy.html", "Buy list"), ("files.html", "Sheets, code, CAD")]
    links = "".join(f'<a href="{h}"{" aria-current=page" if h == slug else ""}>{t}</a>' for h, t in nav)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>{FONTS}<link rel="stylesheet" href="assets/style.css">{extra_head}</head>
<body class="{body_class}"><div class="sheet"><header class="collar"><div class="mast"><a class="home" href="index.html">Ridgeback Scout</a>
<span class="who">SkyRunners, Stanford Student Robotics</span></div><nav>{links}<button type="button" id="editToggle" class="editbtn" aria-pressed="false">Edit</button></nav></header>
<div id="editbar" class="editbar" hidden></div>
<main>{body}</main>
<footer class="collar foot"><span>Designed in CAD, not yet built or flown. Numbers from the calculation sheets, updated 17 Nov 2026.</span>
<a href="https://github.com/guinterface/skyrunners-ridgeback">Source on GitHub</a></footer></div><script type="module" src="assets/edit.js"></script></body></html>"""


def status_row():
    rows = [("Hover thrust ÷ weight, hot day", f"{val('TW_hot'):.2f}", "at least 1.5", val("TW_hot") >= 1.5),
            ("Loiter time, 20 % reserve left", f"{val('tloit_sl'):.0f} min", "at least 80 min", val("tloit_sl") >= 80),
            ("Survey flights per charge", f"{val('flights_pack'):.1f}", "at least 3", val("flights_pack") >= 3),
            ("Stall speed, clean wing", f"{val('Vs_sl'):.1f} m/s", "at most 15 m/s", val("Vs_sl") <= 15),
            ("Aircraft cost", f"${val('cost_total'):,.0f}", "at most $3,000", val("cost_total") <= 3000),
            ("Aircraft + mission sensors", f"${val('cost_all'):,.0f}", "stretch: at most $5,000", val("cost_all") <= 5000),
            ("Everything to buy, with transmitter and charger", f"${val('cost_every'):,.0f}", "stretch: at most $5,000", val("cost_every") <= 5000)]
    tr = "".join(f'<tr><td>{a}</td><td class="num">{b}</td><td>{c}</td><td class="{"ok" if ok else "no"}">{"meets it" if ok else "short"}</td></tr>' for a, b, c, ok in rows)
    return f'<table class="status"><thead><tr><th>Requirement</th><th class="num">Estimate</th><th>Target</th><th>Result</th></tr></thead><tbody>{tr}</tbody></table>'



def gap_box():
    """The two targets the design misses, and what each lever does to them (Sheet 04, Mission_Energy, Levers)."""
    rows = [("As designed", val("tloit_sl"), val("flights_pack"), "", "estimate"),
            ("Printed fairings on motors and feet, lift props parked fore-aft", val("tloit_fair"), val("flights_fair"), "filament only", f"assumes they remove {val('fair_frac'):.0%} of that drag [A]"),
            ("Survey 12 min over the plot instead of 15", val("tloit_sl"), val("flights_s12"), "none", "only if 12 min covers the plot with the thermal camera's overlap"),
            ("Both", val("tloit_fair12"), val("flights_fair12"), "filament only", "the plan"),
            ("Upper bound: motors, feet and props add no drag at all", val("tloit_clean"), val("flights_clean"), "", "cannot be beaten by fairings")]
    tr = "".join(f'<tr><td>{E(a)}</td><td class="num {"ok" if t >= 80 else "no"}">{t:.0f} min</td><td class="num {"ok" if f >= 3 else "no"}">{f:.2f}</td><td>{E(c)}</td><td class="quiet">{E(n)}</td></tr>' for a, t, f, c, n in rows)
    ft, ff, tc = val("tloit_fair12"), val("flights_fair12"), val("tloit_clean")
    verdict = (f"With fairings and a 12 min survey the field day fits on one charge ({ff:.1f} flights)" if ff >= 3 else f"Even with both levers the field day needs {ff:.1f} of 3 flights") + \
              (f"; loiter reaches {ft:.0f} min, so the 80 min rule is met" if ft >= 80 else
               f"; loiter reaches {ft:.0f} of 80 min. 80 min is possible only if fairings remove most of that drag (the upper bound is {tc:.0f} min)" if tc >= 80 else
               f"; even with no motor, foot or prop drag loiter stays at {tc:.0f} min, so 80 min needs a lighter aircraft")
    return f"""<h3>How we close the two gaps</h3>
<p>Loiter time and flights per charge come out short. These rows use the same formulas with one thing changed each
({sheet('04_Propulsion_Battery_Energy', 'Mission_Energy')}, "Levers"). The field day needs 3 flights; the 80 min loiter rule is a margin target.</p>
<div class="tablewrap"><table class="plain gap"><thead><tr><th>Lever</th><th class="num">Loiter (target 80 min)</th><th class="num">Flights per charge (target 3)</th><th>Cost</th><th>Note</th></tr></thead><tbody>{tr}</tbody></table></div>
<p class="small">{verdict}. A bigger battery is not the way out: a 6S7P pack drops hot-day hover thrust below 1.5 times the weight (Battery_Options). The next real step is to measure: weigh the printed parts, bench-test the pusher and fit the drag from the first flights, since every row here rests on an estimated drag.</p>"""


TIER = {"minimum": "first flights", "add": "worth adding", "later": "later"}


def cost_txt(p):
    return "owned" if p["status"].startswith("reuse") else f"${p['price']:,.0f}"


def payload_section():
    ORDER = ['thermal_cam', 'air_sensor', 'spot_sensor', 'nir_channel', 'rgb_cam', 'payload_computer', 'payload_power']  # same order as the three questions
    pay = sorted((p for p in PARTS if p["system"] == "payload"), key=lambda p: ORDER.index(p['id']) if p['id'] in ORDER else 99)
    tr = "".join(f'<tr data-id="{p["id"]}" tabindex="0"{" class=add" if p.get("tier") != "minimum" else ""}><td>{E(p["name"].split(":")[0].split(" (")[0])}</td><td>{E(p["job"])}</td><td>{E(TIER.get(p.get("tier"), ""))}</td><td class="num">{p["mass"]:.0f} g</td>'
                 f'<td class="num">{(f"{p['power_w']:g} W" if p.get("power_w") else "under 0.1 W")}</td><td class="num">{cost_txt(p)}</td></tr>' for p in pay)
    def refs(p):
        return "".join(f'<li><a href="{E(r["link"])}" target="_blank" rel="noopener">{E(r["cite"])}</a>: {E(r.get("says", ""))}</li>' for r in p.get("refs", []))
    short = lambda p: E(p["name"].split(":")[0].split(" (")[0])
    why = "".join(f'<tr data-id="{p["id"]}" tabindex="0"{" class=add" if p.get("tier") != "minimum" else ""}><td>{short(p)}</td><td>{E(p.get("without", ""))}</td>'
                  f'<td>{f"<ul class=refs>{refs(p)}</ul>" if p.get("refs") else "<span class=quiet>a wiring need; no paper needed</span>"}</td></tr>' for p in pay)
    return f"""<section id="sensors"><h2>What the drone carries for the mission</h2>
<p>The parts above only make the drone fly. The mission is to measure how much water each shrub loses between dawn and midday. That needs
three readings over the same plants on every flight, and each one comes from a different sensor:</p>
<ol class="chain"><li><b>Is the plant stressed?</b> Leaves that run short of water close their pores and warm up compared with the air: the thermal camera, read against the air sensor.</li>
<li><b>How much water do the leaves hold?</b> Water absorbs short-wave infrared light near 1610 nm: the spot sensor, best paired with its 850 nm channel, which water does not absorb (the pair gives a leaf-water index; $214, still to decide).</li>
<li><b>Which plant is it, and how much of each reading is leaf and how much is soil?</b> The colour camera. Its overlapping photos also give each shrub's 3D shape, so no separate 3D sensor is needed.</li></ol>
<p>That is the minimum: drop the thermal camera, the spot sensor or the colour camera and one of the three questions has no answer.
The air sensor on the drone adds the air at flight height (the main air reference is the weather meter on the ground), and the computer and the 5 V regulator make it all work.
A SWIR camera or centimetre GPS would make the readings better; see "Not decided yet" below. Click a row to see the sensor on the drone.</p>
<h3>What we would lose without each one</h3>
<div class="tablewrap"><table class="parts why"><thead><tr><th>Sensor</th><th>Without it</th><th>Evidence</th></tr></thead><tbody>{why}</tbody></table></div>
<h3>Mass, power and price</h3>
<div class="tablewrap"><table class="parts"><thead><tr><th>Sensor</th><th>What it does</th><th>When</th><th class="num">Mass</th><th class="num">Power</th><th class="num">Price</th></tr></thead>
<tbody>{tr}<tr class="tot"><td>Total, first flights</td><td></td><td></td><td class="num">{val('m_pay_g'):.0f} g</td><td class="num">{val('P_payload'):.0f} W</td><td class="num">${val('cost_sensors'):,.0f}</td></tr></tbody></table></div>
<p class="small">Mass and power go into the takeoff mass and the energy budget ({sheet('02_Mass_and_CG', 'Mass_CG')}, {sheet('04_Propulsion_Battery_Energy', 'Mission_Energy')}). With the first-flight sensors on board: takeoff mass {val('m_to'):.2f} kg, hot-day hover thrust {val('TW_hot'):.2f} times the weight (rule: 1.5), loiter {val('tloit_sl'):.0f} min (target 80: short, see Requirements). The pre-dawn flight uses only the thermal camera and the air sensor: the other sensors need sunlight.</p>
<h3>On the ground, every field day</h3>
<table class="plain"><thead><tr><th>Item</th><th>Why</th><th>Cost</th></tr></thead><tbody>
<tr><td>Ground truth from the plants: leaf samples from 5–10 tagged shrubs at each flight time, weighed and oven-dried (the standard live fuel moisture protocol), and leaf water potential with a pressure chamber borrowed from a lab</td><td>The only way to turn sensor readings into plant water. Fire agencies plan burns from live fuel moisture measured this way.</td><td>clippers, sealed bottles, a 0.01 g balance; pressure chamber to borrow</td></tr>
<tr><td>Reference panel for 1610 and 850 nm (white PTFE sheet, measured once on a lab spectrometer)</td><td>Turns the spot sensor's readings into reflectance and catches drift between the morning and midday flights. Flown over before and after each flight.</td><td>estimate $40</td></tr>
<tr><td>Warm and cool thermal targets: 2–3 insulated water tubs, each with a logging probe</td><td>The Lepton reads only to about ±5 °C; targets of known temperature in every flight correct it. Calibrating a FLIR A655sc pixel by pixel against a lab black body cut its error from about 6 °C to under 1 °C (<a href="https://doi.org/10.3390/s20113316" target="_blank" rel="noopener">Aragon et al. 2020</a>); field targets are our cheaper version, and how close the Lepton gets is untested.</td><td>estimate $350</td></tr>
<tr><td>Weather meter on a tripod at canopy height (an SHT45 logger to start; a Kestrel 5500 at $449 if wind is needed)</td><td>The main air reference for leaf-minus-air temperature, through the whole day; the drone's air sensor is checked against it.</td><td>estimate $40</td></tr>
<tr><td>Ground targets visible in both thermal and colour (black and foil squares)</td><td>Lines up the dawn and midday images so the same shrubs are compared.</td><td>about $120, own build</td></tr>
</tbody></table>
<h3>Not decided yet</h3>
<ul class="open">
<li><b>A SWIR camera</b> instead of the spot sensor: images of every shrub instead of one reading per 21 m spot. $2,250 a week to rent, $5,650 and up to buy; asked several companies.</li>
<li><b>The near-infrared channel</b> in the table above (850 nm, $214): recommended before the first mission flights: it turns the 1610 nm reading into a leaf-water index that lighting and shadow affect much less.</li>
<li><b>A vegetation layer on sheet 1</b> showing where the chaparral actually is, to place the plot.</li>
<li><b>Centimetre GPS (RTK)</b> to find the same shrub on every flight without ground targets. About $3,000; later.</li>
</ul></section>"""


def access_section():
    """How each electronics group is held and reached (CAD: cad/fab/f_fuse.py MINI block; build guide section 6-7)."""
    rows = [
        ("Flight controller, receiver, telemetry radio, Remote ID", "Nose, top tray (tray A) between frames F1 and F2, x −330 to −170 mm",
         "Screwed to a printed plate with a 20 mm grid of M3 holes; the plate is held by 4 M3 screws in heat-set inserts. Flight controller on rubber vibration mounts.",
         "Lift the top hatch (held by 4 magnets, no tools). Mount the flight controller with its USB and microSD side toward the opening, so setup and log download need nothing removed.", "good"),
        ("Power module", "Nose, lower tray (tray B), under tray A", "Same grid plate, 4 M3 screws.",
         "Top hatch, then take out tray A (4 screws) because tray B sits under it. Fine for a part that is rarely touched.", "ok"),
        ("Battery", "Under the wing, on a 1.5 mm carbon tray, centre at x −58 mm", "3 straps and a printed stop at the back; the XT90 plug faces the hatch.",
         "Second magnetic hatch (x −165 to −15 mm): unplug, undo the straps, slide forward and out. No tools.", "good"),
        ("Lift speed controllers", "In each boom nacelle, under the tube, behind the motor", "Printed clips in the nacelle hold it; the two nacelle halves close around it.", "Open the nacelle halves. The build guide allows tape or glue to close them: use tape (or two small screws), never glue, so they can be opened again.", "ok"),
        ("Pusher speed controller and servo regulator", "Tail cone (fuselage segment 4)", "Glued trays on the tail-cone floor, cable ties.",
         "Problem: the tail cone has no opening, so they cannot be reached after it is bonded. Fix: a small screwed belly panel under the tail cone, or move the regulator to tray B.", "fix"),
        ("Mission sensors and the Raspberry Pi", "Belly, behind the battery, x +40 to +160 mm, looking down",
         "Not drawn yet: today there is only a reserved space.",
         "Problem: the space is under the wing, so as planned it is reachable only with the wing off. Fix: all sensors and the Pi on one removable belly plate (4 thumb screws, one power plug and one cable to the flight controller), so the whole sensor set comes off from below, can be tested on the bench and swapped between flights.", "fix"),
    ]
    tag = {"good": "easy", "ok": "fine", "fix": "to fix"}
    tr = "".join(f'<tr class="acc-{k}"><td><b>{E(a)}</b><br><span class=quiet>{E(b)}</span></td><td>{E(c)}</td><td>{E(d_)}</td><td class="acctag">{tag[k]}</td></tr>' for a, b, c, d_, k in rows)
    return f"""<section id="access"><h2>How the electronics are held, and how you reach them</h2>
<p>Everything sits on printed plates screwed into heat-set inserts, so parts can be moved without new holes, and every link between groups is a plug
(JST-GH for signals, XT30/XT60/XT90 for power), so a group can come out without cutting or soldering. Two places are not good yet; their fixes are the next CAD change.</p>
<div class="tablewrap"><table class="plain access"><thead><tr><th>What</th><th>How it is held</th><th>How you reach it</th><th></th></tr></thead><tbody>{tr}</tbody></table></div>
<p class="small">From the CAD (cad/fab/f_fuse.py) and the build guide. Hatches are printed (radio-transparent), so the GPS and radios work through them.</p></section>"""


# ------------------------------------------------------------------ index: the drone explorer
groups = {}
for p in PARTS:
    groups.setdefault(p["system"], []).append(p)
rows = []
for sk, (sname, col) in SYSTEMS.items():
    if sk not in groups: continue
    rows.append(f'<tr class="grp"><th colspan="6"><span class="key" style="--c:{col}"></span>{E(sname)}</th></tr>')
    for p in groups[sk]:
        price = "owned" if p["status"].startswith("reuse") else (f"${p['price']:,.2f}" if p["price"] else "")
        buy = p["buy"][0] if p["buy"] else None
        b = f'<a href="{E(buy[1])}" target="_blank" rel="noopener">{E(buy[0].split(" (")[0])}</a>' if buy else ""
        rows.append(f'<tr id="row-{p["id"]}" data-id="{p["id"]}" tabindex="0"><td>{E(p["name"])}</td><td class="num">{p["qty"]}</td><td>{E(p["status"])}</td>'
                    f'<td class="num">{price}</td><td class="num">{p["mass"]:,.0f} g</td><td>{b}</td></tr>')
index_body = f"""
<section class="lead"><h1>Inside the drone</h1>
<p>Our own 2.24 m VTOL drone for measuring how much water chaparral shrubs lose between dawn and midday, for planning prescribed burns.
Click any part on the drone or in the list to see what it does, why we chose it, what it connects to and where to buy it.</p></section>
<section class="explorer">
  <div class="viewer"><div class="viewbar"><div class="mapbar" role="group" aria-label="Flight mode"><button type="button" data-mode="hover">Hover</button><button type="button" data-mode="cruise">Cruise</button><button type="button" data-mode="still">Still</button></div>
  <button type="button" id="reset" class="plainbtn">Whole drone</button></div>
  <div class="picks" role="group" aria-label="Show a part"><span>Show:</span><button type="button" data-pick="battery">Battery</button><button type="button" data-pick="motor_lift">Lift motors</button><button type="button" data-pick="motor_pusher">Pusher</button><button type="button" data-pick="pixhawk">Flight controller</button><button type="button" data-pick="wing">Wing</button><button type="button" data-pick="thermal_cam" class="sens">Thermal camera</button><button type="button" data-pick="spot_sensor" class="sens">1610 nm sensor</button><button type="button" data-pick="rgb_cam" class="sens">Colour camera</button></div>
  <div class="viewwrap"><div id="view" aria-label="3D model of the drone. Drag to turn, scroll to zoom, click a part."></div><div id="tip" class="tip" hidden></div></div>
  <div class="legend">{''.join(f'<span><i style="--c:{c}"></i>{E(n)}</span>' for k, (n, c) in SYSTEMS.items())}</div>
  <p class="hint">Drag to turn, scroll to zoom. Hover spins the lift propellers; Cruise parks them along the booms and runs the pusher. Every part sits at its CAD position and size.</p></div>
  <aside id="detail" class="detail" aria-live="polite"><h2>Eight groups</h2>
  <p>Pick a part on the drone or below; it turns purple and lines show what it is wired or bolted to.</p>
  {''.join(f'<h3><span class="key" style="--c:{SYSTEMS[k][1]}"></span>{E(SYSTEMS[k][0])}</h3><p>{E(t)}</p>' for k, t in [
    ("power", "Battery, power module and servo regulator: 648 Wh at 21.6 V, about 56 A in a hot hover."),
    ("lift", "Four motors, props and speed controllers that lift the drone off a hillside and land it."),
    ("cruise", "The pusher that flies the drone on the wing over the plot."),
    ("control", "Flight controller, GPS, airspeed, radios and Remote ID."),
    ("surfaces", "Four servos for the ailerons and the arch tail."),
    ("airframe", f"Printed wing, fuselage and tail on carbon tubes. Takeoff mass {val('m_to'):.2f} kg."),
    ("payload", f"What the mission needs: thermal camera, 1610 nm spot sensor, colour camera, air sensor and the computer that logs them. {val('m_pay_g'):.0f} g, {val('P_payload'):.0f} W."),
    ("ground", "Stays on the ground: the safety pilot's transmitter and the battery charger (the laptop radio comes with the telemetry pair).")])}</aside>
</section>
<section><h2>Requirements</h2>{status_row()}{gap_box()}</section>
{payload_section()}
{access_section()}
<section><h2>Every part</h2>
<div class="tablewrap"><table class="parts"><thead><tr><th>Part</th><th class="num">Qty</th><th>Status</th><th class="num">Unit price</th><th class="num">Mass each</th><th>Buy</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="small">Connectors, wire and solder for every joint are listed on {sheet('06_Electronics_BOM_Cost', 'Connectors_Wiring')}; the full parts list with duty and shipping on {sheet('06_Electronics_BOM_Cost', 'BOM_Cost')}.</p></section>
<script type="importmap">{{"imports":{{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}}}</script>
<script type="module" src="assets/app.js"></script>"""
katex_idx = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">'
             '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>')
(ROOT / "docs/index.html").write_text(page("Ridgeback Scout", "index.html", index_body, katex_idx))

# ------------------------------------------------------------------ mission and range
mission_body = f"""
<figure class="mapsheet hero" id="siteSheet">
<figcaption class="collar2"><span class="sheetno">Sheet 1</span><b>Jasper Ridge: one survey flight, to scale</b><span class="quiet">10 m contours from real terrain. Hover any line for what it is.</span>
<button type="button" class="plainbtn" id="replay">Fly it again</button></figcaption>
<div class="mapholder" data-src="assets/map/site.svg" aria-busy="true"></div>
<div class="maplegend"><span><i class="sw ring"></i>1 km line-of-sight radius</span><span><i class="sw plot"></i>2 ha survey plot</span><span><i class="sw path"></i>Flight path, 18 lines</span><span><i class="sw line"></i>Preserve boundary</span><span><i class="sw ct"></i>Contour, 10 m</span></div>
</figure>
<section class="lead"><h1>Mission and range</h1>
<p>We plan around an operating radius of about 1 km, set by the rule that the drone must stay in sight.
So the motors and battery are sized for hover thrust and for time over the plants, not for distance.</p></section>
<section class="mapsec"><h2>Where fire meets our flights</h2>
<p>Every wildfire over 50 acres since 2000 within about 40 km of Stanford, and the prescribed burns on record, on the terrain they burned. In August 2020 the CZU Lightning Complex
burned 86,553 acres of the Santa Cruz Mountains, about 25 km from Jasper Ridge. Prescribed burns are the tool for lowering that risk, and they
are planned around how dry the living plants are.</p>
<figure class="mapsheet" id="regionSheet">
<figcaption class="collar2"><span class="sheetno">Sheet 2</span><b>Fires around Stanford, 2000–2024</b><span class="quiet">100 m contours. Hover a fire for its name, year and size.</span>
<span class="toggles" role="group" aria-label="Show on the map"><label><input type="checkbox" data-layer="fire" checked> wildfires</label><label><input type="checkbox" data-layer="rx" checked> prescribed burns</label></span></figcaption>
<div class="mapholder" data-src="assets/map/region.svg" aria-busy="true"></div>
<div class="maplegend"><span><i class="sw fire"></i>Wildfire, 2000–2024</span><span><i class="sw rx"></i>Prescribed burn</span><span><i class="sw line"></i>Jasper Ridge Biological Preserve</span><span><i class="sw sea"></i>Ocean and bay</span><span><i class="sw ct"></i>Contour, 100 m</span></div>
</figure>
<div id="maptip" class="tip" hidden></div>
<p class="small">Terrain: AWS Terrain Tiles (USGS and other public elevation data), contoured by tools/make_map.py. Wildfire perimeters: CAL FIRE historic fire perimeters. Prescribed burns: NIFC interagency fire perimeter history. Preserve boundary: OpenStreetMap.
The take-off point and plot on sheet 1 are placed for scale only; the real plot will be chosen with the preserve.</p></section>
<section><h2>Operating radius, range and endurance</h2>
<table class="plain"><thead><tr><th>Term</th><th class="num">Ours</th><th>What sets it</th></tr></thead><tbody>
<tr><td>Operating radius: how far from the take-off point</td><td class="num">about 1 km</td><td>FAA rule 14 CFR 107.31: the pilot or an observer must see the drone at all times
(<a href="https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-107/subpart-B/section-107.31" target="_blank" rel="noopener">text of the rule</a>). The rule sets no distance; 1 km is how far we expect to see a 2.2 m drone reliably.</td></tr>
<tr><td>Range: distance on one charge</td><td class="num">{val('range_km'):.0f} km</td><td>Loiter speed × loiter time.</td></tr>
<tr><td>Endurance: time in the air</td><td class="num">{val('tloit_sl'):.0f} min</td><td>Battery energy against drag. This is the number that matters for the mission.</td></tr>
</tbody></table></section>
<section><h2>A field day</h2>
<p>Water loss shows up as the difference between dawn and midday. We target three 15-minute surveys of the same 2 ha chaparral plot on one charge,
within 1 km of the take-off point. The current estimate is {val('flights_pack'):.1f} flights per charge. Before sunrise there is no sunlight, so the pre-dawn flight uses
only the thermal camera; the 1610 nm sensor and the colour camera start with the mid-morning flight.</p>
<svg class="day" viewBox="0 0 900 120" role="img" aria-label="Three flights: pre-dawn, mid-morning, midday">
<line x1="40" y1="70" x2="860" y2="70" class="axis"/>
{''.join(f'<line x1="{x}" y1="64" x2="{x}" y2="76" class="tick"/><text x="{x}" y="96" class="t">{h}</text>' for x, h in [(40, "5:00"), (177, "7:00"), (313, "9:00"), (450, "11:00"), (587, "13:00"), (723, "15:00"), (860, "17:00")])}
{''.join(f'<rect x="{40 + (h - 5) * 68.33:.0f}" y="48" width="{0.25 * 68.33:.0f}" height="22" class="fl"/><text x="{40 + (h - 5 + 0.125) * 68.33:.0f}" y="38" class="l">{lab}</text>' for h, lab in [(6.25, "pre-dawn, 6:15"), (9.75, "mid-morning, 9:45"), (12.75, "midday, 12:45")])}
</svg>
<table class="plain"><tbody>
<tr><td>Plot</td><td>2 ha of chaparral (141 m square) plus a 50 m buffer, so 241 m square: 18 lines of 240 m, 14 m apart. That is 3.8 minutes on the lines at 19 m/s; at that speed a turn needs about 64 m radius, so lines are flown in skip order (racetrack turns), which brings it to about 7 minutes (estimate). The thermal camera's wider pixels set the line count.</td></tr>
<tr><td>Energy per flight</td><td><span class="num">{val('E_flight'):.0f} Wh</span>: hover, climb, 15 min survey, 1 km out and back</td></tr>
<tr><td>Usable energy per charge</td><td><span class="num">{val('E_use'):.0f} Wh</span>, keeping 20 % in reserve</td></tr>
<tr><td>Flights per charge</td><td><span class="num">{val('flights_pack'):.1f}</span>, against the 3 we target</td></tr>
</tbody></table>
<p class="small">Numbers from {sheet('04_Propulsion_Battery_Energy', 'Mission_Energy')}. The plot size and flight plan come from our field-day plan (base station document, October 2026).</p></section>
<section><h2>Sources behind the numbers</h2>
<h3 class="refh">Why measure plant water at all</h3>
<ul class="refs">
<li><a href="https://doi.org/10.1071/WF08055" target="_blank" rel="noopener">Dennison and Moritz, Int. J. Wildland Fire 18:1021 (2009)</a>: "strong evidence for a LFM threshold near 79%" for fire in chaparral.</li>
<li><a href="https://doi.org/10.3390/fire5040110" target="_blank" rel="noopener">Park, Fauss and Moritz, Fire 5:110 (2022)</a>: burned area and number of fires "increased dramatically when LFM fell below 62%" in chamise.</li>
</ul>
<h3 class="refh">Why dawn and midday</h3>
<ul class="refs">
<li><a href="https://doi.org/10.1111/gcb.12477" target="_blank" rel="noopener">Pratt et al., Global Change Biology 20:893 (2014)</a>: chaparral shrubs sampled "at predawn when plants were at their most hydrated and at midday … when their tissues would be maximally dehydrated", the same pair of times we fly.</li>
<li><a href="https://doi.org/10.5194/bg-20-1789-2023" target="_blank" rel="noopener">Humphrey and Frankenberg, Biogeosciences 20:1789 (2023)</a>: "28 % of the pre-dawn canopy water content is depleted over the course of the day", measured at a forested site in southern California, not in chaparral.</li>
<li><a href="https://doi.org/10.3390/rs11161853" target="_blank" rel="noopener">Easterday et al., Remote Sensing 11:1853 (2019)</a>: drone imagery of coyote brush separated water stress best "in the morning".</li>
<li><a href="https://gacc.nifc.gov/rmcc/predictive/fuels_fire-danger/live_fm/Live_moisture_sampling_procedures.pdf" target="_blank" rel="noopener">NIFC live fuel moisture sampling procedures</a>: "Samples should be collected between 1100 and 1600 hours", so our midday flight can be compared with agency samples.</li>
</ul>
<h3 class="refh">Why about 1 km</h3>
<ul class="refs">
<li><a href="https://www.law.cornell.edu/cfr/text/14/107.31" target="_blank" rel="noopener">14 CFR 107.31</a>: the pilot or observer must be able to "determine the unmanned aircraft's attitude, altitude, and direction of flight".</li>
<li><a href="https://doi.org/10.1016/j.apergo.2019.102898" target="_blank" rel="noopener">Li et al., Applied Ergonomics 81:102898 (2019)</a> and <a href="https://doi.org/10.3390/app10165501" target="_blank" rel="noopener">Li et al., Applied Sciences 10:5501 (2020)</a>:
small quadcopters were seen at 245–307 m, a visual angle of about 0.065°. At that angle our 2.24 m wingspan would be seen at about 2 km (our scaling, not a measurement), so 1 km leaves margin for judging which way it is pointing.</li>
</ul>
<h3 class="refh">Survey lines and overlap</h3>
<ul class="refs">
<li><a href="https://web.archive.org/web/2023/https://support.micasense.com/hc/en-us/articles/224893167" target="_blank" rel="noopener">MicaSense guidance</a>: "75% or higher overlap in both directions" for multispectral mapping, the basis of our 14 m line spacing.</li>
<li><a href="https://support.pix4d.com/hc/en-us/articles/202557459" target="_blank" rel="noopener">Pix4D image acquisition plans</a>: thermal needs "90% front and side image overlap"; dense vegetation at least 85 %. Our plan at 75 % is too sparse for the thermal camera: an open item that adds survey time.</li>
</ul>
<h3 class="refh">How the drone is sized</h3>
<ul class="refs">
<li><a href="https://doi.org/10.1016/j.jestch.2020.02.002" target="_blank" rel="noopener">Dündar, Bilici and Ünler, Eng. Sci. Tech. 23:1182 (2020)</a>: a battery VTOL with four lift rotors, sized with momentum theory for hover and cruise power for endurance, the same method as our sheets.</li>
<li><a href="https://doi.org/10.3390/aerospace9020071" target="_blank" rel="noopener">An et al., Aerospace 9:71 (2022)</a>: sizing method for lift-plus-cruise electric VTOL drones.</li>
<li>Textbooks: Raymer, Aircraft Design: A Conceptual Approach (AIAA, 2018), for drag buildup and wing CLmax; Leishman, Principles of Helicopter Aerodynamics (Cambridge, 2005), for hover momentum theory; Gundlach, Designing Unmanned Aircraft Systems (AIAA, 2014).</li>
</ul></section>
<section><h2>People we talked to</h2>
<table class="plain"><tbody>
<tr><td>A Stanford geophysics lab that flies a thermal drone at Jasper Ridge</td><td>Video call on 16 Nov about their camera and flights. Their typical flight distance and duration: still to ask.</td></tr>
<tr><td>A UNLV researcher who flew a SWIR hyperspectral camera on a drone</td><td>Offered to share what they learned setting it up and flying it.</td></tr>
<tr><td>Jasper Ridge Biological Preserve research staff</td><td>A camera bought for field work fits their student research grant; meeting to be set up. Flight permission at the preserve goes through them.</td></tr>
</tbody></table>
<p class="small">Names left out on purpose on this public page.</p></section>
<section><h2>Still to find out</h2>
<ul class="plain">
<li>How far and how long the Jasper Ridge drone flights run, from the lab that flies there.</li>
<li>Whether 15 minutes over 2 ha is enough once the thermal camera's 90 % overlap and the spot sensor's hover points are planned.</li>
<li>Whether the preserve allows take-off within 1 km of the plots we want.</li>
</ul></section>"""
leaflet = ""
mission_body += '<script type="module" src="assets/mission_map.js"></script>'
(ROOT / "docs/mission.html").write_text(page("Ridgeback mission and range", "mission.html", mission_body, leaflet, "maptable"))

# ------------------------------------------------------------------ calculations with rendered equations
def step(title, why, tex, numbers, result, where):
    sid = "step-" + title.split(".")[0]
    return (f'<section class="calc" id="{sid}"><h2>{title}</h2><p>{why}</p><div class="eq">\\[{tex}\\]</div>'
            f'<div class="eq sub">\\[{numbers}\\]</div><p class="res">{result}</p><p class="small">In the sheets: {where}</p></section>')


g = 9.80665
m = val("m_to"); W = m * g; S = 0.5
rho = val("rho_sl"); CLmax = val("CLmax"); Vs = val("Vs_sl"); K = val("K"); CD0 = val("CD0_build"); V = val("V_sl")
CL = val("CL_sl"); CD = val("CD_sl"); D = val("D_sl"); Pcr = val("Pcr_sl")
calc_body = "".join([
    '<section class="lead"><h1>Calculations</h1><p>Each step of the sizing, with the equation, our numbers and where the step lives in the sheets. Sea level, standard day, unless noted.</p></section>',
    step("1. Weight", "Everything the rotors and the wing must carry: the CAD parts plus the sensor payload.",
         r"W = m\,g", rf"W = {m:.2f}\ \text{{kg}} \times 9.81\ \text{{m/s}}^2", f"W = {W:.1f} N", sheet("02_Mass_and_CG", "Mass_CG")),
    step("2. Stall speed", "The slowest the wing can fly. The wing's maximum lift coefficient is 0.9 times the SD7037 airfoil's (Raymer).",
         r"V_s = \sqrt{\dfrac{2W}{\rho\, S\, C_{L,\max}}}", rf"V_s = \sqrt{{\dfrac{{2 \times {W:.1f}\ \text{{N}}}}{{{rho:.3f}\ \text{{kg/m}}^3 \times {S:.2f}\ \text{{m}}^2 \times {CLmax:.3f}}}}}",
         f"V<sub>s</sub> = {Vs:.1f} m/s, against the 15 m/s we wanted.", sheet("03_Aerodynamics", "Aero_Cruise")),
    step("3. Drag of the whole drone", "Summed over every component: skin friction on the wing, tail, fuselage, booms and nacelles, and pressure drag on the motors, feet and stopped propellers.",
         r"C_{D0} = \dfrac{\sum C_f\, FF\, Q\, S_{wet} + \sum C_d\, A_{front}}{S}", rf"C_{{D0}} = {CD0:.4f}",
         "The motors, landing feet and stopped propellers make about 45 % of it.", sheet("03_Aerodynamics", "Drag_Buildup")),
    step("4. Loiter speed and drag", "The drone loiters at 1.3 times the stall speed, which here is faster than its minimum-power speed.",
         r"\begin{aligned} V &= 1.3\,V_s \\ C_L &= \dfrac{2W}{\rho V^2 S} \\ C_D &= C_{D0} + K C_L^2 \\ D &= \tfrac12 \rho V^2 S\, C_D \end{aligned}",
         rf"V = {V:.1f},\quad C_L = {CL:.3f},\quad C_D = {CD0:.4f} + {K:.4f}\times{CL:.3f}^2 = {CD:.4f}",
         f"Drag D = {D:.1f} N at {V:.1f} m/s.", sheet("03_Aerodynamics", "Aero_Cruise")),
    step("5. Loiter power", f"Thrust power through the pusher (efficiency η = {val('eta_push'):.2f}, assumed), plus {val('P_av'):.0f} W for the flight electronics and the mission sensors.",
         r"P = \dfrac{D\,V}{\eta} + P_{av}", rf"P = \dfrac{{{D:.1f} \times {V:.1f}}}{{{val('eta_push'):.2f}}} + {val('P_av'):.0f}", f"P = {Pcr:.0f} W", sheet("03_Aerodynamics", "Aero_Cruise")),
    step("6. Hover power", "From T-Motor's own MN5008 test table, fitted as a power law and corrected for air density.",
         r"P_{motor} = e^{c}\, T^{k} \sqrt{\rho_{test}/\rho},\qquad P_{hover} = 4P_{motor} + P_{av}",
         rf"T = {val('Thov_sl'):,.0f}\ \text{{g per motor}},\quad k = {val('fit_k'):.3f}",
         f"P<sub>hover</sub> = {val('Phov_sl'):,.0f} W at sea level, {val('Phov_hot'):,.0f} W on a hot day at 800 m.", sheet("04_Propulsion_Battery_Energy", "Lift_Hover")),
    step("7. Thrust to weight", "Can the four rotors hold the drone steady in gusts on a hot day at 800 m? We require at least 1.5.",
         r"\dfrac{T}{W} = \dfrac{4\,T_{max}\,(V_{load}/V_{test})^2\,(\rho/\rho_{test})}{W}",
         rf"\dfrac{{T}}{{W}} = \dfrac{{4 \times {val('Tmax_hot'):.1f}\ \text{{N}}}}{{{W:.1f}\ \text{{N}}}}",
         f"T/W = {val('TW_hot'):.2f} on the hot day ({val('TW_sl'):.2f} at sea level).", sheet("04_Propulsion_Battery_Energy", "Lift_Hover")),
    step("8. Energy and flights per charge", "Usable energy keeps the cells between 95 % and 10 % charge and leaves 20 % in reserve.",
         r"E_u = E_{pack}\times 0.85 \times 0.8,\qquad n = \dfrac{E_u}{E_{hover} + E_{climb} + P\,(t_{survey} + t_{transit})}",
         rf"E_u = 648 \times 0.85 \times 0.8 = {val('E_use'):.0f}\ \text{{Wh}},\quad n = \dfrac{{{val('E_use'):.0f}}}{{{val('E_flight'):.0f}}}",
         f"{val('flights_pack'):.1f} flights per charge; loiter time {val('tloit_sl'):.0f} min.", sheet("04_Propulsion_Battery_Energy", "Mission_Energy")),
    step("9. Range", "Distance on one charge at loiter speed. Shown to make the point that it never limits us.",
         r"\text{range} = V\, t_{loiter}", rf"\text{{range}} = {V:.1f}\ \text{{m/s}} \times {val('tloit_sl') * 60:,.0f}\ \text{{s}}",
         f"{val('range_km'):.0f} km, against a 1 km operating radius.", sheet("04_Propulsion_Battery_Energy", "Mission_Energy")),
])
# design numbers (data/inputs.toml), editable on the page
INPUT_ROWS, _grp = [], None
for line in (ROOT / "data/inputs.toml").read_text().splitlines():
    mg = re.match(r"^\[(\w+)\]", line)
    if mg: _grp = mg.group(1); continue
    mk = re.match(r"^(\w+) = (.+?)\s+#\s*(.*)$", line)
    if mk:
        label, _, src = mk.group(3).partition("; ")
        unit = re.search(r"\[([^\]]+)\]\s*$", label)
        INPUT_ROWS.append(dict(group=_grp, key=mk.group(1), value=mk.group(2), label=re.sub(r"\s*\[[^\]]+\]\s*$", "", label), unit=unit.group(1) if unit else "", source=src))
(ROOT / "docs/assets/inputs.json").write_text(json.dumps(INPUT_ROWS, indent=0, ensure_ascii=False))
_tr, _last = [], None
for r_ in INPUT_ROWS:
    if r_["group"] != _last:
        _tr.append(f'<tr class="grp"><th colspan="4">{E(r_["group"].replace("_", " "))}</th></tr>'); _last = r_["group"]
    _tr.append(f'<tr data-key="{r_["key"]}"><td>{E(r_["label"])}</td><td class="num val">{E(r_["value"])}</td><td>{E(r_["unit"])}</td><td class="small">{E(r_["source"])}</td></tr>')
calc_body += f"""<section id="inputs"><h2>Design numbers behind the steps</h2>
<p>Every typed number the calculations start from. Press <b>Edit</b> at the top to change one here; saving writes it to data/inputs.toml on GitHub (a commit with your name, undoable) and recomputes every sheet and page in about two minutes.</p>
<p class="small">Source tags: [V] read on the maker's or store's page, [S] from a datasheet or listing not re-read, [C] calculated in the sheets, [A] our assumption until measured.</p>
<div class="tablewrap"><table class="parts inputs"><thead><tr><th>Number</th><th class="num">Value</th><th>Unit</th><th>Where it comes from</th></tr></thead><tbody>{"".join(_tr)}</tbody></table></div></section>"""
katex = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body)"></script>')
(ROOT / "docs/calculations.html").write_text(page("Ridgeback calculations", "calculations.html", calc_body, katex))

# ------------------------------------------------------------------ files
sheets = [("01_Overview_Requirements_Decisions", "Requirements, summary of results, decisions and why, open checks"),
          ("02_Mass_and_CG", "Mass and position of every CAD part, centre of gravity"),
          ("03_Aerodynamics", "Atmosphere, airfoil, drag of every part, loiter speed and power"),
          ("04_Propulsion_Battery_Energy", "Hover motors, pusher, battery options, energy and flights per charge"),
          ("05_Structure_and_Stability", "Spar, boom, servo and stability checks"),
          ("06_Electronics_BOM_Cost", "Electronics, connectors and wiring, full parts list with duty, ways to save")]
srows = "".join(f'<tr><td>{sheet(n)}</td><td>{E(d)}</td><td><a href="sheets/Ridgeback_{n}.xlsx">.xlsx</a></td></tr>' for n, d in sheets)
files_body = f"""
<section class="lead"><h1>Sheets, code and CAD</h1><p>Everything behind the numbers on this site. The sheets and pages are rebuilt from two plain files, so a change made there is permanent and shows up everywhere.</p></section>
<section id="edits"><h2>Recent edits</h2><p class="small">Every change to the parts and design numbers, newest first. Each one is kept in the GitHub history; while editing with the team passcode, <b>Undo</b> puts the file back as it was before that change.</p><ol class="edits" id="editlist"><li class="quiet">Loading the history…</li></ol></section>
<section id="edit"><h2>Change a value or a link</h2>
<p><b>Easiest: press Edit at the top right of any page.</b> On the drone page, pick a part and its panel turns into a form (price, shop links, size, reasons, references); on the calculations page, the design numbers become editable. With the team passcode no GitHub account is needed (<a href="{GH}/blob/main/tools/relay/SETUP.md">how the passcode relay is set up</a>); until it is set up, Edit asks for a GitHub token. Or edit the files directly:</p>
<table class="plain"><thead><tr><th>To change</th><th>Edit this file</th></tr></thead><tbody>
<tr><td>A part: price, quantity, mass, shop link, why we chose it, what it connects to</td><td><a href="{GH}/edit/main/data/parts.toml">data/parts.toml</a></td></tr>
<tr><td>A design number: requirements, air, wing, drag, motors, battery, mission (60 typed numbers)</td><td><a href="{GH}/edit/main/data/inputs.toml">data/inputs.toml</a></td></tr>
</tbody></table>
<ol class="steps"><li>Open the file (link above) and sign in to GitHub. Each line says what the number is and where it comes from.</li>
<li>Change the value and press <b>Commit changes</b>. That saves it for good, with your name and the date in the history.</li>
<li>About 2 minutes later the six sheets, every calculation and these pages are rebuilt from it. Progress: <a href="{GH}/actions">Actions</a>. If a value breaks a formula or a name is mistyped, the rebuild stops, the site keeps the old version and the Actions page says why.</li></ol>
<p class="small">Saving needs write access to the repository (ask a lead); anyone else can propose the change and a lead accepts it. Edits made inside the Google Sheets copies are not kept: the next rebuild replaces them. Numbers in the long tables (drag of each part, the motor maker's test table, connector ratings) are still in <a href="{GH}/blob/main/sheets/build_sheet.py">sheets/build_sheet.py</a>.</p></section>
<section><h2>Calculation sheets</h2>
<table class="plain"><thead><tr><th>Sheet</th><th>What it answers</th><th>Download</th></tr></thead><tbody>{srows}</tbody></table>
<p class="small">The Google Sheets live in the team Drive; ask a lead for access. The .xlsx copies here open in Excel, Numbers or Google Sheets.</p></section>
<section><h2>Code</h2>
<table class="plain"><tbody>
<tr><td><a href="https://github.com/guinterface/skyrunners-ridgeback/tree/main/sheets">sheets/</a></td><td>Builds every sheet with live formulas, splits it into the six files and checks every number.</td></tr>
<tr><td><a href="https://github.com/guinterface/skyrunners-ridgeback/tree/main/analysis">analysis/</a></td><td>Sizing sweep, spar, boom, servo, wiring, filament, duty and stability scripts.</td></tr>
<tr><td><a href="https://github.com/guinterface/skyrunners-ridgeback/tree/main/cad">cad/</a></td><td>The CAD as code (build123d): every printed part, the assembly, the payload fit.</td></tr>
<tr><td><a href="https://github.com/guinterface/skyrunners-ridgeback/tree/main/tools">tools/</a></td><td>This site: the parts list, the 3D model export and the page generator.</td></tr>
</tbody></table></section>
<section><h2>CAD files</h2>
<table class="plain"><tbody>
<tr><td><a href="cad/Ridgeback_print_pack_STL.zip">Print pack, STL (5 MB)</a></td><td>Every printed part in print orientation, with print settings.</td></tr>
<tr><td><a href="https://github.com/guinterface/skyrunners-ridgeback/releases">STEP pack for Fusion 360 (82 MB)</a></td><td>Every part and sub-assembly, attached to the latest release.</td></tr>
<tr><td><a href="assets/ridgeback.glb">3D model, GLB</a></td><td>The model on the drone page, viewable in any glTF viewer.</td></tr>
</tbody></table></section>
<section><h2>Rebuild on your own computer</h2>
<pre>pip install openpyxl formulas
tools/rebuild.sh     # sheets, checks (0 errors, split files equal the full model) and this site</pre></section>"""
(ROOT / "docs/files.html").write_text(page("Ridgeback sheets, code and CAD", "files.html", files_body))
print("site written")

# ------------------------------------------------------------------ buy list: everything to buy, from the sheets (data/buy_list.json)
BUY = json.load(open(ROOT / "data/buy_list.json"))
GROUPS = ["Aircraft", "Mission sensors", "Ground equipment", "Shipping and fees", "Mission sensors: worth adding"]
PART_BY_NAME = {p["name"]: p["id"] for p in PARTS}
buy_html, totals = [], {}
for g in GROUPS:
    rows = [b for b in BUY if b["group"] == g and b["qty"]]
    if not rows: continue
    sub = sum(b["line"] for b in rows); duty = sum(b["duty"] for b in rows); totals[g] = sub + duty
    def shop(b):
        return f'<a href="{E(b["link"])}" target="_blank" rel="noopener">{E(b["store"].split(" (")[0] or "shop")}</a>' if b["link"] else E(b["store"])
    def name(b):
        pid = b.get("id") or PART_BY_NAME.get(b["name"])
        return f'<a href="index.html#{pid}">{E(b["name"])}</a>' if pid else E(b["name"])
    tr = "".join(f'<tr><td>{name(b)}</td><td class="num">{b["qty"]:g}</td><td class="num">${b["unit"]:,.2f}</td><td class="num">${b["line"]:,.2f}</td><td>{shop(b)}</td><td class="quiet">{E(b["note"])}</td></tr>' for b in rows)
    if duty: tr += f'<tr class="sub"><td>Import duty on parts shipped from China</td><td></td><td></td><td class="num">${duty:,.2f}</td><td></td><td class="quiet">rates in Sheet 06, BOM_Cost</td></tr>'
    tr += f'<tr class="tot"><td>{E(g)}: total</td><td></td><td></td><td class="num">${sub + duty:,.2f}</td><td></td><td></td></tr>'
    buy_html.append(f'<h2 id="{g.split(":")[0].lower().replace(" ", "-")}{"-add" if ":" in g else ""}">{E(g)}</h2>'
                    + (f'<p class="small">Not in the total below: recommended before the first mission flights, still to decide.</p>' if ":" in g else "")
                    + f'<div class="tablewrap"><table class="parts buy"><thead><tr><th>Item</th><th class="num">Qty</th><th class="num">Each</th><th class="num">Line</th><th>Shop</th><th>Price from</th></tr></thead><tbody>{tr}</tbody></table></div>')
grand = sum(v for k, v in totals.items() if ":" not in k)
assert abs(grand - val("cost_every")) < 1.5, (grand, val("cost_every"))     # same total as the sheets
buy_body = f"""<section class="lead"><h1>Buy list</h1>
<p>Everything we have to buy to fly the first mission, from the calculation sheets: the aircraft, the mission sensors and the ground equipment.
Nothing comes from Sky4. Every price was read on the shop's page; the date is in the last column. Nothing has been ordered.</p>
<table class="status"><tbody>{''.join(f'<tr><td>{E(k)}</td><td class="num">${v:,.0f}</td></tr>' for k, v in totals.items() if ":" not in k)}
<tr class="tot"><td><b>Everything</b></td><td class="num"><b>${grand:,.0f}</b></td></tr></tbody></table>
<p class="small">Budget: $3,000 for the aircraft, stretch $4,000–5,000 for everything (team, 30 Oct). To change a price or a shop link, press Edit on the drone page and pick the part; this list rebuilds from it.
Not bought: a spot welder for the battery pack (borrow one from a lab first) and the ground-station laptop (a team member's, with QGroundControl, free).</p></section>
{''.join(f'<section>{h}</section>' for h in buy_html)}"""
(ROOT / "docs/buy.html").write_text(page("Ridgeback buy list", "buy.html", buy_body))
print("buy list", len(BUY), "rows, total", round(grand))
