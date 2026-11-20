"""Export per-part mass + CG rows for the mini VTOL, same method as assemble.py (printed meta centers + purchased_mini())."""
import json, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad/fab"))
sys.path.insert(0, str(ROOT / "cad"))
import numpy as np
OUT = Path(os.environ.get("SR3_OUT", os.path.join(os.environ.get("SKY_BUILD", "build"), "sr3_mini_out")))  # CAD build output folder
rows = []
for f in sorted((OUT / "meta").glob("*.json")):
    if f.name.startswith("_job"): continue
    m = json.loads(f.read_text())
    for (dx, dy, dz) in m["instances"]:
        c = np.array(m["center"]) + [dx, dy, dz]
        rows.append(dict(name=m["name"], group=m["group"], kind=m["process"], material=m.get("material"), mass_g=m["mass_g"], cg=[float(v) for v in c]))
from assemble_mini import purchased_mini
P, cut = purchased_mini()
for p in P:
    if p["solid"] is not None:
        c = p["solid"].center(); cg = [c.X, c.Y, c.Z]
    else:
        cg = list(p["cg"])
    rows.append(dict(name=p["name"], group=p["group"], kind="bought", material=None, mass_g=float(p["mass_g"]), cg=[float(v) for v in cg]))
# printed electronics mounts (cad/fab/m_*.py, built by cad/fab/build_mounts.sh into $MOUNTS_OUT): mass from their meta, CG from their STEP
MD = os.environ.get("MOUNTS_OUT")
if MD:
    from build123d import import_step
    ctr = lambda solid: np.array([solid.center().X, solid.center().Y, solid.center().Z])
    esc = {p["name"]: ctr(p["solid"]) for p in P if p["name"].startswith("esc_alpha40_") and p["solid"] is not None}
    for f in sorted((Path(MD) / "meta").glob("mount_*.json")):
        m = json.loads(f.read_text()); c = ctr(import_step(str(Path(MD) / "step" / f"{m['name']}.step")))
        offs = [esc[k] - esc["esc_alpha40_0"] for k in sorted(esc)] if m["name"] == "mount_esc_cradle" and "esc_alpha40_0" in esc else [np.zeros(3)]
        for o in offs:
            rows.append(dict(name=m["name"], group="mounts", kind="print", material=m.get("material"), mass_g=float(m["mass_g"]), cg=[float(v) for v in c + o]))
M = sum(r["mass_g"] for r in rows); cg = sum(r["mass_g"]*np.array(r["cg"]) for r in rows)/M
print(len(rows), "rows", round(M, 1), "g, CG", np.round(cg, 1))
import design as d
print("design CG_X", d.CG_X, "battery", d.BATTERY)
(Path(__file__).resolve().parent / "mass_rows.json").write_text(json.dumps(dict(rows=rows, cut=cut), indent=0, default=float))
