"""Tests for LookupTableCreator and validation."""


import numpy as np
import pandas as pd

from plotting_joseph import LookupTableCreator, LookupTables, validate_lookup_tables


def test_create_location_ids_from_dataframe(tmp_path):
    raw = pd.DataFrame(
        {
            "location_id": [1, 2, 3],
            "lat": [10.0, 20.0, 30.0],
            "lon": [-10.0, 0.0, 10.0],
            "tile_id": ["a", "a", "b"],
        }
    )
    out = tmp_path / "locs.parquet"
    LookupTableCreator.from_dataframe(
        raw, "location_id", "lat", "lon", out, tile_id_column="tile_id"
    )
    df = pd.read_parquet(out)
    assert list(df.columns) == ["location_id", "lat", "lon", "tile_id"]
    assert len(df) == 3
    assert df["location_id"].dtype == np.int64


def test_create_location_ids_from_csv(tmp_path):
    csv = tmp_path / "locs.csv"
    csv.write_text("location_id,latitude,longitude\n1,10,-10\n2,20,0\n")
    out = tmp_path / "locs.parquet"
    LookupTableCreator.from_csv(csv, "location_id", "latitude", "longitude", out)
    df = pd.read_parquet(out)
    assert len(df) == 2
    assert "lat" in df.columns and "lon" in df.columns


def test_create_location_ids_from_grid(tmp_path):
    out = tmp_path / "grid.parquet"
    LookupTableCreator.from_grid(output_path=out, resolution_km=111.0)
    df = pd.read_parquet(out)
    assert len(df) > 0
    assert set(df.columns) == {"location_id", "lat", "lon", "tile_id"}


def test_generate_neighbor_lookup(tmp_path, sample_lookup_location_ids):
    out_dir = tmp_path / "neighbors"
    LookupTableCreator.generate_neighbor_lookup(
        sample_lookup_location_ids,
        out_dir,
        k_neighbors=3,
        max_distance_km=500.0,
    )
    files = list(out_dir.glob("*.parquet"))
    assert len(files) > 0
    df = pd.read_parquet(files[0])
    assert {"location_id", "neighbor_location_id", "distance_km", "rank"} <= set(
        df.columns
    )
    assert df["rank"].max() <= 3


def test_validate_lookup_tables(tmp_path, sample_lookup_location_ids):
    tables = LookupTables(location_ids=sample_lookup_location_ids)
    errors = validate_lookup_tables(tables)
    assert errors == [] or all(
        "location_ids" not in e for e in errors
    ), errors
