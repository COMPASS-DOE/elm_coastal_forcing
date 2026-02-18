
# Run utide
# Recipe here: https://github.com/wesleybowman/UTide/blob/master/notebooks/utide_real_data_example.ipynb

from utide import solve, reconstruct
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys

import utide

# NOTE: This incorrectly imports a different package called 'tide'.
# from pytides.tide import Tide


swot_tidal_wse_df = pd.read_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_nearshore.csv', low_memory=False)

# Rename columns
swot_tidal_wse_df = (swot_tidal_wse_df
    .rename(columns={'wse_mean':'swot_wse_m_navd_mean', 'wse_std':'swot_wse_m_navd_std'})    # Rename columns
    .assign(date = lambda x: pd.to_datetime(x['date'], errors='coerce'))           # Convert datatype
    .assign(datetime_EST = lambda x: x['date'].dt.round('h'))                              # Round to hour
    # .assign(date = lambda x: x['date'].dt.tz_localize('UTC-00:00'))                # If date not localized, localize to GMT
    # .assign(datetime_EST = lambda x: x['date'].dt.tz_convert('UTC-04:00'))         # Convert to local time
    .loc[:, ['site_id', 'datetime_EST', 'swot_wse_m_navd_mean', 'swot_wse_m_navd_std']]      # Subset columns
    )


swot_tidal_wse_df = swot_tidal_wse_df[swot_tidal_wse_df.site_id == 'GCW']
swot_tidal_wse_df = swot_tidal_wse_df.sort_values(by="datetime_EST", ascending=True)


### MAKE INPUTS FOR UTIDE
heights = swot_tidal_wse_df['swot_wse_m_navd_mean'].values
t = swot_tidal_wse_df['datetime_EST'].values


start_time = "2020-09-01 00:00:00"  # Start datetime
end_time = "2025-05-01 00:00:00"    # End datetime
hourly_intervals = pd.date_range(start=start_time, end=end_time, freq="h")



constit_list = ['M2', 'S2', 'N2', 'K1','M4', 'O1']

# Run solver
coef = utide.solve(
    t = t, 
    u = heights, 
    lat=35, # latitude
    # constit = "auto",
    constit = constit_list,
    # order_constit = 'PE',
    method="ols", #'ols' 
    conf_int= 'linear', # 'MC', # 'none',   # Disable confidence interval computation  # SVD does not converge
    Rayleigh_min=1.1,
    trend=False,
    verbose=False,
)


print(coef.keys())


# Reconstruct tide at hourly intervals
tide = utide.reconstruct(hourly_intervals, 
                         coef, 
                         min_SNR = 0.0,  # Include only the constituents with signal-to-noise ratio SNR >= min_SNR.
                        #  min_PE = 1, # Include only the constituents with percent energy PE >= min_PE, where PE is based on the amplitudes in ``coef``.
                         verbose=False)

print(tide.keys())


# Save reconstructed tide from 
outdf = pd.DataFrame({'site_id': 'GCW',
                      'datetime': tide.t_in,
                      'height': tide.h})

outdf.to_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_gcw_utide_reconstructed.csv', index=False)



#%%-----------------------------------------------------------------------
# Plot reconstructed time series

import plotly.graph_objects as go

# Create the figure
fig = go.Figure()


# Add trace for Prediction
fig.add_trace(go.Scatter(
    x=hourly_intervals,
    y=tide.h,
    mode="lines",
    name="Prediction",
    line=dict(color="orange"),
))

# Add Observations as points
fig.add_trace(go.Scatter(
    x=t,
    y=heights,
    mode="markers",  # Only show points (no lines)
    name="Observations",
    marker=dict(color="blue", size=6),  # Customize marker color and size
))

# Update layout
fig.update_layout(
    title="Tidal Data: Observations, Predictions, and Residuals",
    xaxis_title="Time",
    yaxis_title="Tidal Height (Units)",
    xaxis=dict(range=["2023-07-22 00:00:00", "2024-02-15 23:00:00"]),  # Specify start and end limits for x-axis
    height=600, width=1000,  # Adjust figure dimensions
    legend=dict(
        orientation="h",     # Place legend horizontally
        x=0.5,               # Center the legend
        xanchor="center",
        y=1.05,              # Slightly above the plot
        yanchor="bottom"
    )
)

fig.show() # Show the interactive plot


