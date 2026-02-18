
import numpy as np
from pygam import LinearGAM, s  # te unused in this code
from scipy.optimize import minimize
from scripts.config import N_MODES, MAX_LAG, N_SPLINES, LAMBDA_VAL, N_MODES, INIT_LAGS


#%% Helper functions -------------------------------------------------------------

#%% Build a sum of spline terms for each IMF mode
def _build_gam_terms(n_modes: int = N_MODES, 
                     n_splines: int = N_SPLINES):
    """
    Build a sum of spline terms for each IMF mode (and optionally other features).
    Here we treat each column as an independent smooth term: s(0) + s(1) + ... + s(n_modes-1).
    """
    terms = s(0, n_splines=n_splines)
    for imf_idx in range(1, n_modes):
        terms += s(imf_idx, n_splines=n_splines)
    return terms


#%% Apply integer lags to each column of imfs (2D array).
def _apply_lags(imfs: np.ndarray, lags: np.ndarray) -> np.ndarray:

    # Round lags to nearest integer
    lags_int = np.round(lags).astype(int)

    # Create empty array
    imfs_shifted = np.empty_like(imfs)

    # Loop over each feature/column and apply lag to full imfs, inserting the shifted column values into the shifted array
    for i, lag in enumerate(lags_int):
        imfs_shifted[:, i] = np.roll(imfs[:, i], lag)

    return imfs_shifted



#%% Optimize lags and fit final GAM -------------------------------------------------
def optimize_lags_and_fit_gam(imfs: np.ndarray,
                              swot_sparse: np.ndarray,
                              swot_indices: np.ndarray) -> tuple[np.ndarray, LinearGAM]:
   
   
    #  Define formulation of GAM terms (same for optimization and final fit)
    terms = _build_gam_terms(n_modes=N_MODES, n_splines=N_SPLINES)
    

    #%% Objective function for lag optimization (on sparse data only) ---------------------------------------
    def lag_objective(lags: np.ndarray) -> float:

        # Apply lags to IMFs
        imfs_shifted = _apply_lags(imfs, lags)
        imfs_shifted_sparse = imfs_shifted[swot_indices, :]

        # Fit GAM only on rows with valid y
        gam = LinearGAM(terms, lam=LAMBDA_VAL).fit(imfs_shifted_sparse, swot_sparse)

        # Compute residuals and return sum of squared errors
        residuals = swot_sparse - gam.predict(imfs_shifted_sparse)
        return np.sum(residuals ** 2)


    #%%  Optimize lags (Powell works without gradients; L-BFGS-B struggled)  --------------------------------------------------
    minimizer_output = minimize(
        lag_objective,
        x0=INIT_LAGS,     # Initial guess: zero lags
        bounds=[(-MAX_LAG, MAX_LAG)] * N_MODES,
        method="Powell")

    print(minimizer_output)


    #%% Final reconstruction on full dataset --------------------------------

    # Round optimal lags
    optimal_lags = np.round(minimizer_output.x).astype(int)

    # Apply optimal lags to full IMF dataset
    imfs_shifted = _apply_lags(imfs, optimal_lags)
    imfs_shifted_sparse = imfs_shifted[swot_indices, :]

    # Fit final GAM with optimal lags on sparse imfs and swot (same as used in optimization objective)
    gam_final = LinearGAM(terms, lam=LAMBDA_VAL).fit(imfs_shifted_sparse, swot_sparse)

    #%% Reconstruct full WSE time series using lagged IMFs and fitted GAM
    imfs_full_shifted = _apply_lags(imfs, optimal_lags)
    y_pred = gam_final.predict(imfs_full_shifted)

    return optimal_lags, gam_final, y_pred




