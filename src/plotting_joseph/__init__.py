"""plotting_joseph - visualization tools for spatiotemporal Earth observation data.

Provides multi-panel time series plotting and global map plotting with
flexible data formats and user-generated lookup tables.
"""

from .config import Config, LookupTableConfig, LookupTables
from .data import (
    DataLoader,
    LookupTableCreator,
    ensure_country_lookup,
    ensure_grid_lookup,
    ensure_location_ids,
    ensure_neighbor_lookup,
    resolve_lookup_tables,
    validate_lookup_tables,
)
from .plotting import Timeseries, plot_map

__version__ = "0.1.0"

__all__ = [
    "Config",
    "DataLoader",
    "LookupTableConfig",
    "LookupTableCreator",
    "LookupTables",
    "Timeseries",
    "ensure_country_lookup",
    "ensure_grid_lookup",
    "ensure_location_ids",
    "ensure_neighbor_lookup",
    "plot_map",
    "resolve_lookup_tables",
    "validate_lookup_tables",
]
