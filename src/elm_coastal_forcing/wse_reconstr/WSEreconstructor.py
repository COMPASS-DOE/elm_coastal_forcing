
#%% Imports libraries -------------------------------------------------
from datetime import datetime
from typing import Iterable

import numpy as np
import pandas as pd
import pytz

from scripts.dataio import load_noaa_gage_data, load_swot_tidal_wse
from scripts.config import SITE_CODE_LIST, START_DATE, END_DATE, N_MODES
from src.elm_coastal_forcing.wse_reconstr.vmd import run_vmd_on_gauge
from src.elm_coastal_forcing.wse_reconstr.gam_optimize_lag import *



# """
# Reconstructs water surface elevation (WSE) for each site and nearshore unit.
# Instead of writing this as a big top-level script, we keep all the shared
# data and configuration inside 'self', and expose methods like 'process_site'.
# __init__ is the initializer for the class.
# When you do: reconstructor = WSEReconstructor(noaa_wl_df, swot_wse_df)
# Python does:
#     1) Create a new empty WSEReconstructor instance (call __new__)
#     2) Call __init__(that_instance, gauge_wse_df, swot_wse_df, ...) where 'that_instance' is passed in as 'self'.
#     3) Return that initialized instance to you.
# 'self' here refers to the new object being created. We attach data and configuration to 'self' so that all other methods can access them.
# """

#%%   Define WSEReconstructor class  -----------------------------------------
class WSEReconstructor:
    def __init__(self, site_id: str):
        self.ref_wse_df: pd.DataFrame = load_noaa_gage_data(site_id)
        self.swot_wse_df: pd.DataFrame = load_swot_tidal_wse(site_id)
        self.imfs: pd.DataFrame = None
        # Store configuration
        self.n_modes = N_MODES
        self.start_date = START_DATE
        self.end_date = END_DATE

    #%% Internal helper methods ---------------------------------------------------


    def _fix_dates(self) -> None:
        # Fix dates
        self.swot_wse_df = self.swot_wse_df.set_index('datetime_EST').sort_index() #  .sort_values(by='datetime_EST')
        # self.swot_wse_df.index.name = 'datetime_EST'
        self.swot_wse_df = self.swot_wse_df.reset_index()

        #  Get gauge data
        self.ref_wse_df['datetime_LST'] = pd.to_datetime(self.ref_wse_df['datetime_LST'])
        self.ref_wse_df = self.ref_wse_df.set_index('datetime_LST').sort_index()
        # aggregate duplicates by mean (or another aggregation)
        self.ref_wse_df = self.ref_wse_df[['gauge_wse_m']].groupby(self.ref_wse_df.index).mean()
        # self.ref_wse_df.index.name = 'datetime_LST'    # assuming same index
        self.ref_wse_df = self.ref_wse_df.reset_index()

    # Runs VMD on gauge; generates IMFs
    # TODO: repeat for each gauge
    def _run_vmd(self):
        from src.elm_coastal_forcing.wse_reconstr.vmd import run_vmd_on_gauge
        self.imfs = run_vmd_on_gauge(self.ref_wse_df['gauge_wse_m'])




    #%% Public methods (these form the "API" of this class) -----------------------------


    #%% Filter the  gauge/SWOT dataframe to the analysis time window
    # Return a filtered version of the gauge dataframe to the SWOT observation period.
    # TODO: Add buffer to avoid NAs
    def filter_gauge_to_swot_period_inplace(self) -> pd.DataFrame:

        # Get min/max dates from SWOT dataframe
        swot_start = self.swot_wse_df["datetime_EST"].min()
        swot_end   = self.swot_wse_df["datetime_EST"].max()

        # Filter gauge dataframe using SWOT min/max (convert column name as needed)
        self.ref_wse_df = (
            self.ref_wse_df.query("(datetime_LST >= @swot_start) & (datetime_LST <= @swot_end)")
            .reset_index(drop=True))




    #%% Reconstruct WSE for a single site ------------------------------------------------
            # Process a single site: run VMD, fit GAM, generate predictions
    def reconstruct_wse(self) -> pd.DataFrame:  

        # TODO: Interpolate hourly gauge to 6-min


        self._fix_dates()
        self._run_vmd()

        # Joint the imfs and dates
        imfs_dates = pd.merge(pd.concat([self.ref_wse_df, self.imfs], axis=1),   # Append IMFs to dataframe
                    self.swot_wse_df, 
                    left_on= ['datetime_LST'], 
                    right_on=['datetime_EST'], 
                    how='left')

        # Get indices of rows with valid SWOT WSE (these are the rows used in lag optimization and GAM fitting)
        swot_indices = imfs_dates.loc[imfs_dates['swot_wse_m_navd_mean'].notna()].index.values

        # Get lags and GAM model
        optimal_lags, gam_final, reconstructed_wse = \
            optimize_lags_and_fit_gam(
                imfs=np.array(self.imfs),
                # Derive sparse SWOT WSE and corresponding sparse IMFs for optimization inputs using the swot_indices
                # To ensure there are no misalignments, we subset the imfs_dates dataframe to the swot_indices and pull both the swot_wse and the imfs from that subsetted dataframe for the optimization inputs
                swot_sparse=imfs_dates.loc[swot_indices, 'swot_wse_m_navd_mean'].values,
                swot_indices=imfs_dates.loc[swot_indices, 'swot_wse_m_navd_mean'].index.values)

        return(optimal_lags, gam_final, reconstructed_wse)



