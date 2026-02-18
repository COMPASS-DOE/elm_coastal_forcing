
# Finds best lag for parirwise h_sparse and href
#  



import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import correlate


def tidexcorr(t, h, tref, href, timestep, maxlags, options=None):
    """
    Perform lag regression to interpolate sparse/short time series `h` at a
    given timestep using one or more reference time series `href`.

    Parameters:
        t (np.ndarray): Times of the sparse/short time series (1D array).
        h (np.ndarray or list): Sparse/short time series to be interpolated (numeric or list of arrays).
        tref (np.ndarray): Times of the reference time series (1D array).
        href (np.ndarray or list): One or more reference time series (2D array or list of 2D arrays).
        timestep (float): Timestep in minutes.
        maxlags (int): Maximum lags in terms of time steps.
        options (dict): Optional arguments with keys:
            - "smoothparam" (float): Smoothing parameter for input reference series (default=1).
            - "weights" (np.ndarray): Weights for least-squares fit (default=all ones).
            - "trend" (str): Trend to fit ("none", "linear", or "quadratic", default="none").
            - "numparam" (int): Number of parameters for regression models (default=3).

    Returns:
        tuple: (tout, hout, betas, rmse, lags) where:
            - tout (np.ndarray): Interpolated time vector.
            - hout (np.ndarray): Interpolated time series.
            - betas (np.ndarray): Regression coefficients.
            - rmse (float): Root-mean-squared error of the fit.
            - lags (np.ndarray): Final lags for each reference series.
    """
    # --- Parse options ---
    smoothparam = options.get('smoothparam', 1) if options else 1
    W = options.get('weights', np.ones_like(t)) if options else np.ones_like(t)
    trend = options.get('trend', 'none') if options else 'none'
    numparam = options.get('numparam', 3) if options else 3

    # --- Input Validation ---
    t = np.array(t).flatten()  # Ensure t is a 1D array
    if h.ndim == 1:
        h = np.expand_dims(h, axis=1)  # Convert h to a 2D column vector

    # Check and preprocess href
    if isinstance(href, list):
        href = [np.array(x, ndmin=2).T if x.shape[0] < x.shape[1] else np.array(x) for x in href]
        cc = len(href)  # Number of reference series if href is a list
    else:
        href = np.array(href)
        if href.ndim == 1 or href.shape[0] < href.shape[1]:
            href = href.T  # Ensure href is a 2D column-major array
        cc = 1  # Single reference series

    # Assert compatibility
    assert tref.size == href[0].shape[0] if isinstance(href, list) else tref.size == href.shape[0], \
        "Input `tref` and `href` must have the same number of rows (time points)."
    assert t.size == h.shape[0], "`t` and `h` must have the same length."
    assert timestep > 0, "Timestep must be positive."
    assert maxlags > 0, "Maximum lags (`maxlags`) must be positive."
    assert len(W) == t.size, "Weights `W` must have the same length as `t`."
    assert trend in ['none', 'linear', 'quadratic'], \
        "`trend` must be one of: 'none', 'linear', or 'quadratic'."
    assert numparam >= 2, "`numparam` must be at least 2."
    if numparam == 2:
        max_columns = 2 if isinstance(href, list) else href.shape[1]
        assert max_columns <= 2, "Only 2 reference series allowed for `numparam=2`."

    # --- Smoothing (optional) ---
    if smoothparam != 1:
        if isinstance(href, list):
            for i, ref in enumerate(href):
                for col in range(ref.shape[1]):
                    not_nan = ~np.isnan(ref[:, col])
                    if np.sum(not_nan) > 1:  # Only interpolate if enough valid points
                        interpolator = interp1d(
                            tref[not_nan], ref[not_nan, col], kind='cubic', bounds_error=False, fill_value="extrapolate"
                        )
                        ref[:, col] = interpolator(tref)  # Replace the entire column
        else:
            for col in range(href.shape[1]):
                not_nan = ~np.isnan(href[:, col])
                if np.sum(not_nan) > 1:
                    interpolator = interp1d(
                        tref[not_nan], href[not_nan, col], kind='cubic', bounds_error=False, fill_value="extrapolate"
                    )
                    href[:, col] = interpolator(tref)  # Replace the entire column

    # --- Interpolation of Reference Series ---
    trefi = np.arange(tref[0] * 24 * 60, tref[-1] * 24 * 60, timestep) / (24 * 60)  # New time vector
    if isinstance(href, list):
        hrefi = []
        for ref in href:
            assert ref.shape[0] == tref.size, f"Mismatch: tref (length={tref.size}) and href (rows={ref.shape[0]})"
            hrefi.append(interp1d(
                tref, ref, kind='cubic', bounds_error=False, fill_value=np.nan, axis=0
            )(trefi))
    else:
        assert href.shape[0] == tref.size, f"Mismatch: tref (length={tref.size}) and href (rows={href.shape[0]})"
        hrefi = interp1d(
            tref, href, kind='cubic', bounds_error=False, fill_value=np.nan, axis=0
        )(trefi)

    # --- Truncate `t` and `h` ---
    tmin = max(t[0], trefi[0])
    tmax = min(t[-1], trefi[-1])
    ilo = np.searchsorted(t, tmin, side='left')
    iup = np.searchsorted(t, tmax, side='right')
    ttrunc = t[ilo:iup]
    htrunc = h[ilo:iup, :] if h.shape[1] > 1 else h[ilo:iup]


    # --- Lagged Correlation ---
    lags = []
    # hrefi = np.array(hrefi).T if isinstance(hrefi, list) else np.array(hrefi).T

    # Loop through each reference series to find optimal lag
    # for ref in hrefi:
    for i, ref in enumerate(hrefi.T):
        ref = ref.ravel()  # Collapse dimensions into 1D
        corr = correlate(h.flatten(), ref, mode='full')
        # Find the index of the maximum correlation
        lag_index = np.argmax(corr) - len(ref) + 1
        # Append the lag index
        lags.append(lag_index)
    
    
    # Apply lags to hrefi
    hrefilag = []


    lags_expanded = np.array(lags)[:, np.newaxis]
    result = np.column_stack((hrefi.T, lags_expanded))


    # Loop through each reference series and apply the lag
    for ref, lag in np.array(zip(hrefi.T, lags)).T:

        lagged = np.copy(ref)
        if lag > 0:
            lagged[lag:] = lagged[:-lag]
            lagged[:lag] = np.nan
        elif lag < 0:
            lagged[:lag] = lagged[-lag:]
            lagged[lag:] = np.nan
        hrefilag.append(lagged)


    # --- Least Squares Regression ---
    gd = np.where(np.isfinite(h + np.sum(hrefilag, axis=0)))[0]
    X = np.ones((len(gd), 1))  # Add intercept term
    X = np.hstack([X] + [href[:, gd] for href in hrefilag])
    y = h[gd]
    

    # Apply weights
    if not np.all(W == 1):
        sw = np.sqrt(W[gd])
        X *= sw[:, np.newaxis]
        y *= sw

    # Solve least squares regression
    betas = lsq_linear(X, y).x  # Solve using SciPy's bounded regression solver
    
    # Root Mean Squared Error
    residuals = np.nan_to_num(y - X @ betas)
    rmse = np.sqrt(np.mean(residuals**2))

    # --- Trend Adjustment (Optional) ---
    if trend == 'linear':
        logt = np.log(t)
        trend_coeffs = np.linalg.lstsq(np.column_stack((np.ones_like(logt), logt)), residuals)[0]
    elif trend == 'quadratic':
        logt = np.log(t)
        trend_coeffs = np.linalg.lstsq(np.column_stack((np.ones_like(logt), logt, logt**2)), residuals)[0]
    else:
        trend_coeffs = []


    # --- Output Interpolation ---
    hout = np.full_like(trefi, np.nan) # Make empty hout array the size of trefi
    hout[gd] = X @ betas  # Fill hout with the regression result at valid indices
    
    # Return results
    return trefi, hout, betas, rmse, lags



