
#%%-----------------------------------------------------------------------
# EXTREME VALUE ANALYSIS MODELING



def model_return_periods(data):

    from pyextremes import EVA

    # Initialize EVA model
    model = EVA(data)

    # Extract extreme values
    # methods: BM - Block Maxima POT - Peaks Over Threshold
    model.get_extremes(method="BM", block_size="365.2425D")

    # Plot extremes values
    # model.plot_extremes()

    # NOTE:  This Emcee version works; but MLE generates errors
    model.fit_model(model='Emcee', n_walkers=500, n_samples=1000)

    summary = model.get_summary(
        return_period=[1, 2, 5, 10, 25, 50, 100],
        return_period_size="365.2425D",
        alpha=0.95)

    # Plot diagnostic plots
    model.plot_diagnostic(alpha=0.95)

    return summary








#%% Get DATA --------------------------------------

site_id = 'GCW'

import pandas as pd

# NOAA gauge tide measurement
gauge_df = (
    pd.read_csv('../../output/results/tide_gauges/noaa_coops_tide_gauges.csv', low_memory=False, dtype= {'wse_m': 'float'}) 
    .query("site_id == @site_id")
    .rename(columns={'wse_m':'gauge_wse_m'})
    .assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce'))
    .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize('UTC-04:00'))
    .sort_values(by='datetime_LST')
    .assign(dateindices = lambda x: pd.Categorical(x.datetime_LST.values).codes) # Add column of date indices
    .loc[:, ['dateindices', 'datetime_LST', 'site_id', 'gauge_wse_m']]
    )

# NOAA Annapolis harmonics
gauge_harm_df = (
    pd.read_csv('../../data/tide_gauges/noaa_coops/predictions/swe_noaa_coops_GCW_8575512.csv')
    .assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce'))
    .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize("UTC").dt.tz_convert('UTC-04:00'))
    )


# Reconstruction
rcstr_df = (
    pd.read_csv(f'../../output/results/reconstr_wse/{site_id}_nearshore_wse_reconstr.csv')
    .query("unit_id == 11")  # Subset unit to one of GCREW  (id=11)
    .assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce'))
    # .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize('UTC-04:00'))
    )


# Weir/Sonde
weir_depth = (
    pd.read_csv("../../data/sondes/GCW/weir_exotable/GCReW_weir_exo.csv")
    .assign(timestamp_local_hr = lambda x: pd.to_datetime(x['timestamp_local_hr'], errors='coerce'))
    .assign(timestamp_local_hr = lambda x: x['timestamp_local_hr'].dt.tz_localize('UTC-04:00'))
    .assign(depth_m_anomaly=lambda d: d["depth_m_anomaly"] + 0.1)
    )

#%%-------------------------------------
from datetime import datetime
import pytz
eastern = pytz.timezone('US/Eastern')
start_date = eastern.localize(datetime(2020, 6, 1))
end_date   = eastern.localize(datetime(2025, 7, 1))
# end_date   = eastern.localize(datetime(2023, 6, 7))


# Crop to same period
gauge_df = gauge_df.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
rcstr_df = rcstr_df.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
weir_depth = weir_depth.query("(timestamp_local_hr > @start_date) & (timestamp_local_hr <= @end_date)")



#%% Run exceedence curve  -----------------------------------------------



#%%   EXCEEDENCE CURVE --------------------

import numpy as np
import statsmodels.api as sm

def exceedance_statsmodels(values):

    x = np.asarray(values)
    x = x[~np.isnan(x)]

    ecdf = sm.distributions.ECDF(x)
    x_sorted = np.sort(x)

    # non-exceedance = ECDF(x)
    p_non_exc = ecdf(x_sorted)
    p_exc = 1 - p_non_exc

    return x_sorted, p_exc



# Get ECDF Exceedence
gauge_sorted, gauge_p_exc = exceedance_statsmodels(gauge_df['gauge_wse_m'])
rcstr_sorted, rcstr_p_exc = exceedance_statsmodels(rcstr_df['reconstructed_wse'])
weir_sorted, weir_p_exc   = exceedance_statsmodels(weir_depth['depth_m_anomaly'])



# ------------------ 3. Plot exceedance curve with Plotly ------------------

import numpy as np
import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        y=gauge_sorted,
        x=gauge_p_exc,
        mode="lines",
        line=dict(color="blue"),
        name="NOAA gauge - Empirical exceedance"))

fig.add_trace(
    go.Scatter(
        y=rcstr_sorted,
        x=rcstr_p_exc,
        mode="lines",
        line=dict(color="red"),
        name="SWOT Reconstruction - Empirical exceedance"))

fig.add_trace(
    go.Scatter(
        y=weir_sorted,
        x=weir_p_exc,
        mode="lines",
        line=dict(color="black"),
        name="GCReW weir - Empirical exceedance"))


fig.update_xaxes(
    title="Exceedance probability (%)",
    showline=True,
    autorange="reversed",
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=5,
    showgrid=True,
    gridcolor="lightgray",
    gridwidth=0.5,
)

