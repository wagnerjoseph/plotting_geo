"""plotting_joseph - visualization tools for spatiotemporal Earth observation data.

Provides multi-panel time series plotting and global map plotting with
flexible data formats and user-generated lookup tables.
"""

from .config import Config, LookupTables
from .data import DataLoader, LookupTableCreator, validate_lookup_tables
from .plotting import Timeseries, plot_map

__version__ = "0.1.0"

__all__ = [
    "Config",
    "DataLoader",
    "LookupTableCreator",
    "LookupTables",
    "Timeseries",
    "plot_map",
    "validate_lookup_tables",
]
