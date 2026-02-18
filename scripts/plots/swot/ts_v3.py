

import pandas as pd
import plotly.figure_factory as ff
import numpy as np


#%%-----------------------------------------------------------------------
# GET SWOT RECONSTRUCTED WSE DATA

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

swot_tidal_wse_df = swot_tidal_wse_df[['datetime_EST', 'swot_wse_m_navd_mean']]



#%%-----------------------------------------------------------------------
# GET SWOT RECONSTRUCTED WSE DATA

# Prep input data
swot_reconst_wse_df =  pd.read_csv("../../output/results/swot/nearshore_wse_reconstr/swot_wse_reconstructed_GCW_v01.csv")
                                # index_col=0,  parse_dates=True)

swot_reconst_wse_df = swot_reconst_wse_df[['datetime_LST', 'reconstructed_wse']]

# Parse dates
swot_reconst_wse_df['datetime_LST'] = pd.to_datetime(swot_reconst_wse_df['datetime_LST'], errors='coerce')


swot_reconst_wse_df['datetime_LST'] = swot_reconst_wse_df['datetime_LST'].dt.tz_convert(None)





# Set date as index
# swot_tidal_wse_df.set_index('datetime_LST', inplace=True)

# swot_tidal_wse_df = swot_tidal_wse_df.squeeze()  # To Series
# data=swot_tidal_wse_df


#%%-----------------------------------------------------------------------
# PREPARE GAUGE WSE DATA

# Read in Buoy data
boundary_wl_df = pd.read_csv('../../output/results/tide_gauges/noaa_coops_tide_gauges.csv',  
                             low_memory=False, dtype= {'wse_m': 'float'}) 

boundary_wl_df = ( boundary_wl_df
    .rename(columns={'wse_m':'gauge_wse_m'})
    .assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce'))  # Convert datatype
    .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize('UTC-04:00'))
    .sort_values(by='datetime_LST')
    .assign(dateindices = lambda x: pd.Categorical(x.datetime_LST.values).codes) # Add column of date indices
    .loc[:, ['dateindices', 'datetime_LST', 'site_id', 'gauge_wse_m']]
    )

# Subset to site of interest
boundary_wl_df = boundary_wl_df[boundary_wl_df['site_id']=='GCW']
# Select relevant columns
boundary_wl_df = boundary_wl_df[['datetime_LST', 'gauge_wse_m']]
# Parse dates
boundary_wl_df['datetime_LST'] = pd.to_datetime(boundary_wl_df['datetime_LST'], errors='coerce')
# Set date as index
# boundary_wl_df.set_index('datetime_LST', inplace=True)
# # Convert to Series
# boundary_wl_df = boundary_wl_df.squeeze()  

boundary_wl_df['datetime_LST'] = boundary_wl_df['datetime_LST'].dt.tz_convert(None)



#%%-----------------------------------------------------------------------
# PREP GCREW WEIR DEPTH DATA

# Load and preprocess the weir depth data
weir_depth = (
    pd.read_csv("../../data/sondes/GCW/weir_exotable/GCReW_weir_exo.csv")
    .assign(datetime_LST = lambda x: pd.to_datetime(x['timestamp_local_hr'], errors='coerce'))
    .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize('UTC-04:00'))
)

# Subset to site of interest
# weir_depth = weir_depth[weir_depth['site_id']=='GCW']
# Select relevant columns
weir_depth = weir_depth[['datetime_LST', 'depth_m_anomaly']]
# Parse dates
weir_depth['datetime_LST'] = pd.to_datetime(weir_depth['datetime_LST'], errors='coerce')
# Set date as index
# weir_depth.set_index('datetime_LST', inplace=True)
# Convert to Series
# weir_depth = weir_depth.reset_index(drop=False) #.squeeze()

weir_depth['datetime_LST'] = weir_depth['datetime_LST'].dt.tz_convert(None)




# Add histogram data
utide = pd.read_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_gcw_utide_reconstructed.csv')
utide['datetime'] = pd.to_datetime(utide['datetime'], errors='coerce')



# Combine all into a single DataFrame for plotting

start_time = "2022-10-10 00:00:00"
end_time = "2025-10-12 23:00:00"

# Create the datetime range
hourly_intervals = pd.date_range(start=start_time, end=end_time, freq="h")


all_wse = pd.DataFrame({'hourly_intervals':hourly_intervals})


