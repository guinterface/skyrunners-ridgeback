"""SR-3 fuselage, fabrication version.

Six printed LW-ASA shell segments (1.2 mm skin, 45-deg internal bond flanges), outer shape = the concept
fuse_shell.py stations (PCHIP-interpolated, ruled every 25 mm). Printed standing on the larger end.

Openings (with 1.6 mm bonded rims under the skin so the hatches sit flush):
  avionics hatch  x -480..-250 (Iridium patch + GNSS see the sky through it: printed = RF transparent)
  battery hatch   x -240..-10  (battery goes in here, sits on the tray, then slides aft under the wing)
  wing saddle     x 20..293    (closed by the wing centre section; 4x M6 nylon bolts into frames F3/F4)
  chin turret     D124 at x -400 (pay_turret_mount, concept part reused), nadir thermal window, lidar window

Frames (CF-PETG): F1 x -480, F2 x -250, F3 x 40, F4 x 170. Rings 10 mm wide; F3/F4 carry the wing-bolt
crossbars (M6 heat-set inserts); lugs carry the battery tray (G10, CNC) and two printed avionics trays.
The battery (225x135x75) passes through the F3/F4 rings.
"""
import math
import numpy as np
from scipy.interpolate import PchipInterpolator
from build123d import *
from core import d, FabPart, hollow, resample, loft, bx, cyl_between, isect, biggest, largest
from shapely.geometry import Polygon as SPoly
import fuse_shell as FS
import f_wing as FW

SKIN = 1.2
FLANGE = 6.0
BOUNDS = [-550.0, -325.0, -100.0, 125.0, 350.0, 575.0, 800.0]
import config as _cfg
if not _cfg.MINI:                                           # mini: own stations below (the relay stations are not monotonic there)
    _st = np.array(FS.STATIONS)
    _W, _H, _ZT = (PchipInterpolator(_st[:, 0], _st[:, i]) for i in (1, 2, 3))
    DENSE = sorted(set(np.arange(-550.0, 800.1, 25.0)) | set(_st[:, 0]))

HATCHES = {"avionics": (-480.0, -250.0, 75.0), "battery": (-240.0, -10.0, 75.0)}   # x0, x1, half width
WING_OPEN = (20.0, 20.0 + d.ROOT_CHORD - 40.0, 80.0)
HATCH_GAP = 0.5
RIM = dict(t=1.6, w=8.0)

FRAMES = {"F1": -480.0, "F2": -250.0, "F3": 40.0, "F4": 170.0}
FRAME_T, FRAME_W = 5.0, 10.0
BAT = dict(x=50.0, l=225.0, w=135.0, h=75.0)               # x = centre, solved by fab/assemble.py for CG x 131
TRAY = dict(x0=-245.0, x1=225.0, w=150.0, t=1.5, ztop=-91.0)
BAT_ZTOP = TRAY["ztop"] + BAT["h"]                          # -16: clears the F3/F4 crossbars (bottom -14)
AV_TRAYS = {"A": -72.0, "B": -127.0}                        # tray top z
AV_T = 2.0
LIDAR_X = -300.0

# ------------------------------------------------------------------ Scout config (PROVISIONAL), see docs/SR3_SCOUT_ELECTRONICS.md
import config
SCOUT = config.SCOUT
if SCOUT:
    BOUNDS = [-550.0, -310.0, -100.0, 125.0, 350.0, 575.0, 800.0]    # seg1/seg2 joint aft of the Altum-PT window (seg1 240 long, fits 246)
    BAT = dict(BAT, x=-36.6)                                          # solved by assemble.py for CG x 131 (Scout mass list)
    ALTUM = dict(x=-357.0, l=110.0, w=80.0, h=69.0, win=(70.0, 56.0))  # Altum-PT 110x80x69 [S MicaSense integration guide]; window = lens cluster (MEASURE)
    FC_HOLES = [(92.0, 36.0), (92.0, -36.0), (178.0, 36.0), (178.0, -36.0)]   # FC isolator frame, M3 into heat-set inserts
    PUSH_ESC_VENTS = dict(inlet=(600.0, 645.0), outlet=(705.0, 745.0))
    ANT_MAST_X = 540.0                                                # telemetry dipole mast on top of fuse_seg5
    DLS_X = -290.0                                                    # DLS 2 pedestal on the avionics hatch (flat top; nose top slopes ~38 deg)

