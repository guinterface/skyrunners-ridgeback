# Carbon redesign against the team's requirements [C]

Script: `analysis/cf_redesign.py`. Inputs: sheet values in `data/calc_values.json` (same equations as sheets 03 and 04), bought-part masses from sheet 02 Mass_CG, carbon part sizes drawn from `cad/design.py`. Every carbon mass is an estimate [A] until parts are weighed.

## 1. Structure: printed today, carbon now

Like for like (both include the electronics mounts 300 g, misc pads and horns 19 g and glue): printed + tube today (sheet 02, print/cnc/tube rows + bond lines) **3.90 kg**, carbon at the same 0.50 m² wing **2.77 kg** (-1.13 kg). The carbon structure alone (table below, with its own glue) is 2.35 kg.

| Group | Part | g |
|---|---|---|
| wing | spar | 193 |
| wing | ribs | 60 |
| wing | le rod | 25 |
| wing | te strip | 35 |
| wing | false spar | 42 |
| wing | film | 46 |
| wing | glue | 18 |
| fuselage | rails | 128 |
| fuselage | bulkheads | 87 |
| fuselage | floor | 140 |
| fuselage | foam film skin | 85 |
| fuselage | hatches | 22 |
| fuselage | fairings foam | 23 |
| fuselage | printed connectors | 120 |
| fuselage | glue | 53 |
| tail | foam panels | 23 |
| tail | film | 11 |
| tail | cf strip spar | 16 |
| tail | printed sockets apex and tubes | 142 |
| booms | tubes legs plates feet | 635 |
| booms | cf plate clamps | 386 |
| booms | nacelle fairings | 60 |

Wing: 25 ribs (1.0 mm carbon, every 100 mm, 50% cut out), root chord 271 mm, span 2.24 m.

## 2. The team's requirements, at today's size (0.50 m² wing, 6S6P)

| Requirement | Team | With 1.5 kg payload | With today's 0.23 kg sensors | Pass? |
|---|---|---|---|---|
| All-up weight | ≤ 8 kg | 9.06 kg | 7.79 kg | NO |
| Endurance at 65 km/h | ≥ 60 min | 67 min | 75 min | yes |
| Range (round trip) | ≥ 5 km | 73 km | 81 km | yes |
| Hover thrust / weight (sea level) | ≥ 2.0 | 1.75 (hot day 1.51) | 2.03 (hot day 1.76) | NO |
| Cruise 65 km/h above 1.3 × stall (derived by us, not in the team table) | stall ≤ 13.9 m/s | stall 15.6 m/s | 14.5 m/s | NO |

Endurance = minutes of level flight at 65 km/h on the usable energy (pack Wh × 85% usable × (1 − 20% reserve)) after 120 s of hover and the climb to 120 m, the same definition as sheet 04 Mission_Energy.


Hover power with 1.5 kg payload: 1178 W (53 A); cruise power at 65 km/h: 348 W; CD0 0.0652.

## 3. Sweep with the 1.5 kg payload (MN5008 KV340 + 18 in props)