#%%  Example usage of tidexcorr function


import numpy as np
# Generate time: 0 to 24 hours, sampled hourly
t = np.arange(0, 25, 1)  # Time in hours

# Create a synthetic sparse/short time series `h`, mimicking a sinusoidal tidal signal
# Add a sinusoid with a 12-hour period (typical semi-diurnal tide)
h_clean = 2.0 * np.sin(2 * np.pi * t / 12) + 5.0  # Sinusoidal signal centered around 5

# Add random noise
h = h_clean + np.random.normal(0, 0.3, size=t.shape)  # Add noise with standard deviation 0.3

# Introduce "gaps" (NaN values) to simulate missing data in sparse observations
h_sparse = h.copy()
h_sparse[[3, 5, 7, 10, 12, 15, 19, 22]] = np.nan  # Arbitrary missing data points


# Reference time vector (higher resolution for reference time series)
tref = np.arange(0, 25, 0.5)  # Reference time vector: 30-minute intervals

# Reference sinusoidal time series (mimicking band-filtered water surface levels)
href1 = 2.0 * np.sin(2 * np.pi * tref / 12) + 5.0  # Same sinusoidal tide signal
href2 = 1.5 * np.sin(2 * np.pi * tref / 12 + np.pi / 6) + 5.0  # Phase-shifted reference