# ------------------------------------------------------------------ smaller own design (config.MINI, 2026-11-02)
MINI = config.MINI
if MINI:
    # 6S6P pack (140 x 135 x 75 [C]) centred on the CG under the wing; Sky4 avionics on two trays in the nose; pusher AT3520.
    # Stations [A]: drawn for this pack and a 58 mm tail cone at the AT3520 (42 mm, MEASURE).
    _st = np.array([(-380.0, 40.0, 40.0, -55.0), (-355.0, 110.0, 100.0, -15.0), (-310.0, 150.0, 145.0, -3.0), (-250.0, 165.0, 160.0, 0.0),
                    (-180.0, d.FUSE_W, d.FUSE_H, 0.0), (40.0, d.FUSE_W, d.FUSE_H, 0.0), (280.0, d.FUSE_W, d.FUSE_H, 0.0),
                    (380.0, 140.0, 135.0, 0.0), (460.0, 100.0, 95.0, -20.0), (520.0, 75.0, 70.0, -40.0), (d.FUSE_X1, 58.0, 58.0, d.PUSHER_Z + 29.0)])
    _W, _H, _ZT = (PchipInterpolator(_st[:, 0], _st[:, i]) for i in (1, 2, 3))
    DENSE = sorted(set(np.arange(d.FUSE_X0, d.FUSE_X1 + 0.1, 20.0)) | set(_st[:, 0]))
    BOUNDS = [-380.0, -150.0, 80.0, 320.0, 560.0]          # 4 shells, each <= 240 long (stand on the large end, CORE One 270 high)
    HATCHES = {"avionics": (-330.0, -175.0, 55.0), "battery": (-165.0, -15.0, 55.0)}
    WING_OPEN = (15.0, 15.0 + d.ROOT_CHORD - 35.0, 65.0)
    FRAMES = {"F1": -330.0, "F2": -170.0, "F3": 35.0, "F4": 190.0}
    BAT = dict(x=-58.0, l=140.0, w=135.0, h=75.0)          # x solved by assemble.py for CG x 94 (11-02 run: -58)
    TRAY = dict(x0=-165.0, x1=205.0, w=145.0, t=1.5, ztop=-100.0)    # battery top -25: clears the shell corners
    BAT_ZTOP = TRAY["ztop"] + BAT["h"]                    # -25
    AV_TRAYS = {"A": -60.0, "B": -110.0}
    LIDAR_X = None
    # pusher ESC + servo regulator in the tail cone (11-03). ESC = T-Motor ALPHA 40A 6S 64.5 x 29.4 x 14.7 [S], flat, wires aft to the AT3520.
    # Regulator model unknown: 45 x 25 x 12 PLACEHOLDER (MEASURE). Belly inlet under the ESC, side outlets aft of it.
    PUSH_ESC = dict(x=472.0, z=-100.0, dims=(64.5, 29.4, 14.7))      # x = centre, z = deck top
    SREG = dict(x=395.0, z=-112.0, dims=(45.0, 25.0, 12.0))           # 11-19: +3 so its deck sits inside the tail-panel opening
    MINI_VENTS = dict(inlet=(450.0, 490.0, 6.0), outlet=(512.0, 540.0, -84.0, -77.0))
    # 2026-11-19 electronics access (m_layout.py): plane-cut hatches, removable belly sensor plate, tail-cone panel.
    import m_layout as ML
    HATCHES = {k: (o["x0"], o["x1"], 80.0) for k, o in ML.OPENINGS.items() if k in ("avionics", "battery")}
    TRAY = dict(TRAY, x1=52.0)                             # ends just aft of the F3 lugs: the Pi deck and sensors sit aft of it
    HATCH_GAP = ML.HATCH_GAP
    BAT = dict(BAT, x=ML.BAT_X)                            # battery position now from m_layout (end stop sets it)

# ------------------------------------------------------------------ sections
def params(x):
    return float(_W(x)), float(_H(x)), float(_ZT(x)), d.fuse_n(x)

def sec(x, off=0.0, k=240):
    w, h, zt, n = params(x)
    a, b = w/2, h/2; zc = zt - h/2
    t = np.linspace(0, 2*np.pi, k, endpoint=False); e = 2.0/n
    P = SPoly(np.stack([a*np.sign(np.cos(t))*np.abs(np.cos(t))**e, zc + b*np.sign(np.sin(t))*np.abs(np.sin(t))**e], 1)).buffer(0)
    if off > 0:
        P = largest(P.buffer(-off, join_style=1, quad_segs=6))
    return P

def place(pts, x):
    return Wire.make_polygon([Vector(float(x), float(a), float(b)) for a, b in pts], close=True)

def shell_loft(x0, x1, off):
    xs = sorted({x0, x1, *[k for k in DENSE if x0 < k < x1]})
    return loft([place(resample(sec(x, off)), x) for x in xs])

def half_width(x, z, off):
    P = sec(x, off)
    from shapely.geometry import LineString
    g = LineString([(-500, z), (500, z)]).intersection(P)
    return (g.length/2) if not g.is_empty else 0.0

def _ztop_at(x, y, off):
    """MINI: z of the shell's inner BOTTOM surface (inset `off`) at (x, y)."""
    from shapely.geometry import LineString
    g = LineString([(y, -500), (y, 500)]).intersection(sec(x, off))
    return g.bounds[1]

