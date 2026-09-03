"""Configuration and path management for plotting_joseph."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LookupTables:
    """Paths to the lookup tables used by the plotting functions.

    Only ``location_ids`` is strictly required (for maps). The rest are
    optional and enable extra features (country names in titles, neighbor
    visualization in time series).
    """

    #: Parquet file mapping ``location_id`` -> ``lat``/``lon`` (required for maps).
    location_ids: Path | None = None
    #: Pickle mapping ``location_id`` -> country name (used for time series titles).
    countries: Path | None = None
    #: Directory of per-tile neighbor lookup parquet files (used for time series neighbors).
    neighbors_dir: Path | None = None

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> LookupTables:
        """Build a ``LookupTables`` from a dict of optionally-provided paths."""
        return cls(
            location_ids=Path(d["location_ids"]) if d.get("location_ids") else None,
            countries=Path(d["countries"]) if d.get("countries") else None,
            neighbors_dir=Path(d["neighbors_dir"]) if d.get("neighbors_dir") else None,
        )

    def resolve(self, base_dir: Path) -> LookupTables:
        """Return a copy with relative paths resolved against ``base_dir``."""
        return LookupTables(
            location_ids=self._resolve(self.location_ids, base_dir),
            countries=self._resolve(self.countries, base_dir),
            neighbors_dir=self._resolve(self.neighbors_dir, base_dir),
        )

    @staticmethod
    def _resolve(p: Path | None, base_dir: Path) -> Path | None:
        if p is None:
            return None
        return p if p.is_absolute() else (base_dir / p)


@dataclass
class LookupTableConfig:
    """High-level configuration pointing at the **master** location lookup.

    The master lookup is a single parquet file (e.g. ``location_id_to_tile_id``)
    with at least ``location_id``, ``lat`` and ``lon`` columns and (optionally)
    ``tile_id``. From this one file every other lookup the plotting functions
    need can be **generated on demand** if it is missing:

    * countries (for time-series titles) - via reverse geocoding from the web
    * a grid/map lookup (for ``plot_map``) - built from the lat/lon coordinates
    * per-tile neighbor lookups (for ``add_closest_points``)

    Generated lookups are cached in ``cache_dir`` (or a temporary directory when
    not provided).

    Parameters
    ----------
    master_lookup : Path | None
        Parquet with ``location_id``, ``lat``, ``lon`` and (optionally) ``tile_id``.
    cache_dir : Path | None
        Where generated lookups are stored for reuse. If None, a temporary
        directory is used (files are not persisted between runs).
    grid_sampling : float | None
        Grid resolution in degrees used to build the map grid lookup.
    extent : tuple
        Bounding box ``(lon_min, lon_max, lat_min, lat_max)`` for the map grid
        lookup. Defaults to a global extent.
    k_neighbors : int
        Number of neighbours used when generating the neighbor lookup.
    max_distance_km : float
        Maximum neighbour distance (km) used when generating the neighbor lookup.
    generate_countries : bool
        Automatically generate the country lookup from the web if it is missing.
    """

    master_lookup: Path | None = None
    cache_dir: Path | None = None
    grid_sampling: float | None = None
    extent: tuple[float, float, float, float] = (-180.0, 180.0, -60.0, 85.0)
    k_neighbors: int = 8
    max_distance_km: float = 300.0
    generate_countries: bool = True


@dataclass
class Config:
    """Top-level configuration container.

    Parameters
    ----------
    lookup_tables : LookupTables, optional
        Lookup table paths. Relative paths are resolved against ``base_dir``.
    base_dir : Path, optional
        Directory against which relative lookup table paths are resolved.
        Defaults to the current working directory.
    """

    lookup_tables: LookupTables = field(default_factory=LookupTables)
    base_dir: Path = field(default_factory=Path.cwd)

    def __post_init__(self) -> None:
        self.lookup_tables = self.lookup_tables.resolve(self.base_dir)


def from_config_file(path) -> Config:
    """Load a configuration from a YAML file.

    Not imported at module load time so that ``yaml`` stays an optional
    dependency. Raises an error if ``pyyaml`` is not installed.
    """
    import yaml  # type: ignore

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    return Config(
        lookup_tables=LookupTables.from_dict(raw.get("lookup_tables", {})),
        base_dir=Path(raw.get("base_dir", Path.cwd())),
    )
