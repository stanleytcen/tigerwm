from pathlib import Path
import numpy as np
import nibabel as nib
from dipy.denoise.localpca import mppca
from dipy.denoise.gibbs import gibbs_removal
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.nlmeans import nlmeans
from dipy.io.gradients import read_bvals_bvecs

from .utils import pick_b0


def _rough_mask(data):
    b0 = data[..., 0]
    nz = b0[b0 > 0]
    if nz.size == 0:
        return b0 > 0
    thr = np.percentile(nz, 30)
    mask = (b0 > thr) & (np.std(data, axis=3) > 1e-6)
    if mask.sum() < 50000:
        mask = b0 > 0
    return mask


def mppca_denoise(dwi_path, out_path, force=False):
    out_path = Path(out_path)
    if out_path.exists() and not force:
        return out_path

    img = nib.load(str(dwi_path))
    data = img.get_fdata().astype(np.float32)
    mask = _rough_mask(data)

    out = mppca(data, mask=mask)
    den = out[0] if isinstance(out, tuple) else out

    bad = ~np.isfinite(den)
    if bad.any():
        den[bad] = data[bad]

    nib.save(nib.Nifti1Image(den.astype(np.float32), img.affine), str(out_path))
    return out_path


def nlm_denoise(
    dwi_path,
    out_path,
    bval_path,
    bvec_path,
    *,
    b0_index=0,
    b0_thresh=50.0,
    force=False,
    patch_radius=1,
    block_radius=3,
    rician=True,
):
    out_path = Path(out_path)
    if out_path.exists() and not force:
        return out_path

    img = nib.load(str(dwi_path))
    data = img.get_fdata().astype(np.float32)

    try:
        bvals, _bvecs = read_bvals_bvecs(str(bval_path), str(bvec_path))
    except Exception:
        bvals = None

    b0 = pick_b0(data, bvals=bvals, b0_index=b0_index, b0_thresh=b0_thresh)
    b0_f = b0[np.isfinite(b0)]
    if b0_f.size == 0:
        raise ValueError("b0 has no finite values")

    thr = float(np.percentile(b0_f, 40))
    mask = np.isfinite(b0) & (b0 > thr)

    sigma_map = estimate_sigma(b0, N=4)
    sigma = float(np.median(sigma_map)) if np.ndim(sigma_map) > 0 else float(sigma_map)
    if (not np.isfinite(sigma)) or sigma <= 0:
        sigma = float(np.median(np.abs(b0_f - np.median(b0_f))) / 0.6745)

    den = np.zeros_like(data, dtype=np.float32)
    for i in range(data.shape[-1]):
        vol = data[..., i].astype(np.float32)
        vol[~np.isfinite(vol)] = 0.0
        den[..., i] = nlmeans(
            vol,
            sigma=sigma,
            mask=mask,
            patch_radius=patch_radius,
            block_radius=block_radius,
            rician=rician,
        ).astype(np.float32)

    den[~np.isfinite(den)] = 0.0
    nib.save(nib.Nifti1Image(den, img.affine), str(out_path))
    return out_path


def gibbs_remove_4d(dwi_path, out_path, force=False, slice_axis=2):
    out_path = Path(out_path)
    if out_path.exists() and not force:
        return out_path

    img = nib.load(str(dwi_path))
    data = img.get_fdata().astype(np.float32)

    out = np.empty_like(data, dtype=np.float32)
    for i in range(data.shape[-1]):
        v = gibbs_removal(data[..., i], slice_axis=slice_axis)
        bad = ~np.isfinite(v)
        if bad.any():
            v[bad] = data[..., i][bad]
        out[..., i] = v

    nonfinite = int((~np.isfinite(out)).sum())
    if nonfinite != 0:
        raise RuntimeError("gibbs output has non-finite values")

    nib.save(nib.Nifti1Image(out, img.affine), str(out_path))
    return out_path