def top_z(x, off=0.0):
    w, h, zt, n = params(x)
    return zt - off

# ------------------------------------------------------------------ openings
def opening_region(name, g=0.0, ge=None):
    """MINI: solid removed from the shell for opening `name` (m_layout.OPENINGS). g > 0 moves the cut plane into the
    fuselage by g and widens the x range by ge (default g x rim_end/rim): used for the rims (+rim / -rim) and hatches (-gap)."""
    import math as _m
    from build123d import Box as _Box, Location as _Loc, Axis as _Ax
    o = ML.OPENINGS[name]
    if ge is None:
        ge = g if o["rim"] == 0 else g*o["rim_end"]/o["rim"]
    x0, x1 = o["x0"] - ge, o["x1"] + ge
    if o["kind"] == "top":
        return bx(x0, x1, -300, 300, o["z"] - g, 200)
    if o["kind"] == "bottom":
        return bx(x0, x1, -300, 300, -500, o["z"] + g)
    (xa, za), (xb, zb) = o["a"], o["b"]
    th = _m.atan2(zb - za, xb - xa)
    n = (-_m.sin(th), 0.0, _m.cos(th))
    half = _Box(3000, 600, 1000).moved(_Loc((0, 0, -500))).rotate(_Ax.Y, -_m.degrees(th)).moved(_Loc((xa + g*n[0], 0, za + g*n[2])))
    return half & bx(x0, x1, -300, 300, -500, 200)

def opening_boxes(gap=0.0):
    if MINI:
        x0, x1, hw = WING_OPEN
        zt = max(top_z(x0), top_z(x1), top_z((x0 + x1)/2))
        return [opening_region(k, -gap) for k in ML.OPENINGS] + [bx(x0 + gap, x1 - gap, -hw + gap, hw - gap, zt - 60, zt + 20)]
    out = []
    for x0, x1, hw in [*HATCHES.values(), WING_OPEN]:
        zt = max(top_z(x0), top_z(x1), top_z((x0 + x1)/2))
        out.append(bx(x0 + gap, x1 - gap, -hw + gap, hw - gap, zt - 60, zt + 20))
    return out

def band(lo, hi, off, t):
    """Shell layer between insets off and off + t over x lo..hi (face-built, no boolean)."""
    s, _ = hollow((lo, hi), lambda x, o: sec(x, off + o), place, t, flange=0.0, kinks=[k for k in DENSE if lo < k < hi])
    return s

def rims(x_range=(-1e9, 1e9)):
    out = []
    if MINI:
        for k, o in ML.OPENINGS.items():
            lo, hi = o["x0"] - max(o["rim"], o["rim_end"]) - 2, o["x1"] + max(o["rim"], o["rim_end"]) + 2
            if hi < x_range[0] or lo > x_range[1]:
                continue
            r = isect(band(lo, hi, SKIN, RIM["t"]), opening_region(k, o["rim"], ge=max(o["rim_end"], 1.0)) - opening_region(k, -o["rim"]))   # >= 1 mm past the ends so it fuses
            if r is None:
                continue
            slabs = [bx(fx - FRAME_T/2 - 0.3, fx + FRAME_T/2 + 0.3, -300, 300, -400, 200) for fx in FRAMES.values() if lo - 5 < fx < hi + 5]
            if slabs:
                r = r.cut(*slabs)
            out.append(r)
        x0, x1, hw = WING_OPEN
        x_range_ok = not (x1 + RIM["w"] < x_range[0] or x0 - RIM["w"] > x_range[1])
        if x_range_ok:
            lo, hi = x0 - RIM["w"], x1 + RIM["w"]
            zt = max(top_z(x0), top_z(x1), top_z((x0 + x1)/2))
            ring = bx(lo, hi, -hw - RIM["w"], hw + RIM["w"], zt - 60, zt + 20) - bx(x0 + RIM["w"], x1 - RIM["w"], -hw + RIM["w"], hw - RIM["w"], zt - 70, zt + 30)
            r = isect(band(lo, hi, SKIN, RIM["t"]), ring)
            if r is not None:
                out.append(r)
        return out
    for x0, x1, hw in [*HATCHES.values(), WING_OPEN]:
        lo, hi = x0 - RIM["w"], x1 + RIM["w"]
        if hi < x_range[0] or lo > x_range[1]:
            continue
        band_ = band(lo, hi, SKIN, RIM["t"])
        zt = max(top_z(x0), top_z(x1), top_z((x0 + x1)/2))
        ring = bx(lo, hi, -hw - RIM["w"], hw + RIM["w"], zt - 60, zt + 20) - bx(x0 + RIM["w"], x1 - RIM["w"], -hw + RIM["w"], hw - RIM["w"], zt - 70, zt + 30)
        r = isect(band_, ring)
        if r is not None:
            out.append(r)
    return out

