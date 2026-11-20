"""Shared helpers for the electronics mounts (m_*.py, SR3_CONFIG=mini). One printed part per m_ file; this file only exports.

export(solid, name, material, ...) writes, under $MOUNTS_OUT (default /scratch/users/gsbonfim/skyrunners/mounts_out):
    step/<name>.step   in place, aircraft frame (mm)
    stl/<name>.stl     print orientation on the CORE One bed (core.print_orient)
    png/<name>.png     preview (look at it)
    meta/<name>.json   volume, mass (CAD volume x density x fill), print size, bed fit, watertight
and ASSERTS the mesh is watertight (skill rule). Densities: core.MATERIALS (CF-PETG 1.30, PETG 1.27, ASA 1.07, LW-ASA 0.60 [A]).
"""
import json, os, sys
from pathlib import Path
os.environ.setdefault("SR3_CONFIG", "mini")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / "parts")]
import core                                     # noqa: E402
from core import bx, cyl_between, isect, biggest   # noqa: E402,F401

OUT = Path(os.environ.get("MOUNTS_OUT", "/scratch/users/gsbonfim/skyrunners/mounts_out"))
for sub in ("step", "stl", "png", "meta"):
    (OUT / sub).mkdir(parents=True, exist_ok=True)
core.OUT = OUT                                   # mesh_of() temp files


def mesh(solid, tol=0.05, ang=0.2):
    return core.mesh_of(solid, tol, ang)


def export(solid, name, material, fill=1.0, up=(0, 0, 1), notes="", qty=1, title=None):
    import trimesh
    from build123d import export_step
    import build as B
    n = len(solid.solids()) if hasattr(solid, "solids") else 1
    assert n == 1, f"{name}: {n} separate solids (something is not joined)"
    export_step(solid, str(OUT / "step" / f"{name}.step"))
    m = None
    for tol, ang in ((0.05, 0.2), (0.02, 0.1), (0.01, 0.05)):
        m = mesh(solid, tol, ang)
        if m.is_watertight:
            break
    assert m.is_watertight, f"{name}: mesh not watertight"
    mo, dims, fits, up_used = core.print_orient(m, up)
    mo.export(str(OUT / "stl" / f"{name}.stl"))
    rho = core.MATERIALS[material]["rho"]
    vol = solid.volume/1000.0
    g = vol*rho*fill
    B.render(m, OUT / "png" / f"{name}.png", title or f"{name}  {material}  {g:.0f} g  print {dims[0]:.0f}x{dims[1]:.0f}x{dims[2]:.0f}", elev=25, azim=-55)
    bb = solid.bounding_box()
    meta = dict(name=name, material=material, density_g_cm3=rho, fill=fill, vol_cm3=round(vol, 2), mass_g=round(g, 1), qty=qty,
                print_dims=[round(float(v), 1) for v in dims], fits_bed=bool(fits), watertight=bool(m.is_watertight), valid=bool(solid.is_valid),
                bbox=[[round(bb.min.X, 1), round(bb.min.Y, 1), round(bb.min.Z, 1)], [round(bb.max.X, 1), round(bb.max.Y, 1), round(bb.max.Z, 1)]], notes=notes)
    (OUT / "meta" / f"{name}.json").write_text(json.dumps(meta, indent=1))
    print(f"{name:28s} {material:8s} {g:7.1f} g  print {'x'.join(f'{v:.0f}' for v in dims)}  fits={fits}  watertight={m.is_watertight}  valid={solid.is_valid}")
    return meta


def rbox(x0, x1, y0, y1, z0, z1, r=2.0):
    """Box with vertical edges rounded (r)."""
    from build123d import fillet, Axis
    b = bx(x0, x1, y0, y1, z0, z1)
    try:
        return fillet(b.edges().filter_by(Axis.Z), r)
    except Exception:
        return b


def zcyl(x, y, z0, z1, r):
    return cyl_between((x, y, z0), (x, y, z1), r)


# FDM numbers (cad skill): M3 insert hole r 2.0, M2.5 insert r 1.8, M2 insert r 1.6; clearance M3 r 1.7, M2.5 r 1.45, M2 r 1.2
M3_INS, M25_INS, M2_INS, M3_CLR, M25_CLR, M2_CLR = 2.0, 1.8, 1.6, 1.7, 1.45, 1.2
