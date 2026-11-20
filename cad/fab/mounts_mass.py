"""Mass and CG change of the 11-19 electronics mounts vs the 11-03 CAD (SR3_CONFIG=mini).

Printed parts: CAD volume x density x fill from the meta files (old: $SKY_BUILD_OLD/sr3_mini_out/meta, new: $MOUNTS_OUT/meta and
$MOUNTS_OUT/build/sr3_mini_out/meta). Bought parts: purchased_mini() of the untouched copy ridgeback/cad/fab/assemble_mini.py
(old) vs this folder's (new). Reference aircraft: assembly_summary.json of the 11-03 build (8478 g, CG x 94.2) [C].
Writes $MOUNTS_OUT/mass.json. Run: SR3_CONFIG=mini cadenv/bin/python mounts_mass.py
"""
import importlib.util, json, os, sys
from pathlib import Path
os.environ.setdefault("SR3_CONFIG", "mini")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / "parts")]
OUT = Path(os.environ.get("MOUNTS_OUT", "/scratch/users/gsbonfim/skyrunners/mounts_out"))
OLD = Path(os.environ.get("SKY_BUILD_OLD", "/scratch/users/gsbonfim/skyrunners")) / "sr3_mini_out"


def metas(d):
    r = {}
    for f in Path(d).glob("*.json"):
        if f.name.startswith("_"):
            continue
        m = json.loads(f.read_text())
        bb = m["bbox"]; n = len(m.get("instances", [[0, 0, 0]]))
        c = m.get("center") or [(bb[0][i] + bb[1][i])/2 for i in range(3)]
        r[m["name"]] = (m["mass_g"]*max(n, m.get("qty", 1)), c[0])
    return r


old_p = {k: v for k, v in metas(OLD / "meta").items() if k.startswith("fuse_")}
new_p = {k: v for k, v in metas(OUT / "build/sr3_mini_out/meta").items() if k.startswith("fuse_")}
new_p.update(metas(OUT / "meta"))


def purchased(path):
    spec = importlib.util.spec_from_file_location("am_" + str(abs(hash(path))), path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    P, _ = mod.purchased_mini()
    out = {}
    for p in P:
        x = p["cg"][0] if p["solid"] is None else p["solid"].center().X
        out[p["name"]] = (p["mass_g"], x)
    return out


old_b = purchased(str(HERE.parents[2] / "ridgeback/cad/fab/assemble_mini.py"))
# that copy imports THIS folder's f_fuse (sys.path), so put the battery back where the 11-03 build had it
old_b["battery_6S6P_P50B"] = (old_b["battery_6S6P_P50B"][0], -58.0)
new_b = purchased(str(HERE / "assemble_mini.py"))
summ = json.loads((OLD / "assembly_summary.json").read_text())
M0, X0 = summ["mass_g"], summ["cg"][0]


def delta(old, new):
    rows = []
    for k in sorted(set(old) | set(new)):
        mo, xo = old.get(k, (0.0, 0.0)); mn, xn = new.get(k, (0.0, 0.0))
        if abs(mn - mo) > 0.05 or abs(mn*xn - mo*xo) > 5:
            rows.append(dict(part=k, old_g=round(mo, 1), new_g=round(mn, 1), old_x=round(xo, 1), new_x=round(xn, 1)))
    dm = sum(r["new_g"] - r["old_g"] for r in rows)
    dmx = sum(r["new_g"]*r["new_x"] - r["old_g"]*r["old_x"] for r in rows)
    return rows, dm, dmx


rp, dmp, dmxp = delta(old_p, new_p)
rb, dmb, dmxb = delta(old_b, new_b)
M1 = M0 + dmp + dmb
X1 = (M0*X0 + dmxp + dmxb)/M1
bat = old_b["battery_6S6P_P50B"][0]
res = dict(reference=dict(mass_g=round(M0, 1), cg_x=round(X0, 2), src="11-03 assembly_summary.json [C]"),
           printed=dict(rows=rp, delta_g=round(dmp, 1)), bought=dict(rows=rb, delta_g=round(dmb, 1)),
           new=dict(mass_g=round(M1, 1), cg_x=round(X1, 2), cg_shift_mm=round(X1 - X0, 2)),
           battery_move_to_restore_cg_mm=round((X0 - X1)*M1/bat, 1),
           note="Wiring not included: PM07 moved from x -130 to the nose cassette (x -200) adds ~0.3 m to each of 5 feeds [A]")
(OUT / "mass.json").write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k not in ("printed", "bought")}, indent=1))
print("printed delta", round(dmp, 1), "g; bought delta", round(dmb, 1), "g")
for r in rp + rb:
    print("  ", r)
