"""Export the electronics mounts and hatches as a web 3D model + their data (SR3_CONFIG=mini, 2026-11-19).

  docs/assets/mounts.glb : one node per mount ("mount:<id>") and per hatch/panel ("hatch:<id>"), child node
                           "<node>:hardware" for screws (darker), SAME frame/units as ridgeback.glb (CAD x aft, y right,
                           z up, metres; tools/export_model.py), each mesh simplified so the file stays <= 1.5 MB.
  data/mounts.json       : per mount: what it holds (parts.toml ids), fastening, removal steps, tools, time (estimate),
                           connectors, wiring route, material, mass (CAD volume x density), hardware to buy (store pages read
                           2026-11-19), motion (for the page to animate opening / pulling out), and which ridgeback.glb
                           nodes ride along (carries_nodes).
Inputs: the m_*.py STEP files in $MOUNTS_OUT/step and the fuselage build in $MOUNTS_OUT/build/sr3_mini_out/step
(cad/fab: SR3_CONFIG=mini; run each m_*.py and build.py f_fuse with SKY_BUILD=$MOUNTS_OUT/build first).
Run: SR3_CONFIG=mini /scratch/users/gsbonfim/skyrunners/cadenv/bin/python tools/export_mounts.py
"""
import json, math, os, sys
from pathlib import Path
import numpy as np, trimesh
ROOT = Path(__file__).resolve().parents[1]
FAB = ROOT / "cad/fab"
os.environ.setdefault("SR3_CONFIG", "mini")
sys.path[:0] = [str(FAB), str(FAB.parent), str(FAB.parent / "parts")]
from build123d import import_step                       # noqa: E402
import m_layout as L                                    # noqa: E402
from m_common import OUT, mesh                          # noqa: E402
import f_misc as FM, f_wing as FW, f_boom as FB         # noqa: E402

FUSE = OUT / "build/sr3_mini_out/step"
S = 1e-3
FILAMENT = [232, 122, 36, 255]        # printed mounts: orange (CF-PETG is black in real life; orange so they stand out)
HATCH = [214, 216, 208, 255]          # LW-ASA hatches, shell colour of ridgeback.glb
HARD = [55, 57, 60, 255]              # screws, inserts
FACES = 2500
READ = "2026-11-19"


def meta(name):
    return json.loads((OUT / "meta" / f"{name}.json").read_text())


def tri(solid, faces=FACES):
    m = mesh(solid, 0.15, 0.3)
    if len(m.faces) > faces:
        try:
            m = m.simplify_quadric_decimation(face_count=faces)
        except Exception:
            pass
    m.apply_scale(S)
    return m


def screw(x, y, z_head_bottom, down=False, head_d=11.0, head_h=7.0, length=12.0):
    """Knurled thumb screw / button screw envelope: head + shank (mm in, mesh in metres out)."""
    sgn = -1 if down else 1
    h = trimesh.creation.cylinder(radius=head_d/2, height=head_h, sections=20)
    h.apply_translation((x, y, z_head_bottom + sgn*head_h/2))
    sh = trimesh.creation.cylinder(radius=1.5, height=length, sections=10)
    sh.apply_translation((x, y, z_head_bottom - sgn*length/2))
    m = trimesh.util.concatenate([h, sh]); m.apply_scale(S)
    return m


