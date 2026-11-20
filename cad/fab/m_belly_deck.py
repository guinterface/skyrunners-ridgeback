"""Pi deck on the belly sensor plate (part of mount "belly_plate"): a 2 mm CF-PETG deck at z -102..-100 on 4 legs screwed
from below through the plate (M3 x 10 into heat-set inserts in the leg feet). Carries the Raspberry Pi 5 (M2.5 inserts on
its 58 x 49 hole pattern [V Raspberry Pi mechanical drawing]) and the Pololu D36V50F5 regulator (2 M2 holes, MEASURE).
It bridges over the 1610 nm spot sensor (0.5 mm above its box). Run: SR3_CONFIG=mini cadenv/bin/python m_belly_deck.py
"""
from m_common import export, bx, zcyl, rbox, M3_INS, M25_INS
import m_layout as L

D = L.DECK
PI_HOLES = (58.0, 49.0)
PI_STANDOFF = 3.0


def build():
    z1 = D["z_top"]; z0 = z1 - D["t"]
    s = rbox(D["x0"], D["x1"], D["y0"], D["y1"], z0, z1, 4.0)
    h = D["leg"]/2
    for x, y in D["legs"]:
        s = s.fuse(bx(x - h, x + h, y - h, y + h, D["leg_z0"], z0 + 0.1))
    (_, (pcx, pcy, pcz), _) = L.PAYLOAD["payload_computer"]
    for dx in (-PI_HOLES[0]/2, PI_HOLES[0]/2):
        for dy in (-PI_HOLES[1]/2, PI_HOLES[1]/2):
            s = s.fuse(zcyl(pcx + dx, pcy + dy, z1 - 0.1, z1 + PI_STANDOFF, 3.0))
    cuts = [zcyl(x, y, D["leg_z0"] - 1, D["leg_z0"] + 7, M3_INS) for x, y in D["legs"]]
    cuts += [zcyl(pcx + dx, pcy + dy, z1 - 4, z1 + PI_STANDOFF + 1, M25_INS) for dx in (-PI_HOLES[0]/2, PI_HOLES[0]/2) for dy in (-PI_HOLES[1]/2, PI_HOLES[1]/2)]
    (_, (rcx, rcy, _), _) = L.PAYLOAD["payload_power"]
    cuts += [zcyl(rcx + dx, rcy, z0 - 1, z1 + 1, 1.2) for dx in (-10.0, 10.0)]           # M2 (MEASURE vs Pololu drawing)
    cuts += [rbox(pcx - 22, pcx + 22, -16, 16, z0 - 1, z1 + 1, 4.0)]                      # air under the Pi, cable pass
    cuts += [rbox(D["x0"] + 12, D["x0"] + 20, 30, 50, z0 - 1, z1 + 1, 2.0)]               # camera ribbon pass
    return s.cut(*cuts)


if __name__ == "__main__":
    export(build(), "mount_belly_deck", "CF-PETG", fill=0.8, up=(0, 0, 1), notes="Pi deck on the belly plate")