# Add small random noise to reference signals
href1 += np.random.normal(0, 0.2, size=tref.shape)
href2 += np.random.normal(0, 0.2, size=tref.shape)

# Combine reference signals into a 2D array
href = np.column_stack((href1, href2))

# Options for tidexcorr
options = {
    'smoothparam': 0.8,  # Smoothing parameter for input series
    'weights': np.ones_like(t),  # Weights of the same length as `t`
    'trend': 'none',  # No trend correction
    'numparam': 3,  # Number of parameters for regression
}

timestep = 60  # Time step (resolution for interpolation): 1 hour # In minutes

maxlags = 3  # Maximum allowed time lags (measured in time steps)




#%%-------------------------------
### PLOT THE INTERPOLATED TIME SERIES
import matplotlib.pyplot as plt

def plot_time_series_with_refs(t, h, trefi, hout, tref, href):
    """
    Plot original sparse time series, interpolated time series, and reference series.

    Parameters:
        t (np.ndarray): Time vector for original sparse data.
        h (np.ndarray): Original sparse data corresponding to `t`.
        trefi (np.ndarray): Interpolated time vector.
        hout (np.ndarray): Interpolated time series corresponding to `trefi`.
        tref (np.ndarray): Reference time vector.
        href (np.ndarray): Reference series (2D array with columns as reference signals).
    """
    # Ensure `h` and `hout` are 1D arrays if they are not already
    h = h.flatten() if h.ndim > 1 else h
    hout = hout.flatten() if hout.ndim > 1 else hout

    plt.figure(figsize=(12, 6))

    # Plot the original sparse time series
    plt.plot(t, h, 'o', label='t - Sparse height', markersize=8, color='blue', alpha=0.75)

    # Plot the interpolated time series
    # plt.plot(trefi, hout, '-', label='hout - interpolated height', color='orange', linewidth=2, alpha=0.9)

    # Plot all reference series
    if hout.ndim > 1:  # Multiple reference series
        for i in range(hout.shape[1]):
            plt.plot(trefi, hout[:, i], '-', label=f'Interpolated {i+1}', alpha=0.8)

    else:  # Single reference series
        plt.plot(trefi, hout, '-', label='Interpolated', alpha=0.8)


    # Plot all reference series
    if href.ndim > 1:  # Multiple reference series
        for i in range(href.shape[1]):
            plt.plot(tref, href[:, i], '--', label=f'Reference {i+1}', alpha=0.8)

    else:  # Single reference series
        plt.plot(tref, href, '--', label='Reference 1', alpha=0.8)

    # Add labels, title, and legend
    plt.xlabel('Time (hours)', fontsize=12)
    plt.ylabel('Value', fontsize=12)
    plt.title('Original vs Interpolated vs Reference Series', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)

    # Add grid
    plt.grid(True, which='both', linestyle='--', linewidth=0.7, alpha=0.7)

    # Show plot
    plt.show()