# ------------------------------------------------------------------ hardware to buy (prices read 2026-11-19 [V], see MOUNTS.md)
HW = {
    "thumb": dict(item="M3 x 12 knurled thumb screw, 304 stainless (5-pack)", store="Harfington (uxcell)", link="https://www.harfington.com/products/p-1479356", price_usd=7.77, read_on=READ),
    "retainer": dict(item="Nylon retaining washer #4 (50-pack): grips the thumb-screw thread so it stays in the tab (fit not checked on M3)", store="Micro Fasteners WRT04", link="https://www.microfasteners.com/products/wrt04", price_usd=2.40, read_on=READ),
    "insert": dict(item="CNC Kitchen heat-set insert M3 x 5.7 (100)", store="CNC Kitchen", link="https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces", price_usd=10.90, read_on=READ),
    "button": dict(item="M3 x 8 stainless button-head hex screw (20)", store="Micro Fasteners SBMS3008", link="https://www.microfasteners.com/products/sbms3008", price_usd=3.30, read_on=READ),
    "strap": dict(item="Lumenier Kevlar battery strap 20 x 500 mm (2) - buckle strap with rubber grip, not hook-and-loop", store="RaceDayQuads", link="https://www.racedayquads.com/products/lumenier-indestructible-kevlar-lipo-strap-20x500mm-2pcs", price_usd=10.49, read_on=READ),
    "micro_strap": dict(item="RDQ Kevlar micro strap 180 x 10 mm (3)", store="RaceDayQuads", link="https://www.racedayquads.com/products/rdq-180mm-kevlar-micro-battery-strap-w-woven-rubber-grip-metal-buckle-3pk", price_usd=6.99, read_on=READ),
    "m25_kit": dict(item="Adafruit 3299 M2.5 nylon screw and standoff set (380 pcs)", store="Adafruit", link="https://www.adafruit.com/product/3299", price_usd=16.95, read_on=READ),
    "m3_kit": dict(item="M3 nylon standoff kit, 260 pcs (Cube carrier 4 mm standoffs, PM07 5 mm standoffs)", store="Harfington (uxcell)", link="https://www.harfington.com/products/p-1498270", price_usd=9.79, read_on=READ),
    "magnets": dict(item="1/4 x 1/8 in N42 disc magnets (100) for the 2 top hatches (8 per hatch + rims)", store="Total Element", link="https://www.totalelement.com/products/1-4-x-1-8-inch-neodymium-rare-earth-permanent-disc-magnets-n42-100-pack", price_usd=22.79, read_on=READ),
}
def hw(key, qty, note=""):
    d = dict(HW[key], qty=qty)
    if note:
        d["note"] = note
    return d


def fa(name):
    return f"{name}"


