# -*- coding: utf-8 -*-

# import pandas as pd
# import numpy as np

#%%-----------------------------------------------------------------------
# Loop through sites
from elm_coastal_forcing.wse_reconstr.WSEreconstructor import WSEReconstructor
from scripts.config import END_DATE, SITE_CODE_LIST, START_DATE
for site_id in SITE_CODE_LIST:
    # print(site_id)


    #%% WSE reconstructor  -----------------------------------------------
    
    # Create an instance of the reconstructor
    site_reconstructor = WSEReconstructor(site_id)

    optimal_lags, gam_final, reconstructed_wse = site_reconstructor.reconstruct_wse() 



#**END**************************************

#     # Run Variational Mode Decomposition (VMD) to get IMFs
#     from src.elm_coastal_forcing.wse_reconstr.vmd import run_vmd_on_gauge
#     imfs = run_vmd_on_gauge(ref_wse_df['gauge_wse_m'])
#     imfs.columns = [f'D{i}' for i in range(imfs.shape[1])]


#     #%%-----------------------------------------------------------------------
#     # JOIN GAUGE AND SWOT WSE ON DATES
#     wse_df = pd.merge(pd.concat([ref_wse_df, imfs], axis=1),   # Append IMFs to dataframe
#                 swot_tidal_wse_df, 
#                 left_on= ['site_id', 'datetime_LST'], 
#                 right_on=['site_id', 'datetime_EST'], 
#                 how='left')

#     #%%-----------------------------------------------------------------------
#     #  Filter the joined WSE df

#     # Create timezone-aware comparison dates
#     from datetime import datetime
#     import pytz
#     eastern = pytz.timezone('US/Eastern')
#     start_date = eastern.localize(datetime(2023, 9, 1))
#     end_date   = eastern.localize(datetime(2025, 5, 1))

#     # Clean up wse dataframe; filter to time period covered by SWOT
#     wse_swotperiod = ( wse_df
#         .query("site_id == @site_id")
#         .drop_duplicates(subset=['datetime_LST'], keep='last')
#         .query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
#     )

#     #%%-----------------------------------------------------------------------
#     # Declare inputs to TideGAM reconstruction

#     # Sparse SWOT time series
#     t =               np.array(wse_swotperiod['dateindices'])
#     h_sparse =        np.array(wse_swotperiod['swot_wse_m_navd_mean'])
#     h_sparse_uncert = np.array(wse_swotperiod['swot_wse_m_navd_std'])

#     # Reference time and water surface elevation series
#     tref = np.array(wse_swotperiod['dateindices'], dtype=np.float64) 
#     # href = np.array(wse_swotperiod['gauge_wse_m'])
#     href = np.array(wse_swotperiod.loc[:, 'D0':'D8'])

#     timestep = 60
#     maxlags = 11

#     # # Options for tidexcorr
#     # options = {
#     #     'smoothparam': 0.8,          # Smoothing parameter for input series
#     #     'weights': np.ones_like(t),  # Weights of the same length as `t`
#     #     'trend': 'none',             # No trend correction
#     #     'numparam': 5,               # Number of parameters for regression
#     #     }

#     #%% Run lag optimization and GAM fitting  ----------------------------
#     from elm_coastal_forcing.wse_reconstr.old.gam_reconstruct import optimize_lags_and_fit_gam
#     optimal_lags, gam_final = optimize_lags_and_fit_gam(IMFs, swot_indices, y_sparse, n_modes)


#     print(gam_final)
#     print("Optimal lags:", optimal_lags)
#     # print("Shape of training IMF predictors:", imfs_sparse.shape)
#     print("Shape of full IMF predictors:", IMFs.shape)

#     # Test predictions on full series
#     y_pred = gam_final.predict(IMFs)

#     #%%-----------------------------------------------------------------------
#     # Convert outputs into a dataframe
#     wse_rcstr_unit =  pd.DataFrame({
#         'unit_id': unit_id,
#         'datetime_LST': wse_swotperiod['datetime_LST'],
#         'reconstructed_wse': y_pred.ravel()
#         })


#     #%%  JOIN GAUGE AND SWOT WSE ON DATES  -----------------------------------------------------------------------
#     wse_swotperiod_recstr = pd.merge(wse_swotperiod, 
#                 wse_rcstr_unit, 
#                 left_on= ['datetime_LST'], 
#                 right_on=['datetime_LST'], 
#                 how='left')



