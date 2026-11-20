"""Battery sled (mount "battery_sled"): 2 mm CF-PETG frame under the 6S6P pack with low end walls and a pull loop at the
front. The pack + sled sit on the carbon tray against m_battery_stop (that stop sets the CG position every time) and are held
by 2 straps through the tray slots at m_layout.STRAP_X.
Remove: lift the battery hatch -> unplug the XT90 (lies on top of the pack front, no tools) -> open the 2 straps ->
pull the loop: the sled slides 36 mm forward (its aft end leaves the skin strip ahead of the wing) -> lift it out (clear
opening ~+/-72 mm vs pack +/-67.5) [C]. Run: SR3_CONFIG=mini cadenv/bin/python m_battery_sled.py
"""
from m_common import export, bx, rbox, zcyl
import m_layout as L
from core import cyl_between

S = L.SLED


def build():
    x0, x1, hw, z0 = L.SLED_X0, L.SLED_X1, L.BAT_W/2, L.TRAY_TOP
    z1 = z0 + S["t"]
    s = rbox(x0, x1, -hw, hw, z0, z1, 4.0)
    f = S["frame"]
    xs = [x0 + S["wall"] + f, L.STRAP_X[0] - 15, L.STRAP_X[0] + 15, L.STRAP_X[1] - 15, L.STRAP_X[1] + 15, x1 - S["wall"] - f]
    for a, b in zip(xs[::2], xs[1::2]):                               # 3 windows between the strap bands
        s = s.cut(rbox(a, b, -hw + f, hw - f, z0 - 1, z1 + 1, 4.0))
    for xa, xb in ((x0, x0 + S["wall"]), (x1 - S["wall"], x1)):
        s = s.fuse(bx(xa, xb, -hw + 8, hw - 8, z1, z1 + S["wall_h"]))
    # pull loop on the front wall
    loop = bx(x0, x0 + S["wall"], -16, 16, z1 + S["wall_h"], z1 + S["wall_h"] + 18) - bx(x0 - 1, x0 + S["wall"] + 1, -11, 11, z1 + S["wall_h"] + 2, z1 + S["wall_h"] + 14)
    s = s.fuse(loop)
    s = s.cut(bx(x1 - S["wall"] - 1, x1 + 1, -20, 20, z1 + 6, z1 + S["wall_h"] - 4))   # balance-lead / air window, aft wall
    return s


if __name__ == "__main__":
    export(build(), "mount_battery_sled", "CF-PETG", fill=0.8, up=(0, 0, 1), notes="battery sled")
