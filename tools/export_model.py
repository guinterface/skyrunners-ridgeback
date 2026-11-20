"""Export the drone as a web 3D model (GLB) with one named node per part.

Airframe (wing, fuselage, tail, booms, props) comes from the CAD mesh cache, merged per group and simplified.
Every bought part (motors, ESCs, battery, flight controller, sensors, servos...) is tessellated from the CAD solid
at its exact CAD position and kept as its own node, so the web page can highlight and pick it.
Run (CAD venv): SR3_CONFIG=mini $SKY_BUILD/cadenv/bin/python tools/export_model.py
"""
import json, os, sys
from pathlib import Path
import numpy as np, trimesh
FAB = Path(__file__).resolve().parents[1] / "cad/fab"
sys.path[:0] = [str(FAB), str(FAB.parent)]
from assemble_mini import purchased_mini
OUT = Path(__file__).resolve().parents[1] / "docs/assets"
CACHE = Path(os.environ.get("MESH_CACHE", os.path.join(os.environ.get("SKY_BUILD", "build"), "payload_fit/mesh_cache.npz")))  # from cad/fab/render_payload.py
S = 1e-3  # mm -> m

scene = trimesh.Scene()
groups = list(np.load(CACHE, allow_pickle=True)["groups"])
# the two top hatches are drawn (and moved) by docs/assets/mounts.glb (tools/export_mounts.py): leave them out here
META = CACHE.parent.parent / "sr3_mini_out/meta"
HATCH_BB = [json.loads((META / f"{h}.json").read_text())["bbox"] for h in ("fuse_hatch_avionics", "fuse_hatch_battery") if (META / f"{h}.json").exists()]
same_bb = lambda bb, h: all(abs(bb[i] - v) < 1.5 for i, v in enumerate((h[0][0], h[1][0], h[0][1], h[1][1], h[0][2], h[1][2])))
by = {}
skipped = 0
for kind, tri, bb in groups:
    if kind in ("purchased", "battery"):      # these come from the named CAD solids below
        continue
    if kind in ("fuselage", "shell") and any(same_bb(bb, h) for h in HATCH_BB):
        skipped += 1; continue
    by.setdefault(kind, []).append(np.asarray(tri, float))
COL = {"wing": [222, 224, 218, 255], "fuselage": [222, 224, 218, 255], "shell": [222, 224, 218, 255], "tail": [222, 224, 218, 255],
       "booms": [60, 62, 64, 255], "prop": [120, 124, 128, 140]}
stats = {}
for kind, tris in by.items():
    t = np.concatenate(tris) * S
    m = trimesh.Trimesh(vertices=t.reshape(-1, 3), faces=np.arange(len(t) * 3).reshape(-1, 3), process=True)
    target = {"booms": 12000, "wing": 14000, "fuselage": 8000, "shell": 8000, "tail": 5000, "prop": 2000}.get(kind, 4000)
    if len(m.faces) > target:
        m = m.simplify_quadric_decimation(face_count=target)
    m.visual.face_colors = COL.get(kind, [200, 200, 200, 255])
    scene.add_geometry(m, node_name=f"airframe:{kind}", geom_name=f"airframe:{kind}")
    stats[kind] = len(m.faces)

P, _ = purchased_mini()
parts = []
for p in P:
    if p["solid"] is None:
        continue
    v, f = p["solid"].tessellate(0.5, 0.5)
    V = np.array([[q.X, q.Y, q.Z] for q in v]) * S
    m = trimesh.Trimesh(vertices=V, faces=np.array(f), process=True)
    m.visual.face_colors = [150, 150, 150, 255]
    scene.add_geometry(m, node_name=f"part:{p['name']}", geom_name=f"part:{p['name']}")
    c = p["solid"].center()
    parts.append(dict(node=p["name"], group=p["group"], mass_g=p["mass_g"], center_mm=[round(c.X, 1), round(c.Y, 1), round(c.Z, 1)]))
OUT.mkdir(parents=True, exist_ok=True)
scene.export(OUT / "ridgeback.glb")
json.dump(dict(airframe_faces=stats, parts=parts, frame="CAD: x aft, y right, z up, metres in the GLB"),
          open(OUT.parent.parent / "data/model_nodes.json", "w"), indent=1)
print("glb", (OUT / "ridgeback.glb").stat().st_size // 1024, "KB;", len(parts), "parts;", stats, "; hatches left to mounts.glb:", skipped)
