from pathlib import Path
import json
import pandas as pd

from .steps.denoise import mppca_denoise, nlm_denoise, gibbs_remove_4d
from .steps.gdm import gdm_correct_epi
from .steps.mask import make_b0_3d, tigerbx_mask_bmgz
from .steps.tensor import tensor_fit_and_save
from .steps.roi import roi_atlas_to_native


PIPELINE_STEPS = {
    "P0": "STR",
    "P1": "MGSTR",
    "P2": "NGSTR",
    "P3": "MGDSTR",
    "P4": "NGDSTR",
    "P5": "DSTR",
    "P6": "DMGSTR",
    "P7": "DNGSTR",
}
DEFAULT_PIPELINE = "P4"
DEFAULT_STEPS = PIPELINE_STEPS[DEFAULT_PIPELINE]


def _resolve_steps(steps):
    if not steps:
        return DEFAULT_STEPS
    steps = str(steps).upper()
    return PIPELINE_STEPS.get(steps, steps)


def _normalize_steps(steps):
    steps = _resolve_steps(steps)
    steps_list = [c for c in steps.upper() if c.isalpha()]
    if not steps_list:
        raise ValueError("steps is empty")
    return steps_list


def _pipeline_name_from_steps(steps):
    steps = "".join(steps)
    for name, pipeline_steps in PIPELINE_STEPS.items():
        if steps == pipeline_steps:
            return name
    return steps


def _dwi_name(tags):
    return "dwi_" + "_".join(tags) + ".nii.gz"


def _append_csv(csv_path, row):
    csv_path = Path(csv_path)
    df = pd.DataFrame([row])
    if csv_path.exists():
        df.to_csv(csv_path, mode="a", header=False, index=False, float_format="%.6f")
    else:
        df.to_csv(csv_path, index=False, float_format="%.6f")


def tigerwm(
    steps=None,
    dwi_path=None,
    bval_path=None,
    bvec_path=None,
    out_dir=None,
    *,
    subject=None,
    pipeline_name=None,
    csv_path=None,
    b0_index=0,
    b0_thresh=50.0,
    force=False,
    templates_dir=None,
    jhu_fa=None,
    jhu_lbl=None,
    jhu_trk=None,
    mask_path=None,
    fa_path=None,
    md_path=None,
    rd_path=None,
    ad_path=None,
    gibbs_slice_axis=2,
    nlm_patch_radius=1,
    nlm_block_radius=3,
    nlm_rician=True,
):
    if out_dir is None:
        out_dir = bvec_path
        bvec_path = bval_path
        bval_path = dwi_path
        dwi_path = steps
        steps = DEFAULT_STEPS

    if dwi_path is None or bval_path is None or bvec_path is None or out_dir is None:
        raise ValueError("dwi_path, bval_path, bvec_path, and out_dir are required")

    steps_list = _normalize_steps(steps)
    if "M" in steps_list and "N" in steps_list:
        raise ValueError("Use M or N, not both.")
    resolved_pipeline_name = pipeline_name or _pipeline_name_from_steps(steps_list)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tigerbx").mkdir(parents=True, exist_ok=True)
    (out_dir / "roi").mkdir(parents=True, exist_ok=True)

    dwi_path = Path(dwi_path)
    bval_path = Path(bval_path)
    bvec_path = Path(bvec_path)

    if templates_dir:
        tdir = Path(templates_dir)
        if jhu_fa is None:
            jhu_fa = tdir / "JHU-ICBM-FA-1mm.nii.gz"
        if jhu_lbl is None:
            jhu_lbl = tdir / "JHU-ICBM-labels-1mm.nii.gz"
        if jhu_trk is None:
            jhu_trk = tdir / "JHU-ICBM-tracts-maxprob-thr25-1mm.nii.gz"

    tags = []
    cur_dwi = dwi_path
    results = {"steps": "".join(steps_list), "pipeline": resolved_pipeline_name}

    mask_final = Path(mask_path) if mask_path else None
    fa_final = Path(fa_path) if fa_path else None
    md_final = Path(md_path) if md_path else None
    rd_final = Path(rd_path) if rd_path else None
    ad_final = Path(ad_path) if ad_path else None

    for step in steps_list:
        if step == "M":
            tags.append("mppca")
            out_path = out_dir / _dwi_name(tags)
            cur_dwi = mppca_denoise(cur_dwi, out_path, force=force)
        elif step == "N":
            tags.append("nlm")
            out_path = out_dir / _dwi_name(tags)
            cur_dwi = nlm_denoise(
                cur_dwi,
                out_path,
                bval_path,
                bvec_path,
                b0_index=b0_index,
                b0_thresh=b0_thresh,
                force=force,
                patch_radius=nlm_patch_radius,
                block_radius=nlm_block_radius,
                rician=nlm_rician,
            )
        elif step == "G":
            tags.append("gibbs")
            out_path = out_dir / _dwi_name(tags)
            cur_dwi = gibbs_remove_4d(
                cur_dwi, out_path, force=force, slice_axis=gibbs_slice_axis
            )
        elif step == "D":
            tags.append("gdm")
            gdm_dir = out_dir / "gdm"
            out_name = _dwi_name(tags)
            cur_dwi = gdm_correct_epi(
                cur_dwi, gdm_dir, out_name=out_name, force=force, b0_index=b0_index
            )
        elif step == "S":
            b0_path = out_dir / "b0_for_tigerbx.nii.gz"
            make_b0_3d(
                cur_dwi,
                bval_path,
                bvec_path,
                b0_path,
                b0_index=b0_index,
                b0_thresh=b0_thresh,
                force=force,
            )
            mask_path = out_dir / "mask_tigerbx.nii.gz"
            mask_final = tigerbx_mask_bmgz(b0_path, mask_path, force=force)
            results["mask"] = mask_final
        elif step == "T":
            if mask_final is None:
                raise ValueError("Mask is required for tensor step.")
            fa_final, md_final, rd_final, ad_final, qc_path, qc = tensor_fit_and_save(
                cur_dwi, bval_path, bvec_path, mask_final, out_dir, force=force
            )
            results["tensor"] = {
                "fa": fa_final,
                "md": md_final,
                "rd": rd_final,
                "ad": ad_final,
                "qc_path": qc_path,
            }
            results["qc"] = qc
        elif step == "R":
            if fa_final is None or md_final is None or rd_final is None or ad_final is None:
                raise ValueError("FA/MD/RD/AD are required for ROI step.")
            if mask_final is None:
                raise ValueError("Mask is required for ROI step.")
            if not (jhu_fa and jhu_lbl and jhu_trk):
                raise ValueError("JHU templates are required for ROI step.")
            roi = roi_atlas_to_native(
                fa_final,
                md_final,
                rd_final,
                ad_final,
                mask_final,
                jhu_fa,
                jhu_lbl,
                jhu_trk,
            )
            results["roi"] = roi
        else:
            raise ValueError(f"Unknown step: {step}")

    results["dwi"] = cur_dwi

    if csv_path is not None:
        if subject is None:
            raise ValueError("subject is required when csv_path is provided")
        row = {"subject": subject, "pipeline": resolved_pipeline_name}
        if "qc" in results:
            row.update(results["qc"])
        if "roi" in results:
            row.update(results["roi"])
        _append_csv(csv_path, row)

    return results


