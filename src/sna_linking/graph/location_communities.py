from __future__ import annotations

import numpy as np
import pandas as pd


def assign_communities(df: pd.DataFrame, radius_meters: float = 50.0) -> pd.DataFrame:
    # Approximate 1 degree latitude ~= 111,320 meters.
    lat_step = max(radius_meters / 111_320.0, 1e-6)
    lat = df["PROJECT_LATITUDE"].to_numpy(dtype=float)
    lon = df["PROJECT_LONGITUDE"].to_numpy(dtype=float)

    # Longitude degree size shrinks with latitude; use per-row scaling.
    lon_meters_per_degree = np.maximum(111_320.0 * np.cos(np.deg2rad(lat)), 1.0)
    lon_step = radius_meters / lon_meters_per_degree

    lat_bin = np.floor(lat / lat_step).astype(np.int64)
    lon_bin = np.floor(lon / lon_step).astype(np.int64)
    cell_key = pd.Series(lat_bin.astype(str) + ":" + lon_bin.astype(str), index=df.index)

    cell_codes, _ = pd.factorize(cell_key, sort=False)
    community_ids = pd.Series(cell_codes + 1, index=df.index).map(lambda x: f"C{x:06d}")
    return df.assign(Community_ID=community_ids)
