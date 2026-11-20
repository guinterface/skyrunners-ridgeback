"""Carbon wing ribs for the Ridgeback Scout carbon redesign (2026-11-20): flat 1.0 mm carbon plate, waterjet-cut by
SendCutSend from the DXF files written here.

User (11-20): "THE WING SHOUL BE MOSTLY CF!!!" -> built-up wing (analysis/cf_redesign.py): tube spar, 29 ribs, 3 mm carbon
rod leading edge, flush 26 x 0.5 mm carbon strip trailing edge, 6/4 rear tubes kept, foam-core ailerons, film skin.

Geometry is the CURRENT mini wing, the same stations as cad/fab/f_wing.py (SR3_CONFIG=mini): SD7037, root 270.6 /
tip 175.9 mm, 2.0 deg incidence, 1.5 deg washout from y 390 to the tip, 10 deg tip polyhedral outboard of y 870,
spar tubes 21/19 | 17/15 | 13/11 at x 68, rear 6/4 tubes (x 160 to y 358; then x 160 -> 97 from y 360 to 860),
ailerons y 503..868 hinged at f_wing.HINGE_X. Hard ribs at y 0, 34.5, 390, 501, 800, 870, 1120, filled so no bay is over
100 mm: 15 stations per half, 29 ribs (cf_redesign.py now reads this count and the rib mass from ribs.json).

Each rib, drawn in its own plane (chord along x, thickness along y, leading edge at 0):
  * outline = airfoil, nose cut back to a 3.2 mm half-round notch that cradles the 3 mm leading-edge rod;
  * SPLIT at the spar axis into a front and a rear piece, each with a half-round cradle bonded to the tube. Why: a 21 mm
    tube in a 255-270 mm SD7037 leaves only 1.0-1.4 mm of rib above and below a closed hole (< 2 mm SendCutSend web),
    and one-piece ribs could not be threaded onto spar tubes that are already joined and bent at the tip break.
    The cradle arms are trimmed back to 2 mm thickness; 'spar contact' = share of the half circle still bonded;
  * tail: the rib stops where it is 2.5 mm deep; a 0.5 mm deep x 8 mm long rebate in its lower edge takes a 26 x 0.5 mm
    carbon strip flush with the lower surface, running back to the true trailing edge (a 1 mm strip would leave only
    ~0.2 mm of rib; the 0.5 mm sheet is not stocked by HaoZhong: parts.toml cf_te_sheet [A]);
  * holes: rear tube 6.2 mm (6/4 + bond gap) at the axis position f_wing.py uses, moved into the rib frame
    (incidence + washout undone); the spar axis likewise;
  * lightening cut-outs: everything more than EDGE mm inside the outline and RING mm away from each hole, split by
    vertical bars every BAR_PITCH mm, corners rounded;
  * in the aileron span the rear piece stops HINGE_GAP/2 ahead of the hinge line and a separate aileron rib starts
    behind it (aileron hinge / spar detail still open);
  * the tip rib at y 1120 is a closing rib: the 13/11 tip tube ends at y 1105.
Status 11-20 after the independent review (all MUST/SHOULD geometry fixes applied):
  * every part is under SendCutSend's 1 x 2 in minimum part size (ribs are 16-25 mm tall): cut them nested in a tabbed
    frame if SendCutSend accepts that, or use another waterjet / CNC router shop (decision registered);
  * aileron ribs fail the 2 mm web around the 3 mm torque rod outboard (aileron only 6-9 mm deep): ailerons become
    foam-core panels like the tail (decision taken 11-20, reversible); their DXFs are kept only for reference;
  * the 3 mm leading-edge rod in a notch gives a faceted nose on a low-Re section: D-box (thin carbon skin LE to spar,
    also settles the twist question) vs shaped foam LE (decision registered);
  * still missing: cap strips (~3 mm) on the rib edges for the film, an assembly jig for incidence/washout, collars or
    fillets at the 1 mm rib-to-tube bonds.
Checks against SendCutSend's carbon rules [V sendcutsend.com, read 11-19]: hole >= 0.125 in (3.18 mm) and webs >= 2 x
thickness (2.0 mm). Prints a summary and writes cad/out/cf_ribs/{*.dxf, ribs.png, ribs.json}.
Run: cad/run.sh cad/cf/ribs.py   (or the cadenv python; needs SR3_CONFIG=mini, set below)
"""
import json, math, os, sys
from pathlib import Path
os.environ["SR3_CONFIG"] = "mini"
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad"))
import numpy as np
import design as d
import aerosandbox as asb
import ezdxf
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union

