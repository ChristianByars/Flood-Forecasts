# Flood Forecasts

Extreme-precipitation forecasts for the 2025 Tennessee Valley flood using [NVIDIA Earth2Studio](https://github.com/NVIDIA/earth2studio), comparing GraphCast and AIFS deterministic runs against each other across initial conditions and models.

Each notebook runs deterministic AI weather model inference, then visualizes daily precipitation totals, point time series, and multi-panel lead-time/model comparisons.

## Case Studies

| Notebook | Event | Init Date | Forecast Window |
|---|---|---|---|
| `graphcast_tennessee_valley_flood.ipynb` | 2025 Tennessee Valley Flood | 2025-04-01 | Apr 1--6 (6 days) |
| `graphcast_tennessee_valley_flood_ic_compare.ipynb` | 2025 Tennessee Valley Flood — IC comparison | 2025-04-01 & 2025-04-02 | Apr 1/2--5, compared over Apr 2--5 |
| `tennessee_valley_flood_model_comparison.ipynb` | 2025 Tennessee Valley Flood — GraphCast vs. AIFS v1 | 2025-04-01 (ERA5/ARCO, shared IC) | Apr 1--6, compared over Apr 2--5 |

## Prerequisites

- Python 3.12
- NVIDIA GPU with CUDA 13.2
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
uv sync
```

This installs all dependencies (Earth2Studio, PyTorch with CUDA 13.2, cartopy, etc.) and the `ipykernel` dev dependency for running notebooks.

## Running

Open any notebook in JupyterLab and run all cells. Each notebook writes forecast output to a local Zarr store (`tn_flood_outputs/`, `tn_flood_ic_compare_outputs/`, or `tn_model_compare_outputs/` + `aifs_tn_flood_outputs/`) and renders precipitation maps inline.