#%%----------------------------------------------------------------
# Call tidexcorr
try:
    # Run the function
    trefi, hout, betas, rmse, lags = tidexcorr(t, h_sparse, tref, href, timestep, maxlags, options)


    # Plot the comparison
    plot_time_series_with_refs(t, h_sparse, trefi, hout, tref, href)
    # plot_time_series(t, h, trefi, hout, tref)

    # Print results
    print("Regression Coefficients (betas):", betas)
    print("Root Mean Squared Error (RMSE):", rmse)
    print("Optimal Lags:", lags)

    except AssertionError as e:
        print("AssertionError:", str(e))





    # tout, hout, betas, rmse, lags = tidexcorr(swot_tidal_wse_df.wse_mean, swot_tidal_wse_df.date, 
    #                                         boundary_wl_df.water_height_m, boundary_wl_df.datetime, 
    #                                         60, 3)





#%%----------------------------------------------

# # Sparse/short time series with gaps
# t = np.array([0, 1, 2, 3, 4])  # Time points
# h = np.array([np.nan, 2.5, np.nan, 4.1, 3.3])  # Sparse series with missing values

# # Reference time series with gaps
# tref = np.array([0, 1, 2, 3, 4, 5, 6])  # Reference time
# href = np.array([
#     [2.0, 2.5, np.nan, 4.0, 5.0, 6.1, 7.2],  # Reference series 1
#     [np.nan, 2.0, 2.8, 3.8, 4.9, np.nan, 7.1]  # Reference series 2
# ]).T  # Shape (7, 2)

# # Time step (in minutes)
# timestep = 60

# # Maximum allowed time lags
# maxlags = 2

# # Additional options
# options = {
#     'smoothparam': 0.7,
#     'weights': np.ones_like(t),
#     'trend': 'none',
#     'numparam': 3,
# }

# import numpy as np
# from scipy.interpolate import interp1d
# from scipy.linalg import lstsq
# from scipy.signal import correlate
# import warnings


# # Outputs: trefi, hout, betas, rmse, lags
# # trefi: interpolated tidal reference
# # hout: hout


# def tidexcorr(t, h, tref, href, timestep, maxlags, options=None):
    
#     # Set defaults and parse options
#     default_options = {
#         'smoothparam': 1,
#         'weights': np.ones_like(t),
#         'trend': 'none',
#         'numparam': 3
#     }
    
#     if options is not None:
#         default_options.update(options)
    
#     smoothparam = default_options['smoothparam']
#     W = default_options['weights']
#     trend = default_options['trend']
#     numparam = default_options['numparam']

#     # Convert inputs to numpy arrays
#     t = np.array(t).flatten()


#     # Reshape h and href
#     # h = np.atleast_2d(h).T if len(h.shape) == 1 else h

#     # Ensure h is 2D; if h (the sparse time series) is 1D, convert it to 2D
#     # h = np.atleast_2d(h) if len(h.shape) == 1 else h

#     # Ensure href is 2D; if href (the reference time series) is 1D, convert it to 2D
#     # href = [np.array(x) for x in href] if isinstance(href, list) else [np.atleast_2d(href).T] if href.shape[0] < href.shape[1] else [href]
#     # href = np.atleast_2d(href).T #if len(h.shape) == 1 else h
#     # href = href.T

#     for href_item in href:
#         print("href_item:", href_item)
#         assert tref.shape[0] == href_item.shape[0], "Input tref and href must be the same length"

#     assert t.shape[0] == h.shape[0], 'Input t and h must be the same length'

#     assert timestep > 0, "Time step must be positive"
#     assert maxlags > 0, "Maxlags must be positive"
#     assert W.shape[0] == t.shape[0], "Weights and input t must be the same length"
#     assert trend in ['none', 'linear', 'quadratic'], 'trend option must be "none", "linear", or "quadratic"'


#     # Check numparam
#     # np.array(href).shape[1]
#     if numparam >= 3 and href.shape[0] == 1:
#         numparam = 2

