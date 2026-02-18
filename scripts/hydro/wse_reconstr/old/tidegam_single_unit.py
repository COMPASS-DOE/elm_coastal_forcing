

import numpy as np
from pygam import LinearGAM, s, te
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import pandas as pd


#%% Simulate data for a 365-day time series
np.random.seed(42)
n_days = 600
n_modes = 8  # Max mode index (is the number of IMFs + number of cyclic predictors)

# Generate cyclic time and IMF predictors
time_idx = np.arange(n_days)
cyclic_time_sin = np.sin(2 * np.pi * time_idx / n_days)  # Annual cyclicity (sin)

# Test with constant cyclic component
cyclic_time_sin = np.full(n_days, 1)

# NOTE: For some reason, the VMD returns an array 1 shorter than input for series that are uneven length...
 

#%% Use the gauge water level data from the boundary_wl_df_sub dataframe  ---------
# y = boundary_wl_df_sub['gauge_wse_m'][0:1200].values



#%%  Get gauge data  ------------------------------------------------------------

boundary_wl_df = pd.read_csv('../../output/results/tide_gauges/noaa_coops_tide_gauges.csv',  
                             low_memory=False, dtype= {'wse_m': 'float'}) 

boundary_wl_df = ( boundary_wl_df
    .rename(columns={'wse_m':'gauge_wse_m'})
    .assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce'))  # Convert datatype
    .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize('UTC-04:00'))
    .sort_values(by='datetime_LST')
    .assign(dateindices = lambda x: pd.Categorical(x.datetime_LST.values).codes) # Add column of date indices
    .loc[:, ['dateindices', 'datetime_LST', 'site_id', 'gauge_wse_m']]
    )
# TODO: figure out why duplicates...? 



#%%-----------------------------------------------------------------------
#   Get SWOT water elevation
# swot_tidal_wse_df = pd.read_csv('../../output/results/swot_wse_synoptic_tidal_poly.csv', low_memory=False)
# swot_tidal_wse_df = pd.read_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_nearshore.csv', low_memory=False)

# # Rename columns
# swot_tidal_wse_df = (swot_tidal_wse_df
#     .rename(columns={'wse_mean':'swot_wse_m_navd_mean', 'wse_std':'swot_wse_m_navd_std'})    # Rename columns
#     .assign(date = lambda x: pd.to_datetime(x['date'], errors='coerce'))           # Convert datatype
#     .assign(date = lambda x: x['date'].dt.round('h'))                              # Round to hour
#     .assign(date = lambda x: x['date'].dt.tz_localize('UTC-00:00'))                # If date not localized, localize to GMT
#     .assign(datetime_EST = lambda x: x['date'].dt.tz_convert('UTC-04:00'))         # Convert to local time
#     .loc[:, ['site_id', 'datetime_EST', 'swot_wse_m_navd_mean', 'swot_wse_m_navd_std']]      # Subset columns
#     )



#%%  Get SWOT water elevation   -----------------------------------------------------------------------

# Get SWOT tidal wse for only nearshore unit sites
swot_tidal_wse_df = pd.read_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_nearshore_v02.csv')

# Filter to remove polygons with few points
swot_tidal_wse_df = swot_tidal_wse_df.query("pt_count >= 5")

# Subset unit to one of GCREW  (id=11)
swot_tidal_wse_df = swot_tidal_wse_df.query("unit_id == 11")



#%% loop through nearshore units -------------------------------------------------------

for unit_id in swot_tidal_wse_df['unit_id'].unique():
    print(unit_id)



    swot_tidal_wse_df = (swot_tidal_wse_df
        .rename(columns={'wse_mean':'swot_wse_m_navd_mean', 'wse_std':'swot_wse_m_navd_std'})    # Rename columns
        .assign(date = lambda x: pd.to_datetime(x['date'], errors='coerce'))           # Convert datatype
        .assign(date = lambda x: x['date'].dt.round('h'))                              # Round to hour
        .assign(date = lambda x: x['date'].dt.tz_localize('UTC-00:00'))                # If date not localized, localize to GMT
        .assign(datetime_EST = lambda x: x['date'].dt.tz_convert('UTC-04:00'))         # Convert to local time
        .loc[:, ['site_id', 'datetime_EST', 'swot_wse_m_navd_mean', 'swot_wse_m_navd_std']]      # Subset columns
        )


#%%-----------------------------------------------------------------------
# Loop through sites
# for site_id in wse.site_id.unique():
# for site_id in ['GCW']:
# print(site_id)

site_id = 'GCW'

#%%-----------------------------------------------------------------------
# Run VMD

# Filter 
boundary_wl_df_sub = boundary_wl_df.query("site_id == 'GCW'")

