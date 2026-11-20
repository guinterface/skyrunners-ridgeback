"""Electronics layout for the mini Ridgeback Scout (SR3_CONFIG=mini): ONE place for every position used by the
electronics mounts (m_*.py), the fuselage openings (f_fuse.py MINI block) and the purchased-part boxes (assemble_mini.py).

Frame: aircraft CAD frame, x aft from the wing-root leading edge, y right, z up, mm (same as design.py / ridgeback.glb x1000).
Tags: [V] read on a maker page 2026-11-19, [A] assumed, (MEASURE) = measure the real part before printing.

Openings (2026-11-19, replace the 11-02 hatches x -330..-175 / -165..-15, half width 55):
  the old openings had an 8 mm ledge on every side, leaving 139 x 94 mm (avionics) and 134 x 94 mm (battery) clear;
  the 140 x 135 mm battery could not come out at all [C]. New: the top hatches are cut by a horizontal plane at
  z -30, so they wrap down the shoulders and leave ~ +/-72 mm clear in the mid body [C, checked in mounts_check.py].
"""
# ------------------------------------------------------------------ openings
TOP_Z = -30.0                    # top hatches: shell removed above this plane
RIM_SIDE, RIM_END = 6.0, 6.0     # ledge width under the hatch edge (fused into the shell segment, LW-ASA)
OPENINGS = {
    # name: kind, x0, x1, plane z (top/bottom) or two points (plane), ledge at the sides, ledge at the ends
    "avionics": dict(kind="top", x0=-330.0, x1=-176.0, z=TOP_Z, rim=RIM_SIDE, rim_end=RIM_END),
    "battery":  dict(kind="top", x0=-164.0, x1=-3.0, z=TOP_Z, rim=RIM_SIDE, rim_end=RIM_END),
    "belly":    dict(kind="bottom", x0=38.5, x1=186.5, z=-150.0, rim=2.5, rim_end=0.0),     # rim measured in z: 6 reached 13 mm in along the curved belly     # ends rest on frames F3/F4 bosses
    "tail":     dict(kind="plane", x0=362.0, x1=515.0, a=(362.0, -118.0), b=(515.0, -86.5), rim=4.0, rim_end=RIM_END),
}
HATCH_GAP = 0.5

# ------------------------------------------------------------------ avionics cassette (between F1 x -330 and F2 x -170)
CAS = dict(x_fwd=-315.6, x_aft=-190.4, wall=2.4,          # outer faces of the two end walls
           deck_top=-62.0, deck_t=2.4, tab_top=-16.0, tab_t=3.0,
           clear_margin=2.0)                                # deck outline = clear opening - this
RAIL = dict(fwd=(-327.5, -316.0), aft=(-190.0, -172.5),      # rail block x ranges (bonded to F1 aft / F2 fwd face)
            hw=14.0, z0=-68.0, z1=-19.3, groove_w=6.4, groove_d=4.5, groove_bot=-64.8,
            insert_fwd=(-319.0, 9.0), insert_aft=(-187.5, 9.0))    # M3 heat-set insert (x, y) for the thumb screws
# items on the cassette: name: (dims x, y, z), centre (x, y, z bottom), mass g, tag
# Flight controller (club lead 11-19): CubePilot Cube Orange on its carrier (ADS-B carrier assumed, TO CONFIRM), not the Pixhawk 6C.
# [V docs.px4.io cubepilot_cube_orange]: Cube 38.25 x 38.25 x 22.3 mm, carrier 94.5 x 44.3 x 17.3 mm; "Cube includes vibration
# isolation on two of the IMUs" -> carrier HARD-mounted on 4 M3 nylon standoffs, no grommets. Carrier hole pattern (MEASURE).
# Mass: cube ~35 g [A, one retailer listing, not a datasheet]; carrier (MEASURE) ~40 g [A]; total 75 g [A] vs 34.6 g for the 6C [V].
FC = dict(carrier=(44.3, 94.5, 17.3), cube=(38.25, 38.25, 22.3), x=-244.0, standoff=4.0,
          holes=(36.3, 86.5), g_cube=35.0, g_carrier=40.0)       # carrier turned 90 deg: long side along y, servo rail at +y end [A]
