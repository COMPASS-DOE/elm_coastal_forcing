
# standard library
from datetime import datetime

# third-party
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pytz
from pygam import LinearGAM, s, te
from scipy.optimize import minimize

# local
from scripts.dataio import load_noaa_gage_data, load_swot_tidal_wse
from scripts.config import SITE_CODE_LIST
from proc.wse_reconstr.vmd import run_vmd_on_gauge
from proc.wse_reconstr.fcn.gam_reconstruct import optimize_lags_and_fit_gam
from plots.fcn.lineplot_interpolated_swot import plot_time_series_with_refs



#%%  Load gauge data ------------------------------------------------------------
# TODO: figure out why duplicates...? 
noaa_wl_df = load_noaa_gage_data()


#%%-----------------------------------------------------------------------
#   Get SWOT water elevation per nearshore unit
swot_tidal_wse_df = load_swot_tidal_wse()


#%%-----------------------------------------------------------------------
# Loop through sites
for site_id in SITE_CODE_LIST:
    print(site_id)

    # Filter to single site for testing
    boundary_wl_df_sub = noaa_wl_df.query("site_id == 'GCW'")


    #%%-----------------------------------------------------------------------
    # Run Variational mode decomposition

    # Max mode index (is the number of IMFs + number of cyclic predictors)
    n_modes = 8  

    imfs = run_vmd_on_gauge(signal=boundary_wl_df_sub['gauge_wse_m'].values, 
                            n_modes=n_modes)

    # Append IMFs to dataframe
    boundary_wl_df_sub_wimfs = pd.concat([boundary_wl_df_sub, imfs], axis=1)

    # Initialize empty dataframe to store results
    wse_rcstr_df = pd.DataFrame(columns =  ['unit_id', 'datetime_LST', 'reconstructed_wse'])  


    #%% Loop through nearshore units -------------------------------------------------------
    for unit_id, swot_tidal_wse_df_singleunit in swot_tidal_wse_df.groupby("unit_id"):
        print(unit_id)

    for unit_id in swot_tidal_wse_df['unit_id'].unique():
        

        print(unit_id)

        #%% Subset unit to one of GCREW  (id=11)
        # swot_tidal_wse_df = swot_tidal_wse_df.query("unit_id == 11")

        swot_tidal_wse_df_singleunit = swot_tidal_wse_df.query(f"unit_id == {unit_id}")


        #%%-----------------------------------------------------------------------
        # JOIN GAUGE AND SWOT WSE ON DATES
        wse = pd.merge(boundary_wl_df_sub_wimfs, 
                    swot_tidal_wse_df_singleunit, 
                    left_on= ['site_id', 'datetime_LST'], 
                    right_on=['site_id', 'datetime_EST'], 
                    how='left')


        #%%-----------------------------------------------------------------------
        #  Filter dates of joined WSE df

        # Create timezone-aware comparison dates
        from datetime import datetime
        import pytz
        eastern = pytz.timezone('US/Eastern')
        start_date = eastern.localize(datetime(2022, 9, 1))
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
        
        
        # Get values
        y = wse_swotperiod['gauge_wse_m'].values


        # Get indices of valid SWOT observations
        swot_indices = wse_swotperiod[wse_swotperiod['swot_wse_m_navd_mean'].notna()].index
        
        # Subset gauge values
        # y_sparse = y[swot_indices]
        # Ysparse should be SWOT measures
        y_sparse = np.array(wse_swotperiod['swot_wse_m_navd_mean'])[swot_indices]

        # Get time indices
        time_idx = wse_swotperiod['dateindices']#.values

        print(y_sparse)



        #%% Run VMD  ---------------------------------------------
        from proc.wse_reconstr.vmd import run_vmd_on_gauge

        # TODO: Instead use: from sktime.transformations.series.vmd import VmdTransformer  ???
        IMFs = run_vmd_on_gauge(y)

        # Full IMF dataset
        IMFs = pd.DataFrame(IMFs.T) #.values

        IMFs = np.array(IMFs)


        # IMFs = IMFs.values  
        # Extract sparse rows for valid observations
        # imfs_sparse = IMFs.values[swot_indices, :]
        # imfs_sparse = IMFs[swot_indices, :]

        print(f'Y shape: {y.shape}')
        print(f'y_sparse shape: {y_sparse.shape}')
        print(f'IMFs shape: {IMFs.shape}')



        #%% Run lag optimization and GAM fitting  ----------------------------
        from proc.wse_reconstr.fcn.gam_reconstruct import optimize_lags_and_fit_gam


        optimal_lags, gam_final = optimize_lags_and_fit_gam(IMFs, swot_indices, y_sparse, n_modes)


        print(gam_final)
        print("Optimal lags:", optimal_lags)
        # print("Shape of training IMF predictors:", imfs_sparse.shape)
        print("Shape of full IMF predictors:", IMFs.shape)

        # Test predictions on full series
        y_pred = gam_final.predict(IMFs)



        #%%-----------------------------------------------------------------------
        # Convert outputs into a dataframe
        wse_rcstr_unit =  pd.DataFrame({
            'unit_id': unit_id,
            'datetime_LST': wse_swotperiod['datetime_LST'],
            'reconstructed_wse': y_pred.ravel()
            })


        #%%  JOIN GAUGE AND SWOT WSE ON DATES  -----------------------------------------------------------------------
        wse_swotperiod_recstr = pd.merge(wse_swotperiod, 
                    wse_rcstr_unit, 
                    left_on= ['datetime_LST'], 
                    right_on=['datetime_LST'], 
                    how='left')


        from plots.fcn.lineplot_interpolated_swot import plot_time_series_with_refs
        plot_time_series_with_refs(wse_swotperiod_recstr, 
                                    None, 
                                    eastern.localize(datetime(2025, 1, 1)),
                                    eastern.localize(datetime(2025, 5, 1)),
                                    suffix= f'_v06_gam_voronoi_{site_id}_{unit_id}')



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

            weir_depth['elev_m'] = weir_depth['depth_m_anomaly'] + swot_tidal_wse_df.swot_wse_m_navd_mean.mean() + 0.15
            # weir_depth["timestamp_local_hr"] = weir_depth["timestamp_local_hr"].dt.tz_localize('UTC-04:00')


            plot_time_series_with_refs(wse_swotperiod_recstr, 
                                        weir_depth, 
                                        eastern.localize(datetime(2023, 8, 17)),
                                        eastern.localize(datetime(2023, 8, 23)),
                                        f'v06_gam_voronoi_sonde_{site_id}_{unit_id}')

        #%% Append to overall dataframe
        wse_rcstr_df = pd.concat([wse_rcstr_df, wse_rcstr_unit], axis=0)


    # Save combined df of all units to file
    wse_rcstr_df.to_csv(f'../../output/results/reconstr_wse/{site_id}_nearshore_wse_reconstr.csv')

##### END OF LOOP #####
