"""Avionics cassette rail blocks (mount "avionics_rails", fixed): two CF-PETG blocks bonded to the aft face of frame F1
and the front face of frame F2 (epoxy, before the shell segments are joined). Each has a vertical 6.4 x 4.5 mm groove
(closed at the bottom = the cassette's down stop) for the cassette tongue, and one M3 heat-set insert (CNC Kitchen M3 x 5.7,
4.0 mm hole) for the cassette's captive thumb screw. The outer faces follow the inner shell (bonded there too).
Print: groove face up, 4 walls, 60 % infill. Run: SR3_CONFIG=mini cadenv/bin/python m_av_rail.py
"""
from m_common import export, bx, zcyl, isect, M3_INS
import m_layout as L
import f_fuse as FF

R = L.RAIL


def build(which):
    x0, x1 = R[which]
    s = bx(x0, x1, -R["hw"], R["hw"], R["z0"], R["z1"])
    s = isect(s, FF.shell_loft(x0 - 1, x1 + 1, FF.SKIN + 0.2)) or s
    gx0, gx1 = (x1 - R["groove_d"], x1 + 1) if which == "fwd" else (x0 - 1, x0 + R["groove_d"])
    s = s.cut(bx(gx0, gx1, -R["groove_w"]/2, R["groove_w"]/2, R["groove_bot"], R["z1"] + 1))
    ix, iy = R["insert_" + which]
    s = s.cut(zcyl(ix, iy, R["z1"] - 7.0, R["z1"] + 1, M3_INS))
    s = s.cut(bx(x0 + 2.5, x1 - 2.5, -R["hw"] + 3, -5.0, R["z0"] + 3, R["z1"] - 12))     # lightening pocket (side away from the insert)
    return s


if __name__ == "__main__":
    for w in ("fwd", "aft"):
        export(build(w), f"mount_av_rail_{w}", "CF-PETG", fill=0.8, up=(0, 0, 1), notes=f"rail block on {'F1 aft' if w == 'fwd' else 'F2 front'} face")
