
import pandas as pd
import numpy as np
import sys


def run_tidercstr_on_swot(wse, site_id, start_date, end_date):

    # print(site_id) 

    # wse_swotperiod = ( wse
    #     .query("site_id == @site_id")
    #     .drop_duplicates(subset=['datetime_LST'], keep='last')
    #     .query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
    # )


    #%%-----------------------------------------------------------------------
    # Declare inputs to function

    # Sparse SWOT time series
    t =               np.array(wse_swotperiod['dateindices'])
    h_sparse =        np.array(wse_swotperiod['swot_wse_m_navd_mean'])
    h_sparse_uncert = np.array(wse_swotperiod['swot_wse_m_navd_std'])

    # Reference time and water surface elevation series
    tref = np.array(wse_swotperiod['dateindices'], dtype=np.float64) 
    href = np.array(wse_swotperiod['gauge_wse_m'])

    timestep = 60
    maxlags = 11

    # Options for tidexcorr
    options = {
        'smoothparam': 0.8,  # Smoothing parameter for input series
        'weights': np.ones_like(t),  # Weights of the same length as `t`
        'trend': 'none',  # No trend correction
        'numparam': 5,  # Number of parameters for regression
        }


    #%%-----------------------------------------------------------------------
    import sys
    sys.path.append('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/scripts')

    # Import tidexcorr functions (developed by Pascal Matte)
    from tidexcorr.py.tidercstr import tidercstr
    from tidexcorr.py.tidexcorr import tidexcorr



    #%%-----------------------------------------------------------------------
    # Run TIDEXCORR function
    trefi, hout, betas, rmse, lags = tidexcorr(t, h_sparse, tref, href, timestep, maxlags, options)



    #%%-----------------------------------------------------------------------
    # Run TIDERCSTR function

    # Reshape lags  # TODO: insert inside function
    lags = np.array(lags.reshape(1, -1), dtype=int)

    trefi, hout = tidercstr(tref, href, timestep, betas, lags, options=None)



    #%%-----------------------------------------------------------------------
    # Combine outputs into a dataframe
    wse_rcstr =  pd.DataFrame({
        'datetime_LST': wse_swotperiod['datetime_LST'],
        'reconstructed_wse': hout.ravel()
        })


    #%%-----------------------------------------------------------------------
    # JOIN GAUGE AND SWOT WSE ON DATES
    wse_swotperiod = pd.merge(wse_swotperiod, 
                wse_rcstr, 
                left_on= ['datetime_LST'], 
                right_on=['datetime_LST'], 
                how='left')


    return(wse_swotperiod)