MOUNTS = [
    dict(id="avionics_tray", name="Avionics cassette (removable tray in the nose)", kind="mount", nodes=["mount:avionics_tray"],
         parts=["mount_avionics_cassette"],
         holds=["pixhawk", "pm07", "rc_rx", "telemetry", "remote_id"],
         note_holds="flight controller is now the CubePilot Cube Orange on its carrier (club lead 11-19); parts.toml id 'pixhawk' still names the 6C",
         fastening="2 tongues slide down vertical grooves in 2 rail blocks (F1, F2); 2 captive M3 thumb screws through the end-wall tabs into heat-set inserts in the rail blocks. Cube carrier hard-mounted on 4 M3 nylon standoffs (the Cube isolates its IMUs inside); radios and Remote ID on hook-and-loop through deck slots; PM07 on 4 M3 standoffs on the aft wall.",
         remove_steps=["Lift the avionics hatch off (magnets).", "Unplug the battery XT90 in the battery bay (or keep the battery out).",
                       "Unplug at the cassette: 5 ESC feeds (XT60) and 2 XT30 (servo regulator, payload) from the PM07 leads; servo/ESC signal leads from the carrier servo rail (9 x 3-pin, labelled M1-M5, A1-A4); GPS (GPS1), airspeed (I2C), payload MAVLink (TELEM2).",
                       "Undo the 2 thumb screws (they stay in the tabs).", "Lift the cassette straight up by its two end-wall handles (110 mm)."],
         tools="none", time_to_remove_s=240, time_note="estimate [A]: ~20 plugs at ~8 s + screws + hatch; not timed on hardware. USB and microSD of the Cube are reachable with the hatch off, without removing anything.",
         connectors=[dict(part="pm07", connector="XT90H (battery input)", goes_to="battery", faces="hatch side (mated pair lies on top of the pack front in the battery bay)"),
                     dict(part="pm07", connector="XT60 x 5 (14 AWG feeds)", goes_to="esc_lift x4, esc_pusher", faces="hatch side (pigtails out of the aft cable window)"),
                     dict(part="pm07", connector="XT30 x 2", goes_to="servo_reg, payload_power", faces="hatch side"),
                     dict(part="pm07", connector="6-pin power cable", goes_to="pixhawk (Cube carrier POWER1)", faces="hatch side"),
                     dict(part="pixhawk", connector="servo rail 0.1 in headers (MAIN 1-5 ESCs, AUX 1-4 servos)", goes_to="esc_lift, esc_pusher, servos", faces="hatch side (+y end of the carrier, turned 90 deg) [A: MEASURE on the ADS-B carrier]"),
                     dict(part="pixhawk", connector="JST-GH 10-pin GPS1", goes_to="gnss", faces="hatch side"),
                     dict(part="pixhawk", connector="JST-GH 4-pin I2C", goes_to="airspeed", faces="hatch side"),
                     dict(part="pixhawk", connector="JST-GH 6-pin TELEM1", goes_to="telemetry (on the cassette)", faces="hatch side"),
                     dict(part="pixhawk", connector="JST-GH 6-pin TELEM2", goes_to="payload_computer", faces="hatch side"),
                     dict(part="pixhawk", connector="RCIN (3-pin) / serial", goes_to="rc_rx (on the cassette)", faces="hatch side"),
                     dict(part="pixhawk", connector="JST-GH serial", goes_to="remote_id (on the cassette)", faces="hatch side")],
         wiring_route="Power: battery XT90 in the battery bay -> PM07 lead over the F2 ring (frames are open rings) -> PM07 on the cassette aft wall; 5 ESC feeds + 2 XT30 leave by the aft cable windows with a 100 mm slack loop each, then run aft along the left fuselage wall beside the battery (y 68..83 gap) to the wing root. Signals: carrier servo rail leads run aft along the right wall; GPS lead up into the wing root; airspeed I2C forward through F1. Labels: every lead gets a printed label in heat shrink at both ends (M1..M5, A1..A4, GPS, I2C, TEL2, BAT, ESC1..5, SREG, PAY).",
         material="CF-PETG", hardware=[hw("thumb", 2, "2 of the 6 thumb screws (buy 2 packs of 5 for this + the belly plate)"), hw("retainer", 2), hw("insert", 2), hw("m3_kit", 1, "4 standoffs for the Cube carrier, 4 for the PM07"), hw("micro_strap", 1, "holds the SiK radio and Remote ID through the deck slots")],
         motion=dict(type="lift", vector_mm=[0, 0, 1], distance_mm=110, after=["hatch:avionics"]),
         carries_nodes=["part:pixhawk_6C", "part:power_module_PM07", "part:telemetry_radio", "part:rc_receiver", "part:remote_id_ruko_R111S"]),
    dict(id="avionics_rails", name="Cassette rail blocks (bonded to frames F1 and F2)", kind="mount", nodes=["mount:avionics_rails"],
         parts=["mount_av_rail_fwd", "mount_av_rail_aft"], holds=[], fixed=True,
         fastening="epoxy to the F1 aft face / F2 front face and to the shell, before the shell segments are joined; 1 M3 heat-set insert each",
         remove_steps=["Not removable (bonded)."], tools="none", time_to_remove_s=None, connectors=[], wiring_route="", material="CF-PETG",
         hardware=[], motion=None, carries_nodes=[]),
    dict(id="battery_sled", name="Battery sled", kind="mount", nodes=["mount:battery_sled"], parts=["mount_battery_sled"], holds=["battery"],
         fastening="sled + pack sit on the carbon tray against the aft end stop (sets the CG every time), between 2 side guides; 2 straps through the tray slots at x -87.6 and -11.6",
         remove_steps=["Lift the battery hatch off (magnets).", "Unplug the XT90 (on top of the pack front) and the balance lead.", "Open the 2 straps.",
                       "Pull the front loop: the sled slides 36 mm forward.", "Lift the pack and sled out."],
         tools="none", time_to_remove_s=40, time_note="estimate [A], not timed",
         connectors=[dict(part="battery", connector="XT90H", goes_to="pm07", faces="hatch side (on top of the pack, front end)"),
                     dict(part="battery", connector="JST-XH 7-pin balance lead", goes_to="charger (ground) - tucked on the pack top", faces="hatch side")],
         wiring_route="Pack lead exits the front top of the pack; the PM07 input lead comes back over F2 from the cassette; the mated XT90 lies on the pack top under the hatch.",
         material="CF-PETG", hardware=[hw("strap", 1, "2 straps; pack + sled + tray girth ~430 mm [C], strap 500 mm")],
         motion=dict(type="slide", vector_mm=[-1, 0, 0], distance_mm=L.SLED["slide"], then=dict(type="lift", vector_mm=[0, 0, 1], distance_mm=120), after=["hatch:battery"]),
         carries_nodes=["part:battery_6S6P_P50B"]),
    dict(id="battery_stop", name="Battery end stop and side guides", kind="mount", nodes=["mount:battery_stop"], parts=["mount_battery_stop"], holds=[], fixed=True,
         fastening="2 M3 x 8 screws + nylon nuts through the carbon tray (holes at x 33.9, y +/-30)", remove_steps=["Stays in (2 screws if it must come out)."],
         tools="2 mm hex key (only to remove the stop)", time_to_remove_s=None, connectors=[], wiring_route="", material="CF-PETG",
         hardware=[hw("button", 1, "2 of the 20")], motion=None, carries_nodes=[]),
    dict(id="belly_plate", name="Belly sensor plate (removable, with the Pi deck)", kind="mount", nodes=["hatch:belly", "mount:belly_plate"],
         parts=["mount_belly_plate", "mount_belly_deck"],
         holds=["payload_computer", "payload_power", "thermal_cam", "rgb_cam", "spot_sensor", "air_sensor", "nir_channel"],
         fastening="4 captive M3 thumb screws up into heat-set inserts in bosses on frames F3 and F4; sensors on corner posts with 1 zip tie each; Pi 5 on 4 M2.5 nylon standoffs on the deck; deck on 4 legs, M3 screws from below into inserts.",
         remove_steps=["Turn the drone over (or reach under it on its stand).", "Undo the 4 thumb screws (they stay in the plate).",
                       "Lower the plate ~60 mm on its pigtails.", "Unplug the 2 plugs: XT30 power and JST-GH 6-pin MAVLink.", "Take the whole sensor set to the bench."],
         tools="none", time_to_remove_s=60, time_note="estimate [A], not timed",
         connectors=[dict(part="payload_power", connector="XT30", goes_to="pm07", faces="inside, on a 150 mm pigtail (reach it with the plate lowered)"),
                     dict(part="payload_computer", connector="JST-GH 6-pin (UART on the Pi GPIO via adapter)", goes_to="pixhawk TELEM2", faces="inside, on a 150 mm pigtail")],
         wiring_route="Both airframe leads come from the cassette along the fuselage floor under the battery tray (z -102..-165 is empty now) to x ~40, slack loop at the plate. All sensor cables (USB to the PureThermal, CSI ribbon, I2C to the spot sensor and SHT45) stay on the plate.",
         material="CF-PETG", hardware=[hw("thumb", 4), hw("retainer", 4), hw("insert", 8, "4 in F3/F4 bosses, 4 in the deck legs"), hw("m25_kit", 1, "Pi 5 standoffs, camera screws")],
         motion=dict(type="slide", vector_mm=[0, 0, -1], distance_mm=100, after=[]),
         carries_nodes=["payload_computer", "payload_power", "thermal_cam", "rgb_cam", "spot_sensor", "air_sensor", "nir_channel"]),
    dict(id="tail_panel", name="Tail-cone access panel (pusher ESC + servo regulator ride on it)", kind="mount", nodes=["hatch:tail", "mount:tail_panel"],
         parts=["mount_tail_panel", "fuse_pusher_esc_tray", "fuse_servo_reg_mount"], holds=["esc_pusher", "servo_reg"],
         fastening="4 M3 x 8 button-head screws into heat-set inserts in 4 small blocks bonded on the end ledges; the existing ESC tray and regulator mount are bonded to the panel instead of the shell floor; ESC and regulator on 2 cable ties each",
         remove_steps=["Undo the 4 screws (2 mm hex key).", "Lower the panel ~50 mm: ESC and regulator come with it on their leads.",
                       "To take them off: unplug XT60 (ESC feed), XT30 (regulator in), 2 servo leads, and the 3 motor bullets."],
         tools="2 mm hex key", time_to_remove_s=90, time_note="estimate [A], not timed",
         connectors=[dict(part="esc_pusher", connector="XT60", goes_to="pm07", faces="panel side (reach after lowering)"),
                     dict(part="esc_pusher", connector="3 x 3.5 mm bullets", goes_to="motor_pusher", faces="aft, at the firewall"),
                     dict(part="esc_pusher", connector="servo lead", goes_to="pixhawk MAIN 5", faces="panel side"),
                     dict(part="servo_reg", connector="XT30 in, servo lead out", goes_to="pm07 / carrier servo rail power", faces="panel side")],
         wiring_route="Feeds come aft along the left fuselage wall from the cassette over the battery bay floor and through F4; 150 mm slack each at the panel so it drops without unplugging.",
         material="CF-PETG", hardware=[hw("button", 1, "4 of the 20"), hw("insert", 4)],
         motion=dict(type="slide", vector_mm=[0, 0, -1], distance_mm=50, after=[]),
         carries_nodes=["part:esc_pusher_alpha40", "part:servo_regulator_PLACEHOLDER"]),
    dict(id="tail_insert_blocks", name="Tail-panel insert blocks (bonded, 4)", kind="mount", nodes=["mount:tail_insert_blocks"],
         parts=[f"mount_tail_insert_block_{i}" for i in range(4)], holds=[], fixed=True, fastening="epoxy on the end ledges of fuse_seg4",
         remove_steps=["Not removable."], tools="none", time_to_remove_s=None, connectors=[], wiring_route="", material="CF-PETG", hardware=[], motion=None, carries_nodes=[]),
    dict(id="esc_cradle", name="Lift ESC cradle (one per boom nacelle, 4)", kind="mount", nodes=["mount:esc_cradle"], parts=["mount_esc_cradle"], qty=4, holds=["esc_lift"],
         fastening="2 C-clips snap on the 30 mm boom tube; ESC on its side on the floor, 2 zip ties; nacelle halves closed with tape (never glue)",
         remove_steps=["Peel the tape and open the outboard nacelle half.", "Cut the 2 zip ties.", "Unplug the 3 motor bullets, the 14 AWG feed (XT60 at the wing root) and the signal lead."],
         tools="side cutters (zip ties)", time_to_remove_s=120, time_note="estimate [A], not timed",
         connectors=[dict(part="esc_lift", connector="3 x 3.5 mm bullets", goes_to="motor_lift", faces="forward, up the pylon"),
                     dict(part="esc_lift", connector="14 AWG feed + signal lead", goes_to="pm07 / carrier servo rail", faces="inboard, along the boom bore")],
         wiring_route="Feed and signal run inside the boom tube to the wing saddle, then through the wing to the root junction (existing XT60 wing-break pairs).",
         material="CF-PETG", hardware=[], motion=None, carries_nodes=["part:esc_alpha40_0", "part:esc_alpha40_1", "part:esc_alpha40_2", "part:esc_alpha40_3"],
         instances_mm="right-front shown; the other 3 are f_boom._four() translations"),
    dict(id="gps_holder", name="GPS holder on the right wing pad", kind="mount", nodes=["mount:gps_holder"], parts=["mount_gps_holder"], holds=["gnss"],
         fastening="cup screwed to the existing misc_gnss_pad_R with 4 M3 x 8 into its inserts; puck on one VHB pad, arrow forward (front notch)",
         remove_steps=["Undo 4 screws (2 mm hex key) or peel the puck out of the cup.", "Unplug the GPS lead at the wing root."],
         tools="2 mm hex key", time_to_remove_s=60, time_note="estimate [A]",
         connectors=[dict(part="gnss", connector="JST-GH 10-pin", goes_to="pixhawk GPS1", faces="aft slot into the pad hole")],
         wiring_route="Cable down the pad hole, inside the wing to the root, into the fuselage at the wing saddle, forward to the cassette. Keep the ESC feeds >= 100 mm away from the puck [A].",
         material="CF-PETG", hardware=[hw("button", 1, "4 of the 20 (M3 x 8 into the pad inserts)")], motion=None, carries_nodes=["part:gnss_M9N"]),
    dict(id="pitot_mount", name="Pitot and airspeed bulkhead in the nose", kind="mount", nodes=["mount:pitot_mount"], parts=["mount_pitot_bulkhead"], holds=["airspeed"],
         fastening="bulkhead bonded inside the nose cap at x -352; PT40 tube through the nose tip and the bulkhead; MS5525 board on 2 M2.5 inserts on the aft face",
         remove_steps=["Take the avionics cassette out.", "Reach forward past F1: unplug the I2C lead, undo 2 M2.5 screws, pull the 2 silicone tubes off."],
         tools="Phillips/hex for M2.5", time_to_remove_s=300, time_note="estimate [A], includes the cassette",
         connectors=[dict(part="airspeed", connector="JST-GH 4-pin I2C", goes_to="pixhawk I2C", faces="aft, toward the hatch")],
         wiring_route="I2C lead aft through the open F1 ring to the carrier.", material="CF-PETG", hardware=[hw("m25_kit", 0, "screws from the Pi kit")],
         motion=None, carries_nodes=["part:airspeed_sensor"]),
    dict(id="servo_bays", name="Servos (existing pockets)", kind="existing", nodes=[], parts=[], holds=["servos"],
         fastening="existing CAD: aileron servos in the wing pockets at SERVO_Y (f_wing), ruddervator servos in the tail roots (f_tail); not changed here",
         remove_steps=["Open the servo cover (existing design)."], tools="see the build guide", time_to_remove_s=None, connectors=[dict(part="servos", connector="servo lead (60 cm extensions)", goes_to="pixhawk AUX 1-4", faces="wing root / boom")],
         wiring_route="existing build guide", material="", hardware=[], motion=None, carries_nodes=[]),
    dict(id="motor_mounts", name="Motors (existing)", kind="existing", nodes=[], parts=[], holds=["motor_lift", "motor_pusher"],
         fastening="existing CAD: MN5008 on boom_motor_plate (carbon) on the pylons; AT3520 on fuse_firewall. Motor hole patterns are still PLACEHOLDERS (MEASURE).",
         remove_steps=["4 motor screws each."], tools="hex key", time_to_remove_s=None, connectors=[], wiring_route="", material="", hardware=[], motion=None, carries_nodes=[]),
]
HATCHES = [
    dict(id="avionics", name="Avionics hatch (top, magnets)", kind="hatch", nodes=["hatch:avionics"], parts=["fuse_hatch_avionics"], material="LW-ASA",
         fastening="sits on the 6 mm ledge fused into the shell; 4 magnet pairs (6.35 x 3.2) in the ledge and hatch [A count]", tools="none", time_to_remove_s=5,
         motion=dict(type="lift", vector_mm=[0, 0, 1], distance_mm=80), hardware=[hw("magnets", 1, "16 used of the 100 for both top hatches")]),
    dict(id="battery", name="Battery hatch (top, magnets)", kind="hatch", nodes=["hatch:battery"], parts=["fuse_hatch_battery"], material="LW-ASA",
         fastening="same as the avionics hatch", tools="none", time_to_remove_s=5, motion=dict(type="lift", vector_mm=[0, 0, 1], distance_mm=80), hardware=[]),
]