#%% Example usage as main  -----------------------------------------------------
def main() -> None:
    """
    Top-level entry point. This loads data, create a WSEReconstructor instance, call its method to process all sites
    """


    # Load gauge and SWOT data
    # ref_wse_df = load_noaa_gage_data('GCW')
    # swot_wse_df = load_swot_tidal_wse('GCW')

    # Create an instance of the reconstructor
    gcw_reconstructor = WSEReconstructor('GCW')

    optimal_lags, gam_final, reconstructed_wse = gcw_reconstructor.reconstruct_wse()  # Process all sites from your config


    # Print atteributes and 
    dir(gcw_reconstructor)

    # Print the data attributes
    gcw_reconstructor.__dict__



if __name__ == "__main__":
    main()




# ref_wse_df = ref_wse_df,
# swot_wse_df = swot_wse_df,
# start_date=START_DATE,
# end_date=END_DATE)

# gcw_reconstructor.fix_dates()  # Fix dates and filter to SWOT period
# gcw_reconstructor.run_vmd()     # Run VMD to get IMFs

# # Enforce even number of rows; if odd, drop the last row
# if len(wse_swotperiod) % 2 == 1:
#     wse_swotperiod = wse_swotperiod.iloc[:-1]

# gcw_reconstructor.swot_wse_df.info()
# gcw_reconstructor.ref_wse_df.info()
# gcw_reconstructor.imfs.info()

# self.imfs = run_vmd_on_gauge(
#     signal=self.ref_wse_df['gauge_wse_m'],
#     n_modes=self.n_modes,)
# # Full gauge WSE series (target for reconstruction)
# y_sparse = swot_wse_df["swot_wse_m_navd_mean"].values
# # Sparse IMFs; filtered to SWOT obs dates
# imfs_sparse = self._filter_imfs_to_swot_dates()
# print(f"    Y shape: {y.shape},    y_sparse shape: {y_sparse.shape}")

# # Optimize lags and fit GAM on the IMF predictors
# optimal_lags, gam_final = \
#     optimize_lags_and_fit_gam(swot_wse = y_sparse,
#                               imfs_full= self.imfs.values) 
#                             # swot_indices= np.arange(len(y_sparse)))
# print("    Optimal lags:", optimal_lags)

# # Predict reconstructed WSE over the full time series
# y_pred = gam_final.predict(self.imfs)

# # Create reconstruction dataframe for this unit
# wse_rcstr = pd.DataFrame({
#     # "unit_id": unit_id,
#     "datetime_LST": wse_swotperiod["datetime_LST"],
#     "reconstructed_wse": y_pred.ravel(),
# })

# # Merge reconstruction back with original period for plotting
# wse_swotperiod_recstr = pd.merge(
#     wse_swotperiod,
#     wse_rcstr,
#     on="datetime_LST",
#     how="left",
# )

# Append unit reconstruction to the site-level dataframe
# wse_rcstr_df = pd.concat([wse_rcstr_df, wse_rcstr_unit], axis=0)

# Return combined reconstruction for all units at this site
# return wse_swotperiod_recstr
