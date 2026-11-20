"""Belly sensor plate (mount "belly_plate" = hatch "belly"): the fuselage belly between frames F3 (x 35) and F4 (x 190)
below z -150 becomes ONE removable CF-PETG panel (same outer shape as the shell, so it sits flush) that carries every
mission sensor and, on m_belly_deck, the Raspberry Pi 5 and its regulator. 4 captive M3 thumb screws go up into inserts
in bosses on F3 / F4. The whole set connects to the aircraft by 2 plugs: XT30 (battery power from the PM07) and
JST-GH 6-pin (MAVLink from Pixhawk TELEM2), both on 150 mm pigtails so the plate hangs while you unplug.
Down-looking sensors sit on corner posts at their parts.toml boxes (thermal and colour camera +5 mm aft; the air sensor
moved here from x -40) and look through windows in the plate. Print outer face down, tree supports under the posts' bridges
none needed (posts are vertical), 4 walls 40 %. Run: SR3_CONFIG=mini cadenv/bin/python m_belly_plate.py
"""
from m_common import export, bx, zcyl, isect, rbox, M3_CLR
from core import cyl_between
import m_layout as L
import f_fuse as FF

POST = 8.0              # L-corner post leg length
POST_T = 1.6
DOWN = ("thermal_cam", "rgb_cam", "spot_sensor", "nir_channel")
WINDOWS = {"thermal_cam": ("box", 18, 18), "rgb_cam": ("cyl", 15.5), "spot_sensor": ("box", 34, 16), "nir_channel": ("cyl", 6.0)}


def interior(x0, x1):
    return FF.shell_loft(x0, x1, FF.SKIN - 0.05)


def build():
    o = L.OPENINGS["belly"]
    s = FF.make_hatch("belly")
    inner = interior(o["x0"] - 2, o["x1"] + 2)
    add = []
    for k in DOWN:
        (lx, ly, lz), (cx, cy, cz), _ = L.PAYLOAD[k]
        zb = cz - lz/2                                         # sensor bottom = post top
        if k == "nir_channel":
            continue                                           # sits in the spot-sensor head
        for sx in (-1, 1):
            for sy in (-1, 1):
                xc, yc = cx + sx*(lx/2 + 0.3), cy + sy*(ly/2 + 0.3)
                xa, xb = sorted((xc, xc - sx*POST)); ya, yb = sorted((yc, yc - sy*POST))
                leg_x = bx(*sorted((xc - sx*POST, xc + sx*POST_T)), *sorted((yc, yc + sy*POST_T)), -170, zb + 8)
                leg_y = bx(*sorted((xc, xc + sx*POST_T)), ya, yb, -170, zb + 8)
                base = bx(xa, xb, ya, yb, -170, zb)            # solid below the sensor = seat
                add += [isect(q, inner) for q in (leg_x, leg_y, base)]
        # zip-tie bar across the top of the posts (one tie over each sensor)
    # air sensor pocket: walls + roof, louvres in the plate under it
    (lx, ly, lz), (cx, cy, cz), _ = L.PAYLOAD["air_sensor"]
    pk = bx(cx - lx/2 - 1.9, cx + lx/2 + 1.9, cy - ly/2 - 1.9, cy + ly/2 + 1.9, -170, cz + lz/2 + 2) - bx(cx - lx/2 - 0.3, cx + lx/2 + 0.3, cy - ly/2 - 0.3, cy + ly/2 + 0.3, -171, cz + lz/2)
    pk = pk.cut(bx(cx + lx/2 - 4, cx + lx/2 + 3, cy - 3, cy + 3, cz - 2, cz + lz/2 - 1))   # cable exit
    add.append(isect(pk, inner))
    # bosses for the m_belly_deck legs (screw from below)
    for x, y in L.DECK["legs"]:
        add.append(isect(zcyl(x, y, -170, L.DECK["leg_z0"], 5.0), inner))
    s = s.fuse(*[a for a in add if a is not None]).clean()
    cuts = []
    for k, w in WINDOWS.items():
        (lx, ly, lz), (cx, cy, cz), _ = L.PAYLOAD[k]
        if w[0] == "box":
            cuts.append(rbox(cx - w[1]/2, cx + w[1]/2, cy - w[2]/2, cy + w[2]/2, -180, cz - lz/2 - 0.5, 2.0))
        else:
            cuts.append(zcyl(cx, cy, -180, cz - lz/2 - 0.5, w[1]))
    (lx, ly, lz), (cx, cy, cz), _ = L.PAYLOAD["air_sensor"]
    cuts += [bx(cx - lx/2 + 2 + 6*i, cx - lx/2 + 4 + 6*i, cy - ly/2 + 2, cy + ly/2 - 2, -180, -158) for i in range(4)]   # louvres
    cuts += [bx(170 + 5*i, 172.5 + 5*i, -20, 20, -180, -150) for i in range(2)]            # Pi exhaust / plate vents aft
    cuts += [zcyl(x, y, -180, L.DECK["leg_z0"] + 1, M3_CLR) for x, y in L.DECK["legs"]]
    cuts += [zcyl(x, y, -180, -140, M3_CLR) for x, y in L.BELLY_SCREWS]
    return s.cut(*cuts).clean()


if __name__ == "__main__":
    export(build(), "mount_belly_plate", "CF-PETG", fill=0.8, up=(0, 0, -1), notes="removable belly sensor plate, 4 thumb screws")