# Outer join dataframes
all_wse = pd.merge(all_wse, utide, left_on="hourly_intervals", right_on='datetime', how="left") 
all_wse = pd.merge(all_wse, boundary_wl_df, left_on="hourly_intervals", right_on='datetime_LST', how="left") 
all_wse = pd.merge(all_wse, swot_tidal_wse_df, left_on="hourly_intervals", right_on='datetime_EST', how="left") 
all_wse = pd.merge(all_wse, swot_reconst_wse_df, left_on="hourly_intervals", right_on='datetime_LST', how="left") 
all_wse = pd.merge(all_wse, weir_depth, left_on="hourly_intervals", right_on='datetime_LST', how="left") 




#%%-----------------------------------------------------------------------
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Create plot with Plotly express
fig = px.line(template="simple_white")



# Add the points with Y-values from the DataFrame
fig.add_trace(go.Scatter(
    x=all_wse.hourly_intervals,   
    y=all_wse.depth_m_anomaly,  
    name='GCReW weir',
    line=dict(
        color='black',  
        width=2  ), 
))

# Add the points with Y-values from the DataFrame
fig.add_trace(go.Scatter(
    x=all_wse.hourly_intervals,           
    y=all_wse.gauge_wse_m,        
    name='NOAA Gauge', 
    line=dict(
        color='blue',  # Line color
        width=1   ),     # Line width
    
))

# Add the points with Y-values from the DataFrame
fig.add_trace(go.Scatter(
    x=all_wse.hourly_intervals,               # X-values: return periods from DataFrame
    y=all_wse.height,               # Y-values: elevations from DataFrame
    # mode='markers',           
    name='UTide',  
    line=dict(
        color='green',  # Line color
        width=1  ),      # Line width
))


# Reconstructed SWOT
fig.add_trace(go.Scatter(
    x=all_wse.hourly_intervals,               
    y=all_wse.reconstructed_wse,              
    name='Reconstructed SWOT',
    line=dict(color='red', width=1),        # Line width
))


# Add the points with Y-values from the DataFrame
fig.add_trace(go.Scatter(
    x=all_wse.hourly_intervals,              
    y=all_wse.swot_wse_m_navd_mean,              
    mode='markers',
    marker=dict(color='red', size=10),      
    name='SWOT SWE',  
))

# Update layout
fig.update_layout(
    # title="Tidal Data: Observations, Predictions, and Residuals",
    # xaxis_title="Time",
    yaxis_title="Surface Water Elevation (m)",
    xaxis=dict(range=["2023-08-01 00:00:00", "2023-09-15 23:00:00"]),  # Specify start and end limits for x-axis
    yaxis=dict(range=[-0.6, 0.6]),  # Specify start and end limits for x-axis
    height=600, width=1000,  # Adjust figure dimensions
    # xaxis_rangeslider_yaxis_rangemode="auto",
    legend=dict(
        orientation="h",     # Place legend horizontally
        x=0.5,               # Center the legend
        xanchor="center",
        y=1.05,              # Slightly above the plot
        yanchor="bottom"
    )
)

# Show the plot
fig.show()

import plotly.io as pio
#save a figure of 300dpi, with 5 inches, and  height 3inches
pio.write_image(fig, 
                "../../output/figures/swot/ts/GCW_wse_ts_v07.png", 
                width=3*250, height=2*250, scale=10)






#-----------------------------------------------------------------------
# Group data together
hist_data = [utide.height.dropna(), 
             weir_depth.depth_m_anomaly.dropna(), 
             boundary_wl_df.gauge_wse_m.dropna(), 
             swot_reconst_wse_df.reconstructed_wse.dropna()]

group_labels = ['UTide harmonic reconstruction (height)', 'GCRew Weir (Depth)', 'NOAA Annapolis gauge (WSE)', 'Reconstructed SWOT (WSE)']


colors=['green', 'black', 'blue', 'red']

# Create distplot with custom bin_size
fig = ff.create_distplot(hist_data, group_labels, bin_size=.2, colors=colors, 
                         show_hist=False, show_rug=False)

fig.update_layout(
    # title=dict(
    #     text="Plot Title"
    # ),
    xaxis=dict(
        title=dict(
            text="Water Surface Elevation (m)"
        )
    ),
    yaxis=dict(
        title=dict(
            text="Density"
        )
    )
)

fig.show()

pio.write_image(fig, 
                "../../output/figures/swot/ts/GCW_wse_density_v07.png", 
                width=5*250, height=2*250, scale=10)