| Wing m² | Span m | Pack | Mass kg | Stall m/s | Endurance at 65 km/h min | Best-speed endurance min | T/W sea level / hot | Fails |
|---|---|---|---|---|---|---|---|---|
| 0.45 | 2.13 | 6S3P 324 Wh | 7.67 | 15.2 | 33 | 28 | 2.07 / 1.78 | endurance, cruise |
| 0.45 | 2.13 | 6S4P 432 Wh | 8.13 | 15.6 | 45 | 36 | 1.95 / 1.69 | auw, endurance, tw, cruise |
| 0.45 | 2.13 | 6S5P 540 Wh | 8.58 | 16.0 | 56 | 43 | 1.85 / 1.60 | auw, endurance, tw, cruise |
| 0.45 | 2.13 | 6S6P 648 Wh | 9.04 | 16.5 | 66 | 49 | 1.75 / 1.52 | auw, tw, cruise |
| 0.45 | 2.13 | 6S7P 756 Wh | 9.49 | 16.9 | 75 | 54 | 1.67 / 1.44 | auw, tw, cruise |
| 0.45 | 2.13 | 6S8P 864 Wh | 9.94 | 17.3 | 83 | 58 | 1.59 / 1.38 | auw, tw, cruise |
| 0.50 | 2.24 | 6S3P 324 Wh | 7.70 | 14.4 | 34 | 31 | 2.06 / 1.78 | endurance, cruise |
| 0.50 | 2.24 | 6S4P 432 Wh | 8.15 | 14.8 | 46 | 40 | 1.94 / 1.68 | auw, endurance, tw, cruise |
| 0.50 | 2.24 | 6S5P 540 Wh | 8.61 | 15.2 | 57 | 48 | 1.84 / 1.59 | auw, endurance, tw, cruise |
| 0.50 | 2.24 | 6S6P 648 Wh | 9.06 | 15.6 | 67 | 55 | 1.75 / 1.51 | auw, tw, cruise |
| 0.50 | 2.24 | 6S7P 756 Wh | 9.52 | 16.0 | 77 | 60 | 1.66 / 1.44 | auw, tw, cruise |
| 0.50 | 2.24 | 6S8P 864 Wh | 9.98 | 16.4 | 85 | 65 | 1.59 / 1.37 | auw, tw, cruise |
| 0.55 | 2.35 | 6S3P 324 Wh | 7.72 | 13.8 | 34 | 34 | 2.05 / 1.77 | endurance |
| 0.55 | 2.35 | 6S4P 432 Wh | 8.18 | 14.2 | 46 | 44 | 1.94 / 1.67 | auw, endurance, tw, cruise |
| 0.55 | 2.35 | 6S5P 540 Wh | 8.64 | 14.6 | 57 | 53 | 1.83 / 1.59 | auw, endurance, tw, cruise |
| 0.55 | 2.35 | 6S6P 648 Wh | 9.10 | 14.9 | 68 | 60 | 1.74 / 1.51 | auw, tw, cruise |
| 0.55 | 2.35 | 6S7P 756 Wh | 9.55 | 15.3 | 78 | 66 | 1.66 / 1.43 | auw, tw, cruise |
| 0.55 | 2.35 | 6S8P 864 Wh | 10.01 | 15.7 | 87 | 71 | 1.58 / 1.37 | auw, tw, cruise |
| 0.60 | 2.45 | 6S3P 324 Wh | 7.76 | 13.2 | 34 | 37 | 2.04 / 1.77 | endurance |
| 0.60 | 2.45 | 6S4P 432 Wh | 8.22 | 13.6 | 46 | 48 | 1.93 / 1.67 | auw, endurance, tw |
| 0.60 | 2.45 | 6S5P 540 Wh | 8.68 | 14.0 | 58 | 57 | 1.83 / 1.58 | auw, endurance, tw, cruise |
| 0.60 | 2.45 | 6S6P 648 Wh | 9.14 | 14.3 | 68 | 65 | 1.73 / 1.50 | auw, tw, cruise |
| 0.60 | 2.45 | 6S7P 756 Wh | 9.60 | 14.7 | 79 | 71 | 1.65 / 1.43 | auw, tw, cruise |
| 0.60 | 2.45 | 6S8P 864 Wh | 10.06 | 15.0 | 88 | 77 | 1.58 / 1.36 | auw, tw, cruise |
| 0.65 | 2.55 | 6S3P 324 Wh | 7.79 | 12.7 | 34 | 40 | 2.03 / 1.76 | endurance |
| 0.65 | 2.55 | 6S4P 432 Wh | 8.25 | 13.1 | 46 | 51 | 1.92 / 1.66 | auw, endurance, tw |
| 0.65 | 2.55 | 6S5P 540 Wh | 8.71 | 13.5 | 58 | 61 | 1.82 / 1.57 | auw, endurance, tw |
| 0.65 | 2.55 | 6S6P 648 Wh | 9.17 | 13.8 | 69 | 70 | 1.73 / 1.49 | auw, tw |
| 0.65 | 2.55 | 6S7P 756 Wh | 9.63 | 14.1 | 79 | 77 | 1.65 / 1.42 | auw, tw, cruise |
| 0.65 | 2.55 | 6S8P 864 Wh | 10.09 | 14.5 | 89 | 83 | 1.57 / 1.36 | auw, tw, cruise |
| 0.70 | 2.65 | 6S3P 324 Wh | 7.83 | 12.3 | 34 | 42 | 2.02 / 1.75 | endurance |
| 0.70 | 2.65 | 6S4P 432 Wh | 8.29 | 12.6 | 46 | 55 | 1.91 / 1.65 | auw, endurance, tw |
| 0.70 | 2.65 | 6S5P 540 Wh | 8.75 | 13.0 | 58 | 65 | 1.81 / 1.56 | auw, endurance, tw |
| 0.70 | 2.65 | 6S6P 648 Wh | 9.21 | 13.3 | 69 | 74 | 1.72 / 1.49 | auw, tw |
| 0.70 | 2.65 | 6S7P 756 Wh | 9.67 | 13.7 | 79 | 82 | 1.64 / 1.42 | auw, tw |
| 0.70 | 2.65 | 6S8P 864 Wh | 10.13 | 14.0 | 89 | 88 | 1.56 / 1.35 | auw, tw, cruise |

