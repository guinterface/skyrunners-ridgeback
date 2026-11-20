"""Where can carbon rails run inside the Ridgeback Scout fuselage? (carbon redesign, 2026-11-20)

analysis/cf_redesign.py fuselage_cf() assumes a carbon FRAME: four 8/6 carbon tube rails, 1 mm carbon bulkheads, a 1.6 mm
floor under the battery and payload, and a non-structural 3 mm foam + film skin. The current internal layout was drawn for
a printed load-carrying shell (cad/fab/m_layout.py, f_fuse.py MINI block), so this script maps, at every 5 mm along the
fuselage, the cross-section area a rail centre may use, and tests candidate rail paths (straight segments between
bulkheads) against it. Read-only use of the layout values: they are copied here with their source lines, nothing in
cad/fab is imported or changed (cad/fab has unreviewed edits in progress).

Keep-outs (y, z rectangles over an x range; all mm, aircraft frame x aft, y right, z up):
  * skin: rail centre at least SKIN_T + R + MARGIN inside the outer shape (f_fuse.py MINI station table _st, superellipse
    exponent design.fuse_n);
  * top hatches (m_layout OPENINGS avionics x -330..-176, battery -164..-3): shell removed above z -30, so a rail there must
    sit at z <= -30 - R, outside the lift-out width;
  * battery 140 x 135 x 75 on its sled, lifted out through the battery hatch: |y| <= 67.5 + 2, z >= -100 (tray top), x -164..-3;
  * avionics cassette lifted out through its hatch: |y| <= 69, z >= -70, x -330..-176 [A from CAS deck = clear opening - 2];
  * belly sensor plate, removed downward: shell removed below z -150 (+2.5 rim), x 38.5..186.5; payload deck + sensors
    |y| <= 60, z -150..-77, x 72..168;
  * tail-cone panel: removed below the plane through (x 362, z -118) and (x 515, z -86.5), x 362..515;
  * pusher ESC + servo regulator: |y| <= 17, z -112..-84, x 370..505.
Run: python3 cad/cf/fuse_rails.py  (needs numpy, scipy, shapely, matplotlib) -> cad/out/cf_fuse/rails.png, rails.json
"""
import json, math
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cad/out/cf_fuse"; OUT.mkdir(parents=True, exist_ok=True)

# f_fuse.py MINI station table (x, width, height, z top) and design.py mini values
FUSE_W, FUSE_H, PUSHER_Z, FUSE_X1 = 170.0, 165.0, -80.0, 560.0
ST = np.array([(-380.0, 40.0, 40.0, -55.0), (-355.0, 110.0, 100.0, -15.0), (-310.0, 150.0, 145.0, -3.0), (-250.0, 165.0, 160.0, 0.0),
               (-180.0, FUSE_W, FUSE_H, 0.0), (40.0, FUSE_W, FUSE_H, 0.0), (280.0, FUSE_W, FUSE_H, 0.0),
               (380.0, 140.0, 135.0, 0.0), (460.0, 100.0, 95.0, -20.0), (520.0, 75.0, 70.0, -40.0), (FUSE_X1, 58.0, 58.0, PUSHER_Z + 29.0)])
_W, _H, _ZT = (PchipInterpolator(ST[:, 0], ST[:, i]) for i in (1, 2, 3))
FUSE_N, FUSE_N_MID, FUSE_MID_X = 2.4, 3.0, (-180.0, 280.0)        # design.py


def fuse_n(x):
    a, b = FUSE_MID_X
    if a <= x <= b: return FUSE_N_MID
    dd = (a - x) if x < a else (x - b)
    return max(FUSE_N, FUSE_N_MID - (FUSE_N_MID - FUSE_N) * min(1.0, dd / 250.0))


def section(x, k=360):
    w, h, zt, n = float(_W(x)), float(_H(x)), float(_ZT(x)), fuse_n(x)
    a, b = w / 2, h / 2; zc = zt - h / 2; e = 2.0 / n
    t = np.linspace(0, 2 * np.pi, k, endpoint=False)
    return Polygon(np.stack([a * np.sign(np.cos(t)) * np.abs(np.cos(t)) ** e, zc + b * np.sign(np.sin(t)) * np.abs(np.sin(t)) ** e], 1)).buffer(0)


