# Description:  This script combines the individual gauge data files for each site into a single file per site. 
# with an outer join on the datetime index. The combined files are saved to the results directory. 


import glob
import os
import pandas as pd
from pathlib import Path
import pytz
est = pytz.timezone('America/New_York')

from scripts.config import DATA_DIR, RESULTS_DIR, SITE_CODE_LIST
from scripts.dataio import load_noaa_gage_data, load_nerrs_gage_data

# Make dir of individual data sources
NERRS_DIR = DATA_DIR/'tide_gauges/nerrs/combined/'
NOAA_DIR  = DATA_DIR/'tide_gauges/noaa/'
VECOS_DIR = DATA_DIR/'tide_gauges/vecos/combined/'
USGS_DIR  = DATA_DIR/'tide_gauges/usgs/'   
SONDE_DIR = RESULTS_DIR/'tide_gauges/sondes/'

COMBINED_GAUGE_DIR = RESULTS_DIR/'tide_gauges/combined/'


# Get all the reference and training stations together
gauge_list = pd.read_csv(DATA_DIR/'tide_gauges/all_gauges_list/synoptic_wse_train_val_stations.csv')


#%% Filter stations to dates within common period
def filter_times_all_stations_have_any_value(df,
                                             time_col="datetime_LST",
                                             id_col="station_id",
                                             value_cols=("wse_m", "depth_m"),
                                             floor=None):
    """
    Keep only times where EVERY station has at least one non-NA among value_cols.
    Works if only one (or both) of the value columns exist in df.
    Returns df in the same (long) format.
    """
    out = df.copy()

    # time handling
    out[time_col] = pd.to_datetime(out[time_col], errors="coerce")
    out = out.dropna(subset=[time_col])

    if floor is not None:
        out[time_col] = out[time_col].dt.floor(floor)

    # only use value columns that actually exist
    cols = [c for c in value_cols if c in out.columns]
    if not cols:
        raise ValueError(f"None of {value_cols} are present in df columns.")

    has_val = out[cols].notna().any(axis=1)

    # only require stations that ever have a value (otherwise condition can never be met)
    required = out.loc[has_val, id_col].dropna().unique()
    n_required = len(required)
    if n_required == 0:
        return out.iloc[0:0].copy()

    counts = (out.loc[has_val & out[id_col].isin(required)]
                .groupby(time_col)[id_col]
                .nunique())

    good_times = counts.index[counts.eq(n_required)]
    return out[out[time_col].isin(good_times)].copy()

# usage:
# df_complete = filter_times_all_stations_have_any_value(combined, floor="15min")
# (omit floor=... if timestamps already line up exactly)





#%% Outlier rejection function using rolling MAD

import numpy as np
import pandas as pd
from typing import Optional

def reject_outliers_hard_and_rolling(
    s: pd.Series,
    window: int = 49,
    abs_min: Optional[float] = None,
    abs_max: Optional[float] = None,
    max_dev_from_med: float = 10.0,
    min_periods: int = 10,
) -> pd.Series:
    s = s.astype(float)

    keep = pd.Series(True, index=s.index)

    if abs_min is not None:
        keep &= s >= abs_min
    if abs_max is not None:
        keep &= s <= abs_max

    med = s.rolling(window=window, center=True, min_periods=min_periods).median()
    keep &= (s - med).abs() <= max_dev_from_med

    return s.where(keep, np.nan)


