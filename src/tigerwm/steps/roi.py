from functools import lru_cache
from pathlib import Path
import inspect
import numpy as np
import nibabel as nib
from dipy.align.imaffine import AffineRegistration, MutualInformationMetric, transform_centers_of_mass
from dipy.align.transforms import RigidTransform3D, AffineTransform3D
from dipy.align.imaffine import AffineMap


@lru_cache(maxsize=4)
def _build_affreg():
    metric = MutualInformationMetric(nbins=32, sampling_proportion=None)
    level_iters = [80, 20, 5]
    sigmas = [3.0, 1.0, 0.0]
    factors = [4, 2, 1]
    return AffineRegistration(metric=metric, level_iters=level_iters, sigmas=sigmas, factors=factors)


@lru_cache(maxsize=4)
def _load_jhu(jhu_fa, jhu_lbl, jhu_trk):
    jhu_fa = Path(jhu_fa)
    jhu_lbl = Path(jhu_lbl)
    jhu_trk = Path(jhu_trk)

    fa_img = nib.load(str(jhu_fa))
    lbl_img = nib.load(str(jhu_lbl))
    trk_img = nib.load(str(jhu_trk))

    fa_data = fa_img.get_fdata().astype(np.float32)
    lbl = lbl_img.get_fdata()
    trk = trk_img.get_fdata()

    label_ids = [int(x) for x in np.unique(lbl) if x != 0]
    tract_ids = [int(x) for x in np.unique(trk) if x != 0]

    return {
        "fa_data": fa_data,
        "fa_affine": fa_img.affine,
        "lbl": lbl,
        "trk": trk,
        "label_ids": label_ids,
        "tract_ids": tract_ids,
    }


def _affine_map_subject_fa_to_jhu(subject_fa_path, jhu_fa, jhu_lbl, jhu_trk):
    jhu = _load_jhu(str(jhu_fa), str(jhu_lbl), str(jhu_trk))
    affreg = _build_affreg()

    mov_img = nib.load(str(subject_fa_path))
    moving = mov_img.get_fdata().astype(np.float32)
    moving_aff = mov_img.affine

    static = jhu["fa_data"]
    static_aff = jhu["fa_affine"]

    com = transform_centers_of_mass(static, static_aff, moving, moving_aff)

    rigid = affreg.optimize(
        static, moving, RigidTransform3D(), None, static_aff, moving_aff, starting_affine=com.affine
    )
    aff = affreg.optimize(
        static, moving, AffineTransform3D(), None, static_aff, moving_aff, starting_affine=rigid.affine
    )

    amap = AffineMap(
        aff.affine,
        domain_grid_shape=static.shape,
        domain_grid2world=static_aff,
        codomain_grid_shape=moving.shape,
        codomain_grid2world=moving_aff,
    )

    return amap


def _warp_atlas_to_native(amap, atlas_vol):
    sig = inspect.signature(amap.transform_inverse)
    if "interp" in sig.parameters:
        out = amap.transform_inverse(atlas_vol, interp="nearest")
    elif "interpolation" in sig.parameters:
        out = amap.transform_inverse(atlas_vol, interpolation="nearest")
    else:
        out = amap.transform_inverse(atlas_vol)
    return np.rint(out).astype(np.int16)


def roi_atlas_to_native(fa_path, md_path, rd_path, ad_path, mask_path, jhu_fa, jhu_lbl, jhu_trk):
    jhu = _load_jhu(str(jhu_fa), str(jhu_lbl), str(jhu_trk))

    amap = _affine_map_subject_fa_to_jhu(fa_path, jhu_fa, jhu_lbl, jhu_trk)

    fa = nib.load(str(fa_path)).get_fdata().astype(np.float32)
    md = nib.load(str(md_path)).get_fdata().astype(np.float32)
    rd = nib.load(str(rd_path)).get_fdata().astype(np.float32)
    ad = nib.load(str(ad_path)).get_fdata().astype(np.float32)
    brain_mask = nib.load(str(mask_path)).get_fdata().astype(np.float32)

    lbl_native = _warp_atlas_to_native(amap, jhu["lbl"])
    trk_native = _warp_atlas_to_native(amap, jhu["trk"])

    valid = np.isfinite(fa) & (fa > 0)
    valid = valid & (brain_mask > 0)

    def safe_mean(v):
        v = v[np.isfinite(v) & (v > 0)]
        return float(v.mean()) if v.size else np.nan

    rec = {}
    for lid in jhu["label_ids"]:
        m = (lbl_native == lid) & valid
        rec[f"FA_label_{lid}"] = safe_mean(fa[m])
        rec[f"MD_label_{lid}"] = safe_mean(md[m])
        rec[f"RD_label_{lid}"] = safe_mean(rd[m])
        rec[f"AD_label_{lid}"] = safe_mean(ad[m])

    for tid in jhu["tract_ids"]:
        m = (trk_native == tid) & valid
        rec[f"FA_tract_{tid}"] = safe_mean(fa[m])
        rec[f"MD_tract_{tid}"] = safe_mean(md[m])
        rec[f"RD_tract_{tid}"] = safe_mean(rd[m])
        rec[f"AD_tract_{tid}"] = safe_mean(ad[m])

    return rec