OUT = ROOT / "cad/out/cf_ribs"; OUT.mkdir(parents=True, exist_ok=True)

T = 1.0                     # mm plate (SendCutSend 0.040 in carbon)
RHO = 1.55                  # g/cm3 [A], same as cf_redesign.py RHO_CF
MIN_HOLE, MIN_WEB = 3.18, 2.0 * T
EDGE, RING, BAR, BAR_PITCH, R_CORNER = 4.0, 4.0, 4.0, 40.0, 2.0     # mm [A, design choices]
LE_ROD = 3.0
TE_T, TE_REB = 0.5, 8.0     # trailing-edge strip thickness, flush rebate length in the rib's lower edge (reviewer 11-20) [A]
MIN_PART = (25.4, 50.8)     # SendCutSend minimum part size 1 x 2 in [V sendcutsend.com carbon fiber page, read 11-20 by reviewer]
HOLE_GAP = 0.2              # diameter clearance for bonded tubes
HINGE_GAP = 3.5             # f_wing.AIL_GAP

SPAR_X = 68.0                                                   # f_wing.py mini
# widest tube at y; the 13/11 tip tube is EXTENDED from y 1105 (printed-wing depth limit) to 1118 so the tip rib holds it:
# the carbon wing is 16.6 mm deep there at x 68 (reviewer 11-20) [C]
TUBES = [(0.0, 200.0, d.INNER_SPAR[0]), (200.0, 720.0, d.OUTER_SPAR[0]), (720.0, 1120.0, d.TIP_SPAR_T[0])]
ROD_C_X, ROD_C_HALF = 160.0, 358.0
ROD_O = ((160.0, 360.0), (97.0, 860.0))
AIL = (503.0, 868.0)
_ym = sum(AIL) / 2
HINGE_X = d.le_x(_ym) + (1 - d.CONTROL_CHORD_FRAC) * d.chord_at(_ym)
HALF = d.SPAN / 2
# hard ribs where something happens (reviewer 11-20), then filled so no bay is longer than PITCH_MAX
SERVO_Y = 800.0                                                 # f_wing.py MINI SERVO_Y (aileron horn)
HARD = {0.0: "centre", 34.5: "bolt rib (wing-bolt sleeves at x 35 and 190 bond to its outboard face)",
        d.BOOM_Y: "boom rib (boom clamp station)", 501.0: "aileron bay inner end", SERVO_Y: "servo / horn rib",
        d.TIP_BREAK_Y: "tip break (spar joint, 10 deg polyhedral, aileron bay outer end)", HALF: "tip rib"}
PITCH_MAX = 100.0
def _stations():
    hs = sorted(HARD); ys = []
    for a, b in zip(hs, hs[1:]):
        n = math.ceil((b - a) / PITCH_MAX); ys += [a + (b - a) * k / n for k in range(n)]
    return ys + [hs[-1]]
YS = _stations()
AIL_END_RIBS = (AIL[0], AIL[1])                                  # aileron-only end ribs at y 503 and 868

AF = np.asarray(asb.Airfoil(d.AIRFOIL).repanel(n_points_per_side=120).coordinates)


def station(y):
    out = max(0.0, (y - d.CENTER_HALF) / (HALF - d.CENTER_HALF))
    return d.chord_at(y), d.WING_INCIDENCE_DEG - d.WASHOUT_DEG * out, d.le_x(y)


def to_aircraft(px, pz, y):
    """Rib-frame (x along chord, z up) -> aircraft x, z relative to the leading edge height of that station."""
    c, inc, xle = station(y); t = math.radians(inc)
    return px * math.cos(t) + pz * math.sin(t) + xle, -px * math.sin(t) + pz * math.cos(t)


def to_rib(x, z, y):
    c, inc, xle = station(y); t = math.radians(inc); x = x - xle
    return x * math.cos(t) - z * math.sin(t), x * math.sin(t) + z * math.cos(t)


