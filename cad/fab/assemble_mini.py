"""Purchased items for the smaller own design (SR3_CONFIG=mini, 2026-11-02): tubes, propulsion, battery, Sky4 avionics.
Used by assemble.py in place of its relay list. Masses: [S] store/maker page, [A] assumed (MEASURE on arrival).
Buy list with store links: ridgeback/docs/BUY_LIST_2026-11-02.md.
"""
import math
import numpy as np
from build123d import *
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from core import d, cyl_between, bx
import f_wing as FW, f_fuse as FF, f_boom as FB, f_tail as FT

RHO_CF = 1.55          # g/cm3 roll-wrapped CF [A]


def tube(p0, p1, od, wall):
    return cyl_between(p0, p1, od/2) - cyl_between(p0, p1, od/2 - wall)


def purchased_mini():
    P, cut = [], []
    def add(name, grp, solid, g, cg=None):
        P.append(dict(name=name, group=grp, solid=solid, mass_g=g, cg=cg))
    def ctube(name, p0, p1, od, wall, grp="tube"):
        L = float(np.linalg.norm(np.subtract(p1, p0)))
        add(name, grp, tube(p0, p1, od, wall), math.pi*(od**2 - (od - 2*wall)**2)/4*L/1e3*RHO_CF)
        return L
    xs = FW.SPAR_X
    # spars: 21/19 centre, 17/15 outer, 13/11 tip-inner (inside the 17) and 13/11 tip on the 10 deg polyhedral
    a, b = FW.SPAR_PARTS["inner"]
    Lc = ctube("tube_spar_centre_21x19", (xs, a, FW.ZS), (xs, b, FW.ZS), *d.INNER_SPAR)
    cut.append(("CF tube spar, centre (HaoZhong 21/19)", 21, 1.0, Lc, 1))
    for s in (1, -1):
        sd = "R" if s > 0 else "L"
        for key, (od, w) in (("outer", d.OUTER_SPAR), ("tip_inner", d.TIP_SPAR_T), ("tip", d.TIP_SPAR_T)):
            a, b = FW.SPAR_PARTS[key]
            za, zb = FW.spar_axis_z(a, a if key == "tip" else 0.0), FW.spar_axis_z(b, a if key == "tip" else 0.0)
            L = ctube(f"tube_spar_{key}_{sd}", (xs, s*a, za), (xs, s*b, zb), od, w)
            if s > 0:
                cut.append((f"CF tube spar, {key.replace('_', ' ')}", od, w, L, 2))
    # booms 30/28, jointed with a 27/25 sleeve (joint position: mini_boom.md; sleeve length [A] 250)
    for s in (1, -1):
        L = ctube(f"tube_boom_{'R' if s > 0 else 'L'}", (d.BOOM_FRONT_X, s*d.BOOM_Y, d.BOOM_Z), (d.BOOM_REAR_X, s*d.BOOM_Y, d.BOOM_Z), *d.BOOM_TUBE)
        add(f"tube_boom_sleeve_{'R' if s > 0 else 'L'}", "tube", None, math.pi*(27**2 - 25**2)/4*250/1e3*RHO_CF, cg=(250.0, s*d.BOOM_Y, d.BOOM_Z))
    cut += [("CF tube boom (two 1 m pieces per boom, bonded)", 30, 1.0, L, 2), ("CF tube boom joint sleeve [A length]", 27, 1.0, 250, 2)]
    # rear rods 6/4
    xr, RC = FW.ROD_C_X, FW.ROD_C_HALF
    zr = 0.5*(sum(FW.z_bounds(0, xr))/2 + sum(FW.z_bounds(RC, xr))/2)
    ctube("rod_rear_centre", (xr, -RC, zr), (xr, RC, zr), 6.0, 1.0)
    (xa, ya), (xb, yb) = FW.ROD_O
    za, zb = sum(FW.z_bounds(ya, xa))/2, sum(FW.z_bounds(yb, xb))/2
    for s in (1, -1):
        Lo = ctube(f"rod_rear_outer_{'R' if s > 0 else 'L'}", (xa, s*ya, za), (xb, s*yb, zb), 6.0, 1.0)
    cut += [("CF tube rear rod, centre", 6, 1.0, 2*RC, 1), ("CF tube rear rod, outer", 6, 1.0, Lo, 2)]
    # legs 8/6
    for i, (dx, dy, _) in enumerate([(0, 0, 0)] + FB._four()):
        for sx in (-1, 1):
            x = d.FRONT_MOTOR_X + dx + sx*FB.ROD["dx"]; y = d.BOOM_Y + dy
            Lg = ctube(f"rod_leg_{i}_{sx}", (x, y, FB.ROD["bot"]), (x, y, FB.ROD["top"]), 8.0, 1.0)
    cut.append(("CF tube landing leg", 8, 1.0, Lg, 8))
    # tail spars 6/4 carbon (no VHF element on this aircraft)
    for s in (1, -1):
        a_, b_ = FT.line(FT.SPAR["f"], FT.SPAR["u0"], FT.SPAR["u1"])
        sol = tube(a_, b_, FT.SPAR["od"], FT.SPAR["wall"]); sol = sol if s > 0 else sol.mirror(Plane.XZ)
        Lt = FT.SPAR["u1"] - FT.SPAR["u0"]
        add(f"tube_tail_spar_{'R' if s > 0 else 'L'}", "tube", sol, math.pi*(36 - 16)/4*Lt/1e3*RHO_CF)
    cut += [("CF tube tail spar", 6, 1.0, Lt, 2), ("CF rod aileron joiner", 3, None, FW.AIL[1] - FW.AIL[0] - 4, 2),
            ("Glass/CF rod ruddervator joiner", 3, None, FT.RV_U[1] - FT.RV_U[0], 2),
            ("Printed shim, 17/15 end inside the 21/19", 19, 1.0, 100, 2), ("Printed shim, 13/11 end inside the 17/15", 15, 1.0, 100, 2)]
    # propulsion
    zseat = FB.PY["ztop"] + FB.PLATE["t"]
    M = d.LIFT_MOTOR
    for i, (dx, dy, _) in enumerate([(0, 0, 0)] + FB._four()):
        x, y = d.FRONT_MOTOR_X + dx, d.BOOM_Y + dy
        add(f"motor_MN5008_{i}", "motor", Cylinder(M["d"]/2, M["h"], align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, zseat))), M["g"])
        add(f"prop_P18_{i}", "prop", Cylinder(d.LIFT_PROP_D/2, 4).moved(Location((x, y, zseat + M["h"] + 8))), 31)        # [A] P18x6.1 mass NOT FOUND
        add(f"esc_alpha40_{i}", "avionics", bx(x + 25, x + 89.5, y - 7.35, y + 7.35, d.BOOM_Z - 46.4, d.BOOM_Z - 17), 54.5)   # [S uav-en.tmotor.com alpha_0502] 64.5 x 29.4 x 14.7 mm, 54.5 g with cables, on its side
    PM = d.PUSH_MOTOR
    add("motor_pusher_AT3520", "motor", Cylinder(PM["d"]/2, PM["h"], rotation=(0, 90, 0), align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((d.PUSHER_X + 5, 0, d.PUSHER_Z))), PM["g"])
    add("prop_pusher_12x6E", "prop", Cylinder(d.PUSH_PROP_D/2, 4, rotation=(0, 90, 0)).moved(Location((d.PUSHER_X + PM["h"] + 15, 0, d.PUSHER_Z))), 28)   # [A]
    E = FF.PUSH_ESC; (lx, ly, lz) = E["dims"]                                   # on fuse_pusher_esc_tray (11-03)
    add("esc_pusher_alpha40", "avionics", bx(E["x"] - lx/2, E["x"] + lx/2, -ly/2, ly/2, E["z"], E["z"] + lz), 54.5)   # [S] 54.5 g
    R = FF.SREG; (lx, ly, lz) = R["dims"]                                       # PLACEHOLDER size, model unknown
    add("servo_regulator_PLACEHOLDER", "avionics", bx(R["x"] - lx/2, R["x"] + lx/2, -ly/2, ly/2, R["z"], R["z"] + lz), 20)   # [A] 20 g
    # battery
    B = FF.BAT
    zb = FF.TRAY["ztop"] + (2.0 if FF.MINI else 0.0)                                # 11-19: on the 2 mm m_battery_sled
    add("battery_6S6P_P50B", "battery", bx(B["x"] - B["l"]/2, B["x"] + B["l"]/2, -B["w"]/2, B["w"]/2, zb, zb + B["h"]), d.BATTERY["g"])
    # avionics on the removable cassette (m_av_cassette, positions in m_layout, 2026-11-19). Flight controller = CubePilot Cube
    # Orange on its carrier (club lead 11-19, replaces the Pixhawk 6C); node name kept "pixhawk_6C" so data/parts.toml still maps.
    import m_layout as ML
    def lbox(dims, c):                     # m_layout gives the bottom z
        return Box(*dims).moved(Location((c[0], c[1], c[2] + dims[2]/2)))
    I = ML.AV_ITEMS
    add("pixhawk_6C", "avionics", Compound([lbox(*I["cube_carrier"][:2]), lbox(*I["cube_orange"][:2])]),
        I["cube_carrier"][2] + I["cube_orange"][2])                                    # [A] 75 g total, MEASURE
    for n, k in (("telemetry_radio", "telemetry"), ("rc_receiver", "rc_rx"), ("remote_id_ruko_R111S", "remote_id")):
        add(n, "avionics", lbox(*I[k][:2]), I[k][2])
    P7 = ML.PM07
    add("power_module_PM07", "avionics", bx(P7["x_back"] - P7["dims"][0], P7["x_back"], -P7["dims"][1]/2, P7["dims"][1]/2,
                                            P7["zc"] - P7["dims"][2]/2, P7["zc"] + P7["dims"][2]/2), P7["g"])   # [V] 40.3 g, on the cassette aft wall
    PT = ML.PITOT; bd = PT["board"]
    add("airspeed_sensor", "avionics", bx(PT["x_plate"] + PT["t"] + 2, PT["x_plate"] + PT["t"] + 2 + bd[2], -bd[1]/2, bd[1]/2, -50 - bd[0]/2, -50 + bd[0]/2), 17.4)   # MS5525DSO on m_pitot_mount
    g_ = FW.z_bounds(200.0, 125.0)[1]
    add("gnss_M9N", "avionics", Cylinder(25, 14.4, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((125.0, 200.0, g_ + 4 + 2.4))), 32)   # M10 dia 50 x 14.4, 32 g [V holybro.com], in m_gps_holder (2.4 base)
    # servos KST X10 (30 x 35.5 x 10 [S KST X10 V8 PDF]; mass [A] 23 g)
    c, _, xle, _ = FW.station(FW.SERVO_Y); xc = 0.5*(xle + FW.SPLIT*c + FW.HINGE_X - FW.AIL_GAP/2)
    for s in (1, -1):
        zl = FW.z_bounds(FW.SERVO_Y, xc)[0]
        add(f"servo_aileron_{'R' if s > 0 else 'L'}", "avionics", Box(30, 35.5, 10).moved(Location((xc, s*FW.SERVO_Y, zl + 6))), 23)
        loc = FT.frame_at(FT.SERVO["u"], FT.SERVO["f"])
        sv = Box(30, 35.5, 10).moved(loc*Location((0, 0, -3)))
        add(f"servo_ruddervator_{'R' if s > 0 else 'L'}", "avionics", sv if s > 0 else sv.mirror(Plane.XZ), 23)
    # lumps
    add("wiring_harness", "lump", None, 300, cg=(40.0, 0, -90.0))       # [A] mini_wiring lengths, copper + connectors
    add("hardware_inserts_bolts", "lump", None, 150, cg=(d.CG_X, 0, -40.0))   # [A]
    add("epoxy_bond_lines", "lump", None, 200, cg=(120.0, 0, 0))          # [A]
    return P, cut