# Reverse y-axis so high exceedance percentages are at the top (common in hydrology)
fig.update_yaxes(
    title="Water surface elevation (m; NAVD88)",

    showline=True,
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=5,
    showgrid=True,
    gridcolor="lightgray",
    gridwidth=0.5,
)

fig.update_layout(
    title="Full Distribution Empirical Exceedance Curve",
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=80, r=40, t=80, b=60),
)

fig.show()


fig.write_image("../../output/figures/reconstruct_wse/ts/ecdf_exceedanc_GCW_2023-2025.png", 
                        width=800, height=600, scale=4)





#########################################
######### Peak over threshold

import numpy as np
import plotly.graph_objects as go
from scipy.stats import genpareto


def compute_pot_exceedence(data):

    data = data[~np.isnan(data)] 

    # ------------------ 2. Choose threshold and get exceedances ------------------
    # threshold = np.quantile(data, 0.95)  # 95th percentile threshold (example)

    threshold = 0.24  # Use elevation of marsh as threshold
    exceedances = data[data > threshold] - threshold  # y = x - u
    exceedances = np.sort(exceedances)
    n_exc = len(exceedances)

    # Empirical exceedance probability among exceedances:
    # for ordered exceedances y_(1) <= ... <= y_(n_exc),
    # P(Y > y_(k)) ≈ (n_exc - k + 1) / (n_exc + 1)
    ranks = np.arange(1, n_exc + 1)
    p_exc = (n_exc - ranks + 1) / (n_exc + 1)

    # ------------------ 3. Fit GPD to exceedances ------------------
    # SciPy's genpareto: shape=c, loc, scale
    # We fit to exceedances (already shifted by threshold), so loc ~ 0
    c_hat, loc_hat, scale_hat = genpareto.fit(exceedances, floc=0)  # force loc=0

    # ------------------ 4. Build a GPD probability axis (x) ------------------
    # For a "GPD probability axis", the axis coordinate uses the inverse CDF of the fitted GPD.
    # We want axis coordinate corresponding to non-exceedance of Y: F_Y(y) = P(Y <= y) = 1 - p_exc
    p_non_exc = 1 - p_exc

    # x_axis_coord: GPD quantile corresponding to the non-exceedance prob
    x_axis_coord = genpareto.ppf(p_non_exc, c=c_hat, loc=loc_hat, scale=scale_hat)

    return(exceedances, x_axis_coord)

    # ------------------ 5. Define ticks as exceedance probabilities ------------------
    # Choose exceedance probabilities (conditional on exceeding threshold) for tick labels
    # p_exc_ticks = np.array([0.99, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01])  # fractions
    # p_non_exc_ticks = 1 - p_exc_ticks


    # Map these to GPD quantiles for axis coordinates
    # x_tick_vals = genpareto.ppf(p_non_exc_ticks, c=c_hat, loc=loc_hat, scale=scale_hat)
    # x_tick_labels = [f"{p*100:.1f}%" for p in p_exc_ticks]  # label in % exceedance




# Get ECDF Exceedence
gauge_exceedances, gauge_x_axis_coord = compute_pot_exceedence(gauge_df['gauge_wse_m'])
rcstr_exceedances, rcstr_x_axis_coord = compute_pot_exceedence(rcstr_df['reconstructed_wse'])
weir_exceedances, weir_x_axis_coord   = compute_pot_exceedence(weir_depth['depth_m_anomaly'])
gauge_harm_exceedances, gauge_harm_x_axis_coord   = compute_pot_exceedence(gauge_harm_df['wse_m'])



threshold = 0.24 

# ------------------ 6. Plot with Plotly ------------------
fig = go.Figure()

# Empirical exceedance of exceedances on GPD probability axis
fig.add_trace(
    go.Scatter(
        x=gauge_x_axis_coord,  
        y=threshold + gauge_exceedances, 
        mode="markers",
        marker=dict(size=5, color="blue"),
        name="NOAA Gauge"))

fig.add_trace(
    go.Scatter(
        x=rcstr_x_axis_coord,         
        y=threshold + rcstr_exceedances, 
        mode="markers",
        marker=dict(size=5, color="red"),
        name="Reconstruction"))

fig.add_trace(
    go.Scatter(
        x=weir_x_axis_coord,           # GPD probability axis
        y=threshold + weir_exceedances,  # back to original scale: x = u + y
        mode="markers",
        marker=dict(size=5, color="black"),
        name="Weir"))

fig.add_trace(
    go.Scatter(
        x=gauge_harm_x_axis_coord,           # GPD probability axis
        y=threshold + gauge_harm_exceedances,  # back to original scale: x = u + y
        mode="markers",
        marker=dict(size=5, color="#41d424"),
        name="Gauge harmonics"))


if 0:
    # Optional: add fitted GPD curve in exceedance space
    y_model = np.linspace(exceedances.min(), exceedances.max(), 200)
    p_model_non_exc = genpareto.cdf(y_model, c=c_hat, loc=loc_hat, scale=scale_hat)
    x_model = genpareto.ppf(p_model_non_exc, c=c_hat, loc=loc_hat, scale=scale_hat)

    fig.add_trace(
        go.Scatter(
            x=x_model,
            y=threshold + y_model,    # back to original scale
            mode="lines",
            line=dict(color="red"),
            name="GPD-based axis reference"
        )
    )

