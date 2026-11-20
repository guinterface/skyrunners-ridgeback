"""Tail-cone access panel (mount "tail_panel" = hatch "tail"): the tail-cone belly of fuse_seg4 from x 362 to 515, below a
plane 30 mm above the keel line, is a separate CF-PETG panel held by 4 M3 x 8 button-head screws (2 mm hex key) into
m_tail_insert_block. The pusher-ESC tray (fuse_pusher_esc_tray) and the servo-regulator mount (fuse_servo_reg_mount) are
bonded to THIS panel (not to the shell), so unscrewing it lowers both units on their leads; the belly cooling inlet is in it.
Unplug at the panel: pusher ESC XT60 + servo lead, regulator XT30 + output lead, ESC 3 bullets (to remove fully).
Print outer face down, 3 walls, CF-PETG. Run: SR3_CONFIG=mini cadenv/bin/python m_tail_panel.py
"""
from m_common import export, zcyl, M3_CLR
import m_layout as L
import f_fuse as FF


def build():
    s = FF.make_hatch("tail")
    return s.cut(*[zcyl(x, y, -200, -60, M3_CLR) for x, y in L.TAIL_SCREWS])


if __name__ == "__main__":
    export(build(), "mount_tail_panel", "CF-PETG", fill=0.9, up=(0, 0, -1), notes="tail-cone access panel, 4x M3x8 button head")