def section(y):
    return Polygon(AF * station(y)[0]).buffer(0)


def mid_depth_aircraft(y, x):
    """Mid-height (aircraft z, relative to the station's LE) of the section at aircraft x."""
    xs, zs = to_aircraft(AF[:, 0] * station(y)[0], AF[:, 1] * station(y)[0], y)
    P = Polygon(np.stack([xs, zs], 1)).buffer(0)
    seg = LineString([(x, -500), (x, 500)]).intersection(P)
    b = seg.bounds
    return 0.5 * (b[1] + b[3])


# spar axis height: f_wing.py ZS = mean of mid-depth at y 0 and y 720 (minus 0.18 mm); our z is relative to each station's
# leading edge, which f_wing places at Z_LE_ROOT + polyhedral, so the same straight axis is Z_LE-relative here [C].
ZS = 0.5 * (mid_depth_aircraft(0.0, SPAR_X) + mid_depth_aircraft(720.0, SPAR_X)) - 0.18


def holes(y):
    """[(name, x_rib, z_rib, diameter)] for a rib at span y."""
    H = []
    od = next((od for a, b, od in TUBES if a - 1e-6 <= y <= b + 1e-6), None)
    if od is not None:
        H.append(("spar", *to_rib(SPAR_X, ZS, y), od + HOLE_GAP))
    if y <= ROD_C_HALF:
        xr = ROD_C_X; zr = 0.5 * (mid_depth_aircraft(0.0, xr) + mid_depth_aircraft(ROD_C_HALF, xr))
        H.append(("rear_rod", *to_rib(xr, zr, y), d.REAR_ROD + HOLE_GAP))
    elif ROD_O[0][1] <= y <= ROD_O[1][1]:
        # straight tube between its end mid-depths, as f_wing.py:463 draws it (not the local mid-depth: up to 0.35 mm off)
        (x0, y0), (x1, y1) = ROD_O; f = (y - y0) / (y1 - y0)
        xr = x0 + (x1 - x0) * f
        zr = mid_depth_aircraft(y0, x0) + (mid_depth_aircraft(y1, x1) - mid_depth_aircraft(y0, x0)) * f
        H.append(("rear_rod", *to_rib(xr, zr, y), d.REAR_ROD + HOLE_GAP))
    if AIL[0] <= y <= AIL[1]:
        # 3 mm carbon torque rod in the aileron (f_wing.py make_aileron): x at 22 % of the control chord behind the hinge
        c_m = station(_ym)[0]; xr = HINGE_X + HINGE_GAP / 2 + 0.22 * c_m * d.CONTROL_CHORD_FRAC
        za, zb = mid_depth_aircraft(AIL[0] + 1, xr), mid_depth_aircraft(AIL[1] - 1, xr)
        H.append(("torque_rod", *to_rib(xr, za + (zb - za) * (y - AIL[0] - 1) / (AIL[1] - AIL[0] - 2), y), 3.0 + HOLE_GAP))
    return H


def rounded(P, r):
    return P.buffer(-r, join_style=1).buffer(r, join_style=1)


