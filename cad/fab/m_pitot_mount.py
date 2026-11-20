"""Pitot / airspeed mount (mount "pitot_mount"): a 3 mm CF-PETG bulkhead bonded inside the nose cap (fuse_seg1) at x -358,
ahead of F1. The PT40 tube passes through the nose tip (hole cut in fuse_seg1 by f_fuse, dia tube + 0.6) and a clamp hole in
the bulkhead; the MS5525DSO board (29 x 35.5 x 16.5 envelope) screws to the aft face with 2 M2.5 inserts, short silicone
tubes to the pitot, I2C JST-GH lead aft to the carrier I2C port. Reach it with the avionics cassette out.
PT40 tube OD and board holes (MEASURE). Run: SR3_CONFIG=mini cadenv/bin/python m_pitot_mount.py
"""
from build123d import extrude, Face
from m_common import export, bx, zcyl, M25_INS
from core import cyl_between, resample
import m_layout as L
import f_fuse as FF

P = L.PITOT


def build():
    x = P["x_plate"]
    poly = FF.sec(x, FF.SKIN + 0.2)
    s = extrude(Face(FF.place(resample(poly, 200), x)), P["t"], dir=(1, 0, 0))
    s = s.cut(cyl_between((x - 1, 0, P["tube_z"]), (x + P["t"] + 1, 0, P["tube_z"]), P["tube_d"]/2 + 0.15))
    s = s.cut(cyl_between((x - 1, 0, -30.0), (x + P["t"] + 1, 0, -30.0), 14.0))            # lightening / cable pass
    s = s.fuse(*[cyl_between((x + P["t"] - 0.1, dy, -50.0), (x + P["t"] + 2.0, dy, -50.0), 3.6) for dy in (-12.0, 12.0)])
    s = s.cut(*[cyl_between((x + 1.0, dy, -50.0), (x + P["t"] + 2.1, dy, -50.0), M25_INS) for dy in (-12.0, 12.0)])
    return s


if __name__ == "__main__":
    export(build(), "mount_pitot_bulkhead", "CF-PETG", fill=0.8, up=(1, 0, 0), notes="pitot + MS5525 bulkhead in the nose")
