

import pandas as pd
import numpy as np
import sys

import sys
sys.path.append('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/scripts')



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
swot_tidal_wse_df = pd.read_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_nearshore.csv', low_memory=False)

# Rename columns
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
for site_id in ['GCW']:
    # print(site_id)


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
    start_date = eastern.localize(datetime(2023, 9, 1))
    end_date   = eastern.localize(datetime(2025, 5, 1))

    # Clean up wse dataframe
    wse_swotperiod = ( wse
        .query("site_id == @site_id")
        .drop_duplicates(subset=['datetime_LST'], keep='last')
        .query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
    )


    #%%-----------------------------------------------------------------------
    #  RUN TideXCorr

    # from proc.prep_swot.fcn.run_tidercstr_on_swot import run_tidercstr_on_swot
    # wse_swotperiod = run_tidercstr_on_swot(wse, site_id, start_date, end_date)

    #%%-----------------------------------------------------------------------
    # Declare inputs to function

    # Sparse SWOT time series
    t =               np.array(wse_swotperiod['dateindices'])
    h_sparse =        np.array(wse_swotperiod['swot_wse_m_navd_mean'])
    h_sparse_uncert = np.array(wse_swotperiod['swot_wse_m_navd_std'])

    # Reference time and water surface elevation series
    tref = np.array(wse_swotperiod['dateindices'], dtype=np.float64) 
    # href = np.array(wse_swotperiod['gauge_wse_m'])
    href = np.array(wse_swotperiod.loc[:, 'D0':'D8'])

    timestep = 60
    maxlags = 11

    # Options for tidexcorr
    options = {
        'smoothparam': 0.8,          # Smoothing parameter for input series
        'weights': np.ones_like(t),  # Weights of the same length as `t`
        'trend': 'none',             # No trend correction
        'numparam': 5,               # Number of parameters for regression
        }


    #%%-----------------------------------------------------------------------
    import sys
    sys.path.append('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/scripts')


    #%%-----------------------------------------------------------------------
    # Run TIDEXCORR function
    from tidexcorr.py.tidexcorr import tidexcorr
    trefi, hout, betas, rmse, lags = tidexcorr(t, h_sparse, tref, href, timestep, maxlags, options)


    # Import tidexcorr functions (developed by Pascal Matte)
    from tidexcorr.py.tidercstr import tidercstr

   # Reshape lags  # TODO: insert inside function
    lags = np.array(lags.reshape(1, -1), dtype=int)
    betas = np.array(betas.reshape(1, -1), dtype=int)

    trefi, hout = tidercstr(tref, href, timestep, betas, lags, options=None)



    #%%-----------------------------------------------------------------------
    # Combine outputs into a dataframe
    wse_rcstr =  pd.DataFrame({
        'datetime_LST': wse_swotperiod['datetime_LST'],
        'reconstructed_wse': hout.ravel()
        })

    # Adjust reconstructed WSE to have same mean as input sparse SWOT WSE
    wse_rcstr['reconstructed_wse'] = wse_rcstr['reconstructed_wse'] + wse_swotperiod['swot_wse_m_navd_mean'].mean()


    #%%-----------------------------------------------------------------------
    # JOIN GAUGE AND SWOT WSE ON DATES
    wse_swotperiod_recstr = pd.merge(wse_swotperiod, 
                wse_rcstr, 
                left_on= ['datetime_LST'], 
                right_on=['datetime_LST'], 
                how='left')


    #%%-----------------------------------------------------------------------
    # Compute Kling Gupta Efficiency
    from numpy import array
    from permetrics.regression import RegressionMetric

    wse_swotperiod_recstr = wse_swotperiod_recstr[~pd.isna(wse_swotperiod_recstr['reconstructed_wse'])]
    
    evaluator = RegressionMetric(wse_swotperiod_recstr['gauge_wse_m'].to_numpy(), 
                                 wse_swotperiod_recstr['reconstructed_wse'].to_numpy())
    
    print('KGE: ', evaluator.kling_gupta_efficiency())


    # Save reconstructed WSE time series to file 
    wse_swotperiod.to_csv(f'../../output/results/swot/nearshore_wse_reconstr/swot_wse_reconstructed_{site_id}_v02.csv', index=False)



    #%%-----------------------------------------------------------------------
    # Plot SWOT reconstruction the comparison

    from plots.fcn.lineplot_interpolated_swot import plot_time_series_with_refs
    plot_time_series_with_refs(wse_swotperiod_recstr, 
                               None, 
                               eastern.localize(datetime(2023, 8, 1)),
                               eastern.localize(datetime(2025, 5, 1)),
                               suffix='v04')


    #%%-----------------------------------------------------------------------
    # Plot SWOT reconstruction VS sonde
    if site_id == 'GCW':  # Only GCW has sonde data

        # Load and preprocess the weir depth data
        weir_depth = (
            pd.read_csv("../../data/sondes/GCW/weir_exotable/GCReW_weir_exo.csv")
            .assign(timestamp_local_hr = lambda x: pd.to_datetime(x['timestamp_local_hr'], errors='coerce'))
            .assign(timestamp_local_hr = lambda x: x['timestamp_local_hr'].dt.tz_localize('UTC-04:00'))
        )
        # weir_depth["timestamp_local_hr"] = weir_depth["timestamp_local_hr"].dt.tz_localize('UTC-04:00')


        plot_time_series_with_refs(wse_swotperiod_recstr, 
                                   weir_depth, 
                                   eastern.localize(datetime(2023, 7, 1)),
                                   eastern.localize(datetime(2023, 7, 5)),
                                   'v04_with_sonde')



# #%%-----------------------------------------------------------------------
# # This filter happens inside the function?  Double check
# if 0: 

#     # Filter to only rows with SWOT id  
#     swot_indices = wse[~pd.isna(wse["wse_navd88_mean"])]

#     # Remove empty rows from swot
#     # TODO:  This is because gauges don't go as recent as SWOT
#     swot_indices = swot_indices[~pd.isna(swot_indices["dateindices"])]


    # wse_forKGE = pd.merge(wse_swotperiod[['datetime_LST','site_id','gauge_wse_m']], wse, how='left', on=['datetime_LST', 'site_id'])
    