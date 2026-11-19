# Ridgeback Scout design

Our own 2.24 m VTOL quadplane (SkyRunners, Stanford Student Robotics) for measuring how much water chaparral shrubs lose
between dawn and midday, for prescribed-burn planning.

Website: https://guinterface.github.io/skyrunners-ridgeback/

- **Drone**: the model in 3D. Click a part to see what it does, why we chose it, what it connects to and where to buy it.
- **Mission and range**: how far and how long we fly, and why, with the papers and rules behind it.
- **Calculations**: every sizing step as an equation with our numbers.
- **Sheets, code, CAD**: the six calculation sheets, the code that builds them, and the CAD files.

Status: designed in CAD, not yet built or flown.

## What is where

| Folder | Contents |
|---|---|
| `docs/` | The website (GitHub Pages serves this folder). `docs/sheets/` has the six sheets as .xlsx. |
| `sheets/` | Builds the sheets with live formulas (`build_sheet.py`), recalculates them (`calc_check.py`), splits them into six files (`split_workbooks.py`) and checks every number (`verify_split.py`). |
| `tools/` | The website: `parts.py` (every part, used by the site, the 3D model and the sheets), `export_model.py` (CAD to 3D model), `gen_site.py` (pages). |
| `analysis/` | Sizing sweep, spar, boom, servo, wiring, filament, import duty, tail layout and AVL flight-mode scripts. |
| `cad/` | The CAD as code (build123d). `cad/fab/build.py` builds every part; `cad/fab/assemble_mini.py` the assembly. |

## How to change something

1. Change a part, a price or a link in `tools/parts.py`, or a number or equation in `sheets/build_sheet.py`.
2. Rebuild:
   ```
   cd sheets && python3 build_sheet.py && python3 calc_check.py && python3 split_workbooks.py && python3 verify_split.py
   cp split/*.xlsx ../docs/sheets/ && cp calc_values.json refs.json ../data/
   cd .. && python3 tools/gen_site.py
   ```
3. Open a pull request. The site updates when it is merged to `main`.

The CAD and the 3D-model export need build123d and a build folder; set `SKY_BUILD` to that folder. The sheet scripts need
`openpyxl` and `formulas`.

## Not in this repository

How the water measurement is computed stays private until Stanford's technology licensing office has reviewed it.

## Change a value or a link

- A part (price, quantity, mass, shop link, why, connections): edit [data/parts.toml](data/parts.toml).
- A design number (requirements, air, wing, drag, motors, battery, mission): edit [data/inputs.toml](data/inputs.toml).

Press **Commit changes** on GitHub. The workflow `.github/workflows/rebuild.yml` then rebuilds the sheets
(`docs/sheets/*.xlsx`), checks every formula (0 errors, split files equal to the full model) and regenerates
the site, in about 2 minutes. If a check fails, nothing is published and the Actions tab says why.
Locally: `pip install openpyxl formulas && tools/rebuild.sh`.
