"""Tests for plot_map."""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd

from plotting_joseph import plot_map


def _make_master(tmp_path, n_lat=10, n_lon=20, grid_sampling=1.0):
    """Build a master location_id -> tile_id (with lat/lon) lookup."""
    extent = (-180.0, 180.0, -60.0, 85.0)
    lon_min, lon_max, lat_min, lat_max = extent
    # Build a few locations spread on the grid, with the given sampling.
    n_lon_cells = int(round((lon_max - lon_min) / grid_sampling))
    n_lat_cells = int(round((lat_max - lat_min) / grid_sampling))
    rows = []
    for i in range(0, n_lat_cells, max(1, n_lat_cells // n_lat)):
        for j in range(0, n_lon_cells, max(1, n_lon_cells // n_lon)):
            rows.append(
                {
                    "location_id": int(i * n_lon_cells + j),
                    "lat": lat_max - (i + 0.5) * grid_sampling,
                    "lon": lon_min + (j + 0.5) * grid_sampling,
                    "tile_id": "tile0",
                }
            )
    df = pd.DataFrame(rows)
    path = tmp_path / "location_id_to_tile_id.parquet"
    df.to_parquet(path, index=False)
    return path, df


def test_plot_map_basic(tmp_path):
    master, master_df = _make_master(tmp_path)
    data = pd.DataFrame(
        {
            "location_id": master_df["location_id"],
            "backscatter40": np.random.RandomState(0).normal(size=len(master_df)),
        }
    )

    fig = plot_map(
        data=data,
        var="backscatter40",
        master_lookup=master,
        grid_sampling=1.0,
        show_plot=False,
    )
    assert fig is not None
    out = tmp_path / "out"
    plot_map(
        data=data,
        var="backscatter40",
        master_lookup=master,
        grid_sampling=1.0,
        save_path=out / "map.png",
        title="Test map",
    )
    assert (out / "map.png").exists()

    import matplotlib.pyplot as plt

    plt.close("all")