# X-axis: GPD probability axis labeled by exceedance %
fig.update_xaxes(
    title="Exceedance probability (%) on GPD probability axis",
    tickvals=x_tick_vals,      # in GPD-quantile space
    ticktext=x_tick_labels,    # shown as % exceedance
    showline=True,
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=5,
    showgrid=True,
    gridcolor="lightgray",
    gridwidth=0.5,
)

# Y-axis: original variable
fig.update_yaxes(
    title="Water surface elevation (m; NAVD88)",
    showline=True,
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=5,
    showgrid=True,
    gridcolor="lightgray",
    gridwidth=0.5,
)

fig.update_layout(
    title=f"Empirical Exceedance above marsh elevation ({threshold:.2f}m) over 2020-2025",
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=80, r=40, t=80, b=60),
)

fig.show()


fig.write_image("../../output/figures/reconstruct_wse/ts/exceedance_pot_gdp_marshelev_GCW_2023-2025.png", 
                        width=800, height=600, scale=4)







#################################
#### EXTREME VALUE PLOT ON ANNUAL MAXIMA

import numpy as np
import plotly.graph_objects as go
from scipy.stats import genextreme

# ------------------ 1. Example: GEV fit to maxima ------------------
np.random.seed(0)
shape_true = -0.1
loc_true   = 0.0
scale_true = 1.0
n_years    = 50

maxima = genextreme.rvs(c=shape_true, loc=loc_true, scale=scale_true, size=n_years)
c_hat, loc_hat, scale_hat = genextreme.fit(maxima)

# ------------------ 2. Build GEV probability axis on X ------------------
y_sorted = np.sort(maxima)
n = len(y_sorted)
ranks = np.arange(1, n + 1)
p = ranks / (n + 1)  # non-exceedance

# GEV probability-axis coordinate for each empirical point
x_axis_coord = genextreme.ppf(p, c=c_hat, loc=loc_hat, scale=scale_hat)

# Order points by x so markers follow the fitted line visually
order = np.argsort(x_axis_coord)
x_axis_coord = x_axis_coord[order]
y_sorted = y_sorted[order]

# ------------------ 3. Define ticks for x-axis at equal return-period steps ------------------
# Choose a range of return periods (in years) and step
T_min, T_max, T_step = 1.1, 100, 2  # e.g. 1.1, 3.1, 5.1, ...
# T_ticks = np.arange(T_min, T_max + T_step, T_step)
T_ticks = np.array([1.1, 2, 5, 10, 15, 20, 25, 50, 100])

# Convert to non-exceedance probabilities: p = 1 - 1/T
p_ticks = 1 - 1 / T_ticks
# Map to GEV-quantile coordinates for x-axis
x_tick_vals = genextreme.ppf(p_ticks, c=c_hat, loc=loc_hat, scale=scale_hat)

# Label every Nth tick to avoid clutter (e.g., every 5th)
label_every = 5
x_tick_labels = []
for i, T in enumerate(T_ticks):
    if i % label_every == 0:
        x_tick_labels.append(f"{T:.0f} yr")
    else:
        x_tick_labels.append("")  # unlabeled, but still gridlines

# ------------------ 4. Plot with Plotly ------------------
fig = go.Figure()

# Empirical annual maxima
fig.add_trace(
    go.Scatter(
        x=x_axis_coord,
        y=y_sorted,
        mode="markers",
        marker=dict(size=8, color="blue"),
        name="Annual maxima"
    )
)

# Fitted GEV line
y_model = np.linspace(y_sorted.min(), y_sorted.max(), 200)
p_model = genextreme.cdf(y_model, c=c_hat, loc=loc_hat, scale=scale_hat)
x_model = genextreme.ppf(p_model, c=c_hat, loc=loc_hat, scale=scale_hat)

fig.add_trace(
    go.Scatter(
        x=x_model,
        y=y_model,
        mode="lines",
        line=dict(color="red"),
        name="Fitted GEV"
    )
)
# X-axis: GEV probability axis with equal return-period steps (grid at each tick)
fig.update_xaxes(
    title="GEV probability axis (return period)",
    tickvals=x_tick_vals,
    ticktext=x_tick_labels,
    showline=True,
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=5,
    showgrid=True,
    gridcolor="lightgray",
    gridwidth=0.5,
)

# Y-axis: equal value intervals via dtick
# Pick dtick based on your data spread; here we use 0.5 arbitrarily
fig.update_yaxes(
    title="Maxima (e.g. tidal elevation)",
    showline=True,
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=5,
    showgrid=True,
    gridcolor="lightgray",
    gridwidth=0.5,
    dtick=0.5,
)

fig.update_layout(
    title="GEV Probability Plot (x-axis in GEV quantile space)",
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=80, r=40, t=80, b=60),
)

fig.show()

