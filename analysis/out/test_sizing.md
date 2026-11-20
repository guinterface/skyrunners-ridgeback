# Ridgeback test version: sizing and the alternatives (2026-11-19)

[C] = `analysis/test_sizing.py` (run `python3 analysis/test_sizing.py`), [V date] = read on the maker/store page, [A] = assumed.
Every option carries the 230 g sensors and the moved-over avionics (Cube Orange, GPS, airspeed, telemetry, receiver,
Remote ID, PM07, servo regulator, 4 servos) at $0. Drag uses the CAD buildup (Scout CD0 0.063) scaled to the smaller size.
The model reproduces the workbook for the Scout itself (57.5 vs 57.4 min, T/W 1.536, stall 15.49 vs 15.52 m/s).

## Answer

1. **A same-layout test version that carries the sensors does not come out small.** About 2 kg does not shrink with the
   wing: avionics 0.36 kg, sensors 0.23 kg, a fuselage that must still hold the 40 mm-tall Cube and the sensor bay, the pusher,
   and the harness. The VTOL hardware also grows relative to a smaller wing, so CD0 rises from 0.063 to 0.076-0.11 [C].
   With new 15 in motors (MN4010/MN3510/MN4006, all with real T-Motor tables), **no span in 1.2-1.9 m meets T/W 1.5 on a
   hot day, a 15 m/s stall and 25 min together** (e.g. T1: 1.5 m, 4.82 kg, stall 17.2 m/s, 23 min) [C].
2. **The best test version (T6) flies the Scout's own motors, props, ESCs and pusher.** Then they move to the Scout. The
   MN5008 + P18 set weighs 166 g per corner against 158 g for an MN4010 + P15, with nearly twice the thrust [V]. Span
   1.70 m, AR 8, wing 0.361 m² (chord about 0.21 m, close to the Scout's 0.23 m, so the printed wing sections
   are nearly Scout-size), 6S3P, **6.25 kg, stall 15.4 m/s (just over 15), 32 min loiter at CAD drag
   (40 at CD0 0.055, 52 at 0.035), 2.1 short survey flights per charge, T/W 2.19
   at 800 m ISA+20, extra $874, about 219 printer-hours** [C]. 15 m/s needs about 1.8 m at AR 8
   (6.57 kg, 14.9 m/s) [C]; leaving the sensors off gives 15.1 m/s.
3. **The Scout itself flown first on half its pack (6S3P) matches that envelope at no extra cost.** 7.56 kg, stall
   14.3 m/s, 33 min, 2.1 short flights, T/W 1.81 [C]. The CAD and print pack
   already exist. T6 saves only about 80 of 299 printer-hours, and it needs new CAD plus new spar, CG and
   stability checks first.
4. **Recommendation: (a), build the Scout and fly it in stages on a 6S3P first pack. Do not build T6.** If the team wants
   something flying while the Scout prints, (b) the XUWING Albabird-XL 4+1 (1.5 m, $549.90, "Quantity: 6" [V]) beats T6
   on cost and time (about $784 with our pack, no CAD, no printing). Its maker states 400 g of extra payload [V manual],
   so it can carry the sensors. It proves our PX4 VTOL setup and the first measurement, but not our airframe.
   Choosing between (a) alone and (a)+(b) is the user's call (direction and spending).

## What each option proves about the Scout

| | T6 test version | (a) Scout in stages | (b) Albabird-XL |
|---|---|---|---|
| VTOL takeoff/landing, PX4 hover tune | yes, Scout motors/ESCs, but at 0.46 thrust share (Scout 0.65) on a lighter, smaller airframe, so the PX4 gains will not carry over directly | yes, the real aircraft | PX4 setup only; other motors and frame |
| Hover-to-wing transition and back | yes, similar stall (15.4 vs 15.5 m/s) and same pusher | yes, at 14.3 m/s first, then the full pack (half-weight pack: re-check the CG and move the pack or add ballast [A]) | the logic and procedure only; ArduPilot-documented, PX4 as a generic standard VTOL [V docs.px4.io] |
| Printed LW-ASA/CF-PETG wing method | yes, near-Scout chord; spar loads lower, so wing strength is NOT proved | yes, at the real loads | no (foam) |
| Hatch / mount / cassette concept | yes, if the fuselage cross-section is kept | yes | no |
| First flying measurement (230 g sensors) | yes | yes | yes, if the bay fits (bay size NOT FOUND) |
| Scout endurance / drag (CD0 0.063, 57 min) | no; its own CD0 is 0.076 | partly (drag measured in loiter); 6S6P later | no |
| Scout structure, flutter, 8.9 kg handling | no | yes | no |
| Extra cost | $874 | $0 (a separate 6S3P is $192) | about $784 |
| Time to first flight | new CAD + checks + ~219 printer-h | ~299 printer-h, CAD done | shipping + setup; 95 % pre-glued [V] |

