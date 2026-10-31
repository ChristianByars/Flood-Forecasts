# Environment notes

Tested in October 2026 on one NVIDIA L40 (48 GB), Python 3.12, with a CUDA 13 driver.

## Pinned stack

- earth2studio **0.20.0** (the version published on PyPI; uv resolves it through the PyPI and NVIDIA package indexes)
- torch **2.13.0** (CUDA 13.2 wheels from the `pytorch-cu132` index)
- All other versions are resolved in `uv.lock`; use `uv sync` (not `pip install`) so you get exactly the tested set.

## Install

```bash
uv sync
uv run python -m ipykernel install --user --name flood-forecasts --display-name "flood-forecasts"
```

## Known issues and fixes

- **GPU memory between models.** Models from earlier cells stay on the GPU and can cause out-of-memory errors in later sections. Each notebook defines `free_gpu(...)` and calls it in a `finally:` block after every model, so it is released even when a cell fails. If a cell is interrupted by hand, restart the kernel.
- **pytest is a runtime dependency.** The tutorial repos share one package baseline, and in the repos whose models import cupy, `import cupy` needs `pytest` (cupy imports `cupy.testing` internally), so `pytest` is listed in `dependencies`. This repo's lock contains no cupy; here pytest runs the unit tests in `tests/`.
- **Headless runs.** `uv run jupyter nbconvert --to notebook --execute --allow-errors --inplace <notebook>` keeps the outputs of the cells that succeeded when a later cell fails.
- **Prebuilt flash-attn and torch-harmonics wheels.** flash-attn is published on PyPI only as a source distribution, and building it needs torch inside the build environment, `nvcc` and a long CUDA compile; torch-harmonics 0.8.1 is likewise source-only on PyPI and compiles CUDA extensions when it is installed. PyPI offers no prebuilt wheel of either for torch 2.13.0+cu132, so this repo expects two prebuilt cp312 wheels, `flash_attn-2.8.3-cp312-cp312-linux_x86_64.whl` and `torch_harmonics-0.8.1-cp312-cp312-linux_x86_64.whl`, in a git-ignored `wheels/` folder at the repo root. `[tool.uv.sources]` points at them, and `uv sync` fails without them. Build both once against torch 2.13.0+cu132 following the upstream flash-attention and torch-harmonics build instructions, keep those exact file names, then run `uv lock`, because `uv.lock` pins the sha256 of the author's wheels. On the author's machine `wheels` is a symlink to a folder of prebuilt wheels.
- **GraphCast's `weathernext` package comes from GitHub.** earth2studio's `graphcast` extra needs Google DeepMind's `weathernext` package, which is not on PyPI. `pyproject.toml` lists it as a dependency and pins it in `[tool.uv.sources]` to the same git commit that earth2studio 0.20.0 uses, so `uv lock` and `uv sync` need network access to github.com and `git` on the path. `weathernext` also caps xarray at 2026.2.0; with NumPy 2.5 that xarray prints a harmless `DeprecationWarning` about NumPy's generic timedelta unit when it is imported (it shows up in the `pytest` warnings summary).
- **GraphCast (JAX) and AIFS (PyTorch) in one kernel.** `tennessee_valley_flood_model_comparison.ipynb` runs both models in the same kernel and sets `XLA_PYTHON_CLIENT_PREALLOCATE=false` so JAX does not reserve most of the GPU up front. JAX keeps the memory it has used until the kernel exits, so if AIFS runs out of memory after GraphCast, restart the kernel and run all cells again: the GraphCast forecast is then read back from its Zarr store and AIFS has the GPU to itself.
- **ERA5 precipitation needs Copernicus credentials.** The "Verify against ERA5" sections download hourly ERA5 total precipitation from the Copernicus Climate Data Store with `cdsapi`. Put your CDS API key in `~/.cdsapirc` and accept the ERA5 licence on the CDS website once; each notebook caches the download in its output folder (`era5_tp_tn.nc`).
