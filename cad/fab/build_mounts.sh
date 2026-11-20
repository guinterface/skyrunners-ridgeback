#!/usr/bin/env bash
# Build the fuselage (new openings) and every electronics mount, one step at a time under a 6 GB cap (shared machine rule
# until 11-20 07:00), then the fit/removal check and the web export. Run from cad/fab:  ./build_mounts.sh [--no-fuse]
set -e
export SR3_CONFIG=mini MOUNTS_OUT=${MOUNTS_OUT:-/scratch/users/gsbonfim/skyrunners/mounts_out}
export SKY_BUILD=$MOUNTS_OUT/build PYTHONPATH=..:../parts
PY=/scratch/users/gsbonfim/skyrunners/cadenv/bin/python
CAP="systemd-run --user --scope -p MemoryMax=6G -q"
[ "$1" = "--no-fuse" ] || $CAP $PY build.py f_fuse
for f in m_av_cassette m_av_rail m_battery_sled m_battery_stop m_belly_plate m_belly_deck m_tail_panel m_tail_insert_block m_esc_cradle m_gps_holder m_pitot_mount; do
  $CAP $PY $f.py
done
$CAP $PY mounts_check.py > $MOUNTS_OUT/check.log 2>&1 || true
(cd ../.. && $CAP $PY tools/export_mounts.py)