R_RAIL, SKIN_T, MARGIN = 4.0, 3.0, 1.0           # 8/6 tube; 3 mm foam skin [cf_redesign]; build margin [A]
BIG = 500.0
KEEP = [  # (name, x0, x1, polygon in (y, z))
    ("top hatch, avionics", -330.0, -176.0, box(-BIG, -30.0, BIG, BIG)),
    ("top hatch, battery", -164.0, -3.0, box(-BIG, -30.0, BIG, BIG)),
    ("battery lift-out", -164.0, -3.0, box(-69.5, -100.0, 69.5, BIG)),
    ("avionics cassette lift-out", -330.0, -176.0, box(-69.0, -70.0, 69.0, BIG)),
    ("belly plate opening", 38.5, 186.5, box(-BIG, -BIG, BIG, -150.0 + 2.5)),
    ("payload deck + sensors", 72.0, 168.0, box(-60.0, -150.0, 60.0, -77.0)),
    ("pusher ESC + regulator", 370.0, 505.0, box(-17.0, -112.0, 17.0, -84.0)),
]


def tail_panel(x):
    if not 362.0 <= x <= 515.0: return None
    z = -118.0 + (x - 362.0) * (-86.5 + 118.0) / (515.0 - 362.0)
    return box(-BIG, -BIG, BIG, z + 4.0)                       # + rim 4


def free(x):
    """Area where a rail CENTRE may be at station x."""
    F = section(x).buffer(-(SKIN_T + R_RAIL + MARGIN))
    ks = [p for n, a, b, p in KEEP if a <= x <= b]
    tp = tail_panel(x)
    if tp is not None: ks.append(tp)
    if ks: F = F.difference(unary_union(ks).buffer(R_RAIL + MARGIN))
    return F


# candidate layout: bulkhead stations and rail corner points (y, z) at each; straight between them [design choice, iterate]
BULKHEADS = {"F1": -330.0, "F2": -170.0, "F3": 35.0, "F4": 190.0, "F5": 362.0, "FW": 556.0}
RAILS = {
    # side rails at mid height: below the hatch plane, outside the battery and cassette, inside the skin
    "side": {"F1": (58.0, -86.0), "F2": (74.8, -80.0), "F3": (76.0, -80.0), "F4": (76.0, -80.0), "F5": (52.0, -78.0), "FW": (15.0, -77.0)},
    # bottom rails: above the belly opening, outside the payload deck; end at F5 where the tail panel starts
    "bottom": {"F1": (36.0, -118.0), "F2": (55.0, -136.0), "F3": (66.5, -132.0), "F4": (66.5, -132.0), "F5": (50.0, -120.0)},
}


def rail_path(pts):
    names = [n for n in BULKHEADS if n in pts]
    return [(BULKHEADS[n], *pts[n]) for n in names]


def check(path, step=5.0):
    """Worst clearance (mm, negative = inside a keep-out or the skin) along a rail path, and where."""
    worst = (1e9, None)
    for (xa, ya, za), (xb, yb, zb) in zip(path, path[1:]):
        for x in np.arange(xa, xb + 1e-6, step):
            f = (x - xa) / (xb - xa); y, z = ya + f * (yb - ya), za + f * (zb - za)
            F = free(x); p = Point(y, z)
            c = (F.exterior.distance(p) if F.geom_type == "Polygon" else min(g.exterior.distance(p) for g in F.geoms)) \
                if (not F.is_empty and F.contains(p)) else -(F.distance(p) if not F.is_empty else 99.0)
            if c < worst[0]: worst = (c, (round(x, 1), round(y, 1), round(z, 1)))
    return worst


