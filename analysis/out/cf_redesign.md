# Carbon redesign against the team's requirements [C]

Script: `analysis/cf_redesign.py`. Inputs: sheet values in `data/calc_values.json` (same equations as sheets 03 and 04), bought-part masses from sheet 02 Mass_CG, carbon part sizes drawn from `cad/design.py`. Every carbon mass is an estimate [A] until parts are weighed.

## 1. Structure: printed today, carbon now

Like for like (both include the electronics mounts 300 g, misc pads and horns 19 g and glue): printed + tube today (sheet 02, print/cnc/tube rows + bond lines) **3.90 kg**, carbon at the same 0.50 m² wing **2.81 kg** (-1.08 kg). The carbon structure alone (table below, with its own glue) is 2.39 kg.

| Group | Part | g |
|---|---|---|
| wing | spar | 193 |
| wing | ribs | 82 |
| wing | le rod | 25 |
| wing | te strip | 45 |
| wing | false spar | 42 |
| wing | film | 46 |
| wing | glue | 23 |
| wing | aileron foam | 6 |
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

Wing: 29 ribs drawn in cad/cf/ribs.py (1.0 mm carbon, split front/rear at the spar, 38% cut out, hard ribs at the bolts, boom, aileron ends, servo and tip break), flush 26 x 0.5 mm trailing-edge strip, foam-core ailerons; root chord 271 mm, span 2.24 m.

## 2. The team's requirements, at today's size (0.50 m² wing, 6S6P)

| Requirement | Team | With 1.5 kg payload | With today's 0.23 kg sensors | Pass? |
|---|---|---|---|---|
| All-up weight | ≤ 8 kg | 9.10 kg | 7.83 kg | NO |
| Endurance at 65 km/h | ≥ 60 min | 67 min | 74 min | yes |
| Range (round trip) | ≥ 5 km | 72 km | 81 km | yes |
| Hover thrust / weight (sea level) | ≥ 2.0 | 1.74 (hot day 1.50) | 2.02 (hot day 1.75) | NO |
| Cruise 65 km/h above 1.3 × stall (derived by us, not in the team table) | stall ≤ 13.9 m/s | stall 15.7 m/s | 14.5 m/s | NO |

Endurance = minutes of level flight at 65 km/h on the usable energy (pack Wh × 85% usable × (1 − 20% reserve)) after 120 s of hover and the climb to 120 m, the same definition as sheet 04 Mission_Energy.


Hover power with 1.5 kg payload: 1187 W (54 A); cruise power at 65 km/h: 349 W; CD0 0.0652.

## 3. Sweep with the 1.5 kg payload (MN5008 KV340 + 18 in props)

