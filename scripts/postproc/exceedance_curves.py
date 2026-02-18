

import pandas as pd

#%%-----------------------------------------------------------------------
# GET SWOT RECONSTRUCTED WSE DATA

# Prep input data
swot_tidal_wse_df =  pd.read_csv("../../output/results/swot/nearshore_wse_reconstr/swot_wse_reconstructed_GCW_v01.csv")
                                # index_col=0,  parse_dates=True)

swot_tidal_wse_df = swot_tidal_wse_df[['datetime_LST', 'reconstructed_wse']]

# Parse dates
swot_tidal_wse_df['datetime_LST'] = pd.to_datetime(swot_tidal_wse_df['datetime_LST'], errors='coerce')

# Set date as index
swot_tidal_wse_df.set_index('datetime_LST', inplace=True)

swot_tidal_wse_df = swot_tidal_wse_df.squeeze()  # To Series

data=swot_tidal_wse_df


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
boundary_wl_df.set_index('datetime_LST', inplace=True)
# Convert to Series
boundary_wl_df = boundary_wl_df.squeeze()  



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
weir_depth.set_index('datetime_LST', inplace=True)
# Convert to Series
weir_depth = weir_depth.squeeze()  




#%%-----------------------------------------------------------------------
#  EXTREME VALUE ANALYSIS
# https://georgebv.github.io/pyextremes/quickstart/


def analyze_extremes(data):

    from pyextremes import get_extremes, get_return_periods

    # Returns the maximum value for each year
    extremes = get_extremes(
        ts=data,
        method="BM",
        block_size="365.2425D",
    )

    # This produces the return period of the annual extreme for each year 
    return_periods = get_return_periods(
        ts=data,
        extremes=extremes,
        extremes_method="BM",
        extremes_type="high",
        block_size="365.2425D",
        return_period_size="365.2425D",
        plotting_position="weibull",
    )

    # Prints the top return periods
    return_periods = return_periods.sort_values("return period", ascending=False)#.head()


#%%-----------------------------------------------------------------------
# EXTREME VALUE ANALYSIS MODELING
from pyextremes import EVA


def model_return_periods(data):

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





#%%-----------------------------------------------------------------------
# Get return periods for SWOT reconstructed WSE and boundary gauge WSE

# Convert return periods to exceedance probabilities
# exceedance_probabilities = [1 / T for T in return_periods]

swot_tidal_wse_rp = model_return_periods(swot_tidal_wse_df)
swot_tidal_wse_rp['source'] = "SWOT Reconstructed WSE at GCReW "

boundary_wl_rp = model_return_periods(boundary_wl_df)
boundary_wl_rp['source'] = "NOAA Annapolis gauge"

weir_depth_rp = model_return_periods(weir_depth)
weir_depth_rp['source'] = "GCReW marsh weir depth"



# Concatenate return period dataframes
rp_df = pd.concat([swot_tidal_wse_rp, boundary_wl_rp, weir_depth_rp], axis=0)
rp_df = rp_df.reset_index()

# rp_df = pd.concat([swot_tidal_wse_rp, boundary_wl_rp], axis=0)



#%%-----------------------------------------------------------------------
# Get elevation of transect zones

ground_elev = pd.read_csv("../../COMPASS_synoptic_sims/data/processed/synoptic_site_pts/synoptic_elev_zone_v4.csv")
ground_elev = ground_elev.query("site_id == 'GCW' and zone_id != 'OW' and zone_id != 'UP'")  # Tidal limit zone


#%%-----------------------------------------------------------------------
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Create plot with Plotly express
fig = px.line(
    data_frame=rp_df,
    x='return period',
    y='return value',
    color='source',
    log_x=True,
    # title='Return Period vs Elevation',
    template="simple_white",
    labels={'return period': 'Return Period (years)', 
            'return value': 'Surface Water Elevation (m; NAVD88)'}
)



# Add the points with Y-values from the DataFrame
fig.add_trace(go.Scatter(
    x=[10,10,10],               # X-values: return periods from DataFrame
    y=ground_elev['elev'],               # Y-values: elevations from DataFrame
    mode='markers',           # Use markers for points
    name='Transect zones',  # Legend name
    marker=dict(
        color='black',         # Point color
        size=8               # Point size
    )
))

