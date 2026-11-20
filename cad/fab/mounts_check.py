"""Fit and removal check for the electronics mounts (SR3_CONFIG=mini, 2026-11-19).

1. Installed: every mount, its electronics boxes and the airframe (new fuselage build + wing/booms/tail from the CAD mesh
   cache) - any two solids that overlap by more than TOL mm3 are reported (bonded parts touch, they should not overlap).
2. Removal: each removable group is moved along its removal path (data/mounts.json motion) in 2 mm steps; at every step the
   overlap with everything that stays is computed (manifold3d). Hatches are taken off first, as in the real order.
3. Hatch closed over the tallest item (cube top) -> clearance reported.
Inputs: $MOUNTS_OUT/step (mounts), $MOUNTS_OUT/build/sr3_mini_out/step (fuselage parts), payload_fit/mesh_cache.npz.
Writes $MOUNTS_OUT/check.json. Run: SR3_CONFIG=mini cadenv/bin/python mounts_check.py
"""
import json, os, sys
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as mf
from m_common import OUT, mesh, bx
import m_layout as L
from build123d import import_step, Box, Location
import assemble_mini as A
import f_fuse as FF

TOL = 2.0                                     # mm3
FUSE = OUT / "build/sr3_mini_out/step"
CACHE = Path(os.environ.get("MESH_CACHE", "/scratch/users/gsbonfim/skyrunners/payload_fit/mesh_cache.npz"))
_mcache = {}


def tm(solid, tol=0.15):
    return mesh(solid, tol, 0.3)


def to_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


THIN = 0.35                                   # mm: mean thickness below this = surface contact (tessellation), not a clash


def vol_overlap(a, b):
    """a, b: (trimesh, manifold). Overlap volume mm3 of a real clash (bbox prefilter). An intersection whose mean thickness
    (2 x volume / surface area) is under THIN is two faces touching (chord error of the curved shells), counted as 0."""
    (ma, Ma), (mb, Mb) = a, b
    lo = np.maximum(ma.bounds[0], mb.bounds[0]); hi = np.minimum(ma.bounds[1], mb.bounds[1])
    if (hi <= lo).any():
        return 0.0
    I = Ma ^ Mb
    v = float(I.volume())
    if v <= 0:
        return 0.0
    a_ = float(I.surface_area())
    return v if (a_ <= 0 or 2*v/a_ >= THIN) else 0.0


def item(dims, c_bottom):
    return Box(*dims).moved(Location((c_bottom[0], c_bottom[1], c_bottom[2] + dims[2]/2)))


def centre_box(dims, c):
    return Box(*dims).moved(Location(c))


def load_step(path):
    return import_step(str(path))


def entry(name, solid=None, m=None):
    if m is None:
        m = tm(solid)
    if not m.is_watertight:
        m.merge_vertices(); trimesh.repair.fix_normals(m)
    return dict(name=name, mesh=m, mf=to_mf(m) if m.is_watertight else None)


def build_scene():
    S = {}
    def add(group, name, solid=None, m=None):
        S.setdefault(group, []).append(entry(name, solid, m))
    # fuselage parts (new build), hatches go in their own groups
    for f in sorted(FUSE.glob("fuse_*.step")):
        n = f.stem
        g = {"fuse_hatch_avionics": "hatch_avionics", "fuse_hatch_battery": "hatch_battery",
             "fuse_pusher_esc_tray": "tail_panel", "fuse_servo_reg_mount": "tail_panel"}.get(n, "fixed")
        add(g, n, load_step(f))
    # mounts
    grp = {"mount_avionics_cassette": "cassette", "mount_battery_sled": "battery", "mount_belly_plate": "belly", "mount_belly_deck": "belly",
           "mount_tail_panel": "tail_panel"}
    for f in sorted((OUT / "step").glob("mount_*.step")):
        add(grp.get(f.stem, "fixed"), f.stem, load_step(f))
    # electronics on the removable mounts
    for k, (dims, c, g, tag) in L.AV_ITEMS.items():
        add("cassette", "item_" + k, item(dims, c))
    P = L.PM07
    add("cassette", "item_pm07", bx(P["x_back"] - P["dims"][0], P["x_back"], -P["dims"][1]/2, P["dims"][1]/2, P["zc"] - P["dims"][2]/2, P["zc"] + P["dims"][2]/2))
    add("battery", "item_battery", bx(L.BAT_X - L.BAT_L/2, L.BAT_X + L.BAT_L/2, -L.BAT_W/2, L.BAT_W/2, L.BAT_Z0, L.BAT_Z0 + L.BAT_H))
    for k, (dims, c, note) in L.PAYLOAD.items():
        add("belly", "item_" + k, centre_box(dims, c))
    E = FF.PUSH_ESC; R = FF.SREG
    for n, s_ in (("item_esc_pusher", E), ("item_servo_reg", R)):
        lx, ly, lz = s_["dims"]
        add("tail_panel", n, bx(s_["x"] - lx/2, s_["x"] + lx/2, -ly/2, ly/2, s_["z"], s_["z"] + lz))
    # other purchased parts (motors, lift ESCs, GPS, airspeed, servos) stay fixed
    skip = {"pixhawk_6C", "telemetry_radio", "rc_receiver", "remote_id_ruko_R111S", "power_module_PM07", "battery_6S6P_P50B",
            "esc_pusher_alpha40", "servo_regulator_PLACEHOLDER"}
    P_, _ = A.purchased_mini()
    for p in P_:
        if p["solid"] is None or p["name"] in skip or p["name"].startswith(("tube_", "rod_")):
            continue
        add("fixed", "buy_" + p["name"], p["solid"])
    # wing, booms, tail from the CAD mesh cache (11-03 build; unchanged by this work)
    for kind, tri, bb in np.load(CACHE, allow_pickle=True)["groups"]:
        if kind in ("wing", "booms", "tail"):
            t = np.asarray(tri, float)
            m = trimesh.Trimesh(vertices=t.reshape(-1, 3), faces=np.arange(len(t)*3).reshape(-1, 3), process=True)
            add("fixed", f"cad_{kind}_{len(S.get('fixed', []))}", m=m)
    return S