def bottom_cuts():
    zb = lambda x: params(x)[2] - params(x)[1]
    if MINI:                                              # no turret / nadir camera / lidar yet (thermal camera later); pusher-ESC vents only
        x0, x1, hw = MINI_VENTS["inlet"]
        cuts = [bx(x0, x1, -hw, hw, zb(x1) - 20, zb(x0) + 12)]                          # belly inlet between the mount webs
        x0, x1, z0, z1 = MINI_VENTS["outlet"]
        cuts += [bx(x0, x1, -60, 60, z0, z1)]                                           # outlets, both side walls
        P = ML.PITOT                                                                    # 11-19: pitot tube through the nose tip
        cuts += [cyl_between((d.FUSE_X0 - 10, 0, P["tube_z"]), (P["x_plate"], 0, P["tube_z"]), P["tube_d"]/2 + 0.3)]
        return cuts
    if SCOUT:
        A = ALTUM; wl, ww = A["win"]
        cuts = [bx(A["x"] - wl/2, A["x"] + wl/2, -ww/2, ww/2, zb(A["x"]) - 20, zb(A["x"]) + 25)]          # Altum-PT nadir window
        x0, x1 = PUSH_ESC_VENTS["inlet"]
        cuts += [bx(x0, x1, sy*18.0 - 3.5, sy*18.0 + 3.5, zb(x1) - 20, zb(x0) + 18) for sy in (-1, 1)]       # pusher-ESC inlets (belly)
        x0, x1 = PUSH_ESC_VENTS["outlet"]
        zc = params(0.5*(x0 + x1))[2] - params(0.5*(x0 + x1))[1]/2
        cuts += [bx(x0, x1, -60, 60, zc - 9, zc - 3)]                                                    # outlets, both sides
        zt = top_z(ANT_MAST_X)
        cuts.append(cyl_between((ANT_MAST_X, 0, zt - 15), (ANT_MAST_X, 0, zt + 5), 4.0))                 # mast coax
        cuts.append(cyl_between((-560.0, 0, -85.0), (-540.0, 0, -85.0), 3.5))                           # SHT45 probe cable, nose cap
        return cuts
    return [cyl_between((d.TURRET["x"], 0, zb(d.TURRET["x"]) - 20), (d.TURRET["x"], 0, zb(d.TURRET["x"]) + 40), 62.0),
            bx(d.NADIR_CAM_X + 15, d.NADIR_CAM_X + 65, -25, 25, zb(d.NADIR_CAM_X) - 20, zb(d.NADIR_CAM_X) + 40),
            cyl_between((LIDAR_X, 0, zb(LIDAR_X) - 20), (LIDAR_X, 0, zb(LIDAR_X) + 40), 15.0)]

# ------------------------------------------------------------------ parts
def make_segment(i):
    x0, x1 = BOUNDS[i], BOUNDS[i + 1]
    xs = [k for k in DENSE if x0 < k < x1]
    body, _ = hollow((x0, x1), sec, place, SKIN, FLANGE, closed=(i == 0, False), kinks=xs)
    cuts = [c for c in opening_boxes() + bottom_cuts()]
    body = body.cut(*cuts).clean()
    seg_box = bx(x0, x1, -200, 200, -400, 200)
    add = [isect(r, seg_box) for r in rims((x0, x1))]
    add = [a for a in add if a is not None]
    if add:
        body = body.fuse(*add).clean()
    return biggest(body)

def make_hatch(name):
    if MINI:                                                            # avionics, battery (top), belly, tail (m_belly_plate / m_tail_panel use it)
        o = ML.OPENINGS[name]
        sh = band(o["x0"] - 4, o["x1"] + 4, 0.0, SKIN)
        h = sh & opening_region(name, -HATCH_GAP)
        if name in ("belly", "tail"):
            h = h.cut(*bottom_cuts())
        return biggest(h)
    x0, x1, hw = HATCHES[name]
    sh = band(x0 - 2, x1 + 2, 0.0, SKIN)
    zt = max(top_z(x0), top_z(x1), top_z((x0 + x1)/2))
    h = sh & bx(x0 + HATCH_GAP, x1 - HATCH_GAP, -hw + HATCH_GAP, hw - HATCH_GAP, zt - 60, zt + 20)
    if SCOUT and name == "avionics":                                   # DLS 2 cable through the hatch, under its pedestal
        h = h.cut(cyl_between((DLS_X, 0, top_z(DLS_X) - 20), (DLS_X, 0, top_z(DLS_X) + 10), 4.0))
    return biggest(h)

