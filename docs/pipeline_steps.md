# Pipeline Steps

This document summarizes the named pipelines, step codes, inputs, and outputs used by tigerwm.

## Named Pipelines

| Pipeline | Steps | Meaning |
| --- | --- | --- |
| P0 | STR | Skull strip, tensor fit, ROI |
| P1 | MGSTR | MPPCA, Gibbs removal, skull strip, tensor fit, ROI |
| P2 | NGSTR | NLM, Gibbs removal, skull strip, tensor fit, ROI |
| P3 | MGDSTR | MPPCA, Gibbs removal, GDM, skull strip, tensor fit, ROI |
| P4 | NGDSTR | NLM, Gibbs removal, GDM, skull strip, tensor fit, ROI |
| P5 | DSTR | GDM, skull strip, tensor fit, ROI |
| P6 | DMGSTR | GDM, MPPCA, Gibbs removal, skull strip, tensor fit, ROI |
| P7 | DNGSTR | GDM, NLM, Gibbs removal, skull strip, tensor fit, ROI |

P4 is the default pipeline when no step code or pipeline name is provided.

## Step Codes

| Code | Step | Input | Output |
| --- | --- | --- | --- |
| M | MPPCA denoising | 4D DWI | denoised 4D DWI |
| N | NLM denoising | 4D DWI + bvals/bvecs | denoised 4D DWI |
| G | Gibbs removal | 4D DWI | unringed 4D DWI |
| D | GDM distortion correction | 4D DWI | distortion-corrected 4D DWI |
| S | Skull strip | 4D DWI + bvals/bvecs | 3D b0 and 3D brain mask |
| T | Tensor fit | 4D DWI + bvals/bvecs + mask | FA, MD, RD, AD NIfTI files and QC JSON |
| R | ROI extraction | FA/MD/RD/AD + mask + JHU templates | ROI and tract summary values written to CSV |

## 4D and 3D Data Flow

The main DWI stays 4D through the preprocessing steps M, N, G, and D.

The S step extracts a 3D b0 image from the current 4D DWI and uses tigerbx to create a 3D brain mask.

The T step fits a DTI tensor model using the current 4D DWI and the 3D mask, then saves 3D FA, MD, RD, and AD maps.

The R step computes ROI and tract summaries from the 3D tensor-derived maps using JHU templates warped to native space.

## Output Files

Typical outputs include:

- `dwi_nlm.nii.gz`, `dwi_mppca.nii.gz`, or other intermediate 4D DWI files depending on steps
- `gdm/dwi_*_gdm.nii.gz` for GDM-corrected 4D DWI
- `b0_for_tigerbx.nii.gz`
- `mask_tigerbx.nii.gz`
- `dti_FA.nii.gz`
- `dti_MD.nii.gz`
- `dti_RD.nii.gz`
- `dti_AD.nii.gz`
- `qc_metrics.json`
- optional CSV row containing QC and ROI/tract values