def moved(e, v):
    m = e["mesh"].copy(); m.apply_translation(v)
    return (m, to_mf(m) if e["mf"] is not None else None)


def overlap_list(A_, B_, v=(0, 0, 0)):
    hits = []
    for a in A_:
        if a["mf"] is None:
            continue
        ma = moved(a, v)
        for b in B_:
            if b["mf"] is None:
                continue
            o = vol_overlap(ma, (b["mesh"], b["mf"]))
            if o > TOL:
                hits.append((a["name"], b["name"], round(o, 1)))
    return hits


REMOVALS = [  # group, path [(vector unit, distance)], what is already off
    ("hatch_avionics", [((0, 0, 1), 80)], []),
    ("cassette", [((0, 0, 1), 110)], ["hatch_avionics"]),
    ("hatch_battery", [((0, 0, 1), 80)], []),
    ("battery", [((-1, 0, 0), L.SLED["slide"]), ((0, 0, 1), 120)], ["hatch_battery"]),
    ("belly", [((0, 0, -1), 100)], []),
    ("tail_panel", [((0, 0, -1), 50)], []),     # straight down (the tilted normal pushed the trays into the aft ledge)
]


def tail_n():
    (xa, za), (xb, zb) = L.OPENINGS["tail"]["a"], L.OPENINGS["tail"]["b"]
    t = np.array([xb - xa, 0, zb - za]); t /= np.linalg.norm(t)
    return np.array([t[2], 0, -t[0]])            # outward (down) normal of the panel plane


def main():
    S = build_scene()
    nonwt = [e["name"] for g in S.values() for e in g if e["mf"] is None]
    res = dict(not_watertight_skipped=nonwt)
    every = [e for g in S.values() for e in g]
    # 1. installed overlaps between groups and inside "fixed"
    hits = []
    names = list(S)
    for i, ga in enumerate(names):
        for gb in names[i:]:
            A_, B_ = S[ga], S[gb]
            for ia, a in enumerate(A_):
                for b in (B_[ia + 1:] if ga == gb else B_):
                    if a["mf"] is None or b["mf"] is None or (a["name"].startswith("cad_") and b["name"].startswith("cad_")):
                        continue
                    o = vol_overlap((a["mesh"], a["mf"]), (b["mesh"], b["mf"]))
                    if o > TOL:
                        hits.append((a["name"], b["name"], round(o, 1)))
    res["installed_overlaps"] = hits
    print("installed overlaps:", len(hits))
    for h in hits:
        print("   ", h)
    # 2. removal sweeps
    res["removal"] = {}
    for g, path, off in REMOVALS:
        stay = [e for gg, es in S.items() if gg != g and gg not in off for e in es]
        pos = np.zeros(3); worst = []
        for vec, dist in path:
            v = tail_n() if vec == "tail_n" else np.array(vec, float)
            for k in range(1, int(dist/2) + 1):
                p = pos + v*2*k
                h = overlap_list(S[g], stay, p)
                if h:
                    worst.append(dict(at_mm=[round(float(q), 1) for q in p], hits=h[:6]))
            pos = pos + v*dist
        res["removal"][g] = dict(path=[(list(np.round(tail_n(), 3)) if v == "tail_n" else v, d) for v, d in path],
                                 clear=not worst, first_hits=worst[:4], n_steps_hit=len(worst))
        print(f"removal {g:15s} clear={not worst}  steps hit={len(worst)}", worst[:1])
    # 3. clearance from the tallest cassette item to the closed hatch
    hat = next(e for e in S["hatch_avionics"])
    for k in ("cube_orange", "pm07"):
        it = next(e for e in S["cassette"] if e["name"] == "item_" + k)
        d = None
        for dz in np.arange(0, 30, 0.5):
            if overlap_list([it], [hat], (0, 0, dz)):
                d = float(dz); break
        res[f"gap_to_hatch_{k}_mm"] = d
        print(f"gap {k} -> closed avionics hatch: {d} mm (None = > 30)")
    (OUT / "check.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
