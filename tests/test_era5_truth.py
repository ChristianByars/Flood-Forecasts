import numpy as np
import pandas as pd
import pytest

import era5_truth

LAT = np.arange(41.0, 31.0, -1.0)   # descending, like the model grid
LON = np.arange(264.0, 280.0)


def _hourly_rain(start="2025-04-01T01:00", end="2025-04-08T00:00", seed=0):
    """Random hourly rain (mm) at two grid points, stamped at the END of each hour (the ERA5 convention)."""
    times = pd.date_range(start, end, freq="h")
    rain = np.random.default_rng(seed).gamma(0.5, 2.0, size=(times.size, 1, 2))
    return era5_truth.xr.DataArray(rain, dims=("valid_time", "lat", "lon"), coords={"valid_time": times})


def _tp06_store(hourly, init, nsteps):
    """Fake forecast store like run.deterministic writes: tp06[0, s] = rain (m) in the 6 h ending at init + 6s h."""
    init = np.datetime64(init)
    tp = np.zeros((1, nsteps + 1) + hourly.shape[1:])   # step 0 (the initial state) stays all zeros
    for step in range(1, nsteps + 1):
        end = init + np.timedelta64(6 * step, "h")
        window = hourly.sel(valid_time=slice(end - np.timedelta64(5, "h"), end))
        assert window.sizes["valid_time"] == 6
        tp[0, step] = window.sum("valid_time").values / 1000.0
    return {"tp06": tp}


@pytest.mark.parametrize("init, nsteps, days", [
    ("2025-04-01T00:00", 20, ["2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04", "2025-04-05"]),
    ("2025-04-01T00:00", 24, ["2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04", "2025-04-05", "2025-04-06"]),
    ("2025-04-02T00:00", 20, ["2025-04-02", "2025-04-03", "2025-04-04", "2025-04-05", "2025-04-06"]),
])
def test_model_daily_total_matches_the_era5_daily_total(init, nsteps, days):
    hourly = _hourly_rain()
    store = _tp06_store(hourly, init, nsteps)
    era5 = era5_truth.daily_total_from_hourly(hourly)
    for day in days:
        model = era5_truth.compute_daily_total_precip(store, day, init)
        np.testing.assert_allclose(model, era5.sel(day=np.datetime64(day)).values, err_msg=day)


@pytest.mark.parametrize("day", ["2025-03-31", "2025-04-06"])
def test_model_daily_total_raises_for_a_day_the_forecast_does_not_cover(day):
    store = {"tp06": np.zeros((1, 21, 1, 2))}   # init Apr 1 00Z + 20 steps reaches Apr 6 00Z
    with pytest.raises(ValueError):
        era5_truth.compute_daily_total_precip(store, day, "2025-04-01T00:00")


def test_rain_in_the_hour_before_00z_counts_for_the_previous_day_on_both_sides():
    hourly = _hourly_rain() * 0.0
    hourly.loc[{"valid_time": "2025-04-03T00:00"}] = 7.0   # one pulse in (Apr 2 23Z, Apr 3 00Z]
    store = _tp06_store(hourly, "2025-04-01T00:00", 20)
    era5 = era5_truth.daily_total_from_hourly(hourly)
    for day, expected in [("2025-04-02", 7.0), ("2025-04-03", 0.0)]:
        np.testing.assert_allclose(era5_truth.compute_daily_total_precip(store, day, "2025-04-01T00:00"), expected)
        np.testing.assert_allclose(era5.sel(day=np.datetime64(day)).values, expected)


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