FC_Z = CAS["deck_top"] + FC["standoff"]                           # carrier bottom -58, carrier top -40.7, cube top -18.4
AV_ITEMS = {
    "cube_carrier": (FC["carrier"], (FC["x"], 0.0, FC_Z), FC["g_carrier"], "[V size] carrier 94.5 x 44.3 x 17.3; mass (MEASURE) ~40 g [A]"),
    "cube_orange":  (FC["cube"], (FC["x"], 0.0, FC_Z + FC["carrier"][2]), FC["g_cube"], "[V size] 38.25 x 38.25 x 22.3; ~35 g [A retailer]; position on the carrier (MEASURE)"),
    "telemetry": ((32.0, 66.5, 16.5), (-296.8, -16.0, CAS["deck_top"] + 3.0), 23.5, "[V] SiK V3 66.5 x 32 x 16.5 (larger of the two listed sizes)"),
    "remote_id": ((22.0, 32.0, 10.0), (-296.8, 36.0, CAS["deck_top"] + 3.0), 13.5, "[A] Ruko R111S 32 x 22 x 10 listing (MEASURE)"),
    "rc_rx":     ((6.0, 25.0, 15.0), (-195.8, 46.0, -60.0), 1.0, "[A] RP2 V2 envelope with heat shrink, taped upright on the aft wall beside the PM07, antenna up (MEASURE)"),
}
# PM07 [V docs.holybro.com PM07 quick start: 68 x 50 x 10 mm, holes 45 x 45, 40.3 g] stands on the aft wall, facing forward
PM07 = dict(dims=(10.0, 68.0, 50.0), x_back=CAS["x_aft"] - CAS["wall"] - 5.0, zc=-36.0, holes=45.0, standoff=5.0, g=40.3)

# ------------------------------------------------------------------ battery
BAT_X, BAT_L, BAT_W, BAT_H = -47.6, 140.0, 135.0, 75.0      # 11-19: -58 (11-02 CG solve) + 10.4 mm aft to cancel the +149 g of mounts / Cube in the nose (mounts_mass.py) -> CG x 94
TRAY_TOP = -100.0
SLED = dict(t=2.0, wall=3.0, wall_h=22.0, frame=10.0, slide=36.0)   # sled base under the pack, end walls
SLED_X0 = BAT_X - BAT_L/2 - SLED["wall"]                     # -131 (flight position, against the stop)
SLED_X1 = BAT_X + BAT_L/2 + SLED["wall"]                     # +15
BAT_Z0 = TRAY_TOP + SLED["t"]                                 # pack bottom -98, top -23
STOP = dict(x0=SLED_X1 + 0.5, t=4.0, h=30.0, hw=50.0, guide_len=38.5, guide_t=3.0, guide_h=8.0, holes_x=SLED_X1 + 8.5)
STRAP_X = (BAT_X - 40.0, BAT_X + 36.0)                         # strap slots in the carbon tray (3.2 x 25 at y +/-62): x -87.6, -11.6

# ------------------------------------------------------------------ belly sensor plate (x 38.5..186.5, removed downward)
DECK = dict(x0=72.0, x1=168.0, y0=-34.0, y1=56.0, z_top=-100.0, t=2.0, legs=[(92.0, -30.0), (90.0, 52.0), (164.0, -30.0), (164.0, 52.0)], leg=8.0, leg_z0=-150.0)
# payload boxes: parts.toml box (c, dims) unless noted; the plate holds them at these positions
PAYLOAD = {
    "payload_computer": ((85.0, 56.0, 20.0), (110.0, 0.0, -87.0), "on the deck, 3 mm standoffs: parts.toml box z -90 raised 3 mm"),
    "payload_power":    ((25.4, 25.4, 9.5), (150.0, 42.0, -95.25), "on the deck; parts.toml box (y 40, z -100) went through the deck and touched the Pi: y +2, z +4.75"),
    "thermal_cam":      ((40.0, 30.0, 22.0), (65.0, -35.0, -126.0), "parts.toml x 60 moved +5 mm aft: x 40 sat over the F3 frame boss path"),
    "rgb_cam":          ((38.0, 38.0, 28.0), (65.0, 30.0, -124.0), "parts.toml x 60 moved +5 mm aft (same reason)"),
    "spot_sensor":      ((50.0, 40.0, 45.0), (125.0, 0.0, -125.0), "parts.toml box"),
    "nir_channel":      ((20.0, 16.0, 30.0), (125.0, 28.0, -125.0), "parts.toml box (option)"),
    "air_sensor":       ((25.0, 18.0, 12.0), (58.0, -4.0, -156.0), "MOVED from x -40 (under the battery, unreachable) to the plate front, in a vented pocket open to outside air"),
}
BELLY_SCREWS = [(42.0, -56.0), (42.0, 56.0), (182.5, -56.0), (182.5, 56.0)]   # 4 thumb screws up into F3/F4 bosses

# ------------------------------------------------------------------ tail cone panel (pusher ESC + servo regulator ride on it)
TAIL_SCREWS = [(365.0, -24.0), (365.0, 24.0), (513.0, -14.0), (513.0, 14.0)]   # vertical M3 button screws through the panel into m_tail_insert_block (end ledges)

# ------------------------------------------------------------------ pitot / airspeed (nose, ahead of F1)
PITOT = dict(x_plate=-358.0, t=3.0, tube_z=-75.0, tube_d=5.0, board=(29.0, 35.5, 16.5))   # PT40 OD (MEASURE); board [V? Holybro table]
