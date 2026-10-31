"""ERA5 daily-precipitation truth for the Tennessee Valley flood notebooks.

ERA5 precipitation is itself a model (reanalysis) product, so scores against it measure agreement with
ERA5, not with rain gauges.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

TN_BOX = {"lat": (33.0, 40.5), "lon": (265.0, 278.0)}   # Tennessee Valley; longitude in 0-360
TN_ERA5_AREA = [41.5, -96.0, 32.0, -81.0]                # CDS area [N, W, S, E], 1 degree buffer


def daily_total_from_hourly(hourly: xr.DataArray) -> xr.DataArray:
    """Hourly ERA5 precipitation (stamped at the END of each accumulation hour) -> daily totals.

    The model's total for day D sums the 6-hourly steps valid 06Z, 12Z, 18Z and 24Z, so it covers
    (D 00Z, D+1 00Z]. ERA5 stamps 01Z..24Z therefore belong to day D; shifting the stamps back one hour
    lets a plain calendar-day resample do the right thing. A day with fewer than 24 hourly values is
    returned as NaN rather than as a silently low total.
    """
    shifted = hourly.assign_coords(valid_time=hourly["valid_time"] - np.timedelta64(1, "h"))
    return shifted.resample(valid_time="1D").sum(min_count=24).rename(valid_time="day")


def _days_to_request(days) -> list[np.datetime64]:
    """UTC days whose hourly data are needed: each wanted day plus the next one, whose 00Z hour closes it."""
    wanted = {np.datetime64(d, "D") for d in days}
    return sorted(wanted | {d + np.timedelta64(1, "D") for d in wanted})


def _retrieve(client, params: dict, target: str) -> None:
    """CDS changed its request keys in 2024; try the current style first, then the legacy one."""
    dataset = "reanalysis-era5-single-levels"
    try:
        client.retrieve(dataset, {**params, "data_format": "netcdf", "download_format": "unarchived"}, target)
    except Exception:  # noqa: BLE001 - any failure falls back to the legacy request key
        client.retrieve(dataset, {**params, "format": "netcdf"}, target)


def fetch_era5_daily_precip(days, area, cache_path) -> xr.DataArray:
    """ERA5 daily-total precipitation (mm), dims (day, lat, lon), longitude 0-360, cached at `cache_path`.

    `days` are the UTC days wanted. The day after each wanted day is requested as well because its 00Z hour
    closes the wanted day's accumulation. One CDS request per month; needs ~/.cdsapirc credentials.
    """
    cache_path = Path(cache_path)
    wanted = np.array(sorted({np.datetime64(d, "D") for d in days}))
    wanted_ns = wanted.astype("datetime64[ns]")
    if cache_path.exists():
        return xr.open_dataarray(cache_path).sel(day=wanted_ns)

    import cdsapi

    by_month: dict[tuple[str, str], list[str]] = {}
    for day in _days_to_request(wanted):
        text = str(day)
        by_month.setdefault((text[:4], text[5:7]), []).append(text[8:10])
    client = cdsapi.Client()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    for (year, month), day_numbers in sorted(by_month.items()):
        tmp = cache_path.with_name(f"_era5_tp_{year}{month}.nc")
        if not tmp.exists():
            _retrieve(client, {
                "product_type": "reanalysis", "variable": "total_precipitation",
                "year": year, "month": month, "day": sorted(day_numbers),
                "time": [f"{h:02d}:00" for h in range(24)], "area": area,
            }, str(tmp))
        part = xr.open_dataset(tmp)["tp"].drop_vars(["number", "expver"], errors="ignore")
        part = part.rename({"latitude": "lat", "longitude": "lon"})
        time_name = "valid_time" if "valid_time" in part.dims else ("time" if "time" in part.dims else list(part.dims)[0])
        parts.append(part.rename({time_name: "valid_time"}))
    hourly = xr.concat(parts, dim="valid_time") if len(parts) > 1 else parts[0]
    hourly = hourly.assign_coords(lon=hourly["lon"] % 360).sortby("lon")
    hourly = (hourly * 1000.0).clip(min=0.0)   # metres -> millimetres
    daily = daily_total_from_hourly(hourly).sel(day=wanted_ns)
    daily.name = "tp"
    daily.attrs["units"] = "mm"
    daily.load().to_netcdf(cache_path)
    return daily


def as_dataarray(field, lat, lon) -> xr.DataArray:
    """Wrap a 2-D (lat, lon) NumPy field with its coordinates."""
    return xr.DataArray(np.asarray(field), dims=("lat", "lon"),
                        coords={"lat": np.asarray(lat), "lon": np.asarray(lon)})


def crop_box(da: xr.DataArray, box: dict) -> xr.DataArray:
    """Crop to box = {"lat": (lo, hi), "lon": (lo, hi)}, whatever the coordinate ordering."""
    lat_ok = (da["lat"] >= min(box["lat"])) & (da["lat"] <= max(box["lat"]))
    lon_ok = (da["lon"] >= min(box["lon"])) & (da["lon"] <= max(box["lon"]))
    return da.sel(lat=da["lat"][lat_ok], lon=da["lon"][lon_ok])


def forecast_vs_era5(fc_field, era5_day: xr.DataArray, lat, lon, box: dict = TN_BOX):
    """Crop a forecast (2-D NumPy on the model grid) and the matching ERA5 day to `box` on one grid.

    Returns (forecast_values, reference_values, lat_values), ready for metrics.skill_row.
    """
    fc = crop_box(as_dataarray(fc_field, lat, lon), box)
    ref = crop_box(era5_day, box).reindex_like(fc, method="nearest")
    return fc.values, ref.values, fc["lat"].values