Crash exposure is nearly the same in all three. Motors, ESCs, Cube and sensors ride along every time; only the airframe
differs (Scout tubes + filament about $590 [C, workbook lines] against T6's about $480). Fly a 230 g dummy until transitions work.

## Rules check

- T/W ≥ 1.5 at 800 m ISA+20: T6 2.19, (a) 1.81 [C]. With the new 15 in motors the rule caps the mass near 4.8 kg.
- Stall ≤ 15 m/s: **not met by T6 (15.4)**; met by (a) on 6S3P (14.3). The Scout as designed is 15.5 [C workbook].
- Loiter ≥ 25-30 min with 20 % reserve: T6 32, (a) 33 [C] at CAD drag. With 20 % heavier structure, T6 drops to 26.
- 2 short survey flights per charge (10 min over the site [A], 1 km out and back, 2 min of VTOL each): T6 2.1, (a) 2.1 [C].
- 6S1P fails everywhere: 50-57 A per cell at full throttle and about 10 min of loiter.

## Found on the way (not changed; parts.toml and workbook left as they are)

- **ALPHA 40A 6S is rated 20 A continuous, 40 A for 10 s** [V store.tmotor.com 2026-11-19, re-read]. inputs.toml `I_esc = 40`
  and the parts.toml text ("Rated 40 A against ... at full throttle") treat 40 A as continuous. The Scout's hot-day hover is
  14.0 A per motor (fine), but full throttle is 33.5 A, which is a 10 s peak only. Fix the workbook check, or limit PX4 thrust.
- Shrinking the aircraft makes drag worse, not better: the motors, feet and stopped props are a fixed drag area [C].

## Assumptions that move the answer most

Structure mass: printed parts, tubes and epoxy are scaled with wing area; fuselage and mounts with span only [A]. A 20 % heavier
case is given. Wing CLmax is 1.186 x size^0.05 [A]. Pusher efficiency is 0.55 [A]. T/W uses thrust proportional to V² and to
density [A]. The test-stand density is not stated [A]. Motor tables were measured at 22.2-24 V; we fly at 21.6 V (included).
Stock status is NOT FOUND on store.tmotor.com. RobotShop shows the MN3510 and MN4006 "In stock".

## Options (all carry the 230 g sensors and the reused avionics) [C, analysis/test_sizing.py]

| Option | Span m | AR | Wing m² | Pack | Mass kg | CD0 (CAD-scaled) | Stall m/s | Loiter min, CD0 0.035 / 0.055 / **CAD-scaled** | Short flights per charge | T/W 800 m ISA+20 | Hover throttle (thrust share), hot | Extra $ | Printer-h | Fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 new MN4010 KV370, smallest with T/W 1.5 | 1.50 | 10 | 0.225 | 6S2P | 4.82 | 0.081 | 17.2 | 41 / 31 / **23** | 1.7 | 1.55 | 0.64 | 1,481 (1,109 with the Scout's ESCs + pusher) | 155 | stall 17.2, loiter |
| T2 new MN4006 KV380 (lightest motor) | 1.40 | 10 | 0.196 | 6S2P | 4.33 | 0.089 | 17.5 | 45 / 34 / **24** | 1.8 | 1.47 | 0.68 | 1,399 (1,028 with the Scout's ESCs + pusher) | 139 | T/W, stall 17.5, loiter |
| T3 new MN4010 KV580 on 4S | 1.40 | 10 | 0.196 | 4S3P | 4.42 | 0.089 | 17.6 | 43 / 32 / **23** | 1.7 | 1.51 | 0.66 | 1,277 | 139 | stall 17.6, loiter |
| T4 Scout's motors, 1.5 m | 1.50 | 8 | 0.281 | 6S3P | 5.67 | 0.089 | 16.7 | 53 / 41 / **29** | 2.1 | 2.42 | 0.41 | 786 | 178 | stall 16.7 |
| T5 Scout's motors, 1.8 m AR 10 | 1.80 | 10 | 0.324 | 6S3P | 6.06 | 0.081 | 16.0 | 56 / 42 / **32** | 2.2 | 2.26 | 0.44 | 841 | 208 | stall 16.0 |
| **T6 Scout's motors, 1.7 m AR 8 (best test version)** | 1.70 | 8 | 0.361 | 6S3P | 6.25 | 0.076 | 15.4 | 52 / 40 / **32** | 2.1 | 2.19 | 0.46 | 874 | 219 | stall 15.4 |
| (a) the Scout itself, first flights on a 6S3P half pack | 2.24 | 10 | 0.502 | 6S3P | 7.56 | 0.062 | 14.3 | 48 / 36 / **33** | 2.1 | 1.81 | 0.55 | 0 (pack $192 if a separate 6S3P is built) | 299 (needed anyway) | none |
| Scout as designed, 6S6P (reference) | 2.24 | 10 | 0.502 | 6S6P | 8.92 | 0.062 | 15.5 | 84 / 63 / **57** | 3.4 | 1.54 | 0.65 | - | 299 | stall 15.5 |

### T6 cost lines (extra parts only) [C]

| Line | $ |
|---|---|
| 4 x MN5008 KV340 $89.99 [V] (Scout's, moved over) | 0.00 |
| 1 spare pair P18 $82.90 [V] (the 2 Scout pairs moved over) | 82.90 |
| 4 x ALPHA 40A lift ESC $69.99 [V] (Scout's, moved over) | 0.00 |
| pusher AT3520 $79.99 [V] + 13 in prop $12 [A] (Scout's, moved over) | 0.00 |
| pusher ESC AT55A $29.99 [V] | 29.99 |
| 18 P50B cells $8.99 [parts.toml] + strip/BMS $30 [A] | 191.82 |
| carbon tubes, Scout $293 x wing-area ratio [A] | 211.69 |
| filament, Scout $297 (PETG-CF, small spools, LW-ASA) x printed-mass ratio [A] | 217.89 |
| wire, connectors, heat shrink (Scout $156) [A] | 90.00 |
| epoxy, inserts, bolts [A] | 50.00 |
| **Total** | **874.30** |

### T6 mass lines [C from A scaling]

| Line | kg |
|---|---|
| structure: wing (Scout 938 g, scaled by wing area) | 0.678 |
| structure: tail (Scout 250 g, scaled by wing area) | 0.181 |
| structure: boom (Scout 851 g, scaled by wing area) | 0.615 |
| structure: tubes (Scout 758 g, scaled by wing area) | 0.548 |
| structure: epoxy_hw (Scout 350 g, scaled by wing area) | 0.253 |
| structure: fuse (Scout 599 g, scaled by span) | 0.455 |
| structure: mounts (Scout 300 g, scaled by span) | 0.227 |
| battery 6S3P P50B | 1.361 |
| lift motors, props, ESCs, pusher, pusher ESC | 1.193 |
| harness 6S [A] | 0.150 |
| Cube Orange on carrier 75 g [A, weigh it] | 0.075 |
| Holybro M10 GPS 32 g | 0.032 |
| airspeed + pitot 17.4 g | 0.017 |
| SiK telemetry 23.5 g | 0.024 |
| RP2 receiver 1 g | 0.001 |
| Ruko R111S Remote ID 13.5 g | 0.013 |
| PM07 25 g | 0.025 |
| servo regulator 20 g | 0.020 |
| 4 x KST X10 servos 23 g | 0.092 |
| mount hardware 60 g [A] | 0.060 |
| sensors (6 items, parts.toml) | 0.230 |
| **Takeoff** | **6.25** |

T6 detail [C]: loiter 20.0 m/s, drag 9.0 N, loiter power 351 W, hover 688 W, hover current 8.3 A per motor (hot) against the ALPHA's 20 A continuous [V], full throttle 32.1 A against 40 A for 10 s [V], cell current at the T/W 1.5 thrust 20 A against 60 A, pusher static thrust / weight 0.57, wing CLmax 1.170, 20 % heavier structure: loiter 26 min, T/W 1.96, stall 16.3 m/s; without the sensors T/W 2.28.

## Full sweep [C] (CAD-scaled CD0; 6S1P rows dropped: 50-57 A per cell at full throttle and ~10 min loiter)

| Option | Span m | AR | Wing m² | Pack | Mass kg | CD0 (CAD-scaled) | Stall m/s | Loiter min, CD0 0.035 / 0.055 / **CAD-scaled** | Short flights per charge | T/W 800 m ISA+20 | Hover throttle (thrust share), hot | Extra $ | Printer-h | Fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MN4010 KV370 + P15x5 | 1.20 | 10 | 0.144 | 6S2P | 4.19 | 0.109 | 20.1 | 41 / 31 / **18** | 1.5 | 1.78 | 0.56 | 1,388 | 109 | stall 20.1, loiter |
| MN4010 KV370 + P15x5 | 1.20 | 10 | 0.144 | 6S3P | 4.65 | 0.109 | 21.2 | 56 / 42 / **25** | 1.9 | 1.61 | 0.62 | 1,441 | 109 | stall 21.2, loiter |
| MN4010 KV370 + P15x5 | 1.30 | 10 | 0.169 | 6S2P | 4.39 | 0.098 | 19.0 | 41 / 31 / **20** | 1.6 | 1.70 | 0.59 | 1,417 | 123 | stall 19.0, loiter |
| MN4010 KV370 + P15x5 | 1.30 | 10 | 0.169 | 6S3P | 4.84 | 0.098 | 19.9 | 57 / 43 / **28** | 2.0 | 1.54 | 0.65 | 1,471 | 123 | stall 19.9 |
| MN4010 KV370 + P15x5 | 1.40 | 10 | 0.196 | 6S2P | 4.60 | 0.089 | 18.0 | 41 / 31 / **22** | 1.6 | 1.63 | 0.61 | 1,448 | 139 | stall 18.0, loiter |
| MN4010 KV370 + P15x5 | 1.40 | 10 | 0.196 | 6S3P | 5.06 | 0.089 | 18.9 | 57 / 43 / **30** | 2.2 | 1.48 | 0.68 | 1,502 | 139 | T/W, stall 18.9 |
| MN4010 KV370 + P15x5 | 1.50 | 10 | 0.225 | 6S2P | 4.82 | 0.081 | 17.2 | 41 / 31 / **23** | 1.7 | 1.55 | 0.64 | 1,481 | 155 | stall 17.2, loiter |
| MN4010 KV370 + P15x5 | 1.50 | 10 | 0.225 | 6S3P | 5.28 | 0.081 | 18.0 | 57 / 43 / **32** | 2.2 | 1.42 | 0.71 | 1,535 | 155 | T/W, stall 18.0 |
| MN4010 KV370 + P15x5 | 1.60 | 10 | 0.256 | 6S2P | 5.06 | 0.075 | 16.5 | 40 / 30 / **24** | 1.7 | 1.48 | 0.68 | 1,516 | 172 | T/W, stall 16.5, loiter |
| MN4010 KV370 + P15x5 | 1.60 | 10 | 0.256 | 6S3P | 5.51 | 0.075 | 17.2 | 57 / 43 / **34** | 2.3 | 1.36 | 0.74 | 1,570 | 172 | T/W, stall 17.2 |
| MN4010 KV370 + P15x5 | 1.70 | 10 | 0.289 | 6S2P | 5.31 | 0.070 | 15.9 | 39 / 30 / **25** | 1.7 | 1.41 | 0.71 | 1,553 | 189 | T/W, stall 15.9, loiter |
| MN4010 KV370 + P15x5 | 1.70 | 10 | 0.289 | 6S3P | 5.76 | 0.070 | 16.5 | 56 / 42 / **36** | 2.3 | 1.30 | 0.77 | 1,607 | 189 | T/W, stall 16.5 |
| MN4010 KV370 + P15x5 | 1.80 | 10 | 0.324 | 6S2P | 5.57 | 0.066 | 15.3 | 38 / 29 / **25** | 1.7 | 1.34 | 0.74 | 1,592 | 208 | T/W, stall 15.3 |
| MN4010 KV370 + P15x5 | 1.80 | 10 | 0.324 | 6S3P | 6.02 | 0.066 | 15.9 | 55 / 42 / **37** | 2.3 | 1.24 | 0.80 | 1,646 | 208 | T/W, stall 15.9 |
| MN4010 KV370 + P15x5 | 1.90 | 10 | 0.361 | 6S2P | 5.84 | 0.062 | 14.8 | 37 / 28 / **26** | 1.7 | 1.28 | 0.78 | 1,633 | 227 | T/W |
| MN4010 KV370 + P15x5 | 1.90 | 10 | 0.361 | 6S3P | 6.29 | 0.062 | 15.4 | 54 / 41 / **38** | 2.3 | 1.19 | 0.84 | 1,687 | 227 | T/W, stall 15.4 |
| MN3510 KV360 + P15x5 | 1.20 | 10 | 0.144 | 6S2P | 4.11 | 0.099 | 19.9 | 43 / 32 / **21** | 1.6 | 1.54 | 0.65 | 1,381 | 109 | stall 19.9, loiter |
| MN3510 KV360 + P15x5 | 1.20 | 10 | 0.144 | 6S3P | 4.57 | 0.099 | 21.0 | 58 / 44 / **28** | 2.1 | 1.39 | 0.72 | 1,435 | 109 | T/W, stall 21.0 |
| MN3510 KV360 + P15x5 | 1.30 | 10 | 0.169 | 6S2P | 4.31 | 0.090 | 18.8 | 43 / 32 / **22** | 1.7 | 1.47 | 0.68 | 1,410 | 123 | T/W, stall 18.8, loiter |
| MN3510 KV360 + P15x5 | 1.30 | 10 | 0.169 | 6S3P | 4.76 | 0.090 | 19.8 | 59 / 44 / **31** | 2.2 | 1.33 | 0.75 | 1,464 | 123 | T/W, stall 19.8 |
| MN3510 KV360 + P15x5 | 1.40 | 10 | 0.196 | 6S2P | 4.52 | 0.082 | 17.9 | 43 / 32 / **24** | 1.8 | 1.40 | 0.71 | 1,441 | 139 | T/W, stall 17.9, loiter |
| MN3510 KV360 + P15x5 | 1.40 | 10 | 0.196 | 6S3P | 4.98 | 0.082 | 18.7 | 59 / 44 / **33** | 2.3 | 1.28 | 0.78 | 1,495 | 139 | T/W, stall 18.7 |
| MN3510 KV360 + P15x5 | 1.50 | 10 | 0.225 | 6S2P | 4.74 | 0.075 | 17.0 | 42 / 32 / **25** | 1.8 | 1.34 | 0.75 | 1,474 | 155 | T/W, stall 17.0 |
| MN3510 KV360 + P15x5 | 1.50 | 10 | 0.225 | 6S3P | 5.20 | 0.075 | 17.8 | 59 / 44 / **35** | 2.4 | 1.22 | 0.82 | 1,528 | 155 | T/W, stall 17.8 |
| MN3510 KV360 + P15x5 | 1.60 | 10 | 0.256 | 6S2P | 4.98 | 0.070 | 16.3 | 41 / 31 / **26** | 1.8 | 1.27 | 0.78 | 1,509 | 172 | T/W, stall 16.3 |
| MN3510 KV360 + P15x5 | 1.60 | 10 | 0.256 | 6S3P | 5.43 | 0.070 | 17.1 | 58 / 44 / **37** | 2.4 | 1.17 | 0.86 | 1,563 | 172 | T/W, stall 17.1 |
| MN3510 KV360 + P15x5 | 1.70 | 10 | 0.289 | 6S2P | 5.23 | 0.065 | 15.7 | 40 / 31 / **27** | 1.8 | 1.21 | 0.82 | 1,546 | 189 | T/W, stall 15.7 |
| MN3510 KV360 + P15x5 | 1.70 | 10 | 0.289 | 6S3P | 5.68 | 0.065 | 16.4 | 58 / 43 / **38** | 2.5 | 1.12 | 0.89 | 1,600 | 189 | T/W, stall 16.4 |
| MN3510 KV360 + P15x5 | 1.80 | 10 | 0.324 | 6S2P | 5.49 | 0.062 | 15.2 | 39 / 30 / **27** | 1.8 | 1.16 | 0.86 | 1,585 | 208 | T/W, stall 15.2 |
| MN3510 KV360 + P15x5 | 1.80 | 10 | 0.324 | 6S3P | 5.94 | 0.062 | 15.8 | 57 / 43 / **39** | 2.5 | 1.07 | 0.94 | 1,639 | 208 | T/W, stall 15.8 |
| MN3510 KV360 + P15x5 | 1.90 | 10 | 0.361 | 6S2P | 5.76 | 0.058 | 14.7 | 38 / 29 / **28** | 1.8 | 1.10 | 0.91 | 1,626 | 227 | T/W |
| MN3510 KV360 + P15x5 | 1.90 | 10 | 0.361 | 6S3P | 6.21 | 0.058 | 15.3 | 55 / 42 / **40** | 2.4 | 1.02 | 0.98 | 1,680 | 227 | T/W, stall 15.3 |
| MN4006 KV380 + P15x5 | 1.20 | 10 | 0.144 | 6S2P | 3.92 | 0.109 | 19.5 | 46 / 35 / **21** | 1.6 | 1.63 | 0.62 | 1,339 | 109 | stall 19.5, loiter |
| MN4006 KV380 + P15x5 | 1.20 | 10 | 0.144 | 6S3P | 4.37 | 0.109 | 20.6 | 62 / 46 / **28** | 2.1 | 1.46 | 0.69 | 1,393 | 109 | T/W, stall 20.6 |
| MN4006 KV380 + P15x5 | 1.30 | 10 | 0.169 | 6S2P | 4.12 | 0.098 | 18.4 | 46 / 35 / **22** | 1.7 | 1.55 | 0.65 | 1,368 | 123 | stall 18.4, loiter |
| MN4006 KV380 + P15x5 | 1.30 | 10 | 0.169 | 6S3P | 4.57 | 0.098 | 19.4 | 62 / 47 / **30** | 2.2 | 1.39 | 0.72 | 1,422 | 123 | T/W, stall 19.4 |
| MN4006 KV380 + P15x5 | 1.40 | 10 | 0.196 | 6S2P | 4.33 | 0.089 | 17.5 | 45 / 34 / **24** | 1.8 | 1.47 | 0.68 | 1,399 | 139 | T/W, stall 17.5, loiter |
| MN4006 KV380 + P15x5 | 1.40 | 10 | 0.196 | 6S3P | 4.78 | 0.089 | 18.4 | 62 / 47 / **33** | 2.3 | 1.33 | 0.75 | 1,453 | 139 | T/W, stall 18.4 |
| MN4006 KV380 + P15x5 | 1.50 | 10 | 0.225 | 6S2P | 4.55 | 0.081 | 16.7 | 45 / 34 / **25** | 1.8 | 1.40 | 0.71 | 1,432 | 155 | T/W, stall 16.7 |
| MN4006 KV380 + P15x5 | 1.50 | 10 | 0.225 | 6S3P | 5.00 | 0.081 | 17.5 | 62 / 47 / **35** | 2.4 | 1.27 | 0.79 | 1,486 | 155 | T/W, stall 17.5 |
| MN4006 KV380 + P15x5 | 1.60 | 10 | 0.256 | 6S2P | 4.78 | 0.075 | 16.0 | 44 / 33 / **27** | 1.8 | 1.33 | 0.75 | 1,467 | 172 | T/W, stall 16.0 |
| MN4006 KV380 + P15x5 | 1.60 | 10 | 0.256 | 6S3P | 5.24 | 0.075 | 16.8 | 61 / 46 / **37** | 2.4 | 1.22 | 0.82 | 1,521 | 172 | T/W, stall 16.8 |
| MN4006 KV380 + P15x5 | 1.70 | 10 | 0.289 | 6S2P | 5.03 | 0.070 | 15.4 | 43 / 32 / **27** | 1.9 | 1.27 | 0.79 | 1,504 | 189 | T/W, stall 15.4 |
| MN4006 KV380 + P15x5 | 1.70 | 10 | 0.289 | 6S3P | 5.48 | 0.070 | 16.1 | 61 / 46 / **39** | 2.5 | 1.16 | 0.86 | 1,558 | 189 | T/W, stall 16.1 |
| MN4006 KV380 + P15x5 | 1.80 | 10 | 0.324 | 6S2P | 5.29 | 0.066 | 14.9 | 42 / 31 / **28** | 1.8 | 1.20 | 0.83 | 1,543 | 208 | T/W |
| MN4006 KV380 + P15x5 | 1.80 | 10 | 0.324 | 6S3P | 5.75 | 0.066 | 15.6 | 59 / 45 / **40** | 2.5 | 1.11 | 0.90 | 1,597 | 208 | T/W, stall 15.6 |
| MN4006 KV380 + P15x5 | 1.90 | 10 | 0.361 | 6S2P | 5.56 | 0.062 | 14.5 | 40 / 30 / **28** | 1.8 | 1.14 | 0.87 | 1,584 | 227 | T/W |
| MN4006 KV380 + P15x5 | 1.90 | 10 | 0.361 | 6S3P | 6.02 | 0.062 | 15.1 | 58 / 44 / **40** | 2.5 | 1.06 | 0.94 | 1,638 | 227 | T/W, stall 15.1 |
| MN5008 KV340 + P18 (Scout's own) | 1.20 | 10 | 0.144 | 6S2P | 4.23 | 0.142 | 20.2 | 41 / 31 / **15** | 1.2 | 3.24 | 0.31 | 583 | 109 | stall 20.2, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.20 | 10 | 0.144 | 6S3P | 4.68 | 0.142 | 21.3 | 56 / 42 / **20** | 1.6 | 2.93 | 0.34 | 637 | 109 | stall 21.3, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.30 | 10 | 0.169 | 6S2P | 4.43 | 0.126 | 19.1 | 42 / 31 / **16** | 1.3 | 3.10 | 0.32 | 612 | 123 | stall 19.1, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.30 | 10 | 0.169 | 6S3P | 4.88 | 0.126 | 20.0 | 57 / 43 / **22** | 1.8 | 2.81 | 0.36 | 666 | 123 | stall 20.0, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.40 | 10 | 0.196 | 6S2P | 4.64 | 0.113 | 18.1 | 42 / 31 / **18** | 1.4 | 2.96 | 0.34 | 643 | 139 | stall 18.1, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.40 | 10 | 0.196 | 6S3P | 5.09 | 0.113 | 18.9 | 58 / 43 / **25** | 1.9 | 2.69 | 0.37 | 697 | 139 | stall 18.9, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.50 | 10 | 0.225 | 6S2P | 4.86 | 0.102 | 17.2 | 41 / 31 / **19** | 1.5 | 2.82 | 0.35 | 676 | 155 | stall 17.2, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.50 | 10 | 0.225 | 6S3P | 5.31 | 0.102 | 18.0 | 58 / 43 / **27** | 2.0 | 2.58 | 0.39 | 730 | 155 | stall 18.0 |
| MN5008 KV340 + P18 (Scout's own) | 1.60 | 10 | 0.256 | 6S2P | 5.09 | 0.094 | 16.5 | 41 / 31 / **21** | 1.6 | 2.69 | 0.37 | 711 | 172 | stall 16.5, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.60 | 10 | 0.256 | 6S3P | 5.55 | 0.094 | 17.2 | 57 / 43 / **29** | 2.1 | 2.47 | 0.40 | 765 | 172 | stall 17.2 |
| MN5008 KV340 + P18 (Scout's own) | 1.70 | 10 | 0.289 | 6S2P | 5.34 | 0.087 | 15.9 | 40 / 30 / **22** | 1.6 | 2.56 | 0.39 | 748 | 189 | stall 15.9, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.70 | 10 | 0.289 | 6S3P | 5.79 | 0.087 | 16.6 | 57 / 43 / **31** | 2.1 | 2.36 | 0.42 | 802 | 189 | stall 16.6 |
| MN5008 KV340 + P18 (Scout's own) | 1.80 | 10 | 0.324 | 6S2P | 5.60 | 0.081 | 15.4 | 39 / 29 / **22** | 1.6 | 2.45 | 0.41 | 787 | 208 | stall 15.4, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.80 | 10 | 0.324 | 6S3P | 6.06 | 0.081 | 16.0 | 56 / 42 / **32** | 2.2 | 2.26 | 0.44 | 841 | 208 | stall 16.0 |
| MN5008 KV340 + P18 (Scout's own) | 1.90 | 10 | 0.361 | 6S2P | 5.87 | 0.075 | 14.9 | 38 / 29 / **23** | 1.6 | 2.33 | 0.43 | 828 | 227 | loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.90 | 10 | 0.361 | 6S3P | 6.33 | 0.075 | 15.4 | 55 / 42 / **33** | 2.2 | 2.16 | 0.46 | 882 | 227 | stall 15.4 |
| MN4010 KV580 + P15x5 (4S) | 1.20 | 10 | 0.144 | 4S2P | 3.71 | 0.109 | 18.9 | 30 / 22 / **13** | 1.1 | 1.80 | 0.55 | 1,181 | 109 | stall 18.9, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.20 | 10 | 0.144 | 4S3P | 4.01 | 0.109 | 19.7 | 43 / 33 / **19** | 1.5 | 1.67 | 0.60 | 1,217 | 109 | stall 19.7, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.20 | 10 | 0.144 | 4S4P | 4.31 | 0.109 | 20.4 | 54 / 41 / **24** | 1.8 | 1.55 | 0.65 | 1,253 | 109 | stall 20.4, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.30 | 10 | 0.169 | 4S2P | 3.90 | 0.098 | 17.9 | 29 / 22 / **14** | 1.2 | 1.71 | 0.58 | 1,210 | 123 | stall 17.9, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.30 | 10 | 0.169 | 4S3P | 4.21 | 0.098 | 18.6 | 43 / 33 / **21** | 1.6 | 1.59 | 0.63 | 1,246 | 123 | stall 18.6, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.30 | 10 | 0.169 | 4S4P | 4.51 | 0.098 | 19.2 | 55 / 41 / **27** | 2.0 | 1.48 | 0.67 | 1,282 | 123 | T/W, stall 19.2 |
| MN4010 KV580 + P15x5 (4S) | 1.40 | 10 | 0.196 | 4S2P | 4.12 | 0.089 | 17.0 | 29 / 22 / **15** | 1.2 | 1.62 | 0.62 | 1,241 | 139 | stall 17.0, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.40 | 10 | 0.196 | 4S3P | 4.42 | 0.089 | 17.6 | 43 / 32 / **23** | 1.7 | 1.51 | 0.66 | 1,277 | 139 | stall 17.6, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.40 | 10 | 0.196 | 4S4P | 4.72 | 0.089 | 18.2 | 55 / 41 / **29** | 2.0 | 1.42 | 0.71 | 1,313 | 139 | T/W, stall 18.2 |
| MN4010 KV580 + P15x5 (4S) | 1.50 | 10 | 0.225 | 4S2P | 4.34 | 0.081 | 16.3 | 28 / 21 / **16** | 1.2 | 1.54 | 0.65 | 1,274 | 155 | stall 16.3, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.50 | 10 | 0.225 | 4S3P | 4.64 | 0.081 | 16.9 | 42 / 32 / **24** | 1.7 | 1.44 | 0.69 | 1,310 | 155 | T/W, stall 16.9, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.50 | 10 | 0.225 | 4S4P | 4.94 | 0.081 | 17.4 | 54 / 41 / **31** | 2.1 | 1.35 | 0.74 | 1,346 | 155 | T/W, stall 17.4 |
| MN4010 KV580 + P15x5 (4S) | 1.60 | 10 | 0.256 | 4S2P | 4.57 | 0.075 | 15.7 | 27 / 21 / **16** | 1.3 | 1.46 | 0.68 | 1,309 | 172 | T/W, stall 15.7, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.60 | 10 | 0.256 | 4S3P | 4.88 | 0.075 | 16.2 | 42 / 31 / **25** | 1.7 | 1.37 | 0.73 | 1,345 | 172 | T/W, stall 16.2 |
| MN4010 KV580 + P15x5 (4S) | 1.60 | 10 | 0.256 | 4S4P | 5.18 | 0.075 | 16.7 | 54 / 41 / **32** | 2.2 | 1.29 | 0.77 | 1,381 | 172 | T/W, stall 16.7 |
| MN4010 KV580 + P15x5 (4S) | 1.70 | 10 | 0.289 | 4S2P | 4.82 | 0.070 | 15.1 | 26 / 20 / **17** | 1.3 | 1.39 | 0.72 | 1,346 | 189 | T/W, stall 15.1, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.70 | 10 | 0.289 | 4S3P | 5.12 | 0.070 | 15.6 | 41 / 31 / **26** | 1.8 | 1.30 | 0.77 | 1,382 | 189 | T/W, stall 15.6 |
| MN4010 KV580 + P15x5 (4S) | 1.70 | 10 | 0.289 | 4S4P | 5.43 | 0.070 | 16.0 | 53 / 40 / **34** | 2.2 | 1.23 | 0.81 | 1,418 | 189 | T/W, stall 16.0 |
| MN4010 KV580 + P15x5 (4S) | 1.80 | 10 | 0.324 | 4S2P | 5.08 | 0.066 | 14.6 | 25 / 19 / **17** | 1.3 | 1.32 | 0.76 | 1,385 | 208 | T/W, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.80 | 10 | 0.324 | 4S3P | 5.38 | 0.066 | 15.1 | 40 / 30 / **26** | 1.8 | 1.24 | 0.81 | 1,421 | 208 | T/W, stall 15.1 |
| MN4010 KV580 + P15x5 (4S) | 1.80 | 10 | 0.324 | 4S4P | 5.69 | 0.066 | 15.5 | 52 / 39 / **34** | 2.2 | 1.18 | 0.85 | 1,457 | 208 | T/W, stall 15.5 |
| MN4010 KV580 + P15x5 (4S) | 1.90 | 10 | 0.361 | 4S2P | 5.35 | 0.062 | 14.2 | 24 / 18 / **17** | 1.2 | 1.25 | 0.80 | 1,426 | 227 | T/W, loiter |
| MN4010 KV580 + P15x5 (4S) | 1.90 | 10 | 0.361 | 4S3P | 5.66 | 0.062 | 14.6 | 38 / 29 / **27** | 1.7 | 1.18 | 0.85 | 1,462 | 227 | T/W |
| MN4010 KV580 + P15x5 (4S) | 1.90 | 10 | 0.361 | 4S4P | 5.96 | 0.062 | 15.0 | 51 / 38 / **35** | 2.2 | 1.12 | 0.89 | 1,498 | 227 | T/W |
| MN4010 KV370 + P15x5 | 1.40 | 8 | 0.245 | 6S2P | 4.91 | 0.078 | 16.6 | 38 / 29 / **23** | 1.7 | 1.52 | 0.66 | 1,496 | 159 | stall 16.6, loiter |
| MN4010 KV370 + P15x5 | 1.40 | 8 | 0.245 | 6S3P | 5.36 | 0.078 | 17.4 | 54 / 41 / **32** | 2.2 | 1.40 | 0.72 | 1,550 | 159 | T/W, stall 17.4 |
| MN4010 KV370 + P15x5 | 1.50 | 8 | 0.281 | 6S2P | 5.18 | 0.072 | 15.9 | 37 / 29 / **24** | 1.7 | 1.45 | 0.69 | 1,537 | 178 | T/W, stall 15.9, loiter |
| MN4010 KV370 + P15x5 | 1.50 | 8 | 0.281 | 6S3P | 5.63 | 0.072 | 16.6 | 53 / 41 / **34** | 2.3 | 1.33 | 0.75 | 1,591 | 178 | T/W, stall 16.6 |
| MN4010 KV370 + P15x5 | 1.60 | 8 | 0.320 | 6S2P | 5.46 | 0.067 | 15.3 | 36 / 28 / **24** | 1.7 | 1.37 | 0.73 | 1,579 | 198 | T/W, stall 15.3, loiter |
| MN4010 KV370 + P15x5 | 1.60 | 8 | 0.320 | 6S3P | 5.92 | 0.067 | 15.9 | 52 / 40 / **35** | 2.3 | 1.27 | 0.79 | 1,633 | 198 | T/W, stall 15.9 |
| MN4010 KV370 + P15x5 | 1.70 | 8 | 0.361 | 6S2P | 5.76 | 0.063 | 14.8 | 35 / 27 / **25** | 1.7 | 1.30 | 0.77 | 1,625 | 219 | T/W, loiter |
| MN4010 KV370 + P15x5 | 1.70 | 8 | 0.361 | 6S3P | 6.22 | 0.063 | 15.3 | 51 / 39 / **36** | 2.3 | 1.20 | 0.83 | 1,679 | 219 | T/W, stall 15.3 |
| MN5008 KV340 + P18 (Scout's own) | 1.40 | 8 | 0.245 | 6S2P | 4.94 | 0.097 | 16.7 | 39 / 30 / **20** | 1.5 | 2.77 | 0.36 | 692 | 159 | stall 16.7, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.40 | 8 | 0.245 | 6S3P | 5.40 | 0.097 | 17.4 | 54 / 41 / **27** | 2.0 | 2.54 | 0.39 | 746 | 159 | stall 17.4 |
| MN5008 KV340 + P18 (Scout's own) | 1.50 | 8 | 0.281 | 6S2P | 5.21 | 0.089 | 16.0 | 38 / 29 / **21** | 1.5 | 2.63 | 0.38 | 732 | 178 | stall 16.0, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.50 | 8 | 0.281 | 6S3P | 5.67 | 0.089 | 16.7 | 53 / 41 / **29** | 2.1 | 2.42 | 0.41 | 786 | 178 | stall 16.7 |
| MN5008 KV340 + P18 (Scout's own) | 1.60 | 8 | 0.320 | 6S2P | 5.50 | 0.082 | 15.4 | 37 / 28 / **21** | 1.6 | 2.49 | 0.40 | 775 | 198 | stall 15.4, loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.60 | 8 | 0.320 | 6S3P | 5.95 | 0.082 | 16.0 | 53 / 40 / **31** | 2.1 | 2.30 | 0.43 | 829 | 198 | stall 16.0 |
| MN5008 KV340 + P18 (Scout's own) | 1.70 | 8 | 0.361 | 6S2P | 5.80 | 0.076 | 14.8 | 36 / 27 / **22** | 1.6 | 2.36 | 0.42 | 820 | 219 | loiter |
| MN5008 KV340 + P18 (Scout's own) | 1.70 | 8 | 0.361 | 6S3P | 6.25 | 0.076 | 15.4 | 52 / 40 / **32** | 2.1 | 2.19 | 0.46 | 874 | 219 | stall 15.4 |

Validation [C]: the Scout through this model at 8.92 kg gives loiter 57.5 min (workbook 57.4), hot day 53.2 (53.1), T/W 1.536 (1.536), stall 15.49 m/s (15.52), hover 1152 W (1152).

## Sources (read 2026-11-19 unless noted)

- MN4010 KV370/KV580 + P15x5 tables, 137 g, $86.90: https://store.tmotor.com/product/mn4010-kv370-motor-navigator-type.html
- MN3510 KV360 + P15x5 table, 117 g, $79.90: https://store.tmotor.com/product/mn3510-motor-navigator-type.html ; $85.36 "In stock": https://www.robotshop.com/products/t-motor-navigator-mn3510-360kv-brushless-motor
- MN4006 KV380 + 15x5 table (24 V), 68 g: https://store.tmotor.com/product/mn4006-kv380-motor-antigravity-type.html ; $149.75 per 2 "In stock": https://www.robotshop.com/products/tmotor-uav-brushless-motor-antigravity-mn4006-kv380-2x
- P15x5 pair $55.90, 21 g per blade: https://store.tmotor.com/product/polish-carbon-fiber-15x5-prop.html
- MN5008 KV340 + P18 table [V 2026-10-30], $89.99, P18 pair $82.90: workbook Lift_Hover and parts.toml
- AT3520 KV550 13x6.5 table, 218 g, $79.99: https://store.tmotor.com/product/at3520-long-shaft-fixed-wing-motor.html
- AT2826 KV900 table, 175 g, $69.99: https://store.tmotor.com/product/at2826-long-shaft-fixed-wing-motor.html
- ALPHA 40A 6S: 20 A cont., 40 A 10 s, 54.5 g, $69.99: https://store.tmotor.com/product/alpha-40a-6s-esc.html
- AT55A $29.99, 63 g; AT75A $35.99: https://store.tmotor.com/product/at-55a-6s-fixed-wing-esc.html , https://store.tmotor.com/categorys/at-series-fixed-wing-esc
- F35A $28.32 (current and mass NOT FOUND): https://tmotorhobby.com/goods-586-T-MOTOR+F35A+3-6S+AM32+Single+ESC.html
- Albabird-XL 4+1 PNP $549.90, UBEC +$12, gear +$30, "Quantity: 6", no FC/battery: https://www.finwinghobby.com/goods.php?id=186 ; 400 g extra payload, max AUW 4.5 kg, 115 min at 4.1 kg (maker): manual PDF https://www.finwinghobby.com/images/upload/File/Albabird%20XL%20VTOL%204+1%20User%20Manual20240527.pdf
- Makeflyeasy Striver Mini 2.1 m 4+1, $2,150 PNP, 1 kg payload, bay 180x150x110: https://www.aeroflyhobbies.com/airframe-accessories/315-makeflyeasy-striver-mini-2100mm-41-vtol-uav-pnp.html
- PX4 VTOL complete vehicles (none of the above listed): https://docs.px4.io/main/en/complete_vehicles_vtol/index
- Scout numbers: data/calc_values.json (workbook 2026-11-17 tabs Mass_CG, Drag_Buildup, Aero_Cruise, Lift_Hover, Mission_Energy); print hours: mini_1120 BOM.md (~299 printer-h)