def tail_normal():
    (xa, za), (xb, zb) = L.OPENINGS["tail"]["a"], L.OPENINGS["tail"]["b"]
    t = np.array([xb - xa, 0, zb - za]); t /= np.linalg.norm(t)
    return [round(float(t[2]), 4), 0.0, round(float(-t[0]), 4)]


def solid_of(name):
    p = (OUT / "step" / f"{name}.step")
    if not p.exists():
        p = FUSE / f"{name}.step"
    return import_step(str(p))


def mass_of(name):
    p = OUT / "meta" / f"{name}.json"
    if p.exists():
        m = json.loads(p.read_text()); return m["mass_g"], m["density_g_cm3"], m["fill"]
    m = json.loads((OUT / "build/sr3_mini_out/meta" / f"{name}.json").read_text())
    import core
    return m["mass_g"], core.MATERIALS[m["material"]]["rho"], m["fill"]


def hardware_meshes(mid):
    if mid == "avionics_tray":
        return [screw(*L.RAIL["insert_" + w], L.CAS["tab_top"]) for w in ("fwd", "aft")]
    if mid == "belly_plate":
        import f_fuse as FF
        return [screw(x, y, FF._ztop_at(x, y, 0.0) - 0.0, down=True) for x, y in L.BELLY_SCREWS]
    if mid == "tail_panel":
        import f_fuse as FF
        return [screw(x, y, FF._ztop_at(x, y, 0.0), down=True, head_d=5.7, head_h=1.7, length=8) for x, y in L.TAIL_SCREWS]
    return []


