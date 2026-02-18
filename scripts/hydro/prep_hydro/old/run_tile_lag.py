
#!/usr/bin/env python3

import pandas as pd

# Import functions from Pascal Matte
from prep_hydro.tide_lag_reg_matte.py.tidexcorr import tidexcorr
import prep_hydro.tide_lag_reg_matte.py.tidercstr as tidercstr


#%%



#%%  Get buoy data  ------------------------------------------------------------

# Read in Buoy data
boundary_wl_df = pd.read_csv('../../output/results/hydro_forcing_gauges/buoy_wl_all_syn_v4.csv',  low_memory=False)

# Convert datatype
boundary_wl_df['water_height_m'] = pd.to_numeric(boundary_wl_df['water_height_m'], errors='coerce')
boundary_wl_df['datetime'] = pd.to_datetime(boundary_wl_df['datetime'], errors='coerce')

boundary_wl_df = boundary_wl_df[boundary_wl_df['site_name'].str.contains("Goodwin Island")]
boundary_wl_df = boundary_wl_df[['datetime', 'water_height_m']]

boundary_wl_df = boundary_wl_df[(boundary_wl_df['datetime'] >= '2023-08-01') & (boundary_wl_df['datetime'] < '2024-04-01')]


#%%  Get SWOT water elevation  ----------------------------------------------
swot_tidal_wse_df = pd.read_csv('../../output/results/swot_wse_synoptic_tidal_edge.csv')
swot_tidal_wse_df['date'] = pd.to_datetime(swot_tidal_wse_df['date'], errors='coerce')
# swot_tidal_wse_df = pd.merge(swot_tidal_wse_df, site_name_id_lut, on='site_id', how='left')
# swot_tidal_wse_df['zone_name'] = 'SWOT'

swot_tidal_wse_df = swot_tidal_wse_df[swot_tidal_wse_df['site_id'].str.contains("GWI")]

swot_tidal_wse_df.sort_values(by='date', inplace=True)
swot_tidal_wse_df['date'] = swot_tidal_wse_df['date'].dt.round('H')





#%% Tide correlation  ----------------------------------------------


# Example usage:
# t = np.array(...)         # Your time vector for sparse series of tidal height;  
# h = np.array(...)         # Your sparse time series of hours; for sparse SWOT obs.
# tref = np.array(...)      # Your time vector for reference series
# href = [np.array(...)]    # Your list of reference height time series
# timestep = 60             # Time step in minutes
# maxlags = 5               # Maximum lags
# options = {'smoothparam': 1, 'trend': 'linear', 'numparam': 3}

tout, hout, betas, rmse, lags = tidexcorr(swot_tidal_wse_df.wse_mean, swot_tidal_wse_df.date, 
                                          boundary_wl_df.water_height_m, boundary_wl_df.datetime, 
                                          60, 3)



# tidexcorr(t, h, tref, href, timestep, maxlags, options=None)




#%% Tide reconstruction

# tidercstr(tref, href, timestep, betas, lags, options=None)




# Example usage:
# tref = np.array(...)  # Your time reference vector
# href = np.array(...)  # Your reference time series matrix
# timestep = 60  # Time step in minutes
# betas = np.array(...)  # Regression parameters
# lags = np.array(...)  # Lags
# options = {'smoothparam': 0.7, 'trend': 'linear'}
# tout, hout = tidercstr(tref, href, timestep, betas, lags, options)

