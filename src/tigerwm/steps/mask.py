from pathlib import Path
import numpy as np
import nibabel as nib
from dipy.io.gradients import read_bvals_bvecs
import tigerbx

from .utils import pick_b0


def make_b0_3d(
    dwi_path,
    bval_path,
    bvec_path,
    out_b0_path,
    *,
    b0_index=0,
    b0_thresh=50.0,
    force=False,
):
    out_b0_path = Path(out_b0_path)
    if out_b0_path.exists() and not force:
        return out_b0_path

    img = nib.load(str(dwi_path))
    data = img.get_fdata().astype(np.float32)

    bvals, _bvecs = read_bvals_bvecs(str(bval_path), str(bvec_path))
    b0 = pick_b0(data, bvals=bvals, b0_index=b0_index, b0_thresh=b0_thresh)
    b0[~np.isfinite(b0)] = 0.0

    nib.save(nib.Nifti1Image(b0.astype(np.float32), img.affine), str(out_b0_path))
    return out_b0_path


def _pick_mask_file(folder):
    cands = list(folder.glob("*tbetmask*.nii*"))
    if cands:
        return sorted(cands)[0]
    cands = list(folder.glob("*.nii*"))
    if not cands:
        raise FileNotFoundError("No NIfTI found in " + str(folder))
    return sorted(cands)[0]


def tigerbx_mask_bmgz(b0_3d_path, out_mask_path, force=False):
    out_mask_path = Path(out_mask_path)
    if out_mask_path.exists() and not force:
        return out_mask_path

    tbx_dir = out_mask_path.parent / "tigerbx"
    tbx_dir.mkdir(parents=True, exist_ok=True)

    tigerbx.run("bmgz", str(b0_3d_path), str(tbx_dir))

    cand = _pick_mask_file(tbx_dir)
    mimg = nib.load(str(cand))
    m = (mimg.get_fdata() > 0.5).astype(np.uint8)

    nib.save(nib.Nifti1Image(m, mimg.affine), str(out_mask_path))
    return out_mask_path