# fig.add_scatter(#data_frame=rp_df,
#     x=rp_df['return period'],
#     y=rp_df['return value'],
#     color=rp_df['source'], 
#     mode='lines+markers',
#     # log_x=True, 
#     showlegend=False)

# Update the layout to position the legend at the bottom
fig.update_layout(
    legend=dict(
        orientation="h",  # Optional: for horizontal legend items
        yanchor="top",    # Anchor the top of the legend box
        y=-0.2,           # Position below the plot area (adjust as needed)
        xanchor="center", # Anchor the center of the legend box
        x=0.5             # Center horizontally
    ),
    margin=dict(b=100) # Optional: Increase bottom margin to accommodate the legend
)


fig.update_layout(
    xaxis=dict(
        type="log",
        tickmode="array",
        tickvals=[1, 10, 100],
        ticktext=["1", "10", "100"]
    )
)

# Show the plot
fig.show()

import plotly.io as pio
#save a figure of 300dpi, with 5 inches, and  height 3inches
pio.write_image(fig, 
                "../../output/figures/return_period/GCW_return_period_v01.png", 
                width=3*250, height=2*250, scale=10)





# Save the figure as a PNG file
# Change format if needed
# fig.write_image("../../output/figures/return_period/GCW_return_period.png", format="png")  


# #-------------------------------------------------------
# # Create a plot
# fig, ax = plt.subplots(figsize=(8, 6))

# # Plot return period (X-axis) vs elevation (Y-axis)
# ax.plot(return_periods, elevations, marker='o', linestyle='-', color='b', label='Elevation vs Return Period')

# # Set X-axis to logarithmic scale
# ax.set_xscale('log')

# # Label axes
# ax.set_xlabel("Return Period (years, log scale)", fontsize=12)
# ax.set_ylabel("Elevation (meters)", fontsize=12)

# # Add grid for better readability
# ax.grid(which="both", linestyle="--", alpha=0.7)

# # Add title
# ax.set_title("Return Period vs Elevation", fontsize=14)

# # Add legend
# ax.legend()
# # Show the plot
# plt.show()

# #---------------------------------------------------
# # Create the plot
# plt.figure(figsize=(12, 6))
# # Plot reference gauge
# plt.plot( swot_tidal_wse_rp['datetime_LST'], df['gauge_wse_m'], '-', label='Reference tide gauge', linewidth=.25, alpha=0.85)


# #---------------------------------------------------
# # Plot the original sparse time series

# # Reconstructed interpolated SWOT WSE
# plt.plot( df['datetime_LST'],  df['reconstructed_wse'], '-', label='Interpolated SWOT', 
#             color="#fe5b5b", linewidth=.25, alpha=0.95)

#  Fit MLE model
# NOTE:  This throws errors (see message below), but the Emcee MCMC version works.
# model.fit_model(model='MLE')

# summary = model.get_summary(
#     # return_period=[1, 2, 5, 10, 25, 50, 100, 250, 500, 1000],
#     return_period_size="365.2425D",
#     return_period=[1, 2],
#     alpha=0.95,
#     n_samples=100,
# )

# RuntimeError: RuntimeError
#         An attempt has been made to start a new process before the
#         current process has finished its bootstrapping phase.

#         This probably means that you are not using fork to start your
#         child processes and you have forgotten to use the proper idiom
#         in the main module:

#             if __name__ == '__main__':
#                 freeze_support()
#                 ...

#         The "freeze_support()" line can be omitted if the program
#         is not going to be frozen to produce an executable.: 

#         An attempt has been made to start a new process before the
#         current process has finished its bootstrapping phase.

#         This probably means that you are not using fork to start your
#         child processes and you have forgotten to use the proper idiom
#         in the main module:

#             if __name__ == '__main__':
#                 freeze_support()
#                 ...

