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
- **Prebuilt flash-attn wheel.** flash-attn (required by earth2studio's `aifs` extra) is published on PyPI only as a source distribution, and building it needs torch inside the build environment, `nvcc` and a long CUDA compile. PyPI offers no prebuilt wheel for torch 2.13.0+cu132, so this repo expects one prebuilt cp312 wheel, `flash_attn-2.8.3-cp312-cp312-linux_x86_64.whl`, in a git-ignored `wheels/` folder at the repo root. `[tool.uv.sources]` points at it, and `uv sync` fails without it. Build it once against torch 2.13.0+cu132 following the upstream flash-attention build instructions, keep that exact file name, then run `uv lock`, because `uv.lock` pins the sha256 of the author's wheel. On the author's machine `wheels` is a symlink to a folder of prebuilt wheels. The `torch-harmonics` entries in `pyproject.toml` (`[tool.uv.sources]` and `override-dependencies`) are unused lines of the shared baseline and need no wheel here.
- **GraphCast's `weathernext` package comes from GitHub.** earth2studio's `graphcast` extra needs Google DeepMind's `weathernext` package, which is not on PyPI. `pyproject.toml` lists it as a dependency and pins it in `[tool.uv.sources]` to the same git commit that earth2studio 0.20.0 uses, so `uv lock` and `uv sync` need network access to github.com and `git` on the path. `weathernext` also caps xarray at 2026.2.0; with NumPy 2.5 that xarray prints a harmless `DeprecationWarning` about NumPy's generic timedelta unit when it is imported (it shows up in the `pytest` warnings summary).
- **GraphCast (JAX) and AIFS (PyTorch) in one kernel.** All three notebooks set `XLA_PYTHON_CLIENT_PREALLOCATE=false`, so JAX allocates GPU memory as GraphCast needs it instead of reserving most of the GPU up front. `tennessee_valley_flood_model_comparison.ipynb` runs both models in the same kernel, and JAX keeps the memory it has allocated until the kernel exits. A forecast cell that fails deletes its half-written Zarr store, because that notebook reads an existing store back instead of re-running the model. If a forecast run is interrupted or fails part-way (for example AIFS running out of GPU memory after GraphCast), delete that run's `.zarr` folder if it is still there (`aifs_tn_flood_outputs/aifs_tn_ic0401.zarr` for AIFS, `tn_model_compare_outputs/graphcast_tn_era5_ic0401.zarr` for GraphCast), then restart the kernel and run all cells again.
- **ERA5 precipitation needs Copernicus credentials.** The "Verify against ERA5" sections download hourly ERA5 total precipitation from the Copernicus Climate Data Store with `cdsapi`. Put your CDS API key in `~/.cdsapirc` and accept the ERA5 licence on the CDS website once; each notebook caches the download in its output folder (`era5_tp_tn.nc`).
