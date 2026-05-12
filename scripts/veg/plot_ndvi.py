

import pandas as pd
import plotly.express as px

# assume your dataframe is called df

# 1. Extract date from 'system:index'
#    Your pattern: e.g. "1_1_1_1_LT04_014033_19821213_00000000000000000007_0"
#    The date is the part after the 4th underscore, length 8 (YYYYMMDD)
def extract_date(s):
    # split on '_' and find the part that looks like a date
    parts = s.split('_')
    for p in parts:
        if len(p) == 8 and p.isdigit():
            return pd.to_datetime(p, format='%Y%m%d')
    return pd.NaT



# Read in CSV of NDVI values
df =pd.read_csv('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/swot_tidal_forcing/data/ndvi/syoptic_ndvi_v01 - syoptic_ndvi_v01.csv')

# 
df['date'] = df['system:index'].apply(extract_date)

# 2. (Optional) sort by date
df = (df.sort_values('date')
      .query("zone_id in ['UP', 'TR', 'W']")  # filter to zones of interest
    )

cutoff = pd.Timestamp('1990-01-01')
df = df.query('date > @cutoff')

df = df[['date', 'NDVI', 'zone_id', 'site_id']]


#%%  3. Plot NDVI over time, per site, colored by zone -------------------------------------------------------
fig = px.line(
    df,
    x='date',
    y='NDVI',
    color='zone_id',         # UP / TR / W / OW
    facet_col='site_id',     # one panel per site (e.g., MSM, etc.)
    facet_col_wrap=1,        # wrap panels if you have many sites
    # markers=True,            # points on lines
    facet_row_spacing=0.02,
    # labels={'site_id': ''}   # removes the "site_id =" prefix in facet labels
)


# Remove "site_id =" and keep only the value
for ann in fig.layout.annotations:
    if 'site_id=' in ann.text:
        ann.text = ann.text.split('=')[1].strip()


# Add black axis lines for all x and y axes
fig.update_xaxes(
    showline=True,       # draw axis line
    linecolor='black',   # axis line color
    linewidth=1,         # thickness
    mirror=False,        # set True if you want the line on top as well
    # showticklabels=True,
    ticks="outside",
    ticklen=5,
    tickwidth=1,
    tickcolor="black"
)

fig.update_yaxes(
    showline=True,
    linecolor='black',
    linewidth=1,
    mirror=False,        # set True if you want the line on top as well
    # showticklabels=True,
    ticks="outside",
    ticklen=5,
    tickwidth=1,
    tickcolor="black"
)

# 4. Improve layout
fig.update_layout(
    # title='NDVI over time by zone and site',
    xaxis_title='Date',
    yaxis_title='NDVI',
    plot_bgcolor='white',
    xaxis_showgrid=False,
    yaxis_showgrid=False
    # legend_title='Zone'
)


# 5. If you want to guarantee a specific zone order (UP, TR, WET/OW, etc.),
#    you can set category orders:
fig.update_xaxes(matches='x')   # share x-axis scale across facets
# fig.update_yaxes(matches='y')   # share y-axis scale across facets

fig.show()

from scripts.config import FIG_DIR
fig.write_image(FIG_DIR/"synoptic_ndvi_timeseries.png", width=1000, height=1600, scale=2)




#%% COMPUTE ANOMALIES  ------------------------


#!/usr/bin/env python3
"""
Compute NDVI anomalies by fitting a harmonic (Fourier) seasonal model
per site_id–zone_id and subtracting the fitted seasonal cycle.

Requirements:
  - pandas
  - numpy
"""

import numpy as np
import pandas as pd


