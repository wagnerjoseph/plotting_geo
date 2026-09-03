# plotting_joseph

Reusable visualization tools for spatiotemporal Earth observation data: flexible
**multi-panel time series** plotting and **global maps**. Designed to be data-format
agnostic and easy to drop into any project.

## Features

- **Time series** (`Timeseries.plot_time_series`) — multi-panel plots with:
  - overlays on a shared or secondary y-axis
  - Pearson / Spearman correlation annotations
  - threshold shading (per-panel or across all panels)
  - season markers, interpolation, rolling transforms
  - nearest-neighbor background series
- **Global maps** (`plot_map`) — gridded worldwide maps with histogram colorbar,
  robust color ranges, markers and optional coastlines.
- **Flexible data loading** (`DataLoader`) — parquet, CSV, or any in-memory
  DataFrame with automatic column mapping/validation.
- **Auto-generated lookup tables** — point the plotting functions at a single
  master lookup (`location_id` → `tile_id` with lat/lon) and the derived lookups
  they need (countries, grid/map, neighbors) are created **on demand**, cached,
  and reused for identical parameters.

## Installation

From the repository root:

```bash
pip install -e .
# with optional extras
pip install -e ".[all]"
```

Extras:

| Extra        | Provides                                        |
|--------------|--------------------------------------------------|
| `netcdf`     | xarray / netCDF loading (load then pass DataFrame) |
| `geocoding`  | automatic country-name lookup generation         |
| `coastlines` | cartopy natural-earth coastlines on maps         |
| `all`        | all of the above                                 |
| `dev`        | pytest + ruff                                    |

## Quick Start

### Load data and plot time series

```python
from plotting_joseph import DataLoader, Timeseries

# Normalizes + validates columns (rename yours via column_map)
df = DataLoader().load("monthly_mean/0009.parquet")

Timeseries.plot_time_series(
    data=df,
    location_ids=[2156788],
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
    save_dir="figures",
)
```

The country names shown in the titles come from a lookup that is auto-generated
from the web (reverse geocoding) when it doesn't exist yet — just point the call
at your master `location_id_to_tile_id` file:

```python
Timeseries.plot_time_series(
    data=df,
    location_ids=[2156788],
    var_specs=[
        {"name": "backscatter40", "color": "royalblue"},
        {"name": "lai", "color": "forestgreen", "add_to": "backscatter40",
         "add_second_axis": True, "compute_corr": True},
    ],
    master_lookup="lookup_tables/location_id_to_tile_id.parquet",
    add_closest_points=(4, 300.0),   # auto-generates the neighbor lookup too
    cache_dir="lookups/",
    save_dir="figures",
)
```

### Plot a global map

```python
from plotting_joseph import plot_map

plot_map(
    data=df,                      # DataFrame with location_id + a value column
    var="backscatter40",
    master_lookup="lookup_tables/location_id_to_tile_id.parquet",  # required
    extent=(-180, 180, -60, 85),
    grid_sampling=0.5,            # required
    cache_dir="lookups/",
    title="Global Backscatter",
    save_path="figures/global_map.png",
)
```

`plot_map` builds the grid/map lookup automatically from the master lookup. The
lookup is created once per combination of geometric parameters (`grid_sampling`,
`extent`, `k`) and reused afterwards.

## Auto-generated lookups

Pass a **master lookup** (`location_id_to_tile_id.parquet` with `location_id`,
`lat`, `lon` and optional `tile_id`) to the plotting functions and the derived
lookups are **created on demand**, only when they don't already exist:

* **countries** (for time-series titles) — via reverse geocoding from the web
* **grid/map lookup** (for `plot_map`) — built from the lat/lon coordinates,
  keyed by `grid_sampling` + `extent` + `k`
* **neighbors** (for `add_closest_points`) — per-tile nearest neighbors, keyed
  by `k` + `max_distance_km`

Generated lookups are cached to `cache_dir` (default: a `generated_lookups/`
folder next to the master lookup) and **reused whenever the same parameters are
passed again**. The geometric parameters are encoded in the lookup filename, so
different grids/extents produce separate cached files.

The `ensure_*` helpers (`ensure_location_ids`, `ensure_country_lookup`,
`ensure_grid_lookup`, `ensure_neighbor_lookup`) expose the same generation for
manual use.

## Documentation

- [Lookup tables](docs/lookup_tables.md) — how to create & use the geographic lookups
- [Data formats](docs/data_formats.md) — supported formats and column mapping
- [API: timeseries](docs/api/timeseries.md)
- [API: maps](docs/api/maps.md)

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src
```

## License

MIT — see [LICENSE](LICENSE). Maintained by Joseph Wagner
(joseph.wagner@geo.tuwien.ac.at).
