# Data Formats

`plotting_joseph` is designed to be **data-format agnostic**. All plotting
functions accept a normalised `pandas.DataFrame`, and `DataLoader` helps you
normalise it from common storage formats.

## Canonical schema

The plotting functions expect (at minimum):

| Column        | Type     | Required for                 |
|---------------|----------|------------------------------|
| `time`        | datetime | time series                  |
| `location_id` | int      | time series & maps           |
| any variable  | float    | time series panels / map value |

`DataLoader` will rename your columns to these canonical names and validate
that `time` and `location_id` are present.

## Loading

### Parquet (recommended)

```python
from plotting_joseph import DataLoader

df = DataLoader().load("data/combined_all/0009.parquet")
```

### CSV

```python
df = DataLoader().load("data/my_locations.csv")
```

CSV `time` columns are parsed to datetime automatically.

### Other formats (netCDF, zarr, ...)

Load with `xarray` (or any tool) yourself, convert to a DataFrame, then pass
it to `DataLoader`:

```python
import xarray as xr
from plotting_joseph import DataLoader

ds = xr.open_dataset("era5.nc")
df = ds.to_dataframe().reset_index()

df = DataLoader().load(df)
```

## Custom column names

If your columns are named differently, provide a `column_map` that renames
**canonical** names to **your** names:

```python
from plotting_joseph import DataLoader

loader = DataLoader(
    column_map={
        "time": "date",            # your "date" column -> canonical "time"
        "location_id": "loc_id",   # your "loc_id" column -> canonical "location_id"
        "backscatter40": "bs40",   # your "bs40" -> canonical "backscatter40"
    }
)

df = loader.load("my_data.csv")
```

After loading, the DataFrame uses canonical names and can be passed directly
to the plotting functions.

## Column mapping quick reference

| Canonical      | Typical source names          |
|----------------|-------------------------------|
| `time`         | `time`, `date`, `datetime`    |
| `location_id`  | `location_id`, `loc`, `loc_id`, `gpi` |
| `backscatter40`| `backscatter40`, `bs40`, `sig0` |
| `lai`          | `lai`                         |
| `swvl1`        | `swvl1`, `swvl`, `swvl1_normalized` |

## Validation errors

If a required column is missing after mapping, `DataLoader` raises a
`ValueError` listing the missing columns and the available columns — add the
correct entry to `column_map` to fix it.