def make_frame(fid):
    x = FRAMES[fid]
    outer = sec(x, SKIN + 0.3); inner = sec(x, SKIN + 0.3 + FRAME_W)
    ring2d = outer.difference(inner)
    def prism(P2d, xa, xb):
        f = Face(place(resample(largest(P2d) if P2d.geom_type != "Polygon" else P2d, 240), xa))
        return extrude(f, xb - xa, dir=(1, 0, 0))
    ring = prism(SPoly(outer.exterior.coords), x - FRAME_T/2, x + FRAME_T/2) - prism(SPoly(inner.exterior.coords), x - FRAME_T/2 - 1, x + FRAME_T/2 + 1)
    interior = prism(SPoly(outer.exterior.coords), x - 30, x + 30)
    parts = [ring]
    zt_in = top_z(x, SKIN + 0.3)
    # wing-bolt crossbar + bosses (F3, F4)
    if fid in ("F3", "F4"):
        bar = isect(bx(x - 6, x + 6, -120, 120, BAT_ZTOP + 2, zt_in + 0.01), interior)
        parts.append(bar)
        for wx, wy in FW.WING_BOLTS:
            if abs(wx - x) < 1:
                zw = FW.z_bounds(wy, wx)[0] - 0.3
                parts.append(cyl_between((x, wy, BAT_ZTOP + 2), (x, wy, zw), 7.5))
    # tray lugs (z top = tray bottom)
    lugs = []
    if fid in ("F2", "F3"):
        zt = TRAY["ztop"] - TRAY["t"]
        side = (-1, 1) if fid == "F3" else (1,)
        for s in side:
            lugs.append((x + s*FRAME_T/2, x + s*(FRAME_T/2 + 12), zt - 6, zt, 52.0))
    if fid in ("F1", "F2") and not MINI:                   # MINI: the avionics cassette rides on m_av_rail blocks instead
        s = 1 if fid == "F1" else -1
        for zt in AV_TRAYS.values():
            lugs.append((x + s*FRAME_T/2, x + s*(FRAME_T/2 + 12), zt - AV_T - 6, zt - AV_T, 42.0))
    for xa, xb, z0, z1, yin in lugs:
        for sy in (1, -1):
            lug = isect(bx(min(xa, xb) - (FRAME_T if xb > xa else -FRAME_T)*0 - 0.01, max(xa, xb) + 0.01, *sorted((sy*yin, sy*150)), z0, z1), interior)
            if lug is not None:
                parts.append(lug)
    if MINI and fid in ("F3", "F4"):                   # belly plate thumb-screw bosses (M3 insert from below), on the plate side of the ring
        sx = 1 if fid == "F3" else -1
        for bxp, byp in ML.BELLY_SCREWS:
            if abs(bxp - x) > 15:
                continue
            zb_ = min(_ztop_at(xx, byp + dy, SKIN) for xx in (bxp - 4, bxp + 4) for dy in (-4, 4))
            parts.append(isect(bx(min(x, bxp - 4.5), max(x, bxp + 4.5), byp - 4.5, byp + 4.5, zb_ + 0.2, zb_ + 10.0), interior))
    s = parts[0].fuse(*[p for p in parts[1:] if p is not None]).clean()
    holes = []
    if MINI and fid in ("F3", "F4"):
        for bxp, byp in ML.BELLY_SCREWS:
            if abs(bxp - x) <= 15:
                holes.append(cyl_between((bxp, byp, -200), (bxp, byp, _ztop_at(bxp, byp, SKIN) + 7.2), 2.0))   # M3 insert 4.0 x 7
    if fid in ("F3", "F4"):
        for wx, wy in FW.WING_BOLTS:
            if abs(wx - x) < 1:
                zw = FW.z_bounds(wy, wx)[0]
                holes.append(cyl_between((x, wy, zw - 14), (x, wy, zw + 1), 4.0))      # M6 heat-set insert, 8 mm hole x 14
    for xa, xb, z0, z1, yin in lugs:
        xm = (xa + xb)/2 + (2 if xb > xa else -2)
        for sy in (1, -1):
            holes.append(cyl_between((xm, sy*(yin + 8), z0 - 1), (xm, sy*(yin + 8), z1 + 1), 2.0))  # M3 insert 4.0 mm
    if fid in ("F3", "F4") and not (MINI and abs(x - BAT["x"]) > BAT["l"]/2 + 10):   # battery passes through: clear its envelope + 2 mm
        B = BAT
        holes.append(bx(x - 10, x + 10, -B["w"]/2 - 2, B["w"]/2 + 2, TRAY["ztop"] - 0.5, BAT_ZTOP + 1.5))
    if holes:
        s = s.cut(*holes).clean()
    return biggest(s)

