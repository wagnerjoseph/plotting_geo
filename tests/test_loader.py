"""Tests for DataLoader."""

import pandas as pd
import pytest

from plotting_joseph import DataLoader


def test_load_dataframe_roundtrip(sample_timeseries_data):
    df = DataLoader().load(sample_timeseries_data)
    assert "time" in df.columns
    assert "location_id" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["time"])
    assert len(df) == len(sample_timeseries_data)


def test_column_mapping(tmp_path):
    raw = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=5, freq="MS"),
            "loc": [1, 1, 1, 1, 1],
            "bs": [0.5, 0.6, 0.7, 0.8, 0.9],
        }
    )
    path = tmp_path / "raw.csv"
    raw.to_csv(path, index=False)

    df = DataLoader(
        column_map={"time": "date", "location_id": "loc", "backscatter40": "bs"}
    ).load(path)

    assert "time" in df.columns
    assert "location_id" in df.columns
    assert "backscatter40" in df.columns
    assert "loc" not in df.columns
    assert df["backscatter40"].tolist() == [0.5, 0.6, 0.7, 0.8, 0.9]


def test_missing_required_column_raises():
    raw = pd.DataFrame({"foo": [1, 2, 3]})
    with pytest.raises(ValueError, match="location_id"):
        DataLoader().load(raw)
