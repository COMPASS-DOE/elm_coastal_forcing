#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd
from dataretrieval import nwis

from scripts.config import DATA_DIR


FT_TO_M = 0.3048

def download_hourly_stage_height(
    station_number: str,
    start_date: str,
    end_date: str,
    out_csv: str,
    agency: str = "USGS",
    aggregation: str = "mean",
) -> pd.DataFrame:
    df = nwis.get_record(
        sites=str(station_number),
        service="iv",
        start=start_date,
        end=end_date,
        parameterCd="00065",
    )

    if df is None or df.empty:
        raise RuntimeError(f"No data returned for USGS site {station_number} in {start_date}/{end_date}")

    if not isinstance(df.index, pd.DatetimeIndex):
        for c in ("datetime", "time", "dateTime", "date_time"):
            if c in df.columns:
                df = df.copy()
                df[c] = pd.to_datetime(df[c])
                df = df.set_index(c)
                break
        if not isinstance(df.index, pd.DatetimeIndex):
            raise RuntimeError(f"Could not determine datetime index. Columns: {list(df.columns)}")

    df = df.sort_index()

    # Find the gage-height value column
    value_col = None
    for cand in ("00065", "00065_Value", "00065_value"):
        if cand in df.columns:
            value_col = cand
            break
    if value_col is None:
        matches = [c for c in df.columns if str(c).startswith("00065") and "value" in str(c).lower()]
        if matches:
            value_col = matches[0]
    if value_col is None:
        raise RuntimeError(f"Expected a gage-height value column for 00065. Columns: {list(df.columns)}")

    # Hourly aggregation (still in feet)
    hourly_ft = df[[value_col]].resample("1H").agg(aggregation)

    # Convert to meters, name as requested
    out = pd.DataFrame(index=hourly_ft.index)
    out["depth_m"] = hourly_ft[value_col] * FT_TO_M
    out["station_id"] = f"{agency}-{station_number}"

    # out.index = out.index.rename("datetime")
    out = out.reset_index()
    out = out.rename(columns={"datetime": "datetime_LST"})


    out_csv=DATA_DIR/f"tide_gauges/usgs/USGS_{station_number}.csv"
    # Write CSV (keep time as index)
    out.to_csv(out_csv, index=True)
    return out




#%%  Example usage ----------------------------------------------------
if __name__ == "__main__":


    start_date="2018-01-01"
    end_date="2025-12-31"

    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year


    station_id="04195820"
    hourly_df = download_hourly_stage_height(
        station_number=station_id,
        start_date=start_date,
        end_date=end_date,
        out_csv=DATA_DIR/f"tide_gauges/usgs/USGS_{station_id}.csv")

    station_id="04193500"
    hourly_df = download_hourly_stage_height(
        station_number=station_id,
        start_date=start_date,
        end_date=end_date,
        out_csv=DATA_DIR/f"tide_gauges/usgs/USGS_{station_id}.csv")

    station_id="01490000"
    hourly_df = download_hourly_stage_height(
        station_number=station_id,
        start_date=start_date,
        end_date=end_date,
        out_csv=DATA_DIR/f"tide_gauges/usgs/USGS_{station_id}.csv")

    

        # out_csv=DATA_DIR/f"tide_gauges/usgs/USGS_{station_number}_{start_year}_{end_year}.csv")