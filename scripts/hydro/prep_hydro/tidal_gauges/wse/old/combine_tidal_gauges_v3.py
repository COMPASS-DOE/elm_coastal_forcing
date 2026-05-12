

# ONLY WSE
import glob
import os
import pandas as pd
import xarray as xr
import datetime
import pytz
est = pytz.timezone('America/New_York')




#----------------------------------------------------------------------------------
#  SWEETHALL - VECOS water levels
sweethall_wse = (
    pd.read_csv('../../data/tide_gauges/vecos/from_steph/sweethall_vecos.csv') 
    .rename(columns={'datetimestamp': 'datetime_est', 
                     'NAVD88_elev': 'wse_m_navd88',})
    .assign(datetime_est=lambda x: pd.to_datetime(x['datetime_est'], format='%m/%d/%y %H:%M', errors='coerce'))
    .set_index('datetime_est') #, inplace=True))
    .drop(columns=['id']))

sweethall_wse = sweethall_wse.wse_m_navd88.resample('h').mean().reset_index()


# /----------------------------------------------------------------------------------
#/   GOODWIN
goodwin_df = (
    pd.merge(goodwin_wse, goodwin_sal, on='datetime_est', how='outer')
    .assign(site_name='Goodwin Islands',
            station='GoodwinIsland_CH019.38',
            site_id='GWN',
            source='VECOS'))

sweethall_df = (
    pd.merge(sweethall_wse, sweethall_sal, on='datetime_est', how='outer')
    .assign(site_name='Sweet Hall Marsh',
            station = 'SweetHallMarsh_PMK012',
            site_id='SWH',
            source='VECOS'))



gcrew_water_elev_df = ( \
    dfs
    # (pd.concat(dfs, ignore_index=True)
    #  .rename(columns={'Verified (m)': 'wse_m_navd88'}) # verified the datum is NAVD88
     .assign(swe_navd88_m=lambda x: pd.to_numeric(x.swe_navd88_m, errors='coerce'))
     .assign(datetime_LST=lambda x: pd.to_datetime(x['datetime_LST']))
    #  .assign(datetime_est=lambda x: pd.to_datetime(x['Date'] + ' ' + x['Time (GMT)']) -pd.Timedelta(hours=5))
     .assign(source='NOAA',
             station='Annapolis-8575512',
             site_name = 'GCReW',
             site_id = 'GCW')
    )




#----------------------------------------------------------------------------------
# Prep Moneystump water level.
# NOTE: There is a real data gap in 2013

# Define the directory and pattern
dirpat = '../../data/tide_gauges/Moneystump/depth/*.csv'

files = glob.glob(dirpat, recursive=True)  # Find all files matching the pattern
all_data = pd.DataFrame()  # Initialize an empty DataFrame

# Loop through the files and append to the DataFrame
for file in files: # [0:1]:
    print(file)
    df = pd.read_csv(file)
    all_data = pd.concat([all_data, df])  #, ignore_index=True)

# Convert to datetime and from GMT to eastern time
all_data = \
    (all_data
     .assign(datetime_est= lambda x: pd.to_datetime(x['Date'] + ' ' + x['Time (GMT)']) -pd.Timedelta(hours=5))  # convert to EST
     .assign(site_name='Moneystump Swamp', 
             site_id='MSM',
             source='NOAA',
             station='Solomons Island 8577330',)
     .rename(columns= {'Verified (m)':'wse_m_navd88'}))

# Filter columns
all_data = all_data[['site_id', 'site_name','station','datetime_est', 'wse_m_navd88']]

moneystump_waterheight = all_data.copy().sort_values(by=['datetime_est'])




#----------------------------------------------------------------------------------
#  Get Toledo NOAA buoy for Erie

import glob
folder_path = '../../data/tide_gauges/noaa/toledo_9063085/'
files = glob.glob(os.path.join(folder_path, '*.csv'))

# Initialize an empty list to store DataFrames
dfs = []
# Loop through the list of CSV files and read each one into a DataFrame
for file in files:
    df = pd.read_csv(file)
    dfs.append(df)