| Wing m² | Span m | Pack | Mass kg | Stall m/s | Endurance at 65 km/h min | Best-speed endurance min | T/W sea level / hot | Fails |
|---|---|---|---|---|---|---|---|---|
| 0.45 | 2.13 | 6S3P 324 Wh | 7.71 | 15.2 | 33 | 28 | 2.05 / 1.78 | endurance, cruise |
| 0.45 | 2.13 | 6S4P 432 Wh | 8.17 | 15.7 | 45 | 36 | 1.94 / 1.68 | auw, endurance, tw, cruise |
| 0.45 | 2.13 | 6S5P 540 Wh | 8.62 | 16.1 | 55 | 43 | 1.84 / 1.59 | auw, endurance, tw, cruise |
| 0.45 | 2.13 | 6S6P 648 Wh | 9.08 | 16.5 | 65 | 49 | 1.75 / 1.51 | auw, tw, cruise |
| 0.45 | 2.13 | 6S7P 756 Wh | 9.53 | 16.9 | 75 | 54 | 1.66 / 1.44 | auw, tw, cruise |
| 0.45 | 2.13 | 6S8P 864 Wh | 9.98 | 17.3 | 83 | 58 | 1.59 / 1.37 | auw, tw, cruise |
| 0.50 | 2.24 | 6S3P 324 Wh | 7.74 | 14.5 | 33 | 31 | 2.05 / 1.77 | endurance, cruise |
| 0.50 | 2.24 | 6S4P 432 Wh | 8.20 | 14.9 | 45 | 40 | 1.93 / 1.67 | auw, endurance, tw, cruise |
| 0.50 | 2.24 | 6S5P 540 Wh | 8.65 | 15.3 | 56 | 48 | 1.83 / 1.58 | auw, endurance, tw, cruise |
| 0.50 | 2.24 | 6S6P 648 Wh | 9.10 | 15.7 | 67 | 54 | 1.74 / 1.50 | auw, tw, cruise |
| 0.50 | 2.24 | 6S7P 756 Wh | 9.56 | 16.1 | 76 | 60 | 1.66 / 1.43 | auw, tw, cruise |
| 0.50 | 2.24 | 6S8P 864 Wh | 10.02 | 16.5 | 85 | 64 | 1.58 / 1.37 | auw, tw, cruise |
| 0.55 | 2.35 | 6S3P 324 Wh | 7.77 | 13.8 | 34 | 34 | 2.04 / 1.76 | endurance |
| 0.55 | 2.35 | 6S4P 432 Wh | 8.23 | 14.2 | 46 | 44 | 1.93 / 1.66 | auw, endurance, tw, cruise |
| 0.55 | 2.35 | 6S5P 540 Wh | 8.69 | 14.6 | 57 | 52 | 1.82 / 1.58 | auw, endurance, tw, cruise |
| 0.55 | 2.35 | 6S6P 648 Wh | 9.15 | 15.0 | 68 | 59 | 1.73 / 1.50 | auw, tw, cruise |
| 0.55 | 2.35 | 6S7P 756 Wh | 9.61 | 15.4 | 77 | 65 | 1.65 / 1.43 | auw, tw, cruise |
| 0.55 | 2.35 | 6S8P 864 Wh | 10.07 | 15.7 | 87 | 70 | 1.57 / 1.36 | auw, tw, cruise |
| 0.60 | 2.45 | 6S3P 324 Wh | 7.81 | 13.3 | 34 | 37 | 2.03 / 1.75 | endurance |
| 0.60 | 2.45 | 6S4P 432 Wh | 8.27 | 13.6 | 46 | 47 | 1.92 / 1.66 | auw, endurance, tw |
| 0.60 | 2.45 | 6S5P 540 Wh | 8.73 | 14.0 | 57 | 56 | 1.81 / 1.57 | auw, endurance, tw, cruise |
| 0.60 | 2.45 | 6S6P 648 Wh | 9.19 | 14.4 | 68 | 64 | 1.72 / 1.49 | auw, tw, cruise |
| 0.60 | 2.45 | 6S7P 756 Wh | 9.65 | 14.7 | 78 | 71 | 1.64 / 1.42 | auw, tw, cruise |
| 0.60 | 2.45 | 6S8P 864 Wh | 10.11 | 15.1 | 88 | 76 | 1.57 / 1.35 | auw, tw, cruise |
| 0.65 | 2.55 | 6S3P 324 Wh | 7.86 | 12.8 | 34 | 39 | 2.02 / 1.74 | endurance |
| 0.65 | 2.55 | 6S4P 432 Wh | 8.32 | 13.1 | 46 | 51 | 1.91 / 1.65 | auw, endurance, tw |
| 0.65 | 2.55 | 6S5P 540 Wh | 8.78 | 13.5 | 58 | 60 | 1.81 / 1.56 | auw, endurance, tw |
| 0.65 | 2.55 | 6S6P 648 Wh | 9.24 | 13.9 | 68 | 69 | 1.72 / 1.48 | auw, tw |
| 0.65 | 2.55 | 6S7P 756 Wh | 9.70 | 14.2 | 79 | 76 | 1.63 / 1.41 | auw, tw, cruise |
| 0.65 | 2.55 | 6S8P 864 Wh | 10.16 | 14.5 | 88 | 82 | 1.56 / 1.35 | auw, tw, cruise |
| 0.70 | 2.65 | 6S3P 324 Wh | 7.90 | 12.3 | 34 | 42 | 2.01 / 1.73 | endurance |
| 0.70 | 2.65 | 6S4P 432 Wh | 8.36 | 12.7 | 46 | 54 | 1.90 / 1.64 | auw, endurance, tw |
| 0.70 | 2.65 | 6S5P 540 Wh | 8.82 | 13.0 | 58 | 64 | 1.80 / 1.55 | auw, endurance, tw |
| 0.70 | 2.65 | 6S6P 648 Wh | 9.28 | 13.4 | 69 | 73 | 1.71 / 1.48 | auw, tw |
| 0.70 | 2.65 | 6S7P 756 Wh | 9.74 | 13.7 | 79 | 81 | 1.63 / 1.41 | auw, tw |
| 0.70 | 2.65 | 6S8P 864 Wh | 10.20 | 14.0 | 89 | 87 | 1.55 / 1.34 | auw, tw, cruise |

Options passing everything: **0**. Passing everything except thrust/weight: **0**.

## 4. What it takes

- Lightest option that meets endurance, range and cruise speed (weight and T/W still fail): wing 0.65 m², span 2.55 m, 6S6P, 9.24 kg, 68 min at 65 km/h, T/W 1.72. Its spar mass is scaled from today's tubes; a wing this long needs the tubes re-sized (analysis/mini_spar.py) before the mass is firm.
- T/W 2.0 at that mass needs each lift motor to give **4,914 g** at full throttle on the test stand (5,685 g for a hot day at 800 m). The MN5008 KV340 with 18 in props gives 4,215 g [V T-Motor table]. So the lift motors and props must change (bigger motor or prop, or 12S), which adds motor mass: re-run with the new motor's table.

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
| 1.5 kg payload, 60 min, 65 km/h | all-up weight rises above 8 kg | 9.24 kg (wing 0.65 m², 6S6P); T/W 1.72 with today's motors |
| 8 kg, 60 min, 65 km/h | payload must shrink | at most 776 g (wing 0.60 m², 6S5P), T/W 1.98 (still short of 2.0) |
| 8 kg and 1.5 kg payload | endurance must drop | best 34 min |
| T/W 2.0 | bigger lift motors or props | need about 4,914 g of thrust per motor at the chosen mass; adds motor mass not counted here |
