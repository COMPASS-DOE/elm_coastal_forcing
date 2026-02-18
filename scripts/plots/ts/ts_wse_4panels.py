
#%%-----------------------------------------------------------
### PLOT THE INTERPOLATED TIME SERIES


if __name__ == '__main__':

import pandas as pd


site_id='GCW'



#%%  Get SWOT water elevation   -----------------------------------------------------------------------


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


# NOAA subordinate harmonics
rhode_river = (
    pd.read_csv('../../data/tide_gauges/noaa_coops/predictions/swe_noaa_coops_GCW_8575787.csv')
    .assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce'))
    .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize("UTC").dt.tz_convert('UTC-04:00'))
    )


# Get SWOT tidal wse for only nearshore unit sites
swot_df = (
    pd.read_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_nearshore_v02.csv')
    .query("unit_id == 11")  # Subset unit to one of GCREW  (id=11)
    .rename(columns={'wse_mean':'swot_wse_m_navd_mean', 'wse_std':'swot_wse_m_navd_std'})    # Rename columns
    .assign(date = lambda x: pd.to_datetime(x['date'], errors='coerce'))           # Convert datatype
    .assign(date = lambda x: x['date'].dt.round('h'))                              # Round to hour
    .assign(date = lambda x: x['date'].dt.tz_localize('UTC-00:00'))                # If date not localized, localize to GMT
    .assign(datetime_EST = lambda x: x['date'].dt.tz_convert('UTC-04:00'))         # Convert to local time
    .loc[:, ['site_id', 'datetime_EST', 'swot_wse_m_navd_mean', 'swot_wse_m_navd_std']]      # Subset columns
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



#%%-------------------------------------------------------------------------------
#  Get synoptic groundwater wells data
from datetime import timedelta

gw_depth_df = (
    pd.read_csv('../../output/results/sensor_wells/synoptic_gw_elev_v4.csv')
    .assign(TIMESTAMP_hourly = lambda x: pd.to_datetime(x['TIMESTAMP_hourly'], errors='coerce'))
    .assign(TIMESTAMP_hourly = lambda d: d["TIMESTAMP_hourly"] + timedelta(hours=4))
    .assign(TIMESTAMP_hourly = lambda x: x['TIMESTAMP_hourly'].dt.tz_localize('UTC-04:00'))
    # .assign(TIMESTAMP_hourly = lambda x: x['TIMESTAMP_hourly'].dt.tz_localize("UTC").dt.tz_convert('UTC-04:00'))
    .query("site_id == 'GCW'") 
    .assign(gw_elev_m = lambda d: d["elev_m"] + d["wl_below_surface_m"])
    )

gw_depth_df.TIMESTAMP_hourly



#%% ---------------------------------------------------


from datetime import datetime
import pytz
eastern = pytz.timezone('US/Eastern')
start_date = eastern.localize(datetime(2023, 6, 1))
end_date   = eastern.localize(datetime(2023, 7, 1))
# end_date   = eastern.localize(datetime(2023, 6, 7))


# Crop to same period
gauge_df = gauge_df.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
swot_df = swot_df.query("(datetime_EST > @start_date) & (datetime_EST <= @end_date)")
rcstr_df = rcstr_df.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
weir_depth = weir_depth.query("(timestamp_local_hr > @start_date) & (timestamp_local_hr <= @end_date)")
rhode_river = rhode_river.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
gauge_harm_df = gauge_harm_df.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
# Wells

gw_depth_df = gw_depth_df.query("(TIMESTAMP_hourly > @start_date) & (TIMESTAMP_hourly <= @end_date)")




#%%   fucntion plotting -----------------
def make_wse_4panel_plot(gauge_df, rcstr_df, swot_df, weir_depth):

    import numpy as np
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    fig = make_subplots(rows=2, cols=2,
                    shared_xaxes=True,
                    shared_yaxes=True,
                    vertical_spacing=0.1,
                    horizontal_spacing=0.04,
                    subplot_titles= ("NOAA Annapolis gauge", 
                                     "NOAA harmonics", 
                                     "SWOT obs & reconstruction", 
                                     "GCReW weir"))

    # ---- Panel 1 ----
    fig.add_trace(
        go.Scatter(
            x=gauge_df['datetime_LST'], y=gauge_df['gauge_wse_m'],
            mode='lines', line=dict(color='royalblue'),
            showlegend=False),
        row=1, col=1)

    # ---- Panel 2 ----
    fig.add_trace(

    # Annapolis Harmonic
    go.Scatter(
        x=gauge_harm_df['datetime_LST'], y=gauge_harm_df['wse_m'],
        mode='lines', line=dict(color='green'),
        showlegend=False),
    row=1, col=2)

    # Add subordinate station
    fig.add_trace(
    go.Scatter(
        x=rhode_river['datetime_LST'], y=rhode_river['wse_m'],
        mode='lines', line=dict(color='#7cff54'),
        showlegend=False),
    row=1, col=2)


    # ---- Panel 3 ----
    fig.add_trace(
    go.Scatter(
        x=rcstr_df['datetime_LST'], y=rcstr_df['reconstructed_wse'],
        mode='lines', line=dict(color='red'),
        showlegend=False),
    row=2, col=1)


    # Add SWOT observation
    fig.add_trace(
        go.Scatter(
            x=swot_df['datetime_EST'],
            y=swot_df['swot_wse_m_navd_mean'],
            mode="markers",
            marker=dict(color="red", size=6, symbol="circle", 
                        line=dict(color="black", width=2)),
            name="SWOT",
            showlegend=False),
        row=2, col=1)


    # ---- Panel 4 ----
    fig.add_trace(
    go.Scatter(
        x=weir_depth['timestamp_local_hr'], y=weir_depth['depth_m_anomaly'],
        mode='lines', line=dict(color='black'),
        showlegend=False),
    row=2, col=2)


    fig.update_layout(
        height=600,
        width=900,
        margin=dict(l=80, r=40, t=40, b=40),
        template="plotly_white",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(nticks=5, tickmode='auto')) 
        
    # Force axis lines to show on all subplots
    fig.update_xaxes(
        showline=True,
        linecolor="black",
        linewidth=1,
        ticks="outside",
        tickcolor="black",
        ticklen=4
    )

    fig.update_yaxes(
        showline=True,
        linecolor="black",
        linewidth=1,
        ticks="outside",
        tickcolor="black",
        ticklen=4,
        showgrid=True,
        gridcolor="lightgray",
        gridwidth=1,
        range=[-0.4, 1],
        tickmode="array",
        # dtick=0.2
        tickvals=[-0.4, -0.2, 0, .2, 0.4, 0.6, 0.8]
        # nticks= 9
    )

    fig.update_yaxes(title_text= 'Water Surface Elevation\n(m; NAVD88)', row=1, col=1)
    fig.update_yaxes(title_text= 'Water Surface Elevation\n(m; NAVD88)', row=2, col=1)

    fig.show()
    return(fig)



# Call function
fig_4panels = make_wse_4panel_plot(gauge_df, rcstr_df, swot_df, weir_depth)

# Save to file
fig_4panels.write_image("../../output/figures/reconstruct_wse/ts/ts_reconstr_4panels_GCW.png", 
                        width=800, height=600, scale=4)







#%%  Compute Kling Gupta Efficiency  -----------------------------------------------------------------------
from numpy import array
from permetrics.regression import RegressionMetric
# https://permetrics.readthedocs.io/en/latest/pages/regression.html

for i in [gauge_df['gauge_wse_m'], 
          gauge_harm_df['wse_m'],
          rcstr_df['reconstructed_wse']]:
        #   rhode_river['wse_m']]:

    print(i.shape)

    # Set benchmark
    b = weir_depth['depth_m_anomaly'].to_numpy()
    # Set the comparison dataset
    i = i.to_numpy()

    mask = ~np.isnan(b) & ~np.isnan(i)
    b = b[mask] 
    i = i[mask]

    evaluator = RegressionMetric(b, i)    
    evaluator.get_metrics_by_list_names(["KGE", "RMSE"])

    print('KGE: ', evaluator.KGE())
    print('RMSE: ', evaluator.RMSE())
    



# Close up of water level on marsh ---------------------------

from datetime import datetime
import pytz
eastern = pytz.timezone('US/Eastern')
start_date = eastern.localize(datetime(2023, 6, 2))
end_date   = eastern.localize(datetime(2023, 6, 7))
# end_date   = eastern.localize(datetime(2023, 6, 7))


# Crop to same period
gauge_df = gauge_df.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
rcstr_df = rcstr_df.query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)")
weir_depth = weir_depth.query("(timestamp_local_hr > @start_date) & (timestamp_local_hr <= @end_date)")
gw_depth_df = gw_depth_df.query("(TIMESTAMP_hourly > @start_date) & (TIMESTAMP_hourly <= @end_date)")