def make_rib(y, aileron_only=False):
    c = station(y)[0]
    P = section(y)
    # nose: cut back where the section is LE_ROD thick, leave a notch the rod sits in
    xs = np.linspace(0, 0.1 * c, 400)
    def thick(x):
        s = LineString([(x, -100), (x, 100)]).intersection(P); return 0 if s.is_empty else s.bounds[3] - s.bounds[1]
    x_nose = next(x for x in xs if thick(x) >= LE_ROD + 2 * MIN_WEB)
    zc = 0.5 * sum(LineString([(x_nose, -100), (x_nose, 100)]).intersection(P).bounds[1::2])
    P = P.difference(box(-10, -100, x_nose, 100))
    P = P.difference(Point(x_nose, zc).buffer(max(LE_ROD + 0.2, MIN_HOLE + 0.02) / 2, 32))   # half-round cradle, >= SendCutSend min hole
    # tail (reviewer 11-20): the rib stops where it is MIN_WEB + TE_T deep; a TE_T x TE_REB rebate in its lower edge takes a
    # thin carbon strip flush with the lower surface, and the strip runs back to the true trailing edge
    xs_t = np.linspace(0.8 * c, c, 800)
    x_tail = max(x for x in xs_t if thick(x) >= MIN_WEB + TE_T)
    P = P.difference(box(x_tail, -100, c + 1, 100))
    low = LineString([(x_tail - TE_REB, -100), (x_tail - TE_REB, 100)]).intersection(P).bounds[1]
    P = P.difference(box(x_tail - TE_REB, -100, x_tail + 1, low + TE_T))
    te_strip_w = (c - x_tail) + TE_REB
    tail_web = thick(x_tail) - TE_T
    parts = {}
    ail = 501.0 < y < d.TIP_BREAK_Y                              # inside the aileron bay: rib stops at the hinge line
    H = holes(y)
    sp = next((h for h in H if h[0] == "spar"), None)
    xs_ = sp[1] if sp else None                                  # split line through the spar axis (front / rear pieces)
    xe = to_rib(HINGE_X, 0.0, y)[0] - HINGE_GAP / 2 if ail else c + 1
    if sp:
        parts["front"] = P.intersection(box(-10, -100, xs_, 100))
        parts["rear"] = P.intersection(box(xs_, -100, xe, 100))
    else:
        parts["closing"] = P.intersection(box(-10, -100, xe, 100))
    if ail:
        parts["aileron"] = P.intersection(box(xe + HINGE_GAP, -100, c + 1, 100))
    if aileron_only:
        xh = to_rib(HINGE_X, 0.0, y)[0] + HINGE_GAP / 2
        parts = {"aileron_end": P.intersection(box(xh, -100, c + 1, 100))}
    res = []
    for name, R in parts.items():
        R = R if R.geom_type == "Polygon" else max(R.geoms, key=lambda g: g.area)
        hs = [h for h in H if R.buffer(0.5).contains(Point(h[1], h[2]))]
        outer = R
        for hn, hx, hz, hd in hs:
            hole = Point(hx, hz).buffer(hd / 2, 64)
            if hn == "spar" and y > d.TIP_BREAK_Y:              # vertical rib, tube at 10 deg: hole is taller by 1/cos 10
                from shapely import affinity
                hole = affinity.scale(hole, 1.0, 1.0 / math.cos(math.radians(d.TIP_DIHEDRAL_DEG)) + 0.2 / hd, origin=(hx, hz))
            outer = outer.difference(hole)
        sp_ = next((h for h in hs if h[0] == "spar"), None)
        wrap = None
        if sp_:
            # trim the cradle arms back to where they are MIN_WEB thick (morphological opening near the tube only)
            _, hx, hz, hd = sp_
            zone = Point(hx, hz).buffer(hd / 2 + 8.0)
            near = outer.intersection(zone).buffer(-MIN_WEB / 2, join_style=1).buffer(MIN_WEB / 2, join_style=1)
            outer = unary_union([outer.difference(zone), near.intersection(zone)]).buffer(0)
            if outer.geom_type != "Polygon": outer = max(outer.geoms, key=lambda g: g.area)
            # contact: share of the tube's half circle on this side that still touches the rib
            ring = Point(hx, hz).buffer(hd / 2 + 0.05, 128).exterior
            side = box(-10, -100, hx, 100) if name == "front" else box(hx, -100, 400, 100)
            half = ring.intersection(side)
            wrap = half.intersection(outer.buffer(0.1)).length / max(half.length, 1e-9)
        # webs around each hole: distance from hole edge to the rib outline
        # webs: the rear rod is a closed hole (distance to the outline); the spar sits on the split line, so its web is the
        # height of rib left above/below the half-round cradle, measured 2 mm away from the tube on this piece's side
        webs = {hn: R.exterior.distance(Point(hx, hz)) - hd / 2 for hn, hx, hz, hd in hs if hn != "spar"}
        # lightening
        keep = unary_union([Point(hx, hz).buffer(hd / 2 + RING, 32) for _, hx, hz, hd in hs] +
                           [box(x, -100, x + BAR, 100) for x in np.arange(BAR_PITCH, c, BAR_PITCH)])
        inner = R.buffer(-EDGE, join_style=1).difference(keep)
        cuts = []
        for g in (getattr(inner, "geoms", [inner]) if not inner.is_empty else []):
            g = rounded(g, R_CORNER)
            for gg in getattr(g, "geoms", [g]):
                if gg.area > 40 and gg.buffer(-MIN_HOLE / 2).area > 0:
                    cuts.append(gg)
        solid = outer.difference(unary_union(cuts)) if cuts else outer
        solid = clean(solid)
        res.append(dict(part=name, R=R, holes=hs, cuts=cuts, solid=solid, webs=webs,
                        area_full=R.area, area=solid.area, tail_web=tail_web if (name == "aileron" or (name in ("rear", "closing") and not ail)) else None,
                        te_strip_w=te_strip_w, wrap=wrap))
    return c, x_nose, res


