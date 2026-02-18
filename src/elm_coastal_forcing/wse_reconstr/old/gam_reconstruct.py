


import numpy as np
from pygam import LinearGAM, s, te
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import pandas as pd



#%% Function to optimize lags and fit GAM  ---------------------------------------------
def optimize_lags_and_fit_gam(IMFs, 
                              swot_indices, 
                              y_sparse, 
                              n_modes, 
                              lag_bounds=(-10, 10), 
                              lambda_val=5.2):

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

        # Subset IMFs to SWOT
        imfs_sparse = IMFs[swot_indices, :]

        # Initialize an empty array to store lag-shifted IMFs (only valid data)
        # IMFs_shifted = np.zeros_like(imfs_sparse[:, :n_modes])
        imfs_sparse_shifted = np.zeros_like(imfs_sparse)

        # Loop through modes
        for i in range(n_modes):
            # Get starting lag for particular mode
            lag = int(np.round(lags[i]))
            # Apply lag by rolling the IMF data
            imfs_sparse_shifted[:, i] = np.roll(imfs_sparse[:, i], lag)  


        # Combine shifted IMFs with cyclic time component
        # imfs_sparse_shifted = np.column_stack((IMFs_shifted, imfs_sparse[:, n_modes])) 
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

    #%% RECONSTRUCTION Apply optimal lags to the **full dataset** ---------------------------------------



    # Initialize empty shifted IMFs
    IMFs_shifted = np.zeros_like(IMFs[:, :n_modes])
    # np.zeros_like(imfs_sparse[:, :n_modes])


    # Loop through modes to apply optimal lags
    for i in range(n_modes):
        lag = int(np.round(optimal_lags[i]))
        IMFs_shifted[:, i] = np.roll(IMFs[:, i], lag)  # Lagging now applies to entire dataset

    # Combine shifted IMFs with cyclic time for final GAM fitting
    # IMFs_shifted = np.column_stack((IMFs_shifted, IMFs[:, n_modes]))

    # terms = te(0, n_modes, n_splines=[6, 6])  # Tensor interaction for IMF 1
    # for imf_idx in range(1, n_modes):
    #     terms += te(imf_idx, n_modes, n_splines=[6, 6])  # Tensor interactions for other IMFs
    
    terms = s(0, n_splines=4)
    for imf_idx in range(1, n_modes):
        terms += s(imf_idx, n_splines=4)

    # NOTE: Adding lambda=0.1 for some regularization helped to capture the range of variation better.
    # TODO: Add 
    # TODO: Experiment with different λ values by performing a grid search (gam.gridsearch() in pyGAM).
    gam_final = LinearGAM(terms, lam=lambda_val).fit(IMFs_shifted[swot_indices, :], y_sparse)

    return optimal_lags, gam_final

