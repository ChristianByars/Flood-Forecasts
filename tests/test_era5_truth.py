import numpy as np
import pandas as pd

import era5_truth

LAT = np.arange(41.0, 31.0, -1.0)   # descending, like the model grid
LON = np.arange(264.0, 280.0)


def test_daily_total_from_hourly_aligns_to_the_model_day():
    times = pd.date_range("2025-04-01T01:00", periods=48, freq="h")   # 01Z Apr 1 ... 00Z Apr 3
    hourly = era5_truth.xr.DataArray(np.ones(48), dims="valid_time", coords={"valid_time": times})
    daily = era5_truth.daily_total_from_hourly(hourly)
    assert [str(d)[:10] for d in daily["day"].values] == ["2025-04-01", "2025-04-02"]
    assert daily.values.tolist() == [24.0, 24.0]


def test_daily_total_from_hourly_marks_an_incomplete_day_as_missing():
    times = pd.date_range("2025-04-01T01:00", periods=47, freq="h")   # 00Z Apr 3 (closes Apr 2) is missing
    hourly = era5_truth.xr.DataArray(np.ones(47), dims="valid_time", coords={"valid_time": times})
    daily = era5_truth.daily_total_from_hourly(hourly)
    assert daily.values[0] == 24.0
    assert np.isnan(daily.values[1])


def test_days_to_request_adds_the_hour_that_closes_every_day():
    days = era5_truth._days_to_request(["2025-04-01", "2025-04-03"])
    assert [str(d) for d in days] == ["2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04"]


def test_crop_box_handles_descending_latitude():
    da = era5_truth.as_dataarray(np.zeros((LAT.size, LON.size)), LAT, LON)
    out = era5_truth.crop_box(da, era5_truth.TN_BOX)
    assert out.shape == (8, 14)
    assert out["lat"].min() >= 33.0 and out["lat"].max() <= 40.5


def test_forecast_vs_era5_regrids_reference_onto_the_forecast_grid():
    fc = np.full((LAT.size, LON.size), 5.0)
    era5_day = era5_truth.as_dataarray(np.full((LAT.size, LON.size), 4.0), LAT + 0.01, LON + 0.01)
    f, r, lats = era5_truth.forecast_vs_era5(fc, era5_day, LAT, LON)
    assert f.shape == r.shape == (8, 14) and lats.shape == (8,)
    assert (f - r == 1.0).all()
