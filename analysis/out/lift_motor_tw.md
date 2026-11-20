# Lift motors for hover thrust/weight 2 [C from T-Motor test tables]

6S rows only. T/W corrected to our 21.6 V loaded pack and air density as in sheet 04. Hover power = one motor at the hover thrust (mass/4), from the maker's table, at sea level (sheet 04 method: table power x sqrt(rho_test/rho)); four motors hover at 4x this. Motor masses include cable, per KV. The two T/W columns at 8.0 and 9.24 kg hold the take-off mass FIXED; the last T/W column adds each motor's own mass change against today's MN5008 (135 g), so heavy motors are not flattered (props and ESCs not included there).

| Motor | Prop | Motor g | Full throttle (V, A) | Thrust g | T/W at 8.0 kg SL / hot | T/W at 9.24 kg SL / hot | T/W 9.24 kg + motor mass change, SL | Hover W per motor at 8.0 / 9.24 kg, SL |
|---|---|---|---|---|---|---|---|---|
| MN5212 KV420 | 18*6.1 in | 249 | 24.0 V, 59.9 A | 5,918 | 2.45 / 2.11 | 2.12 / 1.83 | 2.02 | - / 332 |
| MN6007 KV320 | 22*6.6 in | 161 | 23.6 V, 44.2 A | 5,882 | 2.52 / 2.18 | 2.18 / 1.89 | 2.16 | 194 / 241 |
| MN6007 KV320 | 21*6.3 in | 161 | 23.7 V, 38.7 A | 5,397 | 2.29 / 1.98 | 1.98 / 1.71 | 1.96 | 204 / 252 |
| MN5212 KV420 | 17*5.8 in | 249 | 24.0 V, 51.6 A | 5,359 | 2.22 / 1.92 | 1.92 / 1.66 | 1.83 | 288 / 349 |
| MN5212 KV420 | 16*5.4 in | 249 | 24.0 V, 44.2 A | 4,903 | 2.03 / 1.75 | 1.76 / 1.52 | 1.67 | 282 / 344 |
| MN5212 KV340 | 18*6.1 in | 249 | 24.0 V, 31.0 A | 4,355 | 1.80 / 1.56 | 1.56 / 1.35 | 1.49 | 235 / 286 |
| MN5008 KV340 | 18*6.1 in | 135 | 22.5 V, 33.5 A | 4,215 | 1.98 / 1.71 | 1.72 / 1.48 | 1.72 | 235 / 292 |
| MN5212 KV420 | 15*5 in | 249 | 24.0 V, 36.7 A | 4,175 | 1.73 / 1.49 | 1.49 / 1.29 | 1.42 | 303 / 378 |
| MN5008 KV400 | 17*5.8 in | 132 | 22.5 V, 32.8 A | 3,982 | 1.87 / 1.61 | 1.62 / 1.40 | 1.62 | 258 / 319 |
| MN5212 KV340 | 17*5.8 in | 249 | 24.0 V, 26.1 A | 3,716 | 1.54 / 1.33 | 1.33 / 1.15 | 1.27 | 253 / 314 |
| MN5008 KV400 | 16*5.4 in | 132 | 22.7 V, 28.2 A | 3,591 | 1.66 / 1.44 | 1.44 / 1.25 | 1.44 | 266 / 327 |
| MN5008 KV340 | 17*5.8 in | 135 | 22.7 V, 26.4 A | 3,556 | 1.64 / 1.42 | 1.42 / 1.23 | 1.42 | 251 / 310 |
| MN5212 KV340 | 16*5.4 in | 249 | 24.0 V, 21.6 A | 3,445 | 1.42 / 1.23 | 1.23 / 1.07 | 1.18 | 248 / 299 |
| MN5008 KV400 | 15*5 in | 132 | 22.8 V, 23.4 A | 3,027 | 1.39 / 1.20 | 1.20 / 1.04 | 1.20 | 289 / 355 |
| MN5212 KV340 | 15*5 in | 249 | 24.0 V, 17.8 A | 2,746 | 1.14 / 0.98 | 0.98 / 0.85 | 0.94 | 269 / 330 |

## Whole aircraft: MN5008 KV340 + P18x6.1 vs MN6007II KV320 + P22x6.6 [C, model of analysis/cf_redesign.py]

Hover fits from the maker tables (P = exp(c + k ln T), W and g per motor): today c -5.757 k 1.479 (sheet 04 uses -5.834 / 1.490); MN6007II c -6.223 k 1.513. The 'today' rows use the sheet fit, our own fit of the same table gives under 1 % less hover power, so the comparison holds. Endurance hardly changes because hover is only 120 s of the flight; the gain is less current and heat in hover. Swap adds 191 g (4 motors +26 g, 4 props +13.5 g, 4 ESCs +8.3 g).

