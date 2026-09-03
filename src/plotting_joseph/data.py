"""Data loading and lookup-table creation.

This module implements the ``DataLoader`` and ``LookupTableCreator`` helpers
referenced by the package ``__init__`` and documented in ``docs/``. It
normalises user data (parquet / CSV / in-memory DataFrame) into the canonical
schema expected by the plotting functions and generates the geographic lookup
tables they rely on.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Canonical name -> list of acceptable source column names (auto-detected).
DEFAULT_ALIASES: dict[str, list[str]] = {
    "time": ["time", "date", "datetime", "timestamp"],
    "location_id": ["location_id", "loc_id", "loc", "gpi"],
    "backscatter40": ["backscatter40", "bs40", "sig0"],
    "lai": ["lai"],
    "swvl1": ["swvl1", "swvl", "swvl1_normalized"],
}

# Canonical columns that are mandatory regardless of use-case.
_REQUIRED = ["time", "location_id"]


class DataLoader:
    """Load and normalise data from common storage formats.

    Parameters
    ----------
    column_map : dict, optional
        Mapping of ``canonical name -> your column name``, e.g.
        ``{"time": "date", "location_id": "loc_id"}``. Can also remap
        arbitrary variable columns (e.g. ``{"backscatter40": "bs40"}``).
    """

    def __init__(self, column_map: dict[str, str] | None = None) -> None:
        self.column_map = column_map or {}

    # -- loading ------------------------------------------------------------
    def load(self, source) -> pd.DataFrame:
        """Load and normalise ``source`` into a canonical DataFrame.

        ``source`` may be a path to a parquet / CSV file, or an in-memory
        pandas.DataFrame.
        """
        if isinstance(source, (str, Path)):
            df = self._load_path(Path(source))
        elif isinstance(source, pd.DataFrame):
            df = source.copy()
        else:
            raise TypeError(
                f"source must be a path (str/Path) or pandas.DataFrame, got {type(source)!r}"
            )

        df = self._rename_known(df)
        df = self._coerce_dtypes(df)
        df = self._validate(df)
        return df

    def _load_path(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(path)
        suffix = path.suffix.lower()
        if suffix == ".parquet":
            return pd.read_parquet(path)
        if suffix in {".csv", ".txt"}:
            # time columns are parsed lazily on a best-effort basis below
            df = pd.read_csv(path)
            if "time" in df.columns or "date" in df.columns:
                df = self._coerce_dtypes(df)
            return df
        raise ValueError(f"Unsupported file format: {suffix}")

    # -- normalisation ------------------------------------------------------
    def _rename_known(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping: dict[str, str] = {}
        for canonical, source in self.column_map.items():
            if source in df.columns:
                mapping[source] = canonical

        used_names = set(df.columns)
        for canonical, aliases in DEFAULT_ALIASES.items():
            if canonical in mapping.values():
                continue
            for alias in aliases:
                if alias in used_names:
                    mapping[alias] = canonical
                    break
        return df.rename(columns=mapping)

    def _coerce_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        if "time" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["time"]):
            df["time"] = pd.to_datetime(df["time"])
        if "location_id" in df.columns:
            df["location_id"] = pd.to_numeric(df["location_id"], errors="coerce").astype(
                "Int64"
            )
        return df

    def _validate(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in _REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(
                "Missing required column(s) after mapping: "
                f"{missing}. Available columns: {list(df.columns)}. "
                "Add the correct entry to `column_map` to fix it."
            )
        if not pd.api.types.is_datetime64_any_dtype(df["time"]):
            raise ValueError("'time' column must be datetime-like.")
        return df


def _latlon_to_flat(lat: np.ndarray, lon: np.ndarray, grid_sampling: float) -> np.ndarray:
    """Compute flat ``pixel_id = row * n_lon + col`` for the default grid."""
    lat_min, lat_max = -60.0, 85.0
    lon_min, lon_max = -180.0, 180.0
    n_lon = int(np.round((lon_max - lon_min) / grid_sampling))
    col = np.floor((lon - lon_min) / grid_sampling).astype(int)
    row = np.floor((lat_max - lat) / grid_sampling).astype(int)
    n_lat = int(np.round((lat_max - lat_min) / grid_sampling))
    flat = row * n_lon + col
    flat[(row < 0) | (row >= n_lat) | (col < 0) | (col >= n_lon)] = -1
    return flat


class LookupTableCreator:
    """Create geographic lookup tables from user data or a regular grid."""

    # -- location_ids -------------------------------------------------------
    @staticmethod
    def _write_location_ids(
        df: pd.DataFrame,
        location_id_column: str,
        lat_column: str,
        lon_column: str,
        output_path,
        tile_id_column: str | None,
    ) -> Path:
        if {location_id_column, lat_column, lon_column} - set(df.columns):
            raise ValueError(
                f"Input must have columns {location_id_column!r}, {lat_column!r}, "
                f"{lon_column!r}. Got: {list(df.columns)}"
            )
        out = df[[location_id_column, lat_column, lon_column]].copy()
        out = out.rename(
            columns={
                location_id_column: "location_id",
                lat_column: "lat",
                lon_column: "lon",
            }
        )
        if tile_id_column is not None:
            if tile_id_column not in df.columns:
                raise ValueError(f"tile_id_column {tile_id_column!r} not found.")
            out["tile_id"] = df[tile_id_column].astype(str)
        out["location_id"] = out["location_id"].astype(np.int64)
        out = out.drop_duplicates("location_id").reset_index(drop=True)
        out.to_parquet(output_path, index=False)
        return Path(output_path)

    @classmethod
    def from_dataframe(
        cls,
        df,
        location_id_column: str,
        lat_column: str,
        lon_column: str,
        output_path,
        tile_id_column: str | None = None,
    ) -> Path:
        """Create ``location_ids.parquet`` from an in-memory DataFrame."""
        return cls._write_location_ids(
            df, location_id_column, lat_column, lon_column, output_path, tile_id_column
        )

    @classmethod
    def from_parquet(
        cls,
        input_path,
        location_id_column: str,
        lat_column: str,
        lon_column: str,
        output_path,
        tile_id_column: str | None = None,
    ) -> Path:
        """Create ``location_ids.parquet`` from a parquet file."""
        df = pd.read_parquet(input_path)
        return cls._write_location_ids(
            df, location_id_column, lat_column, lon_column, output_path, tile_id_column
        )

    @classmethod
    def from_csv(
        cls,
        csv_path,
        location_id_column: str,
        lat_column: str,
        lon_column: str,
        output_path,
        tile_id_column: str | None = None,
    ) -> Path:
        """Create ``location_ids.parquet`` from a CSV file."""
        df = pd.read_csv(csv_path)
        return cls._write_location_ids(
            df, location_id_column, lat_column, lon_column, output_path, tile_id_column
        )

    @classmethod
    def from_grid(
        cls,
        output_path,
        resolution_km: float,
        lat_min: float = -60.0,
        lat_max: float = 85.0,
        lon_min: float = -180.0,
        lon_max: float = 180.0,
    ) -> Path:
        """Create ``location_ids.parquet`` on a regular lat/lon grid.

        Longitude sampling is adjusted by ``cos(lat)`` so cells stay roughly
        square on the ground.
        """
        km_per_deg = 111.0
        res_deg_lat = resolution_km / km_per_deg
        lat = np.arange(lat_min, lat_max, res_deg_lat)

        # location_id must be unique; assign a running counter.
        frames = []
        counter = 0
        for la in lat:
            coslat = max(np.cos(np.radians(float(la))), 0.01)
            res_deg_lon = resolution_km / km_per_deg / coslat
            lon = np.arange(lon_min, lon_max, res_deg_lon)
            n = len(lon)
            ids = np.arange(counter, counter + n, dtype=np.int64)
            counter += n
            frames.append(
                pd.DataFrame(
                    {
                        "location_id": ids,
                        "lat": np.full(n, float(la)),
                        "lon": lon,
                        "tile_id": np.full(n, "tile0", dtype=object),
                    }
                )
            )
        df = pd.concat(frames, ignore_index=True)
        df["location_id"] = df["location_id"].astype(np.int64)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        return Path(output_path)

    # -- countries ----------------------------------------------------------
    @classmethod
    def generate_country_lookup(cls, location_ids_path, output_path) -> Path:
        """Build a ``{location_id: country_name}`` pickle.

        Requires the ``geocoding`` extra (``reverse_geocoder``) and internet
        access on first use.
        """
        try:
            import reverse_geocoder as rg
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "generate_country_lookup requires the 'geocoding' extra: "
                "pip install 'plotting_joseph[geocoding]'"
            ) from e

        loc = pd.read_parquet(location_ids_path)
        coords = list(zip(loc["lat"].to_numpy(), loc["lon"].to_numpy()))
        results = rg.search(coords)
        records = {}
        for loc_id, res in zip(loc["location_id"], results):
            records[int(loc_id)] = res.get("cc") if isinstance(res, dict) else str(res)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import pickle

        with open(output_path, "wb") as f:
            pickle.dump(records, f)
        return output_path

    # -- neighbors ----------------------------------------------------------
    @classmethod
    def generate_neighbor_lookup(
        cls,
        location_ids_path,
        output_dir,
        k_neighbors: int = 10,
        max_distance_km: float = 100.0,
        workers: int = 1,
    ) -> Path:
        """Create per-tile nearest-neighbor lookup parquet files.

        One file per tile in ``output_dir`` (named ``{tile_id}.parquet``),
        with columns ``location_id``, ``neighbor_location_id``, ``distance_km``
        and ``rank``.
        """
        import itertools

        try:
            from scipy.spatial import cKDTree
        except ImportError as e:  # pragma: no cover
            raise ImportError("generate_neighbor_lookup requires scipy") from e

        loc = pd.read_parquet(location_ids_path)
        if "tile_id" not in loc.columns:
            loc["tile_id"] = "tile0"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        km_per_deg = 111.0

        for tile_id, tile in loc.groupby("tile_id"):
            coords_rad = np.radians(tile[["lat", "lon"]].to_numpy(dtype=float))
            tree = cKDTree(coords_rad)

            rows = []
            for i, (loc_id, lat, lon) in enumerate(
                zip(tile["location_id"], tile["lat"], tile["lon"])
            ):
                point_rad = np.radians([[float(lat), float(lon)]])
                dists, idxs = tree.query(point_rad, k=min(k_neighbors + 1, len(tile)))
                dists = np.ravel(dists)
                idxs = np.ravel(idxs).astype(int)
                for d, j in zip(dists[1:], idxs[1:]):
                    dist_km = d * 6371.0
                    if max_distance_km > 0 and dist_km > max_distance_km:
                        continue
                    rows.append(
                        {
                            "location_id": int(loc_id),
                            "neighbor_location_id": int(tile["location_id"].iloc[int(j)]),
                            "distance_km": float(dist_km),
                        }
                    )
            # assign ranks per location after collecting candidates
            df_rows = pd.DataFrame(rows)
            if not df_rows.empty:
                df_rows["rank"] = (
                    df_rows.groupby("location_id")["distance_km"]
                    .rank(ascending=True)
                    .astype(int)
                )
                df_rows.to_parquet(output_dir / f"{tile_id}.parquet", index=False)
        return output_dir


def validate_lookup_tables(lookup_tables) -> list[str]:
    """Validate the lookup tables referenced by a ``LookupTables`` config.

    Returns a list of human-readable error strings (empty when valid).
    """
    from .config import LookupTables

    if not isinstance(lookup_tables, LookupTables):
        lookup_tables = LookupTables(
            location_ids=lookup_tables.get("location_ids"),
            countries=lookup_tables.get("countries"),
            neighbors_dir=lookup_tables.get("neighbors_dir"),
        )

    errors: list[str] = []

    if lookup_tables.location_ids is not None:
        p = Path(lookup_tables.location_ids)
        if not p.exists():
            errors.append(f"location_ids table not found: {p}")
        else:
            df = pd.read_parquet(p)
            if "location_id" not in df.columns:
                errors.append(f"location_ids table missing 'location_id': {p}")
            for c in ("lat", "lon"):
                if c not in df.columns:
                    errors.append(f"location_ids table missing '{c}': {p}")

    if lookup_tables.countries is not None:
        p = Path(lookup_tables.countries)
        if not p.exists():
            errors.append(f"countries table not found: {p}")

    if lookup_tables.neighbors_dir is not None:
        d = Path(lookup_tables.neighbors_dir)
        if not d.exists():
            errors.append(f"neighbors_dir not found: {d}")
        elif not any(d.glob("*.parquet")):
            errors.append(f"neighbors_dir contains no parquet files: {d}")

    return errors
