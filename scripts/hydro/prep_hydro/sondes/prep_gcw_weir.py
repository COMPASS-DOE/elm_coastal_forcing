import pandas as pd
import glob
import os
from datetime import datetime

# Define the directory path
indir = "../../data/tide_gauges/sondes/GCW_sondes/weir_exotable/monthly"
outdir = "../../data/tide_gauges/sondes/GCW_sondes/weir_exotable"

# Use glob to retrieve all file paths in the directory
# Adjust extension based on your files (e.g., .csv, .txt, .xlsx)
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
            .loc[:,['timestamp_local_hr', 'depth_m', 'salinity_ppt']]
            .assign(depth_m_anomaly=lambda x: x["depth_m"] - x["depth_m"].mean())
        )

        dfs.append(df)  # Append the DataFrame to the list
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Concatenate all DataFrames into a single DataFrame
combined_df = (
    pd.concat(dfs, ignore_index=True)
    .sort_values(by='timestamp_local_hr')
)


# Display or save the result
combined_df.to_csv(f"{outdir}/GCReW_weir_exo.csv", index=False)  # Save to a CSV file