def tray_face(x0, x1, z, w, holes, slots=()):
    xc = (x0 + x1)/2
    with BuildSketch() as sk:
        RectangleRounded(x1 - x0, w, 6)
        for hx, hy, r in holes:
            with Locations((hx - xc, hy)):
                Circle(r, mode=Mode.SUBTRACT)
        for sx, sy, a, b in slots:
            with Locations((sx - xc, sy)):
                Rectangle(a, b, mode=Mode.SUBTRACT)
    return sk.sketch.faces()[0].moved(Location((xc, 0, z)))

def battery_tray():
    T = TRAY
    if MINI:
        F2, F3 = FRAMES["F2"], FRAMES["F3"]
        holes = [(x, sy*60.0, 1.65) for x in (F2 + 9.0, F3 - 10.5, F3 + 10.5) for sy in (1, -1)]
        holes += [(ML.STOP["holes_x"], dy, 1.65) for dy in (-30, 30)]                 # m_battery_stop, 2x M3
        holes += [(x, 0.0, 20.0) for x in (-120.0, -50.0)]
    else:
        holes = [(x, sy*60.0, 1.65) for x in (-241.0, 40.0 - 10.5, 40.0 + 10.5) for sy in (1, -1)]     # lug inserts (M3 clearance 3.3)
        holes += [(-150.0 + dx, dy, 1.65) for dx in (-50, 50) for dy in (-32, 32)]                       # repeater radio standoffs
        holes += [(BAT["x"] + BAT["l"]/2 + 8, dy, 1.65) for dy in (-30, 30)]                              # battery stop
        holes += [(x, 0.0, 22.5) for x in (-210.0, -60.0, 60.0, 170.0)]                                   # lightening
    if SCOUT:
        holes += [(x, y, 1.65) for x, y in FC_HOLES]                                                  # FC isolator frame (hangs under the tray)
    slots = [(xs, sy*62.0, 3.2, 25.0) for xs in (ML.STRAP_X if MINI else (-120.0, 0.0, 150.0)) for sy in (1, -1)]   # strap slots
    f = tray_face(T["x0"], T["x1"], T["ztop"] - T["t"], T["w"], holes, slots)
    return extrude(f, T["t"]), f

def av_tray(key):
    zt = AV_TRAYS[key]
    x0, x1 = FRAMES["F1"] + FRAME_T/2 + 0.5, FRAMES["F2"] - FRAME_T/2 - 0.5
    hw = min(half_width(x, zt - AV_T, SKIN + 0.5) for x in np.linspace(x0, x1, 8)) - 1.0
    w = 2*min(hw, 70.0)
    holes = [(x, sy*50.0, 1.65) for x in (x0 + 8.5, x1 - 8.5) for sy in (1, -1)]
    grid = [(x, y, 1.65) for x in np.arange(x0 + 30, x1 - 20, 20.0) for y in (-35.0, -15.0, 15.0, 35.0)]
    if key == "B" and LIDAR_X is not None:
        grid = [g for g in grid if abs(g[0] - LIDAR_X) > 25]
        grid.append((LIDAR_X, 0.0, 14.0))                         # lidar looks down through tray B + the floor
    f = tray_face(x0, x1, zt - AV_T, w, holes + grid)
    return extrude(f, AV_T)

def battery_stop():
    x0 = BAT["x"] + BAT["l"]/2 + 1
    s = bx(x0, x0 + 14, -50, 50, TRAY["ztop"], TRAY["ztop"] + 30) - bx(x0 + 3, x0 + 15, -40, 40, TRAY["ztop"] + 3, TRAY["ztop"] + 31)
    s = s.cut(*[cyl_between((BAT["x"] + BAT["l"]/2 + 8, dy, TRAY["ztop"] - 1), (BAT["x"] + BAT["l"]/2 + 8, dy, TRAY["ztop"] + 4), 2.0) for dy in (-30, 30)])
    return s

def relay_cradle():
    R = d.RELAY["duplexer"]; xc = d.RELAY["x"]
    z1 = -d.FUSE_H + 40 - R["z"]/2                          # duplexer bottom (-187.5)
    plate = bx(xc - R["x"]/2 - 5, xc + R["x"]/2 + 5, -R["y"]/2 - 5, R["y"]/2 + 5, z1 - 3, z1)
    zb = params(xc)[2] - params(xc)[1]
    inner = shell_loft(xc - 110, xc + 110, SKIN + 0.2)          # solid loft (no boolean with another loft)
    posts = [isect(bx(xc + sx*(R["x"]/2 - 8) - 7, xc + sx*(R["x"]/2 - 8) + 7, sy*(R["y"]/2 - 8) - 7, sy*(R["y"]/2 - 8) + 7, zb - 5, z1), inner)
             for sx in (-1, 1) for sy in (-1, 1)]
    s = plate.fuse(*[p for p in posts if p is not None]).clean()
    s = s.cut(*[cyl_between((xc + dx, dy, z1 - 8), (xc + dx, dy, z1 + 1), 2.0) for dx in (-75, 75) for dy in (-45, 45)])   # M3 inserts (MEASURE vs TMND3 drawing)
    return s

