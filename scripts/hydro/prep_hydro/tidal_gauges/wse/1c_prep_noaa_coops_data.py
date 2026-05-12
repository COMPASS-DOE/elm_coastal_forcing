# Description:  Preps only gauge WSE
# NOTE:  This was moved separately from prep_tidal_gauges.


import glob
import os
import pandas as pd
import xarray as xr
import datetime
import pytz
est = pytz.timezone('America/New_York')

from scripts.config import DATA_DIR



#%%  Download NOAA COOPS water levels -------------------------------------------------------
from src.elm_coastal_forcing.prep_hydro.noaa_coops_request_tide import save_noaa_coops_wse

# Get list of stations
noaa_gauges = (
    pd.read_csv(DATA_DIR/'tide_gauges/all_gauges_list/synoptic_wse_train_val_stations.csv')
    .query("run == 1")
    .query("type == 'ref'")
    .query("data_source == 'NOAA'")
    .loc[:, ['site_id', 'station_id', 'station_name', 'datum']]
    .drop_duplicates()
    )

# Define date for annual data pull
years = ["20180101","20190101", "20200101","20210101","20220101","20230101", "20240101", "20250101"]

# Run function
save_noaa_coops_wse(noaa_gauges, 
                    years,
                    outdir = str(DATA_DIR/'tide_gauges/noaa/swe'))





#%% Check for duplicates and overwrite files without duplicates

from pathlib import Path
import pandas as pd

data_dir = Path(DATA_DIR) / "tide_gauges" / "noaa" / "swe"

for f in data_dir.glob("*.csv"):
    print(f"Processing {f.name}")
    df = pd.read_csv(f)

    # Drop exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    print(f"  Dropped {before - after} duplicate rows")

    # Overwrite the file
    df.to_csv(f, index=False)






# #----------------------------------------------------------------------------------
# #  GET NOAA COOPS STATIONS and combine in single df
# if 0:
#     file_pattern = '../../data/tide_gauges/noaa_coops/swe_noaa_coops*.csv'
#     # Use glob to find all matching files
#     files = glob.glob(file_pattern)

#     # Read and concatenate all CSV files
#     combined_df = pd.concat([pd.read_csv(file) for file in files], ignore_index=True)

#     # Save the concatenated DataFrame to a new CSV file
#     output_path = '../../output/results/tide_gauges/noaa_coops_tide_gauges.csv'
#     combined_df.to_csv(output_path, index=False)

# if 0: 
#     #----------------------------------------------------------------------------------
#     #  GOODWIN - NOAA
#     swe_GWI = combine_noaa('../../data/tide_gauges/GWI', 'GWI', 'swe_8637689_all.csv')
#     # swe_GWI = '../data/tide_gauges/CRC/swe_noaa_coops_CRC_9063079.csv'

#     #----------------------------------------------------------------------------------
#     #  GCREW - NOAA
#     swe_GCW = combine_noaa('../../data/tide_gauges/GCW', 'GCW', 'swe_8575512_all.csv')


#     #----------------------------------------------------------------------------------
#     #  MONEYSTUMP - NOAA
#     swe_MSM = combine_noaa('../../data/tide_gauges/MSM', 'MSM', 'swe_8571892_all.csv')


#     #----------------------------------------------------------------------------------
#     # Combine upto date SWE
#     swe_all = pd.concat([
#             swe_GWI,
#             swe_GCW,
#             swe_MSM,],
#             axis=0)
    
#     # Save DataFrame to CSV
#     swe_all.to_csv('../../output/results/tide_gauges/synoptic_tide_gauges.csv', index=False)


# #----------------------------------------------------------------------------------
# # GET NEW GCREW tidal gauge data

# # Define the directory and pattern
# # '../../data/tide_gauges/GCREW/CO-OPS_8575512*.csv'
# dirpat = '../../data/tide_gauges/noaa/annapolis/*.csv'  


# # Find all files matching the pattern
# files = glob.glob(dirpat, recursive=False)

# # Initialize an empty list to store DataFrames
# dfs = pd.DataFrame()

# # Loop through the list of CSV files and read each one into a DataFrame
# for f in files:
#     print(f)
#     df = pd.read_csv(f)
#     dfs = pd.concat([dfs, df])
