# tigerwm

DTI pipeline utilities extracted from the WM notebooks.

## Install

```bash
pip install -e .
```

Note: tigerbx is installed from the htylab/tigerbx GitHub release archive because it is not distributed on PyPI. For reproducible analyses, record the installed tigerbx version used for each run.

## Default pipeline

tigerwm uses **P4** by default when no step code is provided.

P4 = `N G D S T R`

- `N`: NLM denoising
- `G`: Gibbs ringing removal
- `D`: GDM EPI distortion correction
- `S`: skull strip with tigerbx
- `T`: tensor fit
- `R`: ROI extraction with JHU atlas

P4 is the default because it had the best overall age/sex prediction performance and the lowest tensor-residual RMSE in the IXI experiments from this project. This default is a project-based recommendation, not a universal rule for every dataset.

## Basic usage

```python
from tigerwm import tigerwm

# Default P4: NLM + Gibbs + GDM + skull strip + tensor fit + ROI
tigerwm(
    r"N:\path\to\dti_raw.nii.gz",
    r"N:\path\to\bvals.txt",
    r"N:\path\to\bvecs.txt",
    r"N:\path\to\out\IXI002",
    templates_dir=r"N:\N\WM\IXI\_shared\templates",
    subject="IXI002",
    csv_path=r"N:\N\WM\IXI\P4_nlm_gibbs_gdm_tigerbx_tensor_jhu\_reports\P4.csv",
)
```

## Custom pipeline

You can still provide a named pipeline or explicit step code.

```python
# Run P3 by name
tigerwm(
    "P3",
    r"N:\path\to\dti_raw.nii.gz",
    r"N:\path\to\bvals.txt",
    r"N:\path\to\bvecs.txt",
    r"N:\path\to\out\IXI002",
    templates_dir=r"N:\N\WM\IXI\_shared\templates",
    subject="IXI002",
    csv_path=r"N:\N\WM\IXI\P3_mppca_gibbs_gdm_tigerbx_tensor_jhu\_reports\P3.csv",
)

# Run the same P3 steps explicitly
tigerwm("MGDSTR", dwi_path, bval_path, bvec_path, out_dir)
```

## Named pipelines

- `P0` = `STR`
- `P1` = `MGSTR`
- `P2` = `NGSTR`
- `P3` = `MGDSTR`
- `P4` = `NGDSTR` (default)
- `P5` = `DSTR`
- `P6` = `DMGSTR`
- `P7` = `DNGSTR`

## Step codes

- `M` = MPPCA
- `N` = NLM
- `G` = Gibbs
- `D` = GDM
- `S` = skull strip (tigerbx)
- `T` = tensor fit
- `R` = ROI (JHU atlas to native)

The steps run in the order provided.

