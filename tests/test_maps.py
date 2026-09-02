"""Tests for plot_map."""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd

from plotting_joseph import plot_map


def _make_grid_lookup(tmp_path, n_lat=10, n_lon=20):
    """Build a minimal gridSampling_k1 lookup table."""
    n_pixels = n_lat * n_lon
    pc = [
        {"location_id": i, "pixel_id": i} for i in range(0, n_pixels, 3)
    ]  # a few locations
    df = pd.DataFrame(pc)
    path = tmp_path / "location_ids_gridSampling_1.0_k1.parquet"
    df.to_parquet(path, index=False)
    return path


def test_plot_map_basic(tmp_path):
    lut = _make_grid_lookup(tmp_path)
    lut_df = pd.read_parquet(lut)
    data = pd.DataFrame(
        {
            "location_id": lut_df["location_id"],
            "backscatter40": np.random.RandomState(0).normal(size=len(lut_df)),
        }
    )

    fig = plot_map(data=data, var="backscatter40", lookuptable_path=lut)
    assert fig is not None
    # saved figure path
    out = tmp_path / "out"
    plot_map(
        data=data,
        var="backscatter40",
        lookuptable_path=lut,
        save_path=out / "map.png",
        title="Test map",
    )
    assert (out / "map.png").exists()

    import matplotlib.pyplot as plt
    plt.close("all")
