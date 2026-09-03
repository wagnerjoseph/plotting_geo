"""Tests for plot_time_series and related helpers."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from plotting_joseph import LookupTables, Timeseries, plot_time_series


def test_compute_correlation_both_methods(sample_timeseries_data):
    corr = Timeseries.compute_correlation(
        sample_timeseries_data, "backscatter40", "lai"
    )
    assert set(corr) == {"pearson", "spearman"}
    assert np.isfinite(corr["pearson"])
    assert np.isfinite(corr["spearman"])


def test_compute_correlation_insufficient_data(sample_timeseries_data):
    df = sample_timeseries_data.iloc[:2]
    corr = Timeseries.compute_correlation(df, "backscatter40", "lai")
    assert np.isnan(corr["pearson"])
    assert np.isnan(corr["spearman"])


def test_plot_time_series_basic(sample_timeseries_data):
    figs = Timeseries.plot_time_series(
        data=sample_timeseries_data,
        location_ids=[1],
        var_specs=[
            {"name": "backscatter40", "color": "royalblue"},
            {
                "name": "lai",
                "color": "forestgreen",
                "add_to": "backscatter40",
                "add_second_axis": True,
                "compute_corr": True,
            },
        ],
    )
    assert len(figs) == 1
    # correlation annotation present
    texts = [
        t.get_text()
        for ax in figs[0].axes
        for t in ax.texts
        if "pearson:" in t.get_text()
    ]
    assert len(texts) == 1
    assert "spearman:" in texts[0]
    plt.close("all")


def test_plot_time_series_apply_shading_to_all(sample_timeseries_data):
    figs = Timeseries.plot_time_series(
        data=sample_timeseries_data,
        location_ids=[1],
        var_specs=[
            {"name": "backscatter40", "color": "royalblue"},
            {"name": "lai", "color": "forestgreen"},
            {
                "name": "swvl1",
                "color": "red",
                "lower_treshold": (-0.3, "red"),
                "upper_treshold": (0.3, "blue"),
                "apply_shading_to_all": True,
            },
        ],
    )
    # shading applied to all 3 panel axes
    for ax in figs[0].axes:
        rects = [p for p in ax.patches if type(p).__name__ == "Rectangle"]
        assert len(rects) > 0
    plt.close("all")


def test_plot_time_series_multiple_overlays_raises(sample_timeseries_data):
    import pytest

    var_specs = [
        {"name": "backscatter40", "color": "royalblue"},
        {
            "name": "lai",
            "color": "forestgreen",
            "add_to": "backscatter40",
            "add_second_axis": True,
            "compute_corr": True,
        },
        {
            "name": "swvl1",
            "color": "orange",
            "add_to": "backscatter40",
            "add_second_axis": True,
        },
    ]
    with pytest.raises(ValueError, match="exactly 2 lines"):
        Timeseries.plot_time_series(
            data=sample_timeseries_data,
            location_ids=[1],
            var_specs=var_specs,
        )
    plt.close("all")


def test_plot_time_series_lookup_tables(tmp_path, sample_timeseries_data, sample_lookup_location_ids):
    # countries pickl file
    import pickle

    countries = tmp_path / "countries.pkl"
    with open(countries, "wb") as f:
        pickle.dump({1: "Austria", 2: "Germany"}, f)

    figs = Timeseries.plot_time_series(
        data=sample_timeseries_data,
        location_ids=[1],
        var_specs=[{"name": "backscatter40", "color": "royalblue"}],
        lookup_tables=LookupTables(countries=countries),
    )
    assert "Austria" in figs[0]._suptitle.get_text()
    plt.close("all")


def test_plot_time_series_module_level(sample_timeseries_data):
    """Test that the module-level plot_time_series function works."""
    figs = plot_time_series(
        data=sample_timeseries_data,
        location_ids=[1],
        var_specs=[
            {"name": "backscatter40", "color": "royalblue"},
            {
                "name": "lai",
                "color": "forestgreen",
                "add_to": "backscatter40",
                "add_second_axis": True,
                "compute_corr": True,
            },
        ],
    )
    assert len(figs) == 1
    # correlation annotation present
    texts = [
        t.get_text()
        for ax in figs[0].axes
        for t in ax.texts
        if "pearson:" in t.get_text()
    ]
    assert len(texts) > 0
    plt.close("all")
