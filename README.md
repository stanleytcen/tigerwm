# tigerwm

tigerwm is a Python package for running DTI preprocessing and ROI extraction pipelines extracted from the WM notebooks.

The default pipeline is P4:

```text
P4 = NGDSTR = NLM + Gibbs removal + GDM + skull strip + tensor fit + ROI
```

P4 is the default because it showed the best overall age/sex prediction performance and the lowest tensor-residual RMSE in the IXI experiments from this project. This is a project-based default, not a universal rule for every dataset.

## Install From GitHub

```bash
git clone https://github.com/stanleytcen/tigerwm.git
cd tigerwm

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

Check the install:

```bash
python -c "from tigerwm import tigerwm, DEFAULT_PIPELINE, DEFAULT_STEPS; print(DEFAULT_PIPELINE, DEFAULT_STEPS)"
```

Expected output:

```text
P4 NGDSTR
```

Note: tigerbx is installed from the htylab/tigerbx GitHub release archive because it is not distributed on PyPI. For reproducible analyses, record the installed tigerbx version used for each run.

## Required Inputs

- 4D DWI NIfTI file (`.nii` or `.nii.gz`)
- matching bvals file
- matching bvecs file
- output directory
- JHU templates directory when running ROI extraction (`R` step)

The JHU templates directory should contain:

- `JHU-ICBM-FA-1mm.nii.gz`
- `JHU-ICBM-labels-1mm.nii.gz`
- `JHU-ICBM-tracts-maxprob-thr25-1mm.nii.gz`

## Basic Usage

```python
from tigerwm import tigerwm

# Default P4: NLM + Gibbs + GDM + skull strip + tensor fit + ROI
res = tigerwm(
    "/path/to/dwi_raw.nii.gz",
    "/path/to/bvals.txt",
    "/path/to/bvecs.txt",
    "/path/to/output_dir",
    templates_dir="/path/to/templates",
    subject="sub-001",
    csv_path="/path/to/results.csv",
)

print(res["pipeline"], res["steps"])
print(res["dwi"])
```

## Run a Named Pipeline

```python
from tigerwm import tigerwm

# Run P3 by name: MPPCA + Gibbs + GDM + skull strip + tensor fit + ROI
res = tigerwm(
    "P3",
    "/path/to/dwi_raw.nii.gz",
    "/path/to/bvals.txt",
    "/path/to/bvecs.txt",
    "/path/to/output_dir_p3",
    templates_dir="/path/to/templates",
    subject="sub-001",
    csv_path="/path/to/results_p3.csv",
)
```

You can also pass explicit step codes:

```python
tigerwm("MGDSTR", dwi_path, bval_path, bvec_path, out_dir)
```

## Example Scripts

Default P4:

```bash
python examples/run_default_p4.py \
  --dwi /path/to/dwi_raw.nii.gz \
  --bvals /path/to/bvals.txt \
  --bvecs /path/to/bvecs.txt \
  --out-dir /path/to/output_p4 \
  --templates-dir /path/to/templates \
  --subject sub-001 \
  --csv-path /path/to/p4_results.csv
```

Specified P3:

```bash
python examples/run_p3.py \
  --dwi /path/to/dwi_raw.nii.gz \
  --bvals /path/to/bvals.txt \
  --bvecs /path/to/bvecs.txt \
  --out-dir /path/to/output_p3 \
  --templates-dir /path/to/templates \
  --subject sub-001 \
  --csv-path /path/to/p3_results.csv
```

## Named Pipelines

- `P0` = `STR`
- `P1` = `MGSTR`
- `P2` = `NGSTR`
- `P3` = `MGDSTR`
- `P4` = `NGDSTR` (default)
- `P5` = `DSTR`
- `P6` = `DMGSTR`
- `P7` = `DNGSTR`

## Step Codes

- `M` = MPPCA denoising
- `N` = NLM denoising
- `G` = Gibbs ringing removal
- `D` = GDM EPI distortion correction
- `S` = skull strip with tigerbx
- `T` = tensor fit
- `R` = ROI extraction with JHU atlas warped to native space

The steps run in the order provided.

See `docs/pipeline_steps.md` for more detail.
