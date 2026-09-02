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
- **Lookup table creation** (`LookupTableCreator`) — generate the geographic
  lookups the plots need from your own data.

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

### Plot a global map

```python
from plotting_joseph import plot_map

plot_map(
    data=df,                      # DataFrame with location_id + a value column
    var="backscatter40",
    lookuptable_path="lookup_tables/location_ids_gridSampling_k1.parquet",
    title="Global Backscatter",
    save_path="figures/global_map.png",
)
```

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