Options passing everything: **0**. Passing everything except thrust/weight: **0**.

## 4. What it takes

- Lightest option that meets endurance, range and cruise speed (weight and T/W still fail): wing 0.65 m², span 2.55 m, 6S6P, 9.17 kg, 69 min at 65 km/h, T/W 1.73.
- T/W 2.0 at that mass needs each lift motor to give **4,879 g** at full throttle on the test stand (5,645 g for a hot day at 800 m). The MN5008 KV340 with 18 in props gives 4,215 g [V T-Motor table]. So the lift motors and props must change (bigger motor or prop, or 12S), which adds motor mass: re-run with the new motor's table.

## 4b. Does a tube spar alone stop the wing twisting? [C]

| Speed | Tip twist if the tube is wrapped with ±45° plies (G about 20 GPa [A]) | Tip twist if it is a 0/90 woven wrap or pultruded (G about 5 GPa [A]) |
|---|---|---|
| 18 m/s | 0.39° | 1.56° |
| 25 m/s | 0.75° | 2.99° |
| 30 m/s | 1.08° | 4.31° |

Under about 1° the tube alone is enough; above about 2° the wing needs a molded carbon leading edge (D-box). HaoZhong lists its spar tubes as roll-wrapped, but roll-wrapped does not tell the twist stiffness: a 0/90 woven wrap is nearer G 4-6 GPa (the right column) and only ±45° plies reach about 20 GPa. **So the D-box question stays open** until the layup is known (ask HaoZhong) or one wing panel is twist-tested by hand.


## 5. The requirements cannot all hold together: what each relaxation gives

| If we keep... | ...then | Numbers [C] |
|---|---|---|
| 1.5 kg payload, 60 min, 65 km/h | all-up weight rises above 8 kg | 9.17 kg (wing 0.65 m², 6S6P); T/W 1.73 with today's motors |
| 8 kg, 60 min, 65 km/h | payload must shrink | at most 831 g (wing 0.60 m², 6S5P), T/W 1.98 (still short of 2.0) |
| 8 kg and 1.5 kg payload | endurance must drop | best 34 min |
| T/W 2.0 | bigger lift motors or props | need about 4,879 g of thrust per motor at the chosen mass; adds motor mass not counted here |
