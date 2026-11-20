"""GPS holder (mount "gps_holder"): a CF-PETG cup for the Holybro M10 puck (dia 50 x 14.4, 32 g [V holybro.com]) screwed on
the existing wing pad misc_gnss_pad_R (x 125, y 200, 4 M3 inserts at 22 mm, f_misc). Puck on one VHB pad inside the cup,
arrow forward (notch at the front of the rim), cable out of the aft slot into the pad's centre hole.
Keep the 14 AWG ESC feeds in the wing >= 100 mm from the puck (compass) [A rule of thumb]. Run: cadenv/bin/python m_gps_holder.py
"""
from m_common import export, bx, zcyl, M3_CLR
import f_misc as FM
import f_wing as FW

PUCK_D, CUP_H, T = 50.0, 7.0, 2.4


def build():
    x, y = FM.GNSS["x"], FM.GNSS["y"]
    z0 = FW.z_bounds(y, x)[1] + FM.GNSS["t"]
    s = zcyl(x, y, z0, z0 + T, FM.GNSS["r"]).fuse(zcyl(x, y, z0 + T - 0.1, z0 + T + CUP_H, PUCK_D/2 + 0.4 + 1.6))
    s = s.cut(zcyl(x, y, z0 + T, z0 + T + CUP_H + 1, PUCK_D/2 + 0.4))
    s = s.cut(*[zcyl(x + dx, y + dy, z0 - 1, z0 + T + 1, M3_CLR) for dx, dy in ((22, 0), (-22, 0), (0, 22), (0, -22))])
    s = s.cut(zcyl(x, y, z0 - 1, z0 + T + 1, 5.0))                                       # cable to the pad hole
    s = s.cut(bx(x + 20, x + 30, y - 5, y + 5, z0 + T, z0 + T + CUP_H + 1))               # aft cable slot
    s = s.cut(bx(x - 30, x - 24, y - 1.5, y + 1.5, z0 + T + CUP_H - 2, z0 + T + CUP_H + 1))  # front notch = arrow forward
    return s


if __name__ == "__main__":
    export(build(), "mount_gps_holder", "CF-PETG", fill=1.0, up=(0, 0, 1), notes="M10 cup on the wing GNSS pad")
