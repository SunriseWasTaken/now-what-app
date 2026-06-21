"""Newham air quality (PM2.5/NO2) cleaning and ward-level join."""

import pandas as pd
import numpy as np


def load_pm25_grid():
    df = pd.read_csv("E09000025-pm25-2021.csv", skiprows=5)
    return df[["Local_Auth_Code", "x", "y", "Total_PM2.5_21"]].rename(
        columns={"Total_PM2.5_21": "pm25_ugm3"}
    )


def load_no2_grid():
    df = pd.read_csv("E09000025-no2-2021.csv", skiprows=5)
    df["Total_NO2_21"] = pd.to_numeric(df["Total_NO2_21"], errors="coerce")
    df = df.dropna(subset=["Total_NO2_21"])
    return df[["Local_Auth_Code", "x", "y", "Total_NO2_21"]].rename(
        columns={"Total_NO2_21": "no2_ugm3"}
    )


def grid_summary():
    pm25 = load_pm25_grid()
    no2 = load_no2_grid()
    merged = pm25.merge(no2, on=["Local_Auth_Code", "x", "y"])
    print(f"Grid cells covering Newham: {len(merged)}")
    return merged


def join_to_ward(centroids_csv_path, lookup_csv_path, output_path):
    centroids = pd.read_csv(centroids_csv_path)
    lookup = pd.read_csv(lookup_csv_path, encoding="utf-8-sig")
    lookup.columns = [c.strip() for c in lookup.columns]

    newham_lookup = lookup[lookup["LAD24NM"].str.contains("Newham", case=False, na=False)][
        ["LSOA21CD", "WD24CD", "WD24NM"]
    ].rename(columns={"LSOA21CD": "lsoa_code", "WD24CD": "ward_code", "WD24NM": "ward_name"})

    newham_centroids = centroids.merge(newham_lookup, left_on="LSOA21CD", right_on="lsoa_code")

    grid = grid_summary()
    grid_xy = grid[["x", "y"]].to_numpy()

    def nearest_grid_value(row, col):
        dists = np.sqrt((grid_xy[:, 0] - row["x"]) ** 2 + (grid_xy[:, 1] - row["y"]) ** 2)
        return grid.iloc[dists.argmin()][col]

    newham_centroids["pm25_ugm3"] = newham_centroids.apply(lambda r: nearest_grid_value(r, "pm25_ugm3"), axis=1)
    newham_centroids["no2_ugm3"] = newham_centroids.apply(lambda r: nearest_grid_value(r, "no2_ugm3"), axis=1)

    ward_air = (
        newham_centroids.groupby(["ward_code", "ward_name"])
        .agg(n_lsoas=("lsoa_code", "count"), pm25_ugm3=("pm25_ugm3", "mean"), no2_ugm3=("no2_ugm3", "mean"))
        .reset_index()
        .round(2)
    )
    ward_air.to_csv(output_path, index=False)
    print(f"Saved ward-level air quality for {len(ward_air)} wards.")
    return ward_air


if __name__ == "__main__":
    grid_summary()