def main():
    scene = trimesh.Scene()
    out = []
    for M in MOUNTS + HATCHES:
        names = M.get("parts", [])
        g = 0.0; dens = {}
        for n in names:
            mg, rho, fill = mass_of(n)
            g += mg; dens[n] = dict(density_g_cm3=rho, fill=fill, mass_g=mg)
        qty = M.get("qty", 1)
        rec = {k: v for k, v in M.items() if k not in ("parts", "hardware", "nodes")}
        rec["cad_parts"] = names
        rec["mass_g"] = round(g*qty, 1)
        rec["mass_note"] = "CAD volume x density x fill (core.MATERIALS: CF-PETG 1.30, LW-ASA 0.60 [A] g/cm3)" + (f", x{qty} copies" if qty > 1 else "")
        rec["mass_parts"] = dens
        rec["hardware_to_buy"] = M.get("hardware", [])
        rec["node"] = M["nodes"][0] if M.get("nodes") else None
        rec["nodes"] = M.get("nodes", [])
        if rec.get("motion") and rec["motion"].get("vector_mm") == "tail_normal":
            rec["motion"] = dict(rec["motion"], vector_mm=tail_normal())
        if rec.get("motion"):
            rec["motion"]["frame"] = "CAD mm, x aft, y right, z up; vector_mm is a unit direction, distance_mm the travel"
        out.append(rec)
        # geometry: first node = main part(s), second node (if any) = the rest
        if not names:
            continue
        nodes = M["nodes"]
        split = {"belly_plate": (["mount_belly_plate"], ["mount_belly_deck"]),
                 "tail_panel": (["mount_tail_panel"], ["fuse_pusher_esc_tray", "fuse_servo_reg_mount"])}.get(M["id"], (names, []))
        col = HATCH if M["kind"] == "hatch" else FILAMENT
        for node, ns in zip(nodes, split):
            if not ns:
                continue
            ms = [tri(solid_of(n)) for n in ns]
            m = trimesh.util.concatenate(ms)
            c = HATCH if node.startswith("hatch:") and M["id"] not in ("belly_plate", "tail_panel") else (FILAMENT if not node.startswith("hatch:") else [200, 110, 40, 255])
            m.visual.face_colors = c
            scene.add_geometry(m, node_name=node, geom_name=node)
        hwm = hardware_meshes(M["id"])
        if hwm:
            h = trimesh.util.concatenate(hwm); h.visual.face_colors = HARD
            scene.add_geometry(h, node_name=nodes[0] + ":hardware", geom_name=nodes[0] + ":hardware", parent_node_name=nodes[0])
    glb = ROOT / "docs/assets/mounts.glb"
    scene.export(glb)
    kb = glb.stat().st_size/1024
    assert kb <= 1536, f"mounts.glb {kb:.0f} KB > 1.5 MB"
    check = {}
    if (OUT / "check.json").exists():
        check = json.loads((OUT / "check.json").read_text())
    doc = dict(generated="tools/export_mounts.py, " + READ, frame="same as docs/assets/ridgeback.glb: CAD x aft, y right, z up; GLB in metres, numbers here in mm",
               glb="docs/assets/mounts.glb", flight_controller="CubePilot Cube Orange on its carrier (ADS-B carrier assumed, to confirm) - club lead 11-19",
               openings={k: v for k, v in L.OPENINGS.items()}, check_summary=dict(removal={k: v["clear"] for k, v in check.get("removal", {}).items()},
                                                                                 installed_overlaps=len(check.get("installed_overlaps", []))) if check else "not run",
               mounts=out)
    (ROOT / "data/mounts.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"mounts.glb {kb:.0f} KB, {len(scene.graph.nodes_geometry)} geometry nodes; data/mounts.json {len(out)} entries")


if __name__ == "__main__":
    main()