def clean(S):
    """Drop interior rings under 1 mm2 (slivers left where cut-outs meet the hole rings; each would be a waterjet pierce),
    simplify to 0.01 mm and keep the largest region."""
    S = S.buffer(0)
    if S.geom_type != "Polygon": S = max(S.geoms, key=lambda g: g.area)
    S = Polygon(S.exterior, [r for r in S.interiors if Polygon(r).area >= 1.0]).simplify(0.01, preserve_topology=True)
    return S


def _pts(ring):
    """Closed-ring points without the repeated end point and without segments under 0.01 mm."""
    pts = list(ring.coords)[:-1]; out = [pts[0]]
    for q in pts[1:]:
        if math.dist(q, out[-1]) >= 0.01: out.append(q)
    if math.dist(out[0], out[-1]) < 0.01: out.pop()
    return out


def write_dxf(path, solid, hs):
    """Cut paths from the finished solid: outline (with the half-round spar cradle) + every interior (holes, cut-outs).
    Closed round holes are written as true circles (SendCutSend prefers arcs), everything else as closed polylines."""
    doc = ezdxf.new("R2010"); doc.header["$INSUNITS"] = 4; msp = doc.modelspace()
    for g in getattr(solid, "geoms", [solid]):
        msp.add_lwpolyline(_pts(g.exterior), close=True)
        for ring in g.interiors:
            Pr = Polygon(ring); circ = next((h for h in hs if Point(h[1], h[2]).distance(Pr.centroid) < 0.05
                                             and abs(Pr.area - math.pi * h[3] ** 2 / 4) < 0.02 * Pr.area), None)
            if circ: msp.add_circle((circ[1], circ[2]), circ[3] / 2)
            else: msp.add_lwpolyline(_pts(ring), close=True)
    doc.saveas(path)


def check_part(name, S):
    """SendCutSend checks on the finished part: every interior big enough to pierce (fits a 3.18 mm circle) and the part
    bounding box against the 1 x 2 in minimum part size."""
    f = []
    for r in S.interiors:
        if Polygon(r).buffer(-MIN_HOLE / 2 + 0.01).is_empty:
            f.append(f"{name}: interior feature smaller than the {MIN_HOLE} mm minimum hole")
    x0, z0, x1, z1 = S.bounds; a, b = sorted((x1 - x0, z1 - z0))
    small = a < MIN_PART[0] or b < MIN_PART[1]
    return f, small, (round(x1 - x0, 1), round(z1 - z0, 1))


