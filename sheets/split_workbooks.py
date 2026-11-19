"""Split the single design workbook into one workbook per part of the design.

Formulas that point into a tab that lives in another workbook are re-pointed to a 'Linked_inputs' tab in the same file,
which holds that value (as computed in the full model) and says exactly where it comes from. Re-run build_sheet.py,
calc_check.py, then this script to regenerate everything consistently.
Run: $SKY_BUILD/sheetenv/bin/python split_workbooks.py
"""
import json, re
from copy import copy
from pathlib import Path
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

HERE = Path(__file__).resolve().parent
SRC = HERE / "Ridgeback_mini_VTOL_design_2026-11-17.xlsx"
VALS = json.loads((HERE / "calc_values.json").read_text())
FN = SRC.name.upper()
OUT = HERE / "split"; OUT.mkdir(exist_ok=True)

GROUPS = [
    ("01_Overview_Requirements_Decisions", "What the aircraft must do, the summary of results, every decision and why, open checks, sources.",
     ["Summary", "Requirements", "Decisions", "Open_Checks", "Sources"]),
    ("02_Mass_and_CG", "Every part's mass and position from the CAD (161 parts, grouped), payload, takeoff mass and centre of gravity.",
     ["Mass_CG"]),
    ("03_Aerodynamics", "Atmosphere, wing airfoil polar, part-by-part drag buildup, cruise/loiter aerodynamics.",
     ["Constants", "Airfoil_SD7037", "Drag_Buildup", "Aero_Cruise"]),
    ("04_Propulsion_Battery_Energy", "Hover motors (maker data), pusher, battery options, mission energy and loiter time.",
     ["Lift_Hover", "Pusher", "Battery_Options", "Mission_Energy"]),
    ("05_Structure_and_Stability", "Spar, boom, servo, stability and other checks (results of our scripts).",
     ["Structure_Stability"]),
    ("06_Electronics_BOM_Cost", "Electronics (reuse vs buy and why), every connector and solder joint, full bill of materials with duty, ways to cut cost.",
     ["Electronics", "Connectors_Wiring", "BOM_Cost", "Cost_Options"]),
]
HOME = {t: g[0] for g in GROUPS for t in g[2]}