def firewall():
    x = d.PUSHER_X
    def pr(P, xa, xb):
        return extrude(Face(place(resample(P, 200), xa)), xb - xa, dir=(1, 0, 0))
    plate = pr(sec(x, 0.0), x, x + 5)
    spig = pr(sec(x, SKIN + 0.2), x - 10, x) - pr(sec(x, SKIN + 3.2), x - 11, x + 1)
    s = plate.fuse(spig).clean()
    holes = [cyl_between((x - 12, 0, d.PUSHER_Z), (x + 6, 0, d.PUSHER_Z), 7.0)]
    pr_, hr = (12.5, 1.65) if MINI else (15.0, 2.15)     # mini: 4x M3 on PCD 25 for the AT3520 (MEASURE)
    holes += [cyl_between((x - 1, pr_*math.cos(a), d.PUSHER_Z + pr_*math.sin(a)), (x + 6, pr_*math.cos(a), d.PUSHER_Z + pr_*math.sin(a)), hr)
              for a in np.radians([45, 135, 225, 315])]          # 4x M4 on PCD 30 (MEASURE vs the pusher motor)
    return s.cut(*holes).clean()


def tail_mount(spec, tie_dx):
    """MINI: flat PETG-CF deck on two webs + two feet that follow the shell floor (bond into fuse_seg4),
    cable-tie slots each side of the item, a vent cut-out under it."""
    (lx, ly, lz) = spec["dims"]; x, zdeck = spec["x"], spec["z"]
    x0, x1 = x - lx/2 - 4, x + lx/2 + 4
    hw = ly/2 + (3.0 if MINI else 6.0)                 # MINI 11-19: narrower so it drops out through the tail-panel opening
    deck = bx(x0, x1, -hw, hw, zdeck - 2.4, zdeck)
    inner = shell_loft(x0 - 2, x1 + 2, SKIN + 0.2)
    webs = [isect(bx(x0 + 2, x1 - 2, sy*9.0 - 1.2, sy*9.0 + 1.2, -400, zdeck), inner) for sy in (-1, 1)]
    fi = 7.0 if MINI else 6.0                          # MINI 11-19: 1 mm further in, clear of the tail-panel end ledges
    feet = [isect(bx(xx - 4, xx + 4, -hw, hw, -400, zdeck), inner) for xx in (x0 + fi, x1 - fi)]
    s = deck.fuse(*[w for w in webs + feet if w is not None]).clean()
    cuts = [bx(x + dx - 2.2, x + dx + 2.2, sy*(ly/2 + 2.6) - 1.1, sy*(ly/2 + 2.6) + 1.1, zdeck - 3, zdeck + 1)
            for dx in tie_dx for sy in (-1, 1)]                                       # 4.4 x 2.2 slots for 3.6 mm ties
    cuts += [bx(x - lx/2 + 10, x + lx/2 - 10, -6.5, 6.5, zdeck - 3, zdeck + 1)]       # vent under the item (between the webs)
    if MINI:                                            # 11-19: bonded to the tail panel; keep 0.5 mm off the panel ledge (rim) so it drops out
        o = ML.OPENINGS["tail"]
        cuts.append(isect(band(x0 - 6, x1 + 6, SKIN - 0.1, RIM["t"] + 0.6), opening_region("tail", o["rim"] + 0.5) - opening_region("tail", -o["rim"] - 0.5)))
        cuts = [c for c in cuts if c is not None]
    return biggest(s.cut(*cuts).clean())


# ------------------------------------------------------------------ jobs
JOBS = [f"seg{i}" for i in range(6)] + list(HATCHES) + list(FRAMES) + ["tray_bat", "tray_A", "tray_B", "bat_stop", "relay_cradle", "firewall", "turret_mount"]
if SCOUT:       # relay payload out; tray B is replaced by the Altum-PT deck (f_elec)
    JOBS = [j for j in JOBS if j not in ("tray_B", "relay_cradle", "turret_mount")]
if MINI:
    JOBS = [f"seg{i}" for i in range(len(BOUNDS) - 1)] + list(HATCHES) + list(FRAMES) + ["tray_bat", "firewall", "push_esc_tray", "sreg_mount"]
    # 11-19: tray_A/tray_B -> m_av_cassette (removable), bat_stop -> m_battery_stop; belly plate / tail panel in m_belly_plate / m_tail_panel

