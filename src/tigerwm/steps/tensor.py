from pathlib import Path
import json
import numpy as np
import nibabel as nib
from dipy.core.gradients import gradient_table
from dipy.reconst.dti import TensorModel


def tensor_fit_and_save(dwi_path, bval_path, bvec_path, mask_path, out_dir, force=False):
    out_dir = Path(out_dir)
    fa_p = out_dir / "dti_FA.nii.gz"
    md_p = out_dir / "dti_MD.nii.gz"
    rd_p = out_dir / "dti_RD.nii.gz"
    ad_p = out_dir / "dti_AD.nii.gz"
    qc_p = out_dir / "qc_metrics.json"

    if fa_p.exists() and md_p.exists() and rd_p.exists() and ad_p.exists() and not force:
        qc = json.loads(qc_p.read_text()) if qc_p.exists() else {}
        return fa_p, md_p, rd_p, ad_p, qc_p, qc

    img = nib.load(str(dwi_path))
    data = img.get_fdata().astype(np.float32)

    bvals = np.loadtxt(str(bval_path))
    bvecs = np.loadtxt(str(bvec_path))
    gtab = gradient_table(bvals, bvecs)

    mask = nib.load(str(mask_path)).get_fdata() > 0.5
    if mask.shape != data.shape[:3]:
        raise ValueError("Mask shape does not match data")

    tenmodel = TensorModel(gtab)
    fit = tenmodel.fit(data, mask=mask)

    fa = fit.fa
    md = fit.md
    rd = fit.rd
    ad = fit.ad

    nib.save(nib.Nifti1Image(fa.astype(np.float32), img.affine), str(fa_p))
    nib.save(nib.Nifti1Image(md.astype(np.float32), img.affine), str(md_p))
    nib.save(nib.Nifti1Image(rd.astype(np.float32), img.affine), str(rd_p))
    nib.save(nib.Nifti1Image(ad.astype(np.float32), img.affine), str(ad_p))

    qc = {
        "n_mask_vox": int(mask.sum()),
        "fa_mean": float(np.nanmean(fa[mask])),
        "fa_median": float(np.nanmedian(fa[mask])),
        "fa_gt_0p9_ratio": float(np.mean(fa[mask] > 0.9)),
    }
    qc_p.write_text(json.dumps(qc, indent=2))
    return fa_p, md_p, rd_p, ad_p, qc_p, qc