#%% Loop through sites and combine gauge data
for site_id in SITE_CODE_LIST: # ['GCW']:

    rows = []

    print(site_id)

    site_info = (gauge_list
                 .query("site_id == @site_id")
                 .query("run == 1"))

    for _, row in site_info.iterrows():
        if pd.isna(row.station_id):
            continue

        station = str(row.station_id)

        print('  -'+station)

        if row.data_source == "NOAA":
            gauge_path = glob.glob(os.path.join(NOAA_DIR, f"swe/*{station}*.csv"))[0]
            df = load_noaa_gage_data(gauge_path)
            df["datetime_LST"] = (pd.to_datetime(df["datetime_LST"], errors="coerce", utc=True).dt.tz_convert(None))

        elif row.data_source == "VECOS":
            gauge_path = glob.glob(os.path.join(VECOS_DIR, f"*{station}*.csv"))[0]
            df = pd.read_csv(gauge_path)
            df = df.rename(columns={"DEPTH": "depth_m"})
            df["datetime_LST"] = (pd.to_datetime(df["datetime_LST"], errors="coerce", utc=True).dt.tz_convert(None))

        elif row.data_source == "NERRS":
            gauge_path = glob.glob(os.path.join(NERRS_DIR, f"*{station.lower()}*.csv"))[0]
            df = load_nerrs_gage_data(gauge_path)
            df["datetime_LST"] = (pd.to_datetime(df["datetime_LST"], errors="coerce", utc=True).dt.tz_convert(None))

        elif row.data_source == "COMPASS-FME":
            gauge_path = glob.glob(os.path.join(SONDE_DIR, f"*{station}*.csv"))[0]
            df = pd.read_csv(gauge_path)
            df["datetime_LST"] = (pd.to_datetime(df["datetime_LST"], errors="coerce", utc=True).dt.tz_convert(None))
            
        elif row.data_source == "USGS":
            gauge_path = glob.glob(os.path.join(USGS_DIR, f"*{station}*.csv"))[0]
            df = pd.read_csv(gauge_path)
            df["datetime_LST"] = (pd.to_datetime(df["datetime_LST"], errors="coerce", utc=True).dt.tz_convert(None))
            
        elif row.data_source == "NOAA-Harmonics":
            gauge_path = glob.glob(os.path.join(NOAA_DIR, f"predictions/*{station}*.csv"))[0]
            df = pd.read_csv(gauge_path)
            df["datetime_LST"] = (pd.to_datetime(df["datetime_LST"], errors="coerce", utc=True).dt.tz_convert(None))
        # else:
        #     continue
        
        # pick datetime column
        if "datetime_LST" in df.columns:
            dt_col = "datetime_LST"
        elif "datetime" in df.columns:
            dt_col = "datetime"
        else:
            raise ValueError(f"No datetime column found for station {station}")

        # standardize to long format
        df = df.copy()
        df["datetime_LST"] = pd.to_datetime(df[dt_col], errors="coerce")
        df = df.dropna(subset=["datetime_LST"]).drop_duplicates(subset=["datetime_LST"], keep="first")

        # keep only requested vars if present
        keep = ["datetime_LST"]
        for c in ["depth_m", "wse_m"]:
            if c in df.columns:
                keep.append(c)

        # For each station, filter outliers
        df["datetime_LST"] = pd.to_datetime(df["datetime_LST"])
        df = df.sort_values("datetime_LST")
        # Run filter on wse and depth
        if "depth_m" in df.columns:
            df["depth_m_clean"] = reject_outliers_hard_and_rolling(df["depth_m"], window=49,  abs_max=20, max_dev_from_med=8)
        if "wse_m" in df.columns:
            df["wse_m"] = reject_outliers_hard_and_rolling(df["wse_m"], window=49,  abs_max=None, max_dev_from_med=8)

        #%% DATA FILTER
        if "depth_m" in df.columns:
            df["depth_m"] = pd.to_numeric(df["depth_m"], errors="coerce")
            df.loc[df["depth_m"] < 0, "depth_m"] = np.nan

        # if depth exists, enforce range (special-case OWC)
        if "depth_m" in df.columns:
            df["depth_m"] = pd.to_numeric(df["depth_m"], errors="coerce")
            df.loc[df["depth_m"] < 0, "depth_m"] = np.nan
            if str(site_id) == "OWC":
                df.loc[df["depth_m"] > 2, "depth_m"] = np.nan

        out = df[keep].copy()
        out.insert(0, "station_id", station)   # add station_id column
        rows.append(out)




        # Get CORA zeta for Cheasapeake sites
        if site_id in ["GCW", "SWH", "GWI", "MSM"]:
            from pathlib import Path
            # gauge_path = "/Users/flue473/big_data/from_docs/projects/compass_fme/swot_tidal_forcing/output/results/cora/cora_zeta_PTR_2018-01-01_2025-12-31.csv"
            gauge_path = Path(RESULTS_DIR) / f"cora/cora_zeta_{site_id}_2018-01-01_2025-12-31.csv"
            df = pd.read_csv(gauge_path)[['time', 'wse_m']]
            df['station_id'] = 'NOAA CORA'
            df = df.rename(columns={'time': 'datetime_LST'})
            df["datetime_LST"] = (pd.to_datetime(df["datetime_LST"], errors="coerce", utc=True).dt.tz_convert(None))
            # Append to rows to combine
            rows.append(df)

    # append as rows
    combined = \
        pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["station_id", "datetime_LST", "depth_m", "wse_m"])

    # optional: sort
    # combined = combined.sort_values(["station_id", "datetime_LST"])

    ### NOTE: we used to filter here to keep only times where all stations have a value, but this is too strict for some sites and we can do it later as needed when comparing to SWOT. Instead, we'll just filter to the common date range of 2018-01-01 onward, which is when most stations have data and also covers the SWOT validation period.
    # cols = combined.columns.difference(["station_id", "datetime_LST"]).tolist()
    # df_complete = filter_times_all_stations_have_any_value(combined, value_cols=cols)

    combined["datetime_LST"] = pd.to_datetime(combined["datetime_LST"])
    combined = combined[combined["datetime_LST"] >= "2018-01-01"]



    out_path = COMBINED_GAUGE_DIR / f"{site_id}_combined_gauge_swe_v04_outlierrej.csv"
    combined.to_csv(out_path, index=False)
