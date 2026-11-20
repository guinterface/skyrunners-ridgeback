"""Lift-ESC cradle (mount "esc_cradle", print 4): two C-clips snap on the 30 mm boom tube either side of the ALPHA 40A
(64.5 x 29.4 x 14.7 [V T-Motor]) aft of the pylon; a floor and two lips carry the ESC on its side under the tube, 2 zip
ties through the floor slots. Inside the nacelle (2 LW-ASA halves): close the halves with tape or 2 small screws, never
glue, so the ESC can be reached. Adapted from f_boom.esc_cradle (Scout) to the mini ESC position of assemble_mini.
Print on its side (clip faces on the bed), 5 walls 60 %, CF-PETG. Run: SR3_CONFIG=mini cadenv/bin/python m_esc_cradle.py
"""
import math
from build123d import extrude, Face, Wire, Vector
from m_common import export, bx
from core import cyl_between, biggest
import f_boom as FB
import design as d

E = dict(x0=25.0, l=64.5, h=29.4, t=14.7, ztop=-17.0)       # local: tube axis x, origin tube centre (assemble_mini ESC box)
C = dict(clips=(24.5, 83.5),                                  # first clip just aft of the pylon (local x 23)
          clip_w=6.0, wall=2.0, open_deg=55.0, floor_t=2.0, hw=E["t"]/2 + 2.0)


def local():
    r_in, r_out = FB.BORE, FB.BORE + C["wall"]
    zf1 = E["ztop"] - E["h"]; zf0 = zf1 - C["floor_t"]
    parts = []
    for xa in C["clips"]:
        ring = cyl_between((xa, 0, 0), (xa + C["clip_w"], 0, 0), r_out) - cyl_between((xa - 1, 0, 0), (xa + C["clip_w"] + 1, 0, 0), r_in)
        a = math.radians(C["open_deg"]); h = 40.0
        wedge = extrude(Face(Wire.make_polygon([Vector(xa - 1, 0, 0), Vector(xa - 1, h*math.sin(a), h*math.cos(a)), Vector(xa - 1, -h*math.sin(a), h*math.cos(a))], close=True)), C["clip_w"] + 2, dir=(1, 0, 0))
        parts.append(ring - wedge)
        for sy in (-1, 1):                              # hangers = 2 side plates, the ESC slides between them
            ya, yb = sorted((sy*(E["t"]/2 + 0.3), sy*C["hw"]))
            parts.append(bx(xa, xa + C["clip_w"], ya, yb, zf0, -r_in + 0.6) - cyl_between((xa - 1, 0, 0), (xa + C["clip_w"] + 1, 0, 0), r_in))
    x0, x1 = C["clips"][0], C["clips"][1] + C["clip_w"]
    floor = bx(x0, x1, -C["hw"], C["hw"], zf0, zf1)
    lips = [bx(x0, x1, sy*C["hw"] - (1.6 if sy > 0 else 0), sy*C["hw"] + (0 if sy > 0 else 1.6), zf1, zf1 + 6.0) for sy in (1, -1)]
    s = parts[0].fuse(*parts[1:], floor, *lips).clean()
    slots = [bx(x - 2.0, x + 2.0, -C["hw"] + 1.5, C["hw"] - 1.5, zf0 - 1, zf1 + 1) for x in (E["x0"] + 14.0, E["x0"] + E["l"] - 14.0)]
    vent = [bx(E["x0"] + 22.0, E["x0"] + E["l"] - 22.0, -C["hw"] + 2.5, C["hw"] - 2.5, zf0 - 1, zf1 + 1)]
    return biggest(s.cut(*slots, *vent).clean())


def placed():
    """Right-front instance (motor 0) in the aircraft frame; the other 3 are FB._four() translations."""
    return FB.at_boom(local(), FB.MX[0])


if __name__ == "__main__":
    export(placed(), "mount_esc_cradle", "CF-PETG", fill=0.6, up=(0, 1, 0), qty=4, notes="lift ESC cradle, print 4")