def main():
    rows, flags, small = [], [], []
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    jobs = [(y, False) for y in YS] + [(y, True) for y in AIL_END_RIBS]
    jobs.sort(key=lambda j: j[0])
    fig, axs = plt.subplots(len(jobs), 1, figsize=(11, 1.0 * len(jobs)))
    for i, (y, ail_only) in enumerate(jobs):
        c, x_nose, res = make_rib(y, aileron_only=ail_only)
        qty = 1 if y == 0 else 2                                  # centre rib once, others left + right (flip the plate)
        kind = HARD.get(y, "aileron end rib" if ail_only else "")
        ax = axs[i]
        for r in res:
            name = f"rib_{i:02d}_y{y:04.0f}_{r['part']}"
            write_dxf(OUT / f"{name}.dxf", r["solid"], r["holes"])
            g = r["area"] * T / 1000 * RHO
            light = 1 - r["area"] / r["area_full"]
            fl, sm, bb = check_part(name, r["solid"]); flags += fl
            if sm: small.append(name)
            rows.append(dict(name=name, y=round(y, 1), kind=kind, chord=round(c, 1), qty=qty, part=r["part"], bbox_mm=bb,
                             area_mm2=round(r["area"]), mass_g=round(g, 2), removed=round(light, 3),
                             webs_mm={k: round(v, 2) for k, v in r["webs"].items()},
                             holes=[(n, round(hx, 1), round(hz, 2), round(hd, 2)) for n, hx, hz, hd in r["holes"]],
                             tail_web_mm=None if r["tail_web"] is None else round(r["tail_web"], 2),
                             te_strip_w_mm=round(r["te_strip_w"], 1),
                             spar_contact=None if r["wrap"] is None else round(r["wrap"], 2)))
            for k, v in r["webs"].items():
                if v < MIN_WEB:
                    flags.append(f"{name}: web around {k} {v:.2f} mm < {MIN_WEB} mm")
            if r["wrap"] is not None and r["wrap"] < 0.5:
                flags.append(f"{name}: only {r['wrap']:.0%} of the tube's half circle bonds to this piece (add a printed or carbon collar)")
            S = r["solid"]
            for g_ in getattr(S, "geoms", [S]):
                ax.fill(*g_.exterior.xy, color={"front": "#333", "rear": "#555", "closing": "#333"}.get(r["part"], "#999"), lw=0)
                for h in g_.interiors:
                    ax.fill(*h.xy, color="white", lw=0)
        ax.set_aspect("equal"); ax.set_xlim(-5, 280); ax.axis("off")
        ax.text(-5, 0, f"y {y:.0f}", ha="right", va="center", fontsize=7)
        if kind: ax.text(282, 0, kind.split(" (")[0], ha="left", va="center", fontsize=6, color="#555")
        if not ail_only and not any(h[0] == "spar" for r in res for h in r["holes"]):
            flags.append(f"rib {i} at y {y:.0f}: no spar tube here")
    fig.suptitle("Carbon wing ribs, 1.0 mm plate, half span: front + rear piece split at the spar tube, light grey = aileron rib", fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / "ribs.png", dpi=130)
    tot = sum(r["mass_g"] * r["qty"] for r in rows)
    full = sum(r["area_mm2"] / (1 - r["removed"]) * r["qty"] for r in rows) * T / 1000 * RHO
    n = sum(r["qty"] for r in rows if r["part"] in ("front", "closing"))
    strip_w = max(r["te_strip_w_mm"] for r in rows)
    strip_g = d.SPAN * strip_w * TE_T / 1000 * RHO
    summary = dict(n_wing_ribs=n, n_parts=sum(r["qty"] for r in rows), mass_g=round(tot, 1),
                   mass_uncut_g=round(full, 1), removed_mean=round(1 - tot / full, 3), te_strip=dict(w_mm=strip_w, t_mm=TE_T, g=round(strip_g, 1)),
                   below_min_part_size=small, cf_redesign_ribs_g=None, ZS=round(ZS, 2), hinge_x=round(HINGE_X, 1), flags=flags, rows=rows)
    try:
        summary["cf_redesign_ribs_g"] = round(json.load(open(ROOT / "analysis/out/cf_redesign.json"))["team"]["parts"]["wing"]["ribs"], 1)
    except Exception:
        pass
    json.dump(summary, open(OUT / "ribs.json", "w"), indent=1)
    print(f"{n} wing ribs, {summary['n_parts']} cut parts, {tot:.1f} g cut ({full:.1f} g uncut, {1 - tot/full:.0%} removed); "
          f"cf_redesign.py assumed {summary['cf_redesign_ribs_g']} g. TE strip {strip_w:.0f} x {TE_T} mm, {strip_g:.0f} g for the span")
    for r in rows:
        print(f"  {r['name']:30s} x{r['qty']} {r['bbox_mm']}  {r['mass_g']:5.2f} g  removed {r['removed']:.0%}  webs {r['webs_mm']}  spar contact {r['spar_contact']}  {r['kind'][:28]}")
    print(f"{len(small)} of {len(rows)} part files are under SendCutSend's 1 x 2 in minimum part size")
    print("FLAGS:" if flags else "no flags"); [print("  " + f) for f in flags]


if __name__ == "__main__":
    main()