#         The "freeze_support()" line can be omitted if the program
#         is not going to be frozen to produce an executable.
# /Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/eva.py:131: RuntimeWarning: 12 Null values found in `data` - removing invalid entries
#   warnings.warn(message=message, category=RuntimeWarning)
# /Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/eva.py:131: RuntimeWarning: 12 Null values found in `data` - removing invalid entries
#   warnings.warn(message=message, category=RuntimeWarning)
# Traceback (most recent call last):
#   File "<string>", line 1, in <module>
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 116, in spawn_main
# Traceback (most recent call last):
#   File "<string>", line 1, in <module>
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 116, in spawn_main
#     exitcode = _main(fd, parent_sentinel)
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 125, in _main
#     exitcode = _main(fd, parent_sentinel)
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 125, in _main
#     prepare(preparation_data)
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 236, in prepare
#     prepare(preparation_data)
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 236, in prepare
#     _fixup_main_from_path(data['init_main_from_path'])
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 287, in _fixup_main_from_path
#     _fixup_main_from_path(data['init_main_from_path'])
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/spawn.py", line 287, in _fixup_main_from_path
#     main_content = runpy.run_path(main_path,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/runpy.py", line 288, in run_path
#     main_content = runpy.run_path(main_path,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/runpy.py", line 288, in run_path
#     return _run_module_code(code, init_globals, run_name,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/runpy.py", line 97, in _run_module_code
#     return _run_module_code(code, init_globals, run_name,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/runpy.py", line 97, in _run_module_code
#     _run_code(code, mod_globals, init_globals,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/runpy.py", line 87, in _run_code
#     _run_code(code, mod_globals, init_globals,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/runpy.py", line 87, in _run_code
#     exec(code, run_globals)
#   File "/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/scripts/swot_tidal_forcing/plots/swot/exceedance_curves.py", line 78, in <module>
#     exec(code, run_globals)
#   File "/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/scripts/swot_tidal_forcing/plots/swot/exceedance_curves.py", line 78, in <module>
#         summary = model.get_summary(summary = model.get_summary(

#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/eva.py", line 1313, in get_summary
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/eva.py", line 1313, in get_summary
#     rv = self.get_return_value(
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/eva.py", line 1256, in get_return_value
#     rv = self.get_return_value(
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/eva.py", line 1256, in get_return_value
#         for value in self.model.get_return_value(for value in self.model.get_return_value(

#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/models/model_mle.py", line 127, in get_return_value
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/models/model_mle.py", line 127, in get_return_value
#     self._extend_fit_parameter_cache(n=n_extra_fit_parameters)
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/models/model_mle.py", line 254, in _extend_fit_parameter_cache
#     self._extend_fit_parameter_cache(n=n_extra_fit_parameters)
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/pyextremes/models/model_mle.py", line 254, in _extend_fit_parameter_cache
#     with multiprocessing.Pool(processes=n_cores) as pool:
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/context.py", line 119, in Pool
#     with multiprocessing.Pool(processes=n_cores) as pool:
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/context.py", line 119, in Pool
#     return Pool(processes, initializer, initargs, maxtasksperchild,
#     return Pool(processes, initializer, initargs, maxtasksperchild,  File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/pool.py", line 212, in __init__

#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/pool.py", line 212, in __init__
#     self._repopulate_pool()
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/pool.py", line 303, in _repopulate_pool
#     self._repopulate_pool()
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/pool.py", line 303, in _repopulate_pool
#     return self._repopulate_pool_static(self._ctx, self.Process,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/pool.py", line 326, in _repopulate_pool_static
#     return self._repopulate_pool_static(self._ctx, self.Process,
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/pool.py", line 326, in _repopulate_pool_static
#     w.start()
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/process.py", line 121, in start
#     w.start()
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/process.py", line 121, in start
#         self._popen = self._Popen(self)self._popen = self._Popen(self)

#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/context.py", line 284, in _Popen
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/context.py", line 284, in _Popen
#     return Popen(process_obj)    
# return Popen(process_obj)
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/popen_spawn_posix.py", line 32, in __init__
#   File "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/multiprocessing/popen_spawn_posix.py", line 32, in __init__
#         super().__init__(process_obj)super().__init__(process_obj)