#%% Test unit  ---------------------------------------------------
def main():

    import pandas as pd

    #   Get SWOT water elevation per nearshore unit
    from scripts.dataio import load_swot_tidal_wse
    swot_wse_df = load_swot_tidal_wse('GCW').set_index('datetime_EST').sort_index()#  .sort_values(by='datetime_EST')

    #  Get gauge data
    from scripts.dataio import load_noaa_gage_data
    ref_wse_df = load_noaa_gage_data('GCW')
    ref_wse_df['datetime_LST'] = pd.to_datetime(ref_wse_df['datetime_LST'])
    ref_wse_df = ref_wse_df.set_index('datetime_LST').sort_index()


    # aggregate duplicates by mean (or another aggregation)
    ref_wse_df = ref_wse_df[['gauge_wse_m']].groupby(ref_wse_df.index).mean()

    # # Interpolate linearly to 6-minute intervals
    # ref_wse_df = (
    #     ref_wse_df['gauge_wse_m']
    #     .resample('6min').mean()  
    #     .interpolate('time')
    #     .to_frame()   # back to DataFrame
    #     # .reset_index()
    # )

    # Run VMD
    from src.elm_coastal_forcing.wse_reconstr.vmd import run_vmd_on_gauge
    imfs = run_vmd_on_gauge(ref_wse_df['gauge_wse_m'])


    imfs_dates = pd.merge(pd.concat([ref_wse_df, imfs], axis=1),   # Append IMFs to dataframe
                swot_wse_df, 
                left_on= ['datetime_LST'], 
                right_on=['datetime_EST'], 
                how='left')

    # Get indices of rows with valid SWOT WSE (these are the rows used in lag optimization and GAM fitting)
    swot_indices = imfs_dates.loc[imfs_dates['swot_wse_m_navd_mean'].notna()].index.values

    # Get lags and GAM model
    optimal_lags, gam_final, reconstructed_wse = \
        optimize_lags_and_fit_gam(
            imfs=np.array(imfs),
            # Derive sparse SWOT WSE and corresponding sparse IMFs for optimization inputs using the swot_indices
            # To ensure there are no misalignments, we subset the imfs_dates dataframe to the swot_indices and pull both the swot_wse and the imfs from that subsetted dataframe for the optimization inputs
            swot_sparse=imfs_dates.loc[swot_indices, 'swot_wse_m_navd_mean'].values,
            swot_indices=imfs_dates.loc[swot_indices, 'swot_wse_m_navd_mean'].index.values)

    return(optimal_lags, gam_final, reconstructed_wse)


if __name__ == "__main__":
    optimal_lags, gam_final, reconstructed_wse = main()



 # n_modes: int = N_MODES,
    # lag_bounds=(-MAX_LAG, MAX_LAG)):
   

# print(gam_final)
# print("Optimal lags:", optimal_lags)
# # print("Shape of training IMF predictors:", imfs_sparse.shape)
# print("Shape of full IMF predictors:", imfs_full_shifted.shape)

# # Reconstruct full WSE time series using lagged IMFs and fitted GAM
# y_pred = gam_final.predict(imfs_full_shifted)


# # Keep any extra columns (e.g. cyclic time)
# if imfs_full.shape[1] > N_MODES:
#     extra_full = imfs_full[:, N_MODES:]
#     imfs_full_shifted = np.column_stack((imfs_full_shifted, extra_full))
# else:
#     imfs_full_shifted = imfs_full_shifted





#%% Apply integer lags to each column of imfs (2D array).
# def _apply_lags_n_filter(imfs: np.ndarray, 
#                 lags: np.ndarray,
#                 swot_indices: np.ndarray) -> np.ndarray:

#     # Round lags to nearest integer
#     lags_int = np.round(lags).astype(int)

#     # Create empty array
#     imfs_shifted = np.empty_like(imfs)

#     # Loop over each feature/column and apply lag to full imfs, inserting the shifted column values into the shifted array
#     for i, lag in enumerate(lags_int):
#         imfs_shifted[:, i] = np.roll(imfs[:, i], lag)

#     imfs_shifted_sparse = imfs_shifted[swot_indices, :]

#     return imfs_shifted_sparse

