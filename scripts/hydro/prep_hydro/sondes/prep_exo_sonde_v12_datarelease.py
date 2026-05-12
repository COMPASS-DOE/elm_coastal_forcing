
import os
import glob
import pandas as pd
from scripts.config import RESULTS_DIR

BASE_DIR = "/Users/flue473/big_data/synoptic_data_release/v1-2"

pattern = os.path.join(BASE_DIR, "**", "*CRC_OW*.csv")
files = sorted(glob.glob(pattern, recursive=True))


dfs = []

for f in files:
    try:
        df = pd.read_csv(f)
    except Exception as e:
        print(f"Skipping unreadable file: {f} ({e})")
        continue

    required = {"research_name", "F_OOS", "F_OOB", "Site", "TIMESTAMP", "Value"}
    missing = required - set(df.columns)
    if missing:
        print(f"Skipping (missing columns {sorted(missing)}): {f}")
        continue

    df = df.loc[
        (df["research_name"] == "sonde_depth"),
        # & (df["F_OOS"] != 1)
        # & (df["F_OOB"] != 1),
        ["Site", "TIMESTAMP", "Value"],
    ].copy()

    dfs.append(df)

raw = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(columns=["Site", "TIMESTAMP", "Value"])

raw = raw.rename(columns={
    "Site": "site_id",
    "TIMESTAMP": "datetime_LST",
    "Value": "depth_m",
    })


raw["datetime_LST"] = pd.to_datetime(raw["datetime_LST"], errors="coerce")
raw["depth_m"] = pd.to_numeric(raw["depth_m"], errors="coerce")

# Drop rows where datetime failed to parse
raw = raw.dropna(subset=["datetime_LST"])

# Hourly mean per site
hourly = (
    raw.set_index("datetime_LST")
        .groupby("site_id")["depth_m"]
        .resample("1H")
        .mean()
        .reset_index()
    )

hourly = hourly.assign(station_id='CRC_OW_sonde')

# Save to file
out_path = os.path.join(RESULTS_DIR, "tide_gauges/sondes/CRC_sonde_allflags.csv")
hourly.to_csv(out_path, index=False)