| Case | Lift set | Mass kg | T/W sea level / hot | Hover W (4 motors + avionics) | Endurance at 65 km/h min | Stall m/s |
|---|---|---|---|---|---|---|
| Team 1.5 kg, 0.50 m², 6S6P | MN5008 + P18 (today) | 9.10 | 1.74 / 1.50 | 1,187 | 67 | 15.7 |
| Team 1.5 kg, 0.50 m², 6S6P | MN6007II + P22 | 9.30 | 2.17 / 1.88 | 994 | 67 | 15.8 |
| Team 1.5 kg, 0.65 m², 6S6P | MN5008 + P18 (today) | 9.24 | 1.72 / 1.48 | 1,212 | 68 | 13.9 |
| Team 1.5 kg, 0.65 m², 6S6P | MN6007II + P22 | 9.43 | 2.14 / 1.85 | 1,015 | 69 | 14.0 |
| 8 kg case: 0.78 kg payload, 0.60 m², 6S5P | MN5008 + P18 (today) | 8.00 | 1.98 / 1.71 | 983 | 61 | 13.4 |
| 8 kg case: 0.78 kg payload, 0.60 m², 6S5P | MN6007II + P22 | 8.19 | 2.46 / 2.13 | 826 | 61 | 13.6 |
| Today's sensors, 0.50 m², 6S6P | MN5008 + P18 (today) | 7.83 | 2.02 / 1.75 | 954 | 74 | 14.5 |
| Today's sensors, 0.50 m², 6S6P | MN6007II + P22 | 8.03 | 2.51 / 2.17 | 801 | 74 | 14.7 |

With the swap the 8 kg case is 8.19 kg; to stay at 8.00 kg its payload drops from 776 g to about 584 g.

Full team point with the swap (1.5 kg payload, 6S6P, every requirement except the 8 kg limit): smallest wing that keeps stall at or below 13.9 m/s is 0.67 m² (2.59 m span): 9.45 kg, stall 13.80 m/s, 69 min at 65 km/h, T/W 2.13 sea level / 1.85 hot.

ESC current per lift motor, MN6007II + P22 (ALPHA 60A 6S: 40 A continuous, 60 A for 10 s [V T-Motor page]): full throttle 44.2 A in the maker's test at 23.6 V, about 37 A on our loaded pack (21.6 V) and about 51 A on a fresh pack (25.2 V); hover about 11 A. Full throttle is therefore above the continuous rating and allowed only as a burst under 10 s (climb-out, gust recovery); hover is far below it. Today's ALPHA 40A 6S is 20 A continuous / 40 A for 10 s [V saved page alpha-40a-6s-esc.esc]; inputs.toml I_esc is now 20.

Prices [V T-Motor store, 20 Nov]: MN6007II KV320 $129.99 (MN5008 $89.99), P22x6.6 pair $140.90 (P18x6.1 $82.90), ALPHA 60A 6S $69.99. With duty as the buy list charges it (motors 41.5%, props 37.5%, ESCs 37.5 % from China): new set $1,508 against $1,105 in the buy list today, so about $403 more.

Plan-view clearances (rear motor x 549, booms y 390, pusher prop plane x 627, arch tail leading edge x 828). These are plan-view rules: in 3D the lift prop plane is about 44 mm above the pusher axis, so the real blade gap is larger (about 25-30 mm at 22 in, reviewer); the issue at small plan-view gaps is the lift wake hitting the pusher disc, not a blade strike.

- 18 in: at x 627 the rear disc reaches y 175, pusher disc to y 152: gap +23 mm (booms at y 387 give 20 mm). Disc aft edge x 778 vs tail leading edge 828: +50 mm (fine).
- 21 in: at x 627 the rear disc reaches y 135, pusher disc to y 152: gap -18 mm (booms at y 428 give 20 mm). Disc aft edge x 816 vs tail leading edge 828: +12 mm (tail 13 mm aft gives 25 mm).
- 22 in: at x 627 the rear disc reaches y 122, pusher disc to y 152: gap -31 mm (booms at y 441 give 20 mm). Disc aft edge x 828 vs tail leading edge 828: -0 mm (tail 25 mm aft gives 25 mm).

Open with the 22 in swap: (1) the arch tail must move about 25 mm aft (boom 1358 -> about 1385 mm, still two 1 m pieces) or the rear motor forward (costs the 35 mm wing trailing-edge clearance); re-check static margin. (2) booms to about y 441: CENTER_HALF (= BOOM_Y, the wing centre-section joint and washout start) and the arch tail width move with them. (3) at that boom y the disc reaches y 720, so most of the aileron span (y 500 to that point, of 500-865) sits in the lift wake in hover and transition. (4) mass not yet counted: the MN6007II is 67.2 mm across against the 64 mm motor plate (new plate and bolt pattern), the ALPHA 60A is 71.3 x 32.5 x 15.9 mm against 64.5 x 29.4 x 14.7 (new ESC cradle). A milder option is the same motor with 21 in props: T/W just under 2 with its own motor mass (table above), booms to about y 428 and the tail about 13 mm aft.
