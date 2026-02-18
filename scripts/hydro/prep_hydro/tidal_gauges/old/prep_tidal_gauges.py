

import pandas as pd
import glob
import xarray as xr
import datetime
import pytz
est = pytz.timezone('America/New_York')


#----------------------------------------------------------------------------------
#  VECOS water levels
## Assuming the VECOS data is in local timezone?  Not seeing the time change gap in the data; assuming it is in EST.

goodwin_wse = (
    pd.read_csv('../../data/tide_gauges/vecos/from_steph/goodwin_vecos.csv')
    .rename(columns={'datetimestamp': 'datetime_est', 
                     'NAVD88_elev': 'wse_m_navd88'})
    .assign(datetime_est=lambda x: pd.to_datetime(x['datetime_est'], format='%m/%d/%y %H:%M', errors='coerce'))
    .set_index('datetime_est') #, inplace=True))
    .drop(columns=['id']))

goodwin_wse = goodwin_wse.wse_m_navd88.resample('h').mean().reset_index()



sweethall_wse = (
    pd.read_csv('../../data/tide_gauges/vecos/from_steph/sweethall_vecos.csv') 
    .rename(columns={'datetimestamp': 'datetime_est', 
                     'NAVD88_elev': 'wse_m_navd88',})
    .assign(datetime_est=lambda x: pd.to_datetime(x['datetime_est'], format='%m/%d/%y %H:%M', errors='coerce'))
    .set_index('datetime_est') #, inplace=True))
    .drop(columns=['id']))

sweethall_wse = sweethall_wse.wse_m_navd88.resample('h').mean().reset_index()

# /----------------------------------------------------------------------------------
#/  VECOS salinity
## OLD from before Steph's VECOS data

from prep_hydro.fcn.prep_vecos import prep_vecos_waterquality_station
df_goodwin = prep_vecos_waterquality_station(directory = '../../data/tide_gauges/vecos/from_website/GoodwinIsland_CH019.38')
df_sweethall = prep_vecos_waterquality_station(directory = '../../data/tide_gauges/vecos/from_website/SweetHallMarsh_PMK012.18')



goodwin_sal = (df_goodwin
              .drop('TOTAL_DEPTH', axis=1)
              .rename(columns={'SALINITY': 'salinity_ppt',
                               'STATION': 'station',
                               'SAMPLE_DATETIME': 'datetime_est'}))

sweethall_sal = (df_sweethall
              .drop('TOTAL_DEPTH', axis=1)
              .rename(columns={'SALINITY': 'salinity_ppt',
                               'STATION': 'station',
                               'SAMPLE_DATETIME': 'datetime_est'}))



# /----------------------------------------------------------------------------------
#/  
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


#----------------------------------------------------------------------------------
# Read GCREW - Ben's file
fpath = '../../data/tide_gauges/GCREW/Annapolis_CB3_3W_elev_sal_35yrs_NAVD.nc'

with xr.open_dataset(fpath, decode_times=False) as ds:
    print(ds)

    gcrew = ds[['tide_height','tide_salinity']].to_dataframe().reset_index()
    gcrew['site_name'] = 'GCReW'
    gcrew['site_id'] = 'GCW'
    gcrew['station'] = 'Annapolis'


# Define the start date and end date
start_date = '1984-01-01'
# Calculate the end date based on the number of rows and hourly intervals
end_date = pd.to_datetime(start_date) + pd.DateOffset(hours=len(gcrew) - 1)

# Create a date range with hourly intervals
date_range = pd.date_range(start=start_date, end=end_date, freq='H')

# If 'df' is not empty and you want to add the datetime column
gcrew['datetime_est'] = date_range


gcrew = (gcrew
         .drop(['gridcell','time'], axis=1)
         .rename(columns={'tide_salinity':'salinity_ppt',
                          'tide_height':'wse_m_navd88'}) )


#----------------------------------------------------------------------------------
# GET NEW GCREW tidal gauge data

# Define the directory and pattern

dirpat = '../../data/tide_gauges/noaa/annapolis/*.csv'  # '../../data/tide_gauges/GCREW/CO-OPS_8575512*.csv'

# Find all files matching the pattern
files = glob.glob(dirpat, recursive=False)

# Initialize an empty list to store DataFrames
dfs = pd.DataFrame()

# Loop through the list of CSV files and read each one into a DataFrame
for f in files:
    print(f)
    df = pd.read_csv(f)
    dfs = pd.concat([dfs, df])


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

    #  .drop(columns=['Preliminary (m)', 'Predicted (m)', 'Date', 'Time (GMT)'])
    #  .drop_duplicates()


#----------------------------------------------------------------------------------
# Prep Moneystumps salinity
# TODO: Fix the large gaps

# Define the directory and pattern
dirpat = '../../data/tide_gauges/Moneystump/salinity/*CEDR_tidal*.csv'

# Find all files matching the pattern
files = glob.glob(dirpat, recursive=True)

# Initialize an empty DataFrame
all_data = pd.DataFrame()

# Loop through the files and append to the DataFrame
for file in files:
    print(file)
    df = pd.read_csv(file)
    all_data = pd.concat([all_data, df])  #, ignore_index=True)

# Filter to station and salinity
moneystump_salinity = all_data[ ((all_data['MonitoringLocation']=='EE2.2') & (all_data['Parameter']=='SALINITY')) ]

# Convert to datetime and from GMT to eastern time
moneystump_salinity = \
    (moneystump_salinity
     .assign(datetime_est= lambda x: pd.to_datetime(x['SampleDate'] + ' ' + x['SampleTime']) -pd.Timedelta(hours=5))
     .assign(datetime_est= lambda x: x.datetime_est.round('60min'))
     .assign(site_name = 'Moneystump Swamp',
             site_id = 'MSM',
             station='EE2.2',
             source='CEDR')
     .rename(columns={'MonitoringLocation':'station',
                      'MeasureValue':'salinity_ppt'})
     .drop_duplicates()
     )

# Subset columns
moneystump_salinity = moneystump_salinity[['site_id', 'site_name','station','datetime_est', 'salinity_ppt']]



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
#   USE GCREW SALINITY FOR MONEYSTUMP

gcrew_salinity_formoneystump = (
    gcrew.assign(site_name='Moneystump Swamp',
                 site_id='MSM', 
                 station='GCReW input'))#.drop(columns=['water_height_m', 'site', 'station']))


gcrew_formoneystump = (
    moneystump_waterheight
        .merge(
            gcrew_salinity_formoneystump.loc[:,['datetime_est', 'salinity_ppt']].reset_index(),
            on=['datetime_est'],
            how='left')
        )


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