#     elif numparam == 2:
#         assert href.shape[0] <= 2, 'Only 2 reference series allowed with numparam=2'

#     # Smoothing - using a basic moving average for demonstration
#     if smoothparam != 1:
#         # Apply smoothing to each reference series
#         for i in range(href.shape[0]):
#             for j, href_item in enumerate(href):
#                 href[j][:, i] = np.convolve(href_item[:, i], np.ones((smoothparam,))/smoothparam, mode='same')



#     # Create a time vector for interpolation
#     trefi = np.arange(tref[0]*24*60, tref[-1]*24*60, timestep) / 24 / 60

#     # Interpolate ref series at specified timestep
#     hrefi = [interp1d(tref, h, kind='cubic', fill_value="extrapolate")(trefi) for h in href]


#     #%% Truncate t and h 
#     tmin = max(t[0], trefi[0])
#     tmax = min(t[-1], trefi[-1])
#     ilo = np.searchsorted(t, tmin, side='left')
#     iup = np.searchsorted(t, tmax, side='right')
#     ttrunc = t[ilo:iup].flatten()
#     htrunc = h[ilo:iup] if h.shape[0] > 1 else h[ilo:iup]

#     gd = np.nonzero(np.isfinite(trefi + np.sum(np.stack(hrefi), axis=0)))[0]

#     #%% Lagged correlation between reference series
#     maxlagref = [np.zeros(href_item.shape[0]-1) for href_item in href] if href.shape[0] > 1 else [0]
    
#     for j in range(len(href)):
#         for i in range(1, href[j].shape[0]):
#             xcref = correlate(hrefi[j][gd, 0] - hrefi[j][gd, 0].mean(), hrefi[j][gd, i] - hrefi[j][gd, i].mean(), mode='full')
#             lag_idx = np.argmax(xcref) - len(hrefi[j][gd, 0]) + 1
#             maxlagref[j][i-1] = lag_idx
#             if lag_idx > 0:
#                 hrefi[j][lag_idx:, i] = hrefi[j][:-lag_idx, i]
#                 hrefi[j][:lag_idx, i] = np.nan
#             elif lag_idx < 0:
#                 hrefi[j][:lag_idx, i] = hrefi[j][-lag_idx:, i]
#                 hrefi[j][lag_idx:, i] = np.nan

#     #%% Lagged correlation between reference and h
#     def adjust_lag(hrefi_j, lag_value):
#         if lag_value > 0:
#             hrefi_j[lag_value:] = hrefi_j[:-lag_value]
#             hrefi_j[:lag_value] = np.nan
#         elif lag_value < 0:
#             hrefi_j[:lag_value] = hrefi_j[-lag_value:]
#             hrefi_j[lag_value:] = np.nan
#         return hrefi_j

#     #%%
#     # Initialize lags
#     lagc_values = []
#     # Loop through each reference series to find optimal lag
#     for j in range(len(href)):
#         maxlagsi = min(maxlags, int(np.max(np.abs(maxlagref[j]))))
#         lagvec = np.arange(-maxlagsi, maxlagsi + 1)
#         xc = np.full(lagvec.shape, np.nan)
        
#         for i, lag_value in enumerate(lagvec):
#             hrefilagtmp = adjust_lag(hrefi[j][:, 0].copy(), lag_value)
#             hrefilagtmpt = interp1d(trefi, hrefilagtmp, kind='linear', fill_value="extrapolate")(ttrunc)

#             gd_h = np.isfinite(ttrunc + htrunc[:, 0] + np.sum(hrefilagtmpt))
#             if np.any(gd_h):
#                 xc[i] = np.corrcoef(htrunc[gd_h, 0], hrefilagtmpt[gd_h])[0, 1]
        
#         imaxc = np.nanargmax(xc)
#         lagc_values.append(lagvec[imaxc])

#     lags = np.zeros(len(href))
#     for j, lagc in enumerate(lagc_values):
#         hrefi[j][:, 0] = adjust_lag(hrefi[j][:, 0], lagc)
#         hrefi[j] = interp1d(trefi, hrefi[j], kind='linear', fill_value="extrapolate")(ttrunc)
#         lags[j] = lagc

