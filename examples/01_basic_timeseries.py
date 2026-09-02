"""Example: basic multi-panel time series with correlation annotation.

Run:
    python examples/01_basic_timeseries.py
"""

import numpy as np
import pandas as pd

from plotting_joseph import Timeseries

# ---------------------------------------------------------------------------
# 1. Build some synthetic data (use DataLoader().load(...) in practice)
# ---------------------------------------------------------------------------
dates = pd.date_range("2000-01-01", periods=240, freq="MS")
t = np.linspace(0, 8 * np.pi, len(dates))

df = pd.DataFrame(
    {
        "location_id": [2156788] * len(dates),
        "time": dates,
        "backscatter40": np.sin(t),
        "lai": 2 * np.sin(t) + 1,
        "swvl1": np.linspace(-1, 1, len(dates)),
    }
)

# ---------------------------------------------------------------------------
# 2. Define panels/overlays
# ---------------------------------------------------------------------------
var_specs = [
    {"name": "backscatter40", "label": "Backscatter", "color": "royalblue"},
    {
        "name": "lai",
        "label": "LAI",
        "color": "forestgreen",
        "add_to": "backscatter40",
        "add_second_axis": True,
        "compute_corr": True,  # show Pearson + Spearman vs backscatter
    },
]

# ---------------------------------------------------------------------------
# 3. Plot
# ---------------------------------------------------------------------------
figs = Timeseries.plot_time_series(
    data=df,
    location_ids=[2156788],
    var_specs=var_specs,
    save_dir="figures",
    show_plot=True,
)
print(f"Saved {len(figs)} figure(s) to ./figures")
