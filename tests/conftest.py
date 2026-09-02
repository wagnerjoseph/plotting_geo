"""Shared synthetic fixtures for the test suite."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_timeseries_data() -> pd.DataFrame:
    """Synthetic monthly time series for two locations and three variables."""
    dates = pd.date_range("2000-01-01", periods=240, freq="MS")
    time = np.tile(dates, 2)
    location_ids = np.repeat([1, 2], len(dates))

    # Correlated variables so correlation/overlay tests are meaningful
    t = np.linspace(0, 8 * np.pi, len(dates))
    backscatter = np.sin(t)
    lai = 2 * np.sin(t) + 1
    swvl1 = np.linspace(-1, 1, len(dates))

    df = pd.DataFrame(
        {
            "location_id": location_ids,
            "time": time,
            "backscatter40": np.concatenate([backscatter, backscatter + 0.5]),
            "lai": np.concatenate([lai, lai - 0.5]),
            "swvl1": np.concatenate([swvl1, swvl1]),
        }
    )
    return df


@pytest.fixture(scope="session")
def sample_lookup_location_ids() -> Path:
    """A small location_ids lookup table on a 12.5km grid sample."""
    path = FIXTURE_DIR / "sample_lookup_tables" / "location_ids.parquet"
    if not path.exists():
        from plotting_joseph.data import LookupTableCreator

        LookupTableCreator.from_grid(
            output_path=path,
            resolution_km=55.0,
            lat_min=45.0,
            lat_max=55.0,
            lon_min=10.0,
            lon_max=20.0,
        )
    return path