# ----------------------------------------------------------------------
# 2. Harmonic fit helper
# ----------------------------------------------------------------------
def fit_harmonic_cycle(group, period=365.25, n_harmonics=2):
    """
    Fit a harmonic seasonal model to NDVI in one group (e.g., one site_id–zone_id).

    Parameters
    ----------
    group : pandas.DataFrame
        Must have 'doy' and 'NDVI' columns.
    period : float
        Seasonal period in days (365 or 365.25).
    n_harmonics : int
        Number of harmonics to include (1 = annual only, 2 = annual + semi-annual, etc.)

    Returns
    -------
    group : pandas.DataFrame
        Original group with added columns:
          - NDVI_clim : fitted seasonal cycle
          - NDVI_anom : NDVI - NDVI_clim
    """
    # Ensure numeric arrays
    t = group['doy'].values.astype(float)
    y = group['NDVI'].values.astype(float)

    # Drop rows with missing NDVI (optional; you could also handle differently)
    valid = np.isfinite(y)
    if valid.sum() < (2 * n_harmonics + 1):
        # Not enough data to reliably fit; set climatology and anomalies to NaN
        group['NDVI_clim'] = np.nan
        group['NDVI_anom'] = np.nan
        return group

    t_valid = t[valid]
    y_valid = y[valid]

    # Build design matrix: constant + harmonics
    # Columns: [1, sin(2πt/T), cos(2πt/T), sin(4πt/T), cos(4πt/T), ...]
    cols = [np.ones_like(t_valid)]  # intercept
    for k in range(1, n_harmonics + 1):
        cols.append(np.sin(2 * np.pi * k * t_valid / period))
        cols.append(np.cos(2 * np.pi * k * t_valid / period))
    X = np.column_stack(cols)

    # Fit least squares: y = X @ beta
    beta, _, _, _ = np.linalg.lstsq(X, y_valid, rcond=None)

    # Evaluate fitted model for all rows in the group (including missing if any)
    # Rebuild X_full for all t
    cols_full = [np.ones_like(t)]
    for k in range(1, n_harmonics + 1):
        cols_full.append(np.sin(2 * np.pi * k * t / period))
        cols_full.append(np.cos(2 * np.pi * k * t / period))
    X_full = np.column_stack(cols_full)

    y_fit = X_full @ beta

    group['NDVI_clim'] = y_fit
    group['NDVI_anom'] = group['NDVI'] - group['NDVI_clim']
    return group


#%% 
import numpy as np

# Ensure datetime
df['date'] = pd.to_datetime(df['date'])

# Day-of-year (time-of-year index)
df['doy'] = df['date'].dt.dayofyear

# Optional: sort to make later plotting easier
df = df.sort_values(['site_id', 'zone_id', 'date'])

# Fit harmonic seasonal model per site_id–zone_id
# Change n_harmonics to 1, 2, 3 depending on how complex you want the seasonal shape
df_anom = (
    df
    .groupby(['site_id', 'zone_id'], group_keys=False)
    .apply(fit_harmonic_cycle, period=365.25, n_harmonics=2)
)

# Optional: sort to make later plotting easier
df_anom = df_anom.sort_values(['site_id', 'zone_id', 'date'])



#%% 3. Plot NDVI anomaly over time, per site, colored by zone
fig = px.line(
    df_anom,
    x='date',
    y='NDVI_anom',
    color='zone_id',         # UP / TR / W / OW
    facet_col='site_id',     # one panel per site (e.g., MSM, etc.)
    facet_col_wrap=1,        # wrap panels if you have many sites
    # markers=True,            # points on lines
    facet_row_spacing=0.02,
    # labels={'site_id': ''}   # removes the "site_id =" prefix in facet labels
)


# Remove "site_id =" and keep only the value
for ann in fig.layout.annotations:
    if 'site_id=' in ann.text:
        ann.text = ann.text.split('=')[1].strip()

# Add black axis lines for all x and y axes
fig.update_xaxes(
    showline=True,       # draw axis line
    linecolor='black',   # axis line color
    linewidth=1,         # thickness
    mirror=False,        # set True if you want the line on top as well
    # showticklabels=True,
    ticks="outside",
    ticklen=5,
    tickwidth=1,
    tickcolor="black"
)

fig.update_yaxes(
    showline=True,
    linecolor='black',
    linewidth=1,
    mirror=False,        # set True if you want the line on top as well
    # showticklabels=True,
    ticks="outside",
    ticklen=5,
    tickwidth=1,
    tickcolor="black"
)

# 4. Improve layout
fig.update_layout(
    # title='NDVI over time by zone and site',
    xaxis_title='Date',
    yaxis_title='NDVI',
    plot_bgcolor='white',
    xaxis_showgrid=False,
    yaxis_showgrid=False
    # legend_title='Zone'
)


# 5. If you want to guarantee a specific zone order (UP, TR, WET/OW, etc.),
#    you can set category orders:
fig.update_xaxes(matches='x')   # share x-axis scale across facets
# fig.update_yaxes(matches='y')   # share y-axis scale across facets


fig.add_hline(y=0, line=dict(color='black', width=0.2))
fig.update_traces(line=dict(width=1.6))  # e.g., 0.5, 1, 1.5; default is ~2

fig.show()



from scripts.config import FIG_DIR
fig.write_image(FIG_DIR/"synoptic_ndvi_anomaly_timeseries.png", width=1000, height=1600, scale=2)

