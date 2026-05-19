# Flood Forecasts

GraphCast extreme-precipitation forecasts for historical US flood events using [NVIDIA Earth2Studio](https://github.com/NVIDIA/earth2studio).

Each notebook runs a deterministic GraphCast inference, then visualizes daily precipitation totals, point time series, and multi-panel lead-time progressions.

## Case Studies

| Notebook | Event | Init Date | Forecast Window |
|---|---|---|---|
| `graphcast_ohio_valley_flood.ipynb` | 2019 Ohio Valley Flood | 2019-02-10 | Feb 10--14 (5 days) |
| `graphcast_tennessee_valley_flood.ipynb` | 2025 Tennessee Valley Flood | 2025-04-01 | Apr 1--6 (6 days) |

## Prerequisites

- Python 3.12
- NVIDIA GPU with CUDA 12.4
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
uv sync --group dev
```

This installs all dependencies (Earth2Studio, PyTorch with CUDA 12.4, cartopy, etc.) and the `ipykernel` dev dependency for running notebooks.

## Running

Launch Jupyter and open either notebook:

```bash
uv run jupyter lab
```

Each notebook writes forecast output to a local Zarr store (`ohio_flood_outputs/` or `tn_flood_outputs/`) and renders precipitation maps inline.
# Flood-Forecasts
# Flood-Forecasts
