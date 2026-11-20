"""Nest the carbon wing ribs (cad/cf/ribs.py) into 'cards' that SendCutSend can cut as single parts (2026-11-20).

Why: every rib piece is under SendCutSend's 1 x 2 in minimum part size (ribs are 16-25 mm tall; reviewer 11-20, decision
#102). One way round it, IF SendCutSend accepts it (ask with the quote): each card is one part, a carbon frame (FRAME mm
border, BAR mm bars between rows) holding the rib pieces on two TAB mm break-away tabs each. Tabs are 2 mm = 2 x plate
thickness, SendCutSend's minimum web. After cutting, snip the tabs and sand the stubs.
Aileron ribs are left out (ailerons are foam-core panels, decision 11-20). Quantities as in ribs.json (left + right).
Run: /scratch/users/gsbonfim/skyrunners/cadenv/bin/python cad/cf/rib_cards.py -> cad/out/cf_ribs/cards/card_NN.dxf + cards.png + cards.json
"""
import json, math, sys
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from shapely import affinity

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ribs as RB

CARD_W, CARD_H_MAX = 300.0, 250.0        # mm [A] card size; check SendCutSend's max part size for 1.0 mm carbon with the quote
FRAME, BAR, GAP, TAB = 6.0, 5.0, 4.0, 2.0
OUT = RB.OUT / "cards"; OUT.mkdir(parents=True, exist_ok=True)


def parts():
    P = []
    jobs = [(y, False) for y in RB.YS]
    for y in jobs:
        c, _, res = RB.make_rib(y[0])
        qty = 1 if y[0] == 0 else 2
        for r in res:
            if r["part"].startswith("aileron"): continue
            S = r["solid"]; x0, z0, _, _ = S.bounds
            S = affinity.translate(S, -x0, -z0)
            for k in range(qty):
                P.append((f"y{y[0]:04.0f}_{r['part']}_{'LR'[k] if qty == 2 else 'C'}", S, r["holes"], (-x0, -z0)))
    return sorted(P, key=lambda p: -(p[1].bounds[2]))


def nest(P):
    """Shelf packing with greedy fill: each row starts with the longest piece left and is filled with the longest pieces
    that still fit; a card closes when the next row would pass CARD_H_MAX."""
    left = list(P); cards = []
    inner = CARD_W - 2 * FRAME - 2 * GAP
    while left:
        rows, placed, ytop = [], [], FRAME
        while left:
            row, w_used = [], 0.0
            for q in list(left):
                w = q[1].bounds[2]
                if w_used + w + (GAP if row else 0) <= inner:
                    row.append(q); w_used += w + (GAP if len(row) > 1 else 0); left.remove(q)
            rh = max(q[1].bounds[3] for q in row)
            if ytop + 2 * GAP + rh + FRAME > CARD_H_MAX and rows:
                left = row + left; left.sort(key=lambda p: -p[1].bounds[2]); break
            x = FRAME + GAP
            for name, S, hs, off in row:
                placed.append((name, affinity.translate(S, x, ytop + GAP), hs, (x, ytop + GAP), off)); x += S.bounds[2] + GAP
            rows.append((ytop, rh)); ytop += rh + BAR + 2 * GAP
        cards.append(dict(parts=placed, rows=rows, h=ytop - BAR + FRAME))     # last row top + 2 GAP + frame
    return cards


def card_geometry(cd):
    H = cd["h"]
    frame = box(0, 0, CARD_W, H).difference(box(FRAME, FRAME, CARD_W - FRAME, H - FRAME))
    bars = [box(FRAME, yt + rh + 2 * GAP, CARD_W - FRAME, yt + rh + 2 * GAP + BAR) for yt, rh in cd["rows"][:-1]]
    tabs = []
    for name, S, hs, (px, py), off in cd["parts"]:
        x0, y0, x1, y1 = S.bounds
        for f in (0.25, 0.75):                                   # two tabs down to the bar / frame below the part's row
            xt = x0 + f * (x1 - x0)
            # lowest point of the part near xt
            col = S.intersection(box(xt - TAB / 2, -1e3, xt + TAB / 2, 1e3))
            yb = col.bounds[1] if not col.is_empty else y0
            tabs.append(box(xt - TAB / 2, py - GAP - 1.0, xt + TAB / 2, yb + 0.5))     # down to the bar / frame under the row
    G = unary_union([frame] + bars + tabs + [p[1] for p in cd["parts"]]).buffer(0)
    return G


def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    cards = nest(parts()); summary = []
    fig, axs = plt.subplots(1, len(cards), figsize=(5.5 * len(cards), 5))
    axs = [axs] if len(cards) == 1 else axs
    for i, cd in enumerate(cards):
        G = card_geometry(cd)
        ok = G.geom_type == "Polygon"
        G = RB.clean(G)
        fl = []
        for r in G.interiors:
            pass
        RB.write_dxf(OUT / f"card_{i:02d}.dxf", G, [h for p in cd["parts"] for h in
                     [(n, hx + p[3][0] + p[4][0], hz + p[3][1] + p[4][1], hd) for n, hx, hz, hd in p[2]]])
        x0, y0, x1, y1 = G.bounds
        summary.append(dict(card=i, size_mm=(round(x1 - x0, 1), round(y1 - y0, 1)), n_parts=len(cd["parts"]),
                            one_region=ok, area_mm2=round(G.area), mass_g=round(G.area * RB.T / 1000 * RB.RHO, 1),
                            parts=[p[0] for p in cd["parts"]]))
        ax = axs[i]; ax.fill(*G.exterior.xy, color="#333", lw=0)
        for h in G.interiors: ax.fill(*h.xy, color="white", lw=0)
        ax.set_aspect("equal"); ax.axis("off"); ax.set_title(f"card {i}: {x1-x0:.0f} x {y1-y0:.0f} mm, {len(cd['parts'])} pieces", fontsize=9)
    fig.tight_layout(); fig.savefig(OUT / "cards.png", dpi=110)
    tot = sum(s["n_parts"] for s in summary)
    plate = sum(s["size_mm"][0] * s["size_mm"][1] for s in summary) / 1e6
    json.dump(dict(cards=summary, total_pieces=tot, plate_m2=round(plate, 3), frame=FRAME, bar=BAR, tab=TAB), open(OUT / "cards.json", "w"), indent=1)
    for s in summary:
        print(f"card {s['card']}: {s['size_mm']} mm, {s['n_parts']} pieces, one region {s['one_region']}, {s['mass_g']} g")
    print(f"{tot} rib pieces on {len(summary)} cards, {plate:.3f} m2 of 1.0 mm carbon plate (bounding boxes)")


if __name__ == "__main__":
    main()