#     #%% Linear regression at optimal lag
#     gd = np.isfinite(ttrunc + np.sum(htrunc, axis=1) + np.sum(np.stack(hrefi), axis=0))
#     X = np.ones((ttrunc[gd].shape[0], 1))

#     if numparam == 2 and href[0].shape[1] > 1:
#         X = np.hstack([X, *(hrefi[j][gd, 0] - hrefi[j][gd, 1] for j in range(len(href)))])
#         y = htrunc[gd, 0] - sum((hrefi[j][gd, 1] for j in range(len(href))))

#     else:
#         X = np.hstack([X] + [hrefi[j][gd, :] for j in range(len(href))])
#         y = htrunc[gd, :]

#     # Apply weights
#     if not np.all(W == 1):
#         sw = np.sqrt(W[gd])
#         X *= sw[:, np.newaxis]
#         y *= sw[:, np.newaxis]

#     #%% Least-squares fit
#     betas, residuals, _, _ = lstsq(X, y)

#     if numparam == 2 and href[0].shape[1] > 1:
#         betas = np.insert(betas, 1, 1 - betas[1])
        
#     # Handle trends
#     Xtrend = np.empty((0,))  # Default empty trend term
#     if trend == 'linear':
#         logt = np.log(ttrunc[gd])
#         Xtrend = np.hstack([np.ones_like(logt)[:, np.newaxis], logt[:, np.newaxis]])
#     elif trend == 'quadratic':
#         logt = np.log(ttrunc[gd])
#         Xtrend = np.hstack([np.ones_like(logt)[:, np.newaxis], logt[:, np.newaxis], logt[:, np.newaxis]**2])
    
#     btrend = np.linalg.lstsq(Xtrend, residuals, rcond=None)[0] if Xtrend.size > 0 else 0

#     # Reconstructed signal at tref
#     Xout = np.hstack([np.ones((trefi.shape[0], 1))] + hrefi)
#     hout = Xout @ betas
    
#     if Xtrend.size > 0:
#         tout = trefi
#         hout -= Xtrend @ btrend

#     # Outputs
#     rmse = np.sqrt(np.mean(residuals**2))

#     return trefi, hout, betas, rmse, lags




# #%%
# if __name__ == "__main__":


#     # Example usage:
#     # t = np.array(...)         # Your time vector for sparse series
#     # h = np.array(...)         # Your sparse time series
#     # tref = np.array(...)      # Your time vector for all the reference series; 1D array
#     # href = [np.array(...)]    # Array of reference time series; 2D for multiple series
#     # timestep = 60             # Time step in minutes
#     # maxlags = 5               # Maximum lags
#     # options = {'smoothparam': 1, 'trend': 'linear', 'numparam': 3}

#     # tout, hout, betas, rmse, lags = tidexcorr(t, h, tref, href, timestep, maxlags, options)


#     # Example usage
#     t = np.array([0, 1, 2, 3, 4, 5])
#     h = np.array([1, 2, 3, 4, 5, 6])

    
#     tref = np.array([0, 1, 2, 3, 4, 5])

#     # np.column_stack
#     href = np.array([[1, 2, 3, 4, 5, 6],
#                      [1, 2, 3, 4, 5, 6]])#.T
    

#     timestep = 60  # Time step in minutes ???
#     maxlags = 5 # Maximum lags
#     options = {'smoothparam': 1, 'trend': 'linear', 'numparam': 3}


#     # Call the function
#     tout, hout, betas, rmse, lags = tidexcorr(t, h, tref, href, timestep, maxlags, options)



#     print("tout:", tout)
#     print("hout:", hout)
#     print("betas:", betas)
#     print("rmse:", rmse)
#     print("lags:", lags)



#     # t = swot_tidal_wse_df.wse_mean
#     # h = swot_tidal_wse_df.date
#     # tref = boundary_wl_df.water_height_m
#     # href =  boundary_wl_df.datetime
#     # timestep=60
#     # maxlags=5

