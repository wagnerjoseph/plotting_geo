"""Example: load data with custom column names, then plot.

Run:
    python examples/04_custom_data_format.py
"""

import numpy as np
import pandas as pd

from plotting_joseph import DataLoader, Timeseries

# ---------------------------------------------------------------------------
# Simulate data with non-canonical column names
# ---------------------------------------------------------------------------
dates = pd.date_range("2000-01-01", periods=120, freq="MS")
df_raw = pd.DataFrame(
    {
        "date": dates,                 # -> time
        "loc_id": [7] * len(dates),    # -> location_id
        "bs": np.sin(np.arange(120) / 5),      # -> backscatter40
        "leaf": np.cos(np.arange(120) / 5),    # -> lai
    }
)

# ---------------------------------------------------------------------------
# Tell DataLoader how your columns map to canonical names
# ---------------------------------------------------------------------------
loader = DataLoader(
    column_map={
        "time": "date",
        "location_id": "loc_id",
        "backscatter40": "bs",
        "lai": "leaf",
    }
)
df = loader.load(df_raw)
print("Normalized columns:", list(df.columns))

# ---------------------------------------------------------------------------
# Plot (var specs use canonical names)
# ---------------------------------------------------------------------------
var_specs = [
    {"name": "backscatter40", "color": "royalblue"},
    {
        "name": "lai",
        "color": "forestgreen",
        "add_to": "backscatter40",
        "add_second_axis": True,
        "compute_corr": True,
    },
]
Timeseries.plot_time_series(
    data=df,
    location_ids=[7],
    var_specs=var_specs,
    save_dir="figures",
    show_plot=True,
)
print("Saved figure(s) to ./figures")