# Run VMD
from proc.wse_reconstr.vmd import run_vmd_on_gauge
imfs = run_vmd_on_gauge(boundary_wl_df_sub['gauge_wse_m'].values)
imfs = pd.DataFrame(imfs.T)
imfs.columns = [f'D{i}' for i in range(imfs.shape[1])]

# Append IMFs to dataframe
boundary_wl_df_sub = pd.concat([boundary_wl_df_sub, imfs], axis=1)


#%%-----------------------------------------------------------------------
# JOIN GAUGE AND SWOT WSE ON DATES
wse = pd.merge(boundary_wl_df_sub, 
            swot_tidal_wse_df, 
            left_on= ['site_id', 'datetime_LST'], 
            right_on=['site_id', 'datetime_EST'], 
            how='left')


#%%-----------------------------------------------------------------------
#  Filter the joined WSE df

# Create timezone-aware comparison dates
from datetime import datetime
import pytz
eastern = pytz.timezone('US/Eastern')
start_date = eastern.localize(datetime(2021, 9, 1))
end_date   = eastern.localize(datetime(2025, 5, 1))

# Clean up wse dataframe
wse_swotperiod = ( wse
    .query("site_id == @site_id")
    .drop_duplicates(subset=['datetime_LST'], keep='last')
    .query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
)


# Get nearest even number of rows
even_row_count = len(wse_swotperiod) if len(wse_swotperiod) % 2 == 0 else len(wse_swotperiod) - 1

# Subset dataframe to even number of rows
wse_swotperiod = wse_swotperiod.iloc[0:even_row_count]

# Reset index
wse_swotperiod.reset_index(drop=True, inplace=True)

y = wse_swotperiod['gauge_wse_m'].values
valid_indices = wse_swotperiod[wse_swotperiod['swot_wse_m_navd_mean'].notna()].index

y_sparse = y[valid_indices]

time_idx = wse_swotperiod['dateindices']#.values


#%% Run VMD  ---------------------------------------------
from proc.wse_reconstr.vmd import run_vmd_on_gauge

# TODO: Instead use: from sktime.transformations.series.vmd import VmdTransformer  ???
IMFs = run_vmd_on_gauge(y)

IMFs = pd.DataFrame(IMFs.T)

data = IMFs.values  # Full IMF dataset

# Extract sparse rows for valid observations
imfs_sparse = IMFs.values[valid_indices, :]  

print(f'Y shape: {y.shape}')
print(f'y_sparse shape: {y_sparse.shape}')
print(f'IMFs shape: {IMFs.shape}')



#%% Function to optimize lags and fit GAM  ---------------------------------------------
def optimize_lags_and_fit_gam(y_sparse, imfs_sparse, n_modes, lag_bounds=(-10, 10), lambda_val=5.5):

    # lambda_val = 5.5

    """
    Optimizes lags for IMFs and fits a GAM using tensor interactions.
    Parameters:
        y_sparse (array): Sparse target variable with NaNs for missing values.
        imfs_sparse (array): Predictor variables corresponding to valid y_sparse entries.
        n_modes (int): Number of IMF modes to consider.
        lag_bounds (tuple): Bounds for lag optimization.
    Returns:
        optimal_lags (array): Optimal lags for each IMF mode.
        gam_final (LinearGAM): Fitted GAM model with optimal lags applied.
    """

    #%% Objective function for lag optimization
    def lag_optimization_objective(lags):


        # Initialize an empty array to store lag-shifted IMFs (only valid data)
        IMFs_shifted = np.zeros_like(imfs_sparse[:, :n_modes])

        # Loop through modes
        for i in range(n_modes):
            # Get starting lag for particular mode
            lag = int(np.round(lags[i]))
            # Apply lag by rolling the IMF data
            IMFs_shifted[:, i] = np.roll(imfs_sparse[:, i], lag)  

        # Combine shifted IMFs with cyclic time component
        imfs_sparse_shifted = np.column_stack((IMFs_shifted, imfs_sparse[:, n_modes])) 

        # Define GAM with tensor interactions between cyclic time (`sin_time`) and IMFs
        # terms = te(0, n_modes, n_splines=[6, 6])  # Tensor interaction: IMF 1 with cyclic time; to initiate the terms tensor
        # for imf_idx in range(1, n_modes):
        #     terms += te(imf_idx, n_modes, n_splines=[6, 6])  # Add interactions between cyclic time and other IMF

        terms = s(0, n_splines=4)
        for imf_idx in range(1, n_modes):
            terms += s(imf_idx, n_splines=4)

        # Fit GAM and calculate residuals
        gam = LinearGAM(terms, lam=lambda_val).fit(imfs_sparse_shifted, y_sparse)

        # Compute residuals
        residuals = y_sparse - gam.predict(imfs_sparse_shifted)
        
        # Return SSE to be minimized
        return np.sum(residuals**2)  


    #%% Initial guess for lags as zeros ---------------------------------------
    initial_lags = np.zeros(n_modes)

    # Optimize lags using L-BFGS-B method on the sparse dataset
    result = minimize(
        lag_optimization_objective,
        initial_lags,
        bounds=[lag_bounds] * n_modes,
        method="Powell"  
        # "SLSQP"  # "L-BFGS-B" could not find other solution than 0 lag.
        # options={'eps': 1, 'disp': True}  
    )

    print(result)

    # Get optimal lags
    optimal_lags = result.x
    optimal_lags = optimal_lags.round(0) # * -1

    #%% RECONSTRUCTION ---------------------------------------

    # Apply optimal lags to the **full dataset** for final modeling
    
    # Initialize empty shifted IMFs
    IMFs_shifted = np.zeros_like(data[:, :n_modes])

    # Loop through modes to apply optimal lags
    for i in range(n_modes):
        lag = int(np.round(optimal_lags[i]))
        IMFs_shifted[:, i] = np.roll(data[:, i], lag)  # Lagging now applies to entire dataset

    # Combine shifted IMFs with cyclic time for final GAM fitting
    data_shifted = np.column_stack((IMFs_shifted, data[:, n_modes]))

    # terms = te(0, n_modes, n_splines=[6, 6])  # Tensor interaction for IMF 1
    # for imf_idx in range(1, n_modes):
    #     terms += te(imf_idx, n_modes, n_splines=[6, 6])  # Tensor interactions for other IMFs
    
    terms = s(0, n_splines=4)
    for imf_idx in range(1, n_modes):
        terms += s(imf_idx, n_splines=4)

    # NOTE: Adding lambda=0.1 for some regularization helped to capture the range of variation better.
    # TODO: Experiment with different λ values by performing a grid search (gam.gridsearch() in pyGAM).
    gam_final = LinearGAM(terms, lam=lambda_val).fit(data_shifted[valid_indices, :], y_sparse)

    return optimal_lags, gam_final