# Concatenate all DataFrames in the list into a single DataFrame
toledo_erie_df = (
    pd.concat(dfs, ignore_index=True)

    .rename(columns={'Verified (m)' : 'wse_m_navd88'})

    .assign(wse_m_navd88= lambda x: pd.to_numeric(x.wse_m_navd88, errors='coerce'),
            datetime_est= lambda x: pd.to_datetime(x['Date'] + ' ' + x['Time (GMT)'])-pd.Timedelta(hours=5),
            station='Marblehead',
            source='NOAA',
            salinity_ppt=0)
    .drop(columns=['Preliminary (m)','Predicted (m)', 'Date', 'Time (GMT)'])
    .drop_duplicates()
    )


#----------------------------------------------------------------------------------
#  Get Marblehead NOAA buoy for Erie

import glob
folder_path = '../../data/tide_gauges/noaa/Erie_Marblehead_noaa/'
files = glob.glob(os.path.join(folder_path, '*.csv'))

# Initialize an empty list to store DataFrames
dfs = []
# Loop through the list of CSV files and read each one into a DataFrame
for file in files:
    df = pd.read_csv(file)
    dfs.append(df)

# Concatenate all DataFrames in the list into a single DataFrame
marblehead_erie_df = (
    pd.concat(dfs, ignore_index=True)

    .rename(columns={'Verified (m)' : 'wse_m_navd88'})

    .assign(wse_m_navd88= lambda x: pd.to_numeric(x.wse_m_navd88, errors='coerce'))
    .assign(datetime_est= lambda x: pd.to_datetime(x['Date'] + ' ' + x['Time (GMT)']) -pd.Timedelta(hours=5))
    .assign(station='Marblehead',
            source='NOAA',
            salinity_ppt=0)
    .drop(columns=['Preliminary (m)','Predicted (m)', 'Date', 'Time (GMT)'])
    .drop_duplicates()
    )


#----------------------------------------------------------------------------------
#   COMBINE ERIE DATA
erie_hydro_df_pr =  (toledo_erie_df.copy().assign(site_name = 'Portage River', site_id = 'PTR'))
erie_hydro_df_cc =  (toledo_erie_df.copy().assign(site_name = 'Crane Creek', site_id = 'CRC'))
erie_hydro_df_owc = (marblehead_erie_df.copy().assign(site_name = 'Old Woman Creek', site_id = 'OWC'))


# CONCATENATE REPEATED DFs
erie_hydro_df_3sites = pd.concat([erie_hydro_df_cc, erie_hydro_df_owc, erie_hydro_df_pr], axis=0)


#----------------------------------------------------------------------------------
# Combine data from each transect

df_wl = pd.concat([
        goodwin_df,
        sweethall_df,
        # gcrew, # This is Ben's nc forcing
        gcrew_water_elev_df, # From NOAA, until 2024
        gcrew_formoneystump,
        moneystump_waterheight,
        erie_hydro_df_3sites],
        axis=0)

# df_wl = df_wl.rename(columns={'site':'site_name'})

# Convert datatype
df_wl['salinity_ppt'] = pd.to_numeric(df_wl['salinity_ppt'], errors='coerce')
df_wl['wse_m_navd88'] = pd.to_numeric(df_wl['wse_m_navd88'], errors='coerce')
df_wl['datetime_est'] = pd.to_datetime(df_wl['datetime_est'], errors='coerce')

df_wl['zone_name'] = 'Open Water; Tidal forcing'

# Turn negative salintiy to 0
df_wl['salinity_ppt'] = df_wl['salinity_ppt'].apply(lambda x: max(x, 0))

df_wl = df_wl.drop(columns=['index'], errors='ignore')#.reset_index(drop=False)

# df_wl.info()

df_wl = df_wl[['site_name', 'site_id', 'station', 'source', 'zone_name', 'datetime_est', 'wse_m_navd88', 'salinity_ppt']]

# Save DataFrame to CSV
df_wl.to_csv('../../output/results/hydro_forcing_gauges/buoy_wl_all_syn_v05.csv', index=False)