def bending_check(n_g=4.0):
    """Open-U nose bay (x -330..35, nothing above z -80): bending at F3 (front wing bolts, x 35) under a hard landing.
    The fuselage hangs from the wing (legs are on the booms), so everything forward of F3 is a cantilever.
    Masses [A]: battery 2.72 kg at x -58 (m_layout BAT_X, sheet 02), avionics cassette ~0.60 kg at x -253, nose skin and
    frame ~0.20 kg at x -200. Rails 8/6 carbon tube, E 100 GPa, strength 600 MPa compression [A typical pultruded/roll-wrapped];
    floor ignored (conservative)."""
    loads = [(2.72, -58.0), (0.60, -253.0), (0.20, -200.0)]
    M = n_g * 9.81 * sum(m * (35.0 - x) / 1000 for m, x in loads)            # N m
    A = math.pi / 4 * (8 ** 2 - 6 ** 2); I_t = math.pi / 64 * (8 ** 4 - 6 ** 4)
    zs = [RAILS["side"]["F3"][1]] * 2 + [RAILS["bottom"]["F3"][1]] * 2
    zn = sum(zs) / 4; I = sum(A * (z - zn) ** 2 + I_t for z in zs)               # mm4
    c = max(abs(z - zn) for z in zs); sigma = M * 1000 * c / I                    # MPa
    F_rail = sigma * A; L = BULKHEADS["F3"] - BULKHEADS["F2"]
    P_cr = math.pi ** 2 * 100e3 * I_t / L ** 2
    return dict(n_g=n_g, M_Nm=round(M, 1), I_mm4=round(I), sigma_MPa=round(sigma, 1), strength_margin=round(600 / sigma, 0),
                rail_force_N=round(F_rail), euler_N=round(P_cr), buckling_margin=round(P_cr / F_rail, 1), span_mm=L)


def main():
    bc = bending_check()
    print(f"open-U nose bay at F3, {bc['n_g']:.0f} g landing: M {bc['M_Nm']} N m, rail stress {bc['sigma_MPa']} MPa (margin {bc['strength_margin']:.0f}), "
          f"rail force {bc['rail_force_N']} N vs Euler {bc['euler_N']} N over {bc['span_mm']:.0f} mm (margin {bc['buckling_margin']})")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    res = {}
    for name, pts in RAILS.items():
        P = rail_path(pts); c, where = check(P)
        L = sum(math.dist(a, b) for a, b in zip(P, P[1:]))
        res[name] = dict(points=P, worst_clearance_mm=round(c, 1), at=where, length_each_mm=round(L))
        print(f"{name:7s} rails x2: length {L:.0f} mm each, worst clearance {c:+.1f} mm at {where}")
    tot_len = 2 * sum(r["length_each_mm"] for r in res.values())
    g = tot_len / 10 * math.pi / 4 * (0.8 ** 2 - 0.6 ** 2) * 1.55
    print(f"total rail length {tot_len/1000:.2f} m (cf_redesign assumes 4 x 0.94 = 3.76 m), mass {g:.0f} g")
    stations = [-330, -250, -170, -80, 35, 120, 190, 280, 362, 440, 520]
    fig, axs = plt.subplots(2, 6, figsize=(16, 6.2)); axs = axs.ravel()
    for ax, x in zip(axs, stations):
        S = section(x); ax.fill(*S.exterior.xy, color="#eee"); ax.plot(*S.exterior.xy, color="#999", lw=0.8)
        F = free(x)
        for gg in getattr(F, "geoms", [F]):
            if not gg.is_empty: ax.fill(*gg.exterior.xy, color="#cfe8cf")
        for n, a, b, p in KEEP:
            if a <= x <= b:
                q = p.intersection(S)
                for h in getattr(q, "geoms", [q]):
                    if not h.is_empty and h.geom_type == "Polygon": ax.fill(*h.exterior.xy, color="#f4c7c3", alpha=0.8)
        tp = tail_panel(x)
        if tp is not None:
            q = tp.intersection(S)
            if not q.is_empty: ax.fill(*q.exterior.xy, color="#f4c7c3", alpha=0.8)
        for name, pts in RAILS.items():
            P = rail_path(pts)
            for (xa, ya, za), (xb, yb, zb) in zip(P, P[1:]):
                if xa <= x <= xb:
                    f = (x - xa) / (xb - xa); y, z = ya + f * (yb - ya), za + f * (zb - za)
                    for sy in (1, -1):
                        ax.add_patch(plt.Circle((sy * y, z), R_RAIL, color="#1f4e79"))
        ax.set_aspect("equal"); ax.set_xlim(-95, 95); ax.set_ylim(-175, 10); ax.set_title(f"x {x}", fontsize=9); ax.tick_params(labelsize=7)
    axs[-1].axis("off")
    axs[-1].text(0, 0.5, "grey: fuselage section\ngreen: where a rail centre may go\nred: keep-outs (hatches, battery,\n  cassette, belly plate, payload,\n  tail panel, ESC)\nblue: 8 mm carbon rails\ny across, z up, mm", fontsize=9, va="center")
    fig.suptitle("Carbon fuselage frame: free space for the rails at each station (cad/cf/fuse_rails.py)", fontsize=11)
    fig.tight_layout(); fig.savefig(OUT / "rails.png", dpi=120)
    json.dump(dict(rails=res, total_length_m=tot_len / 1000, mass_g=g, bulkheads=BULKHEADS, bending=bc), open(OUT / "rails.json", "w"), indent=1)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------ bulkhead DXFs (F1, F2, F5, firewall; F3/F4 wait for the wing interface)