#%% Run lag optimization and GAM fitting  ----------------------------
optimal_lags, gam_final = optimize_lags_and_fit_gam(y_sparse, imfs_sparse, n_modes)


print(gam_final)

print("Optimal lags:", optimal_lags)
print("Shape of training IMF predictors:", imfs_sparse.shape)
print("Shape of full IMF predictors:", data.shape)

# Test predictions on full series
y_pred = gam_final.predict(data)



#%%-----------------------------------------------------------------------
# Combine outputs into a dataframe
wse_rcstr =  pd.DataFrame({
    'datetime_LST': wse_swotperiod['datetime_LST'],
    'reconstructed_wse': y_pred.ravel()
    })

# Adjust reconstructed WSE to have same mean as input sparse SWOT WSE
# wse_rcstr['reconstructed_wse'] = wse_rcstr['reconstructed_wse'] + wse_swotperiod['swot_wse_m_navd_mean'].mean()


#%%-----------------------------------------------------------------------
# JOIN GAUGE AND SWOT WSE ON DATES
wse_swotperiod_recstr = pd.merge(wse_swotperiod, 
            wse_rcstr, 
            left_on= ['datetime_LST'], 
            right_on=['datetime_LST'], 
            how='left')





from plots.fcn.lineplot_interpolated_swot import plot_time_series_with_refs
plot_time_series_with_refs(wse_swotperiod_recstr, 
                            None, 
                            eastern.localize(datetime(2025, 1, 1)),
                            eastern.localize(datetime(2025, 5, 1)),
                            suffix='_v06_gam_voronoi')


#%%-----------------------------------------------------------------------
# Plot SWOT reconstruction VS sonde
# Only GCW has sonde data
if site_id == 'GCW':  

    # Load and preprocess the weir depth data
    weir_depth = (
        pd.read_csv("../../data/sondes/GCW/weir_exotable/GCReW_weir_exo.csv")
        .assign(timestamp_local_hr = lambda x: pd.to_datetime(x['timestamp_local_hr'], errors='coerce'))
        .assign(timestamp_local_hr = lambda x: x['timestamp_local_hr'].dt.tz_localize('UTC-04:00'))
    )

    weir_depth['elev_m'] = weir_depth['depth_m_anomaly'] + swot_tidal_wse_df.swot_wse_m_navd_mean.mean() + 0.2
    # weir_depth["timestamp_local_hr"] = weir_depth["timestamp_local_hr"].dt.tz_localize('UTC-04:00')


    plot_time_series_with_refs(wse_swotperiod_recstr, 
                                weir_depth, 
                                eastern.localize(datetime(2022, 8, 17)),
                                eastern.localize(datetime(2022, 8, 23)),
                                'v06_gam_voronoi_sonde')




