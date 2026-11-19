"""Every part of the drone. The data lives in data/parts.toml (edit that file, not this one).

The site, the 3D model and the sheets all read it through PARTS and SYSTEMS below.
"""
import copy
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS_FILE = ROOT / "data/parts.toml"
_d = tomllib.loads(PARTS_FILE.read_text())

SYSTEMS = {k: (v["name"], v["color"]) for k, v in _d["systems"].items()}
RAW = {p["id"]: copy.deepcopy(p) for p in _d["part"]}   # exactly as written in parts.toml (for the in-page editor)
PARTS = []
for p in _d["part"]:
    p = dict(p)
    p["buy"] = [[b["store"], b["link"], b["price"]] for b in p.get("buy", [])]
    p["connects"] = [list(c) for c in p.get("connects", [])]
    for k in ("instead", "source", "job", "why", "status", "where"):
        p.setdefault(k, "")
    p.setdefault("nodes", []); p.setdefault("qty", 1); p.setdefault("price", 0); p.setdefault("mass", 0)
    p.setdefault("china", 0); p.setdefault("duty", 0)
    PARTS.append(p)

# line in parts.toml where each part starts (for the "Edit on GitHub" links)
PART_LINE = {}
_cur = None
for i, line in enumerate(PARTS_FILE.read_text().splitlines(), 1):
    if line.strip() == "[[part]]":
        _cur = i
    elif _cur and line.startswith("id = "):
        PART_LINE[line.split("=", 1)[1].strip().strip('"')] = _cur
        _cur = None

ORDER_STATES = ("to order", "ordered", "arrived", "have it")   # what we have bought (set on the website)
ids = [p["id"] for p in PARTS]
assert len(ids) == len(set(ids)), "two parts have the same id in data/parts.toml"
import re as _re
for _k, (_n, _c) in SYSTEMS.items():
    assert _re.fullmatch(r"#[0-9a-fA-F]{6}", str(_c)), f'system {_k}: color "{_c}" must look like #9a6b16'
for _p in _d["part"]:
    assert _re.fullmatch(r"[a-z0-9_]+", str(_p["id"])), f'part id "{_p["id"]}" may use only a-z, 0-9 and _'
    for _f in ("qty", "mass", "price", "power_w", "china", "duty"):
        if _f in _p: assert isinstance(_p[_f], (int, float)) and not isinstance(_p[_f], bool), f'{_p["id"]}: {_f} must be a number'
for p in PARTS:
    assert p["system"] in SYSTEMS, f'{p["id"]}: system "{p["system"]}" is not one of {list(SYSTEMS)}'
    _gone = [c[0] for c in p["connects"] if c[0] not in ids]
    if _gone: print(f'note: {p["id"]} connects to removed part(s) {_gone}; dropped')
    p["connects"] = [c for c in p["connects"] if c[0] in ids]
    assert p.get("order", "to order") in ORDER_STATES, f'{p["id"]}: order "{p.get("order")}" must be one of {ORDER_STATES}'
    for b in p["buy"]:
        assert str(b[1]).startswith("https://"), f'{p["id"]}: shop link "{b[1]}" must start with https://'
    for r in p.get("refs", []):
        assert r.get("cite") and str(r.get("link", "")).startswith("https://"), f'{p["id"]}: every reference needs a cite and an https:// link'
