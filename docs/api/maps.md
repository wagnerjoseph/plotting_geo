# Maps API

See `src/plotting_joseph/plotting/maps.py` for the full docstring.

## `plot_map(data, var, lookuptable_path, ...)`

Plots a gridded global map of a variable with a histogram colorbar.

### Key parameters

| Parameter         | Description                                                          |
|-------------------|----------------------------------------------------------------------|
| `data`            | DataFrame with `location_id` (and optional `time`) + the value column. |
| `var`             | column name of the value to plot.                                    |
| `lookuptable_path`| grid lookup table filename matching `..._gridSampling_kN.parquet`.   |
| `month`           | filter to a month (e.g. `"2020-01"`) using the `time` column.         |
| `stat`            | aggregation when `k > 1`: min/max/mean/median.                       |
| `title`, `cbar_label` | plot labels.                                                     |
| `cmap`            | matplotlib colormap.                                                 |
| `center_at_zero`  | symmetric color scale centered at 0.                                 |
| `extent`          | `(lon_min, lon_max, lat_min, lat_max)`.                              |
| `value_range`     | fixed `(vmin, vmax)` color range.                                    |
| `plot_robust`     | `(low, high)` percentiles for robust color range.                    |
| `add_coastlines`  | overlay natural-earth coastlines (needs `coastlines` extra).         |
| `add_marker`      | `(style, location_id)` or list of them, placed on the map.           |
| `save_path`       | where to save the figure.                                            |
| `show_plot`       | display the figure interactively.                                    |

Returns the matplotlib figure.

### Example

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

See [Lookup tables](../lookup_tables.md) for the grid lookup format.
