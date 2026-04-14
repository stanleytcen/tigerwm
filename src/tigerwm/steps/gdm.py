from pathlib import Path
import shutil
import tigerbx

from .utils import strip_nii_suffix


def gdm_correct_epi(dwi_4d_path, out_dir, *, out_name=None, force=False, b0_index=0):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gdm_in = out_dir / "input"
    gdm_out = out_dir / "output"
    gdm_in.mkdir(parents=True, exist_ok=True)
    gdm_out.mkdir(parents=True, exist_ok=True)

    if out_name is None:
        base = strip_nii_suffix(Path(dwi_4d_path).name)
        out_name = base + "_gdm.nii.gz"

    out_dwi = out_dir / out_name
    if out_dwi.exists() and not force:
        return out_dwi

    in_dwi = gdm_in / Path(dwi_4d_path).name
    if (not in_dwi.exists()) or force:
        try:
            if in_dwi.exists():
                in_dwi.unlink()
            in_dwi.symlink_to(dwi_4d_path)
        except Exception:
            shutil.copy2(dwi_4d_path, in_dwi)

    before = set(p.name for p in gdm_out.glob("*.nii*"))
    tigerbx.gdm(str(gdm_in), str(gdm_out), b0_index=b0_index)

    after = sorted(gdm_out.glob("*.nii*"))
    new_files = [p for p in after if p.name not in before]
    cands = new_files if new_files else after
    if not cands:
        raise FileNotFoundError("GDM output not found in " + str(gdm_out))

    def score(p):
        name = p.name.lower()
        bad = any(k in name for k in ("disp", "field", "warp", "mask"))
        good = any(k in name for k in ("gdm", "corr", "correct", "unwarp", "epi"))
        return (0 if bad else 1, 1 if good else 0, p.stat().st_mtime)

    pick = sorted(cands, key=score, reverse=True)[0]
    if pick != out_dwi:
        try:
            pick.replace(out_dwi)
        except Exception:
            shutil.copy2(pick, out_dwi)

    return out_dwi
