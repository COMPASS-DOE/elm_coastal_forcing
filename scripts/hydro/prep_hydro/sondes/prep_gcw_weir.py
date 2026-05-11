import pandas as pd
import glob
import os
from datetime import datetime

from scripts.config import DATA_DIR, RESULTS_DIR


# Define the directory path
indir = os.path.join(DATA_DIR, "tide_gauges/sondes/GCW/weir_exotable/monthly")
outdir = os.path.join(RESULTS_DIR, "tide_gauges/sondes")

# Use glob to retrieve all file paths in the directory
file_paths = glob.glob(os.path.join(indir, "*.csv"))

# List to store individual DataFrames
dfs = []

# Iterate over each file to read and append to the DataFrame list
for file in file_paths:
    try:
    
        df = (
            pd.read_csv(file, parse_dates=["timestamp_local"])  # Assumes files are CSVs
            .assign(timestamp_local = lambda x: pd.to_datetime(x['timestamp_local'], errors='coerce'))
            .loc[:,['timestamp_local', 'depth_m', 'salinity_ppt']] 
            .assign(timestamp_local_hr = lambda x: pd.to_datetime(x.timestamp_local).dt.floor('h'))
            .set_index("timestamp_local_hr")
            .resample("h").mean()
            .reset_index()
            .loc[:,['timestamp_local_hr', 'depth_m']] # , 'salinity_ppt']]
            .rename(columns={"timestamp_local_hr": "datetime_LST"})
            # .assign(depth_m_anomaly=lambda x: x["depth_m"] - x["depth_m"].mean())
            .assign(station_id="GCW")
        )

        # combined["datetime_LST"] = pd.to_datetime(combined["datetime_LST"], errors="coerce", utc=True)

        dfs.append(df)  # Append the DataFrame to the list
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Concatenate all DataFrames into a single DataFrame
combined_df = (
    pd.concat(dfs, ignore_index=True)
    .sort_values(by='datetime_LST')
    )


# Display or save the result
combined_df.to_csv(f"{outdir}/GCW_weir_exo.csv", index=False)
