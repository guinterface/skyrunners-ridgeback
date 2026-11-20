"""Insert block for the tail-cone panel screws (part of mount "tail_panel", fixed; print 4): 10 x 10 CF-PETG block bonded
on the panel's end ledge inside fuse_seg4, one M3 heat-set insert (4.0 x 6) from below. Its foot follows the ledge.
Run: SR3_CONFIG=mini cadenv/bin/python m_tail_insert_block.py   (exports the 4 placed copies as one file each)
"""
from m_common import export, bx, zcyl, isect, M3_INS
import m_layout as L
import f_fuse as FF


def build(x, y):
    zl = FF._ztop_at(x, y, FF.SKIN + FF.RIM["t"])                    # top of the ledge
    zf = min(FF._ztop_at(x + dx, y + dy, FF.SKIN + FF.RIM["t"]) for dx in (-4, 4) for dy in (-5, 5))
    s = bx(x - 4, x + 4, y - 5, y + 5, zf - 3, zl + 9)      # 8 long in x: clears the ESC tray (ends x 508.3)
    s = isect(s, FF.shell_loft(x - 5, x + 5, FF.SKIN + FF.RIM["t"]))  # foot follows the ledge
    return s.cut(zcyl(x, y, zl - 5, zl + 6.5, M3_INS))


if __name__ == "__main__":
    for i, (x, y) in enumerate(L.TAIL_SCREWS):
        export(build(x, y), f"mount_tail_insert_block_{i}", "CF-PETG", fill=1.0, up=(0, 0, 1), notes="tail panel insert block")
