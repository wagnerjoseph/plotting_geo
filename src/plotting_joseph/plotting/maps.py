"""Global map plotting (renamed from ``plot_worldwide``).

This module plots a gridded map from per-location values and a lookup table
that maps ``location_id`` -> pixel on a regular grid.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable

try:  # cartopy is used only for optional coastlines
    import cartopy.io.shapereader as shpreader  # type: ignore
    _HAS_CARTOPY = True
except Exception:  # noqa: BLE001 - optional dependency guard  # pragma: no cover
    _HAS_CARTOPY = False


def _build_pixel_mapping(lut: pd.DataFrame, k: int) -> pd.Series:
    """Build a ``location_id`` -> ``pixel_id`` mapping from a grid lookup table.

    The lookup table is expected to contain ``location_id`` and ``pixel_id``
    columns. For ``k == 1`` a direct 1:1 mapping is used. For ``k > 1`` each
    row is expected to have a ``location_ids`` column listing the original
    locations aggregated into the pixel and a ``pixel_id`` column (either a
    scalar or a list aligned with ``location_ids``).
    """
    import ast

    if k == 1:
        return lut.set_index("location_id")["pixel_id"]

    def safe_eval(x):
        return ast.literal_eval(x) if isinstance(x, str) else x

    pixel_series = (
        lut[["pixel_id", "location_ids"]]
        .assign(
            pixel_id=lut["pixel_id"].apply(safe_eval),
            location_ids=lut["location_ids"].apply(safe_eval),
        )
        .explode("location_ids")
        .rename(columns={"location_ids": "location_id"})
        .explode("pixel_id")
        .dropna(subset=["location_id", "pixel_id"])
    )
    pixel_series["pixel_id"] = pixel_series["pixel_id"].astype(int)
    pixel_series["location_id"] = pixel_series["location_id"].astype(int)
    return pixel_series.set_index("location_id")["pixel_id"]


def _aggregate_pixels(
    pixel_ids: np.ndarray, values: np.ndarray, n_pixels: int, stat: str = "median"
) -> np.ndarray:
    """Aggregate multiple values per pixel using the specified statistic."""
    stat_funcs = {
        "min": np.min,
        "max": np.max,
        "mean": np.mean,
        "median": np.median,
    }
    if stat not in stat_funcs:
        raise ValueError(f"stat must be one of {list(stat_funcs)}, got '{stat}'")
    func = stat_funcs[stat]

    image_flat = np.full(n_pixels, np.nan, dtype=np.float64)
    pixel_bins = {}
    for p, v in zip(pixel_ids, values):
        if 0 <= p < n_pixels:
            pixel_bins.setdefault(p, []).append(v)
    for p, vals in pixel_bins.items():
        image_flat[p] = func(vals)
    return image_flat


def _get_color_norm(
    image: np.ndarray,
    center_at_zero: bool = False,
    value_range: tuple[float, float] | None = None,
):
    """Return a matplotlib color normalization for the image."""
    if value_range is None:
        value_range = (np.nanmin(image), np.nanmax(image))

    vmin, vmax = value_range
    if center_at_zero:
        vmax_symmetric = max(abs(vmin), abs(vmax))
        return TwoSlopeNorm(vmin=-vmax_symmetric, vcenter=0, vmax=vmax_symmetric)
    return plt.Normalize(vmin=vmin, vmax=vmax)


def _make_title(var: str, stat: str, month: str | None = None, k: int = 1) -> str:
    """Construct a descriptive title for the plot."""
    title = var.capitalize() + (f" — {month}" if month else "")
    if k > 1:
        title += f" ({k} neighbors combined using {stat})"
    return title


def plot_map(
    data: pd.DataFrame,
    var: str,
    lookuptable_path: str | Path | None = None,
    master_lookup: str | Path | None = None,
    cache_dir: str | Path | None = None,
    month: str | None = None,
    stat: str = "median",
    title: str | None = None,
    cbar_label: str | None = None,
    cmap: str = "viridis",
    center_at_zero: bool = False,
    extent: tuple[float, float, float, float] = (-180, 180, -60, 85),
    grid_sampling: float | None = None,
    k: int = 1,
    value_range: tuple[float, float] | None = None,
    save_path: str | Path | None = None,
    plot_robust: tuple[float, float] | None = None,
    add_coastlines: bool = False,
    add_marker: object | None = None,
    dpi: int = 300,
    figsize: tuple[int, int] | None = (15, 6),
    font_scale: float = 1.0,
    show_plot: bool = False,
):
    """Plot a global map of the given variable.

    Parameters
    ----------
    data : pd.DataFrame
        Data with ``location_id`` (and optional ``time`` for month filtering)
        columns and the variable to plot.
    var : str
        Column name of the variable to plot.
    lookuptable_path : str or Path, optional
        Path to the lookup table mapping ``location_id`` -> ``pixel_id`` on a
        regular grid. The grid resolution is parsed from the filename using
        the pattern ``..._gridSampling_kN.parquet`` (``N`` = number of
        aggregated neighbors, ``1`` for a direct 1:1 mapping). If None, it is
        auto-generated from ``master_lookup``.
    master_lookup : str or Path, optional
        Master lookup parquet (``location_id`` -> tile with ``lat``/``lon``).
        Used to auto-build the grid/map lookup when ``lookuptable_path`` is
        None. The generated lookup is cached (see ``cache_dir``) and reused
        for identical ``grid_sampling`` / ``extent`` / ``k``.
    cache_dir : str or Path, optional
        Where auto-generated lookups are stored/reused. If None, a
        ``generated_lookups`` folder next to the master lookup is used.
    month : str, optional
        Filter to a specific month (e.g. ``"2020-01"``) using the ``time``
        column. If None, uses all data.
    stat : str, default="median"
        Aggregation statistic when ``k > 1``: "min", "max", "mean", "median".
    title : str, optional
        Custom title. If None, auto-generated.
    cbar_label : str, optional
        Colorbar label. If None, auto-generated.
    cmap : str, default="viridis"
        Matplotlib colormap name.
    center_at_zero : bool, default=False
        If True, center the color scale at 0 (symmetric range).
    extent : tuple, default=(-180, 180, -60, 85)
        Bounding box ``(lon_min, lon_max, lat_min, lat_max)``.
    grid_sampling : float, optional
        Grid resolution in degrees. If None, parsed from the lookup filename
        pattern ``..._gridSampling_<res>_kN.parquet``. Recommended to pass
        explicitly for clarity.
    value_range : tuple, optional
        Fixed color range ``(vmin, vmax)``; values outside are clipped. If
        None, uses the data min/max.
    save_path : str or Path, optional
        Where to save the figure. If None, the figure is not saved.
    plot_robust : tuple, optional
        Robust color range as percentiles ``(low, high)``, e.g. ``(2, 98)``.
    add_coastlines : bool, default=False
        If True, overlay natural-earth coastlines (requires ``cartopy``).
    add_marker : tuple or list of tuples, optional
        ``(style, location_id)`` marker(s) placed on the map.
    dpi : int, default=300
        Resolution for the saved figure.
    figsize : tuple, optional
        Figure size ``(width, height)``.
    font_scale : float, default=1.0
        Font-size scale factor.
    show_plot : bool, default=False
        If True, display the figure interactively (otherwise it is closed).
    """

    df = data.copy() if hasattr(data, "copy") else data

    if df is None or not isinstance(df, pd.DataFrame):
        raise TypeError("data must be a pandas.DataFrame")

    if month is not None:
        if "time" not in df.columns:
            raise ValueError("month filtering requires a 'time' column in data")
        df = df[df["time"] == pd.to_datetime(f"{month}-01")]

    if {"location_id", var} - set(df.columns):
        raise ValueError(
            f"data must contain columns 'location_id' and '{var}'. "
            f"Got: {list(df.columns)}. Rename columns via DataLoader column_map."
        )

    data_sub = df[["location_id", var]]

    # Build the grid/map lookup from the master lookup when none was given.
    if lookuptable_path is None:
        if master_lookup is None:
            raise ValueError(
                "plot_map needs a lookup table. Pass 'lookuptable_path' directly "
                "or provide 'master_lookup' to auto-generate one."
            )
        from ..data import ensure_grid_lookup

        lookuptable_path = ensure_grid_lookup(
            master_lookup,
            grid_sampling=grid_sampling,
            extent=extent,
            k=k,
            cache_dir=cache_dir,
        )

    lut = pd.read_parquet(lookuptable_path)

    name_parts = Path(lookuptable_path).stem.split("_")
    if k == 1:
        # honour k parsed from a user-supplied filename when not explicit
        try:
            k = int(name_parts[-1][1:] if name_parts[-1].startswith("k") else 1)
        except ValueError:
            k = 1

    if grid_sampling is None:
        # Try to recover resolution from ..._gridSampling_<res>_kN.parquet
        try:
            gi = name_parts.index("gridSampling")
            grid_sampling = float(name_parts[gi + 1])
        except (ValueError, IndexError) as e:  # pragma: no cover
            raise ValueError(
                "Could not parse 'grid_sampling' from filename. Pass it "
                "explicitly via the grid_sampling parameter."
            ) from e

    location_to_pixel = _build_pixel_mapping(lut, k)

    data_with_pixel_id = data_sub.merge(
        location_to_pixel.to_frame("pixel_id"),
        left_on="location_id",
        right_index=True,
        how="inner",
    )

    pixel_id = data_with_pixel_id["pixel_id"].to_numpy()
    values = data_with_pixel_id[var].to_numpy()

    lon_min, lon_max, lat_min, lat_max = extent
    n_lat = int(np.round((lat_max - lat_min) / grid_sampling))
    n_lon = int(np.round((lon_max - lon_min) / grid_sampling))
    n_pixels = n_lat * n_lon

    if k == 1:
        image_flat = np.full(n_pixels, np.nan, dtype=np.float64)
        valid = (pixel_id >= 0) & (pixel_id < n_pixels)
        image_flat[pixel_id[valid]] = values[valid]
    else:
        image_flat = _aggregate_pixels(pixel_id, values, n_pixels, stat=stat)

    image = image_flat.reshape(n_lat, n_lon)

    # Robust color range
    if plot_robust is not None:
        flat_data = image.ravel()
        flat_data = flat_data[~np.isnan(flat_data)]
        if len(flat_data) > 0:
            q_low, q_high = plot_robust
            value_range = (
                np.quantile(flat_data, q_low / 100.0),
                np.quantile(flat_data, q_high / 100.0),
            )

    norm = _get_color_norm(image, center_at_zero, value_range)

    if cbar_label is None:
        cbar_label = f"{stat}({var})" if k > 1 else var

    if title is None:
        title = _make_title(var, stat, month, k) + (
            " (robust)" if plot_robust is not None else ""
        )

    flat_data = image.ravel()
    flat_data = flat_data[~np.isnan(flat_data)]

    cmap_obj = plt.get_cmap(cmap)

    fig, ax = plt.subplots(figsize=figsize)

    if add_coastlines:
        if not _HAS_CARTOPY:
            raise ImportError(
                "add_coastlines requires the optional 'coastlines' extra: "
                "pip install 'plotting_joseph[coastlines]'"
            )
        coast_shp = shpreader.natural_earth(
            resolution="110m", category="physical", name="coastline"
        )
        for record in shpreader.Reader(coast_shp).geometries():
            ax.plot(*record.xy, color="black", linewidth=1)

    im = ax.imshow(
        image,
        origin="upper",
        extent=[lon_min, lon_max, lat_min, lat_max],
        cmap=cmap,
        norm=norm,
        aspect="auto",
    )

    marker_value = None
    if add_marker is not None:
        markers_to_plot = add_marker if isinstance(add_marker, list) else [add_marker]
        for marker_style, marker_location_id in markers_to_plot:
            if marker_location_id in location_to_pixel.index:
                marker_pixel = int(location_to_pixel.loc[marker_location_id])
                row = marker_pixel // n_lon
                col = marker_pixel % n_lon
                lon = lon_min + (col + 0.5) * grid_sampling
                lat = lat_max - (row + 0.5) * grid_sampling
                ax.plot(
                    lon,
                    lat,
                    marker_style,
                    color="red",
                    markersize=10,
                    markeredgewidth=2,
                )
                current_marker_value = image[row, col]
                if marker_value is None:
                    marker_value = current_marker_value
                if value_range is not None:
                    vmin, vmax = value_range
                    current_marker_value = np.clip(
                        current_marker_value,
                        vmin + 0.005 * (vmax - vmin),
                        vmax - 0.005 * (vmax - vmin),
                    )
            else:
                print(
                    f"  Warning: location_id={marker_location_id} not found in lookup table"
                )

    divider = make_axes_locatable(ax)
    hist_ax = divider.append_axes("right", size="10%", pad=0.07, sharey=None)

    if value_range is not None:
        vmin, vmax = value_range
    elif plot_robust is not None:
        q_low, q_high = plot_robust
        vmin = np.quantile(flat_data, q_low / 100.0)
        vmax = np.quantile(flat_data, q_high / 100.0)
    else:
        vmin, vmax = flat_data.min(), flat_data.max()

    flat_data_clipped = np.clip(flat_data, vmin, vmax)
    unique_vals = np.unique(flat_data)

    if len(unique_vals) == 1:
        val = unique_vals[0]
        bins = [val - 0.5, val + 0.5]
        counts = np.array([len(flat_data)])
        hist_ax.barh(
            y=val,
            width=counts[0],
            height=bins[1] - bins[0],
            color=cmap_obj(im.norm(val)),
            edgecolor="k",
        )
    else:
        number_of_bins = 100
        counts, bins, patches = hist_ax.hist(
            flat_data_clipped,
            bins=number_of_bins,
            range=(vmin, vmax),
            orientation="horizontal",
        )
        for patch, y0, y1 in zip(patches, bins[:-1], bins[1:]):
            y_center = 0.5 * (y0 + y1)
            patch.set_facecolor(cmap_obj(im.norm(y_center)))

    hist_ax.xaxis.set_visible(False)
    hist_ax.yaxis.set_visible(False)
    hist_ax.invert_xaxis()

    if add_marker is not None:
        markers_to_plot = add_marker if isinstance(add_marker, list) else [add_marker]
        marker_values = []
        for marker_style, marker_location_id in markers_to_plot:
            if marker_location_id in location_to_pixel.index:
                marker_pixel = int(location_to_pixel.loc[marker_location_id])
                row = marker_pixel // n_lon
                col = marker_pixel % n_lon
                marker_val = image[row, col]
                if not np.isnan(marker_val):
                    marker_values.append(marker_val)
        for marker_val in marker_values:
            hist_ax.axhline(marker_val, color="red", linewidth=1, alpha=0.7)

    if center_at_zero and vmin <= 0 <= vmax:
        hist_ax.axhline(0, color="black", linewidth=0.4)

    BASE_TITLE_SIZE = 17
    BASE_CBAR_LABEL_SIZE = 12
    BASE_TICK_SIZE = 10

    title_size = BASE_TITLE_SIZE * font_scale
    cbar_label_size = BASE_CBAR_LABEL_SIZE * font_scale
    tick_size = BASE_TICK_SIZE * font_scale

    cax = divider.append_axes("right", size="5%", pad=0.07, sharey=hist_ax)
    cbar = fig.colorbar(im, cax=cax, label=cbar_label)
    cbar.ax.set_ylabel(cbar_label, fontsize=cbar_label_size)
    cbar.ax.tick_params(labelsize=tick_size)

    fig.suptitle(title, fontsize=title_size, y=0.94)

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")

    if show_plot:
        plt.show()

    return fig
