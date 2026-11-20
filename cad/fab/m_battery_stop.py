"""Battery end stop + side guides (mount "battery_stop", fixed): screwed to the carbon tray with 2x M3 x 8 into nuts
(tray holes at x STOP holes_x, y +/-30). Aft wall = flight position of the sled (CG); the two 60 mm side guides keep the
sled square while it slides. Notches let the x -25 strap pass. Print base down, 4 walls 40 %, CF-PETG.
Run: SR3_CONFIG=mini cadenv/bin/python m_battery_stop.py
"""
from m_common import export, bx, zcyl, M3_CLR
import m_layout as L

T = L.STOP


def build():
    z0 = L.TRAY_TOP
    x0 = T["x0"]; gy = L.BAT_W/2 + 0.6
    s = bx(x0, x0 + T["t"], -T["hw"], T["hw"], z0, z0 + T["h"])
    s = s.fuse(bx(x0, x0 + 12.0, -gy - T["guide_t"], gy + T["guide_t"], z0, z0 + 3.0))
    for sy in (-1, 1):
        ya, yb = sorted((sy*gy, sy*(gy + T["guide_t"])))
        s = s.fuse(bx(x0 + T["t"] - T["guide_len"], x0 + 12.0, ya, yb, z0, z0 + T["guide_h"]))
        s = s.cut(bx(L.STRAP_X[1] - 4, L.STRAP_X[1] + 4, ya - 1, yb + 1, z0 - 1, z0 + T["guide_h"] + 1))     # strap notch
    s = s.cut(*[zcyl(T["holes_x"], dy, z0 - 1, z0 + 4, M3_CLR) for dy in (-30, 30)])
    s = s.cut(bx(x0 - 1, x0 + T["t"] + 1, -28, 28, z0 + 8, z0 + T["h"] - 5))          # lightening / balance lead
    return s


if __name__ == "__main__":
    export(build(), "mount_battery_stop", "CF-PETG", fill=0.7, up=(0, 0, 1), notes="battery end stop + guides")