def build(job):
    if job.startswith("seg"):
        i = int(job[3:])
        x0, x1 = BOUNDS[i], BOUNDS[i + 1]
        big_front = params(x0)[0]*params(x0)[1] >= params(x1)[0]*params(x1)[1]
        return [FabPart(f"fuse_seg{i+1}", "fuselage", make_segment(i), "LW-ASA", up=(1, 0, 0) if big_front else (-1, 0, 0),
                        notes=f"shell x {x0:.0f}..{x1:.0f}" + (" (nose, closed)" if i == 0 else ""),
                        print_notes="2-3 walls (1.2 mm), 0 % infill; larger end on the bed")]
    if job in HATCHES:
        x0, x1, _ = HATCHES[job]
        return [FabPart(f"fuse_hatch_{job}", "fuselage", make_hatch(job), "LW-ASA", up=(0, 1, 0),
                        notes=f"x {x0:.0f}..{x1:.0f}; sits on the bonded rim; hold with 4x 6x3 magnets or tape",
                        print_notes="stand on a long edge")]
    if job in FRAMES:
        return [FabPart(f"fuse_frame_{job}", "fuselage", make_frame(job), "CF-PETG", fill=0.6, up=(1, 0, 0),
                        notes=f"bulkhead ring at x {FRAMES[job]:.0f}" + ("; wing-bolt crossbar, 2x M6 heat-set" if job in ("F3", "F4") else "") + "; bond into the shell",
                        print_notes="flat, 4 walls, 40 % infill (100 % around the inserts via slicer modifier)")]
    if job == "tray_bat":
        s, f = battery_tray()
        return [FabPart("fuse_battery_tray", "fuselage", s, "CF-plate", up=(0, 0, 1), dxf=f,
                        notes="1.5 mm carbon plate, CNC from DXF; install before bonding the shell segments; " + ("Scout: PDB plate hangs under it on 4x M3x30 standoffs (ex-radio holes), FC isolator frame on 4 new holes, the x -210 lightening hole is the battery-lead pass-through" if SCOUT else ("4x M3 holes at x -150 free for the power board or Jetson standoffs" if _cfg.MINI else "radio hangs under it on 4x M3x20 standoffs")))]
    if job.startswith("tray_"):
        k = job[-1]
        return [FabPart(f"fuse_avionics_tray_{k}", "fuselage", av_tray(k), "CF-PETG", fill=0.7, up=(0, 0, 1),
                        notes=f"avionics tray {k} (top z {AV_TRAYS[k]:.0f}); M3 grid 20 mm" + ("; lidar hole" if k == "B" and not _cfg.MINI else ""),
                        print_notes="flat, 4 walls, 40 % infill")]
    if job == "bat_stop":
        return [FabPart("fuse_battery_stop", "fuselage", battery_stop(), "CF-PETG", fill=0.6, up=(0, 0, 1), notes="aft battery stop, 2x M3 through the tray")]
    if job == "relay_cradle":
        return [FabPart("fuse_relay_cradle", "fuselage", relay_cradle(), "CF-PETG", fill=0.6, up=(0, 0, 1),
                        notes="duplexer (Telewave TMND3) cradle; posts bond to the floor; hole pattern MEASURE vs the TMND3 drawing")]
    if job == "firewall":
        return [FabPart("fuse_firewall", "fuselage", firewall(), "CF-PETG", fill=1.0, up=(-1, 0, 0),
                        notes="pusher firewall, spigot bonds into fuse_seg6; motor holes 4x M4 PCD 30 (MEASURE)", print_notes="100 % infill")]
    if job == "push_esc_tray":
        return [FabPart("fuse_pusher_esc_tray", "fuselage", tail_mount(PUSH_ESC, (-20.0, 20.0)), "CF-PETG", fill=0.6, up=(0, 0, 1),
                        notes="pusher ESC (ALPHA 40A 6S, 64.5 x 29.4 x 14.7) lies flat on it, 2 cable ties; feet bond to the fuse_seg4 floor before the firewall goes on; "
                              "belly inlet under it, side outlets aft (in fuse_seg4)", print_notes="flat, 4 walls, 40 % infill")]
    if job == "sreg_mount":
        return [FabPart("fuse_servo_reg_mount", "fuselage", tail_mount(SREG, (-12.0, 12.0)), "CF-PETG", fill=0.6, up=(0, 0, 1),
                        notes="PLACEHOLDER: servo regulator 5-6 V >= 5 A, model unknown, drawn for 45 x 25 x 12 (MEASURE the real one, redraw if bigger); "
                              "2 cable ties; feet bond to the fuse_seg4 floor", print_notes="flat, 4 walls, 40 % infill")]
    if job == "turret_mount":
        import pay_turret_mount as TM
        s = TM.make().moved(TM.placements()[0])
        return [FabPart("fuse_turret_mount", "fuselage", s, "CF-PETG", fill=0.5, up=(0, 0, -1),
                        notes="concept part parts/pay_turret_mount.py (saddle bonds inside fuse_seg1/2 at the chin opening); isolators + kit plate per that file")]
    raise KeyError(job)