RING_W, BOSS, HOLE_D = 10.0, 3.0, 8.2       # ring width; carbon left round each rail hole; 8/6 rail + 0.2 bond gap [A]
BH_T = {"F1": 1.0, "F2": 1.0, "F5": 1.0, "FW": 2.0}    # mm plate; firewall 2 mm for the pusher [A]


def bulkhead(fid):
    x = BULKHEADS[fid]
    outer = section(x).buffer(-SKIN_T)                               # the foam skin wraps the bulkhead edge
    pts = [(sy * p[0], p[1]) for n, r in RAILS.items() if fid in r for p in [r[fid]] for sy in (1, -1)]
    if fid == "FW":
        ring = outer                                                 # solid firewall: pusher motor bolts to it (pattern MEASURE)
    else:
        ring = outer.difference(outer.buffer(-RING_W))
    from shapely.ops import nearest_points
    def boss(p):                          # boss round the rail hole, joined to the ring by a web as wide as the boss
        c = Point(p).buffer(HOLE_D / 2 + BOSS, 48)
        q = nearest_points(outer.exterior, Point(p))[0]
        return unary_union([c, Point(q.x, q.y).buffer(HOLE_D / 2 + BOSS, 48)]).convex_hull
    bosses = unary_union([boss(p) for p in pts]).intersection(outer)
    B = unary_union([ring, bosses])
    for p in pts:
        B = B.difference(Point(p).buffer(HOLE_D / 2, 48))
    return B.buffer(0), pts


def write_bulkheads():
    import ezdxf
    rows = []
    for fid in BH_T:
        B, pts = bulkhead(fid)
        doc = ezdxf.new("R2010"); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
        for g in getattr(B, "geoms", [B]):
            msp.add_lwpolyline(list(g.exterior.coords)[:-1], close=True)
            for r in g.interiors:
                c = Polygon(r).centroid
                if any(abs(Point(p).distance(c)) < 0.1 for p in pts): msp.add_circle((c.x, c.y), HOLE_D / 2)
                else: msp.add_lwpolyline(list(r.coords)[:-1], close=True)
        doc.saveas(OUT / f"bulkhead_{fid}.dxf")
        x0, z0, x1, z1 = B.bounds
        web = min(B.exterior.distance(Point(p)) - HOLE_D / 2 for p in pts)
        rows.append(dict(id=fid, x=BULKHEADS[fid], t_mm=BH_T[fid], size_mm=(round(x1 - x0, 1), round(z1 - z0, 1)),
                         mass_g=round(B.area * BH_T[fid] / 1000 * 1.55, 1), one_region=B.geom_type == "Polygon", min_web_mm=round(web, 2)))
    return rows


if __name__ == "__main__":
    for r in write_bulkheads():
        print(r)
