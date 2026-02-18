# Description:  Preps only gauge WSE
# NOTE:  This was moved separately from prep_tidal_gauges;  this is a fucking clusterfuck.  


import glob
import os
import pandas as pd
import xarray as xr
import datetime
import pytz
est = pytz.timezone('America/New_York')


#----------------------------------------------------------------------------------
#  GET NOAA COOPS STATIONS and combine in single df

if 0:
    file_pattern = '../../data/tide_gauges/noaa_coops/swe_noaa_coops*.csv'

    # Use glob to find all matching files
    files = glob.glob(file_pattern)

    # Read and concatenate all CSV files
    combined_df = pd.concat([pd.read_csv(file) for file in files], ignore_index=True)

    # Save the concatenated DataFrame to a new CSV file
    output_path = '../../output/results/tide_gauges/noaa_coops_tide_gauges.csv'
    combined_df.to_csv(output_path, index=False)




if 0: 
    #----------------------------------------------------------------------------------
    #  GOODWIN - NOAA
    swe_GWI = combine_noaa('../../data/tide_gauges/GWI', 'GWI', 'swe_8637689_all.csv')
    # swe_GWI = '../data/tide_gauges/CRC/swe_noaa_coops_CRC_9063079.csv'

    #----------------------------------------------------------------------------------
    #  GCREW - NOAA
    swe_GCW = combine_noaa('../../data/tide_gauges/GCW', 'GCW', 'swe_8575512_all.csv')


    #----------------------------------------------------------------------------------
    #  MONEYSTUMP - NOAA
    swe_MSM = combine_noaa('../../data/tide_gauges/MSM', 'MSM', 'swe_8571892_all.csv')


    #----------------------------------------------------------------------------------
    # Combine upto date SWE
    swe_all = pd.concat([
            swe_GWI,
            swe_GCW,
            swe_MSM,],
            axis=0)
    
    # Save DataFrame to CSV
    swe_all.to_csv('../../output/results/tide_gauges/synoptic_tide_gauges.csv', index=False)






#----------------------------------------------------------------------------------
# GET NEW GCREW tidal gauge data

# Define the directory and pattern
# '../../data/tide_gauges/GCREW/CO-OPS_8575512*.csv'
dirpat = '../../data/tide_gauges/noaa/annapolis/*.csv'  


# Find all files matching the pattern
files = glob.glob(dirpat, recursive=False)

# Initialize an empty list to store DataFrames
dfs = pd.DataFrame()

# Loop through the list of CSV files and read each one into a DataFrame
for f in files:
    print(f)
    df = pd.read_csv(f)
    dfs = pd.concat([dfs, df])
