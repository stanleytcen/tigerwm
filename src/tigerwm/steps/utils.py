from pathlib import Path
import numpy as np


def strip_nii_suffix(name):
    if name.endswith(".nii.gz"):
        return name[:-7]
    if name.endswith(".nii"):
        return name[:-4]
    return name


def pick_b0(data, bvals=None, b0_index=0, b0_thresh=50.0):
    if b0_index is not None:
        return data[..., b0_index]
    if bvals is None:
        return data[..., 0]
    idx = np.where(bvals <= b0_thresh)[0]
    if idx.size == 0:
        return data[..., 0]
    return data[..., idx].mean(axis=3)


def to_path(p):
    return p if isinstance(p, Path) else Path(p)
