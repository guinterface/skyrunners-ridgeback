"""Avionics cassette (mount "avionics_tray"): ONE removable printed tray between frames F1 (x -330) and F2 (x -170).

Holds: CubePilot Cube Orange on its carrier (hard-mounted on 4 M3 nylon standoffs: the Cube isolates its IMUs inside), SiK V3 telemetry radio, Ruko R111S Remote ID, RP2 V2 receiver
on the deck (receiver taped to the front wall); PM07 power board standing on the aft wall, facing forward (all its pads and headers then face up / forward,
reachable from the hatch). Two tongues (one per end wall) slide in the vertical grooves of the m_av_rail blocks;
2 captive M3 thumb screws through the end-wall tabs into heat-set inserts in the rail blocks hold it down.

Remove: lift the avionics hatch (magnets) -> unplug (list in data/mounts.json) -> undo 2 thumb screws -> lift the cassette
straight up 110 mm out of the hatch. The deck outline is the hatch's clear opening minus 2 mm (computed from the shell).
Print: deck down, 4 walls, 40 % infill, CF-PETG. Run: SR3_CONFIG=mini cadenv/bin/python m_av_cassette.py
"""
import numpy as np
from build123d import extrude, Face, Wire, Vector
from m_common import export, bx, zcyl, rbox, M3_INS, M3_CLR
import m_layout as L
import f_fuse as FF

C, R = L.CAS, L.RAIL
WALL = C["wall"]
X_FWD_IN, X_AFT_IN = C["x_fwd"] + WALL, C["x_aft"] - WALL          # inner faces of the end walls
TONGUE = dict(w=6.0, d=4.4, z1=-20.0)                               # tongue in the 6.4 x 4.5 groove (0.2 mm per side)
LEDGE_TOP = L.TOP_Z + L.RIM_SIDE                                     # top of the side ledge, -24: narrowest point of the opening


def clear_hw(x):
    """Half width of the hatch's clear opening at x (inner face of the rim band at the ledge top) [C from the shell]."""
    return FF.half_width(x, LEDGE_TOP, FF.SKIN + FF.RIM["t"])


def hw_at(x):
    return min(clear_hw(x) - C["clear_margin"], 62.0)


def outline(z0, z1, x0=C["x_fwd"], x1=C["x_aft"]):
    xs = np.linspace(x0, x1, 14)
    top = [(x, hw_at(x)) for x in xs]
    pts = top + [(x, -y) for x, y in reversed(top)]
    w = Wire.make_polygon([Vector(float(x), float(y), z0) for x, y in pts], close=True)
    return extrude(Face(w), z1 - z0)


def build():
    zt, t = C["deck_top"], C["deck_t"]
    zb = zt - t
    s = outline(zb, zt)
    # end walls (full width up to z -34, centre part up to the tab) + tongues + thumb-screw tabs
    for xw0, xw1, sgn, ins in ((C["x_fwd"], X_FWD_IN, -1, R["insert_fwd"]), (X_AFT_IN, C["x_aft"], 1, R["insert_aft"])):
        hw = hw_at(xw0 if sgn < 0 else xw1) - 1.0
        s = s.fuse(bx(xw0, xw1, -hw, hw, zb, -34.0), rbox(xw0, xw1, -20.0, 20.0, zb, C["tab_top"], 0.5))
        xf = xw0 if sgn < 0 else xw1                                    # face toward the rail
        s = s.fuse(bx(min(xf, xf + sgn*TONGUE["d"]), max(xf, xf + sgn*TONGUE["d"]), -TONGUE["w"]/2, TONGUE["w"]/2, zb, TONGUE["z1"]))
        tab = bx(min(xf, ins[0] + sgn*3.5), max(xf, ins[0] + sgn*3.5), 2.0, 16.0, C["tab_top"] - C["tab_t"], C["tab_top"])
        s = s.fuse(tab)
        s = s.cut(zcyl(ins[0], ins[1], C["tab_top"] - 5, C["tab_top"] + 1, M3_CLR))            # thumb screw clearance
        s = s.cut(bx(xw0 - 1, xw1 + 1, -13.0, -4.0, -30.0, -20.0))                              # finger hole (handle)
        s = s.cut(bx(xw0 - 1, xw1 + 1, 22.0, hw - 5.0, zt + 4, -38.0), bx(xw0 - 1, xw1 + 1, -hw + 5.0, -22.0, zt + 4, -38.0))   # cable windows
    # side rails tie the walls together at deck level (stiffness when lifted by the handles)
    # (no side rails: they clashed with the Remote ID; the 2.4 mm deck + 2 walls are stiff enough for 150 g [A])
    # Cube carrier: 4 hard-mount bosses (M3 inserts; nylon standoffs 4 mm), pattern (MEASURE)
    hx, hy = L.FC["holes"][0]/2, L.FC["holes"][1]/2
    for dx in (-hx, hx):
        for dy in (-hy, hy):
            s = s.fuse(zcyl(L.FC["x"] + dx, dy, zb, zt + 2.0, 4.0))
            s = s.cut(zcyl(L.FC["x"] + dx, dy, zb - 1, zt + 2.1, M3_INS))
    # PM07 standoff bosses on the aft wall, 45 x 45 pattern, M3 inserts from the front
    P = L.PM07
    for dy in (-P["holes"]/2, P["holes"]/2):
        for dz in (-P["holes"]/2, P["holes"]/2):
            from core import cyl_between
            s = s.fuse(cyl_between((P["x_back"], dy, P["zc"] + dz), (X_AFT_IN + 0.1, dy, P["zc"] + dz), 3.5))
            s = s.cut(cyl_between((P["x_back"] - 0.1, dy, P["zc"] + dz), (P["x_back"] + 7.0, dy, P["zc"] + dz), M3_INS))
    s = s.fuse(bx(X_AFT_IN, C["x_aft"], -36.0, 36.0, -34.0, P["zc"] + P["holes"]/2 + 6.0))       # wall extension behind the PM07
    # deck holes: hook-and-loop strap slots for each radio item, cable pass-throughs, lightening
    cuts = []
    for k, (dims, c, g, tag) in L.AV_ITEMS.items():
        if k in ("cube_carrier", "cube_orange", "rc_rx"):
            continue
        for dx in (-dims[0]/2 - 2.5, dims[0]/2 + 2.5):
            cuts.append(bx(c[0] + dx - 1.2, c[0] + dx + 1.2, c[1] - min(dims[1]/2, 10.0), c[1] + min(dims[1]/2, 10.0), zb - 1, zt + 1))
    cuts += [rbox(L.FC["x"] - 14, L.FC["x"] + 14, -30.0, 30.0, zb - 1, zt + 1, 4.0)]   # under the carrier (cables, weight)
    cuts += [rbox(-214.0, -196.0, -30.0, 30.0, zb - 1, zt + 1, 3.0)]                  # PM07 leads down / aft
    cuts += [rbox(-312.0, -280.0, 17.0 + 2, 25.0 + 2, zb - 1, zt + 1, 1.0)]
    s = s.cut(*cuts).clean()
    return s


if __name__ == "__main__":
    s = build()
    export(s, "mount_avionics_cassette", "CF-PETG", fill=0.75, up=(0, 0, 1),
           notes="removable avionics cassette; 2 tongues in m_av_rail grooves, 2 captive M3 thumb screws")
