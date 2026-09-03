# Maps API

See `src/plotting_joseph/plotting/maps.py` for the full docstring.

## `plot_map(data, var, lookuptable_path=None, master_lookup=None, ...)`

Plots a gridded global map of a variable with a histogram colorbar.

### Key parameters

| Parameter         | Description                                                          |
|-------------------|----------------------------------------------------------------------|
| `data`            | DataFrame with `location_id` (and optional `time`) + the value column. |
| `var`             | column name of the value to plot.                                    |
| `lookuptable_path`| grid lookup table filename matching `..._gridSampling_kN.parquet`.   |
| `master_lookup`   | master lookup (`location_id` -> tile with `lat`/`lon`); auto-generates the grid lookup when `lookuptable_path` is None. |
| `cache_dir`       | where auto-generated lookups are stored/reused (default: `generated_lookups/` next to the master lookup). |
| `grid_sampling`   | grid resolution (°) used to build/interpret the grid lookup.        |
| `extent`          | `(lon_min, lon_max, lat_min, lat_max)`.                             |
| `k`               | number of aggregated neighbors per pixel (`1` = 1:1 mapping).       |
| `month`           | filter to a month (e.g. `"2020-01"`) using the `time` column.         |
| `stat`            | aggregation when `k > 1`: min/max/mean/median.                       |
| `title`, `cbar_label` | plot labels.                                                     |
| `cmap`            | matplotlib colormap.                                                 |
| `center_at_zero`  | symmetric color scale centered at 0.                                 |
| `value_range`     | fixed `(vmin, vmax)` color range.                                    |
| `plot_robust`     | `(low, high)` percentiles for robust color range.                    |
| `add_coastlines`  | overlay natural-earth coastlines (needs `coastlines` extra).         |
| `add_marker`      | `(style, location_id)` or list of them, placed on the map.           |
| `save_path`       | where to save the figure.                                            |
| `show_plot`       | display the figure interactively.                                    |

Returns the matplotlib figure.

> When both are available `lookuptable_path` takes precedence. Without it, the
> grid lookup is auto-generated from `master_lookup` for the given geometric
> parameters and **reused for identical calls** — the lookup filename encodes
> `grid_sampling`, `extent` and `k`.

### Example (explicit lookup)

```python
from plotting_joseph import plot_map

fig = plot_map(
    data=df,                        # location_id + a value column
    var="backscatter40",
    lookuptable_path="lookup_tables/gridSampling_k1.parquet",
    plot_robust=(2, 98),
    title="Global Backscatter (2-98%)",
    save_path="figures/global_backscatter.png",
    add_coastlines=True,
)
```

### Example (auto-generated from a master lookup)

```python
fig = plot_map(
    data=df,
    var="backscatter40",
    master_lookup="lookup_tables/location_id_to_tile_id.parquet",
    extent=(-180, 180, -60, 85),
    grid_sampling=0.5,
    k=1,
    cache_dir="lookups/",
    plot_robust=(2, 98),
    title="Global Backscatter (2-98%)",
    save_path="figures/global_backscatter.png",
)
```

See [Lookup tables](../lookup_tables.md) for the grid lookup format.
