"""Tests for the master-lookup driven configuration (LookupTableConfig)."""

import numpy as np
import pandas as pd
import pytest

from plotting_joseph import (
    LookupTableConfig,
    Timeseries,
    ensure_country_lookup,
    ensure_grid_lookup,
    ensure_location_ids,
    ensure_neighbor_lookup,
    plot_map,
    resolve_lookup_tables,
)


@pytest.fixture
def master(tmp_path):
    """A small master lookup (location_id -> tile_id with lat/lon)."""
    rng = np.random.default_rng(0)
    n = 300
    lat = rng.uniform(-10, 10, n)
    lon = rng.uniform(-20, 20, n)
    loc_id = np.arange(2000, 2000 + n)
    tile = [f"t{i % 4}" for i in range(n)]
    df = pd.DataFrame(
        {"location_id": loc_id, "lat": lat, "lon": lon, "tile_id": tile}
    )
    path = tmp_path / "location_id_to_tile_id.parquet"
    df.to_parquet(path, index=False)
    return tmp_path, path


@pytest.fixture
def cfg(master):
    tmp_path, master_path = master
    return LookupTableConfig(
        master_lookup=master_path,
        cache_dir=tmp_path / "cache",
        grid_sampling=0.5,
        extent=(-25, 25, -15, 15),
        k_neighbors=4,
        max_distance_km=500.0,
    )


def test_ensure_location_ids(cfg):
    out = ensure_location_ids(cfg)
    df = pd.read_parquet(out)
    assert {"location_id", "lat", "lon", "tile_id"} <= set(df.columns)
    assert df["location_id"].is_unique


def test_ensure_grid_lookup(cfg):
    out = ensure_grid_lookup(cfg)
    assert out.exists()
    df = pd.read_parquet(out)
    assert {"location_id", "pixel_id"} <= set(df.columns)


def test_ensure_neighbor_lookup(cfg):
    out = ensure_neighbor_lookup(cfg)
    files = list(out.glob("*.parquet"))
    assert len(files) > 0
    df = pd.read_parquet(files[0])
    assert {
        "location_id",
        "neighbor_location_id",
        "distance_km",
        "rank",
    } <= set(df.columns)


def test_ensure_grid_requires_sampling(master):
    tmp_path, master_path = master
    cfg = LookupTableConfig(master_lookup=master_path, grid_sampling=None)
    with pytest.raises(ValueError, match="grid_sampling"):
        ensure_grid_lookup(cfg)


def test_resolve_lookup_tables(cfg):
    lt = resolve_lookup_tables(cfg, need_neighbors=True)
    assert lt.location_ids is not None
    assert lt.neighbors_dir is not None


def test_plot_map_via_config(cfg, master):
    _, master_path = master
    master_df = pd.read_parquet(master_path)
    data = pd.DataFrame(
        {
            "location_id": master_df["location_id"],
            "backscatter40": np.random.RandomState(1).normal(-12, 3, len(master_df)),
        }
    )
    fig = plot_map(
        data=data,
        var="backscatter40",
        lookup_config=cfg,
        extent=(-25, 25, -15, 15),
        show_plot=False,
    )
    assert fig is not None
    import matplotlib.pyplot as plt

    plt.close(fig)


def test_plot_map_requires_lookup_or_config(master):
    tmp_path, master_path = master
    data = pd.DataFrame({"location_id": [2000], "backscatter40": [-12.0]})
    with pytest.raises(ValueError, match="lookup"):
        plot_map(data=data, var="backscatter40", show_plot=False)


def test_timeseries_via_config(cfg, master):
    _, master_path = master
    master_df = pd.read_parquet(master_path)
    loc_ids = master_df["location_id"].head(20).tolist()

    times = pd.date_range("2000-01-01", periods=24, freq="MS")
    frames = []
    for lid in loc_ids:
        frames.append(
            pd.DataFrame(
                {
                    "location_id": lid,
                    "time": times,
                    "backscatter40": np.full(24, -12.0),
                    "lai": np.full(24, 1.0),
                }
            )
        )
    ts = pd.concat(frames, ignore_index=True)

    figs = Timeseries.plot_time_series(
        data=ts,
        location_ids=[loc_ids[0]],
        var_specs=[{"name": "backscatter40", "color": "royalblue"}],
        add_closest_points=(3, 500.0),
        lookup_config=cfg,
        show_plot=False,
    )
    assert len(figs) == 1
    import matplotlib.pyplot as plt

    for f in figs:
        plt.close(f)


def test_country_lookup_auto(tmp_path, master):
    """Country generation needs internet; tolerate failures."""
    tmp_path, master_path = master
    tiny = tmp_path / "master_tiny.parquet"
    df = pd.read_parquet(master_path).head(3)
    df.to_parquet(tiny, index=False)
    cfg = LookupTableConfig(master_lookup=tiny, cache_dir=tmp_path / "c")
    try:
        out = ensure_country_lookup(cfg)
        assert out.exists()
    except (ImportError, OSError):
        pytest.skip("geocoding extra or internet unavailable")