src = openpyxl.load_workbook(SRC)
HDR = PatternFill("solid", fgColor="1F3A5F"); HFONT = Font(bold=True, color="FFFFFF")
INP = PatternFill("solid", fgColor="FFF4CC")
thin = Side(style="thin", color="C8CCD2"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")
REF_RE = re.compile(r"'([^']+)'!\$?([A-Z]+)\$?(\d+)")


def label_of(sheet, col, row):
    ws = src[sheet]
    a = ws.cell(row=int(row), column=1).value
    hdr = None
    if col in ("C", "D"):  # two-case rows: say which case
        for r in range(int(row), 0, -1):
            v = ws.cell(row=r, column=3).value
            if isinstance(v, str) and v in ("Sea level ISA", "Value", "800 m ISA+20") or ws.cell(row=r, column=1).value == "Quantity":
                hdr = ws.cell(row=r, column=ord(col) - 64).value
                break
    if not isinstance(a, str) or a.startswith("="):
        colhdr = None
        for r2 in range(int(row) - 1, 0, -1):
            cc = ws.cell(row=r2, column=ord(col) - 64)
            if cc.fill and cc.fill.fill_type and cc.fill.fgColor.rgb == "FF1F3A5F":
                colhdr = cc.value; break
        return f"{sheet} row {row}: {colhdr or col}"
    return (str(a) if a else "") + (f" [{hdr}]" if hdr and hdr != "Value" else "")


summary = {}
for name, purpose, tabs in GROUPS:
    wb = Workbook(); wb.remove(wb.active)
    # README
    rd = wb.create_sheet("README")
    rd.column_dimensions["A"].width = 28; rd.column_dimensions["B"].width = 110
    rows = [("Ridgeback mini VTOL design", f"{name.replace('_', ' ')}"), ("Website", "https://guinterface.github.io/skyrunners-ridgeback/"), ("What is in this file", purpose),
            ("Tabs", " | ".join(tabs) + " | Linked_inputs"),
            ("Colours", "Yellow = typed input with its source. Blue = formula (click the cell). Green = key result."),
            ("Linked_inputs tab", "Values this file needs from the other workbooks, copied from the full model with the exact source tab and cell. "
             "They are not live across files: regenerate all files with build_sheet.py → calc_check.py → split_workbooks.py."),
            ("All files", " | ".join(g[0] for g in GROUPS)),
            ("Source code", "sheets/ (build_sheet.py, export_mass.py, calc_check.py, split_workbooks.py)"),
            ("Date", "2026-11-17")]
    for i, (a, b) in enumerate(rows, 1):
        rd.cell(row=i, column=1, value=a).font = Font(bold=True); c = rd.cell(row=i, column=2, value=b); c.alignment = WRAP
    rd.cell(row=1, column=1).font = Font(bold=True, size=14)
    w = rd.cell(row=2, column=2); w.hyperlink = w.value; w.font = Font(color="1155CC", underline="single")
    f = rd.cell(row=len(rows) + 2, column=1, value="Other sheets"); f.font = Font(bold=True)
    l = rd.cell(row=len(rows) + 2, column=2, value="All six sheets, with links: website › Sheets, code, CAD")
    l.hyperlink = "https://guinterface.github.io/skyrunners-ridgeback/files.html"; l.font = Font(color="1155CC", underline="single")
    links = {}  # foreign ref -> local Linked_inputs cell
    li = None
    for t in tabs:
        s = src[t]; d = wb.create_sheet(t)
        for col, dim in s.column_dimensions.items():
            d.column_dimensions[col].width = dim.width
        for row in s.iter_rows():
            for c in row:
                if c.value is None and not c.has_style:
                    continue
                n = d.cell(row=c.row, column=c.column)
                v = c.value
                if isinstance(v, str) and v.startswith("="):
                    def rep(m):
                        sh, col, r = m.group(1), m.group(2), m.group(3)
                        if HOME.get(sh) == name:
                            return m.group(0)
                        key = (sh, col, r)
                        if key not in links:
                            links[key] = None
                        return f"__LINK_{sh}_{col}_{r}__"
                    v = REF_RE.sub(rep, v)
                n.value = v
                if c.has_style:
                    n.font = copy(c.font); n.fill = copy(c.fill); n.border = copy(c.border)
                    n.alignment = copy(c.alignment); n.number_format = c.number_format
                if c.hyperlink:
                    n.hyperlink = c.hyperlink.target; n.font = copy(c.font)
        for mr in s.merged_cells.ranges:
            d.merge_cells(str(mr))
        for r, dim in s.row_dimensions.items():
            if dim.height: d.row_dimensions[r].height = dim.height
    # Linked_inputs
    li = wb.create_sheet("Linked_inputs")
    for col, w in zip("ABCDE", (52, 16, 18, 24, 60)):
        li.column_dimensions[col].width = w
    for i, h in enumerate(["Value needed", "Value", "From file", "From tab › cell", "Note"], 1):
        c = li.cell(row=1, column=i, value=h); c.fill = HDR; c.font = HFONT; c.border = BOX
    r = 2
    for (sh, col, rr) in sorted(links, key=lambda k: (k[0], int(k[2]), k[1])):
        val = VALS.get(f"'[{FN}]{sh.upper()}'!{col}{rr}")
        if val is None:
            val = src[sh][f"{col}{rr}"].value
        li.cell(row=r, column=1, value=label_of(sh, col, rr)).border = BOX
        c = li.cell(row=r, column=2, value=val); c.fill = INP; c.border = BOX
        if isinstance(val, float): c.number_format = "0.0000" if abs(val) < 100 else "#,##0.0"
        li.cell(row=r, column=3, value=HOME[sh]).border = BOX
        li.cell(row=r, column=4, value=f"{sh} › {col}{rr}").border = BOX
        li.cell(row=r, column=5, value="copy of the value computed in the full model (2026-11-17)").border = BOX
        links[(sh, col, rr)] = f"Linked_inputs!$B${r}"
        r += 1
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and "__LINK_" in c.value:
                    c.value = re.sub(r"__LINK_(.+?)_([A-Z]+)_(\d+)__", lambda m: links[(m.group(1), m.group(2), m.group(3))], c.value)
    f = OUT / f"Ridgeback_{name}.xlsx"
    wb.save(f)
    summary[name] = dict(file=str(f), tabs=tabs, linked=len(links))
    print(f"{f.name}: tabs {tabs}, linked inputs {len(links)}")
json.dump(summary, open(OUT / "split_summary.json", "w"), indent=1)
