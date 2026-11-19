#!/usr/bin/env bash
# Rebuild everything from the editable files (data/parts.toml, data/inputs.toml, data/orders.toml) and the code.
# GitHub runs this on every save (.github/workflows/rebuild.yml). Locally: PY=/path/to/python tools/rebuild.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python3}
cd sheets
$PY build_sheet.py
$PY calc_check.py | tee /tmp/calc_check.log
grep -q "errors 0" /tmp/calc_check.log || { echo "Formula errors in the workbook: see above"; exit 1; }
$PY split_workbooks.py
$PY verify_split.py | tee /tmp/verify.log
grep -q "TOTAL problems 0" /tmp/verify.log || { echo "Split files do not match the full model: see above"; exit 1; }
cp split/Ridgeback_0*.xlsx ../docs/sheets/
cp Ridgeback_mini_VTOL_design_2026-11-17.xlsx ../docs/sheets/Ridgeback_00_all_tabs_in_one.xlsx
cp calc_values.json refs.json buy_list.json ../data/
cd ..
$PY tools/gen_site.py
echo "rebuild OK"