import plotly.graph_objects as go

fig = go.Figure()

for zone, sub in gw_depth_df.groupby("zone_name"):
    fig.add_trace(
        go.Scatter(
            x=sub["TIMESTAMP_hourly"],
            y=sub["gw_elev_m"], 
            mode="lines",
            line=dict(width=6),
            name= f'{zone} (groundwater well)' ))

fig.add_trace(
go.Scatter(
    x=rcstr_df['datetime_LST'], y=rcstr_df['reconstructed_wse'],
    mode='lines', line=dict(color='red'),
    showlegend=True,
    name= 'SWOT Reconstruction'))

fig.add_trace(
go.Scatter(
    x=weir_depth['timestamp_local_hr'], y=weir_depth['depth_m_anomaly'],
    mode='lines', line=dict(color='black'),
    showlegend=True,
    name= 'GCReW Weir'))

fig.update_layout(
    xaxis_title="",
    yaxis_title="Water level (m;NAVD)",
    template="plotly_white"
)

fig.update_layout(
    height=600,
    width=900,
    margin=dict(l=80, r=40, t=40, b=40),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    yaxis=dict(nticks=5, tickmode='auto')) 
    
# Force axis lines to show on all subplots
fig.update_xaxes(
    showline=True,
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=4
)

fig.update_yaxes(
    showline=True,
    linecolor="black",
    linewidth=1,
    ticks="outside",
    tickcolor="black",
    ticklen=4,
    # showgrid=True,
    # gridcolor="lightgray",
    # gridwidth=1,
)

fig.show()


# Save to file
fig.write_image("../../output/figures/reconstruct_wse/ts/ts_reconstr_gwwells_closeup_GCW.png", 
                        width=800, height=600, scale=4)