#     #%%-----------------------------------------------------------------------
#     # Run TIDEXCORR function
#     from tidexcorr.py.tidexcorr import tidexcorr
#     trefi, hout, betas, rmse, lags = tidexcorr(t, h_sparse, tref, href, timestep, maxlags, options)


#     # Import tidexcorr functions (developed by Pascal Matte)
#     from tidexcorr.py.tidercstr import tidercstr

#    # Reshape lags  # TODO: insert inside function
#     lags = np.array(lags.reshape(1, -1), dtype=int)
#     betas = np.array(betas.reshape(1, -1), dtype=int)

#     trefi, hout = tidercstr(tref, href, timestep, betas, lags, options=None)



#     #%%-----------------------------------------------------------------------
#     # Combine outputs into a dataframe
#     wse_rcstr =  pd.DataFrame({
#         'datetime_LST': wse_swotperiod['datetime_LST'],
#         'reconstructed_wse': hout.ravel()
#         })

#     # Adjust reconstructed WSE to have same mean as input sparse SWOT WSE
#     wse_rcstr['reconstructed_wse'] = wse_rcstr['reconstructed_wse'] + wse_swotperiod['swot_wse_m_navd_mean'].mean()


#     #%%-----------------------------------------------------------------------
#     # JOIN GAUGE AND SWOT WSE ON DATES
#     wse_swotperiod_recstr = pd.merge(wse_swotperiod, 
#                 wse_rcstr, 
#                 left_on= ['datetime_LST'], 
#                 right_on=['datetime_LST'], 
#                 how='left')


#     #%%-----------------------------------------------------------------------
#     # Compute Kling Gupta Efficiency
#     from numpy import array
#     from permetrics.regression import RegressionMetric

#     wse_swotperiod_recstr = wse_swotperiod_recstr[~pd.isna(wse_swotperiod_recstr['reconstructed_wse'])]
    
#     evaluator = RegressionMetric(wse_swotperiod_recstr['gauge_wse_m'].to_numpy(), 
#                                  wse_swotperiod_recstr['reconstructed_wse'].to_numpy())
    
#     print('KGE: ', evaluator.kling_gupta_efficiency())


#     # Save reconstructed WSE time series to file 
#     wse_swotperiod.to_csv(f'../../output/results/swot/nearshore_wse_reconstr/swot_wse_reconstructed_{site_id}_v02.csv', index=False)



#     #%%-----------------------------------------------------------------------
#     # Plot SWOT reconstruction the comparison

#     from plots.fcn.lineplot_interpolated_swot import plot_time_series_with_refs
#     plot_time_series_with_refs(wse_swotperiod_recstr, 
#                                None, 
#                                eastern.localize(datetime(2023, 8, 1)),
#                                eastern.localize(datetime(2025, 5, 1)),
#                                suffix='v04')


#     #%%-----------------------------------------------------------------------
#     # Plot SWOT reconstruction VS sonde
#     if site_id == 'GCW':  # Only GCW has sonde data

#         # Load and preprocess the weir depth data
#         weir_depth = (
#             pd.read_csv("../../data/sondes/GCW/weir_exotable/GCReW_weir_exo.csv")
#             .assign(timestamp_local_hr = lambda x: pd.to_datetime(x['timestamp_local_hr'], errors='coerce'))
#             .assign(timestamp_local_hr = lambda x: x['timestamp_local_hr'].dt.tz_localize('UTC-04:00'))
#         )
#         # weir_depth["timestamp_local_hr"] = weir_depth["timestamp_local_hr"].dt.tz_localize('UTC-04:00')


#         plot_time_series_with_refs(wse_swotperiod_recstr, 
#                                    weir_depth, 
#                                    eastern.localize(datetime(2023, 7, 1)),
#                                    eastern.localize(datetime(2023, 7, 5)),
#                                    'v04_with_sonde')

# #%%-----------------------------------------------------------------------
# # This filter happens inside the function?  Double check
# if 0: 
#     # Filter to only rows with SWOT id  
#     swot_indices = wse[~pd.isna(wse["wse_navd88_mean"])]

#     # Remove empty rows from swot
#     # TODO:  This is because gauges don't go as recent as SWOT
#     swot_indices = swot_indices[~pd.isna(swot_indices["dateindices"])]

    # wse_forKGE = pd.merge(wse_swotperiod[['datetime_LST','site_id','gauge_wse_m']], wse, how='left', on=['datetime_LST', 'site_id'])
    