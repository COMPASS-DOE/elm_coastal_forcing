

import matplotlib
import os
import numpy as np
import numpy.ma as ma
import pandas as pd
import geopandas as gpd
import fiona
import xarray as xr
import glob
# import rasterstats as rs
from rasterstats import zonal_stats
import rasterio as rio
from matplotlib import pyplot
import rasterstats
import importlib


# Increase the number of rows and columns variables printed
pd.set_option('display.max_rows', 50); pd.set_option('display.max_columns', 45)

# Increase the number of rows and variables printed
xr.set_options(display_max_rows=20)#, display_max_columns=20)

# print cwd
os.getcwd()


# print("sys.path:", sys.path)  # Check the Python import paths
# print("Current directory:", os.getcwd())  # Check where the script runs from

# # Dynamically append project root to sys.path
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))  # Navigate up 3 levels
# sys.path.append(project_root)
# print("sys.path:", sys.path)

# # Import the module path, so the VS debugger works
# sys.path.append('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/COMPASS_synoptic_sims/scripts')



if 0:
    # Optional; add system path to import libraries
    import sys
    sys.path.append('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/scripts')

    import importlib
    importlib.reload(prep_hydro.tide_lag_reg_matte.py.tidexcorr)



#TODO: 01/19/2025
# - Segment synoptic sites elevation
# - Delineate offshore polygon
# - Get the lag regression from Pascal
# - Apply lagged regression to...

# TODO: 03/27/2025
# - Merge DEM tiles for Lake Erie?
# - Fix clipping at edged of bbox



# Config file

# dir of swot data
# dir of 


#---------------------------------------------
# PREP POINTS & TRANSECTS
'prep_points/prep_site_coords.py'


#---------------------------------------------
# PREP ELEVATION
# TODO: convert everything to Mean lower low water (MLLW)?

# TODO:  Check where zone v3 gets saved;  where is latest elev script?

# TODO: Rerun elevation at points; to fix Portage River elevations being inverted when using transect.
'prep_points/prep_site_coords.py'

# Make Synoptic+EXCHANGE points from coordinates
# prep_pts


#---------------------------------------------
# PREP DISTANCE FROM PERMANENT WATERBODY



# COMPUTE LOCAL Z* on DEM

#---------------------------------------------
# PREP BOUNDARY WATER LEVEL & SALINITY
# TODO: Convert everything to local time (or all GMT?)
# TODO Verify shared datum

# Prep hydro tidal forcing
# 'prep_hydro/prep_hydro_forcing.py'

# Gapfill hydro forcings
# 'prep_hydro/gapfill_hydro_forcing.py'

# Fix forcings
# 'prep_hydro/fix_hydro_forcing.py'


#---------------------------------------------
# PREP SYNOPTIC WELLS

# Prep transect groundwater wells
# 'prep_hydro/prep_gw_depth.py'


#---------------------------------------------
# FORMAT FORCING FOR ELM
# 'make_COMPASS_ELM_forcing.py'




#%%---------------------------------------------
# PREP COASTLINE: Convert CUSP coastlines to estuarine water polygons 
prep_coastlines.py


#%%---------------------------------------------
# Download SWOT PixC data

# TODO:  Check if need phase unwrapping error: https://podaac.github.io/tutorials/notebooks/datasets/SWOT_PIXC_PhaseUnwrap_localmachine.html
# TODO:  Check if need to reproject in slant angle to calculate area: https://podaac.github.io/tutorials/notebooks/datasets/SWOT_PIXC_Area_localmachine.html

# Download PixC

# Filter most recent CRID and Product count per date

# CRID: PGC0 > PIC0 > PIC1 > PIC2
# Product#: 01 > 02 > 03

# Convert datum to NAVD88


#%%---------------------------------------------
# Download tide gauges from NOAA COOPS API



#%%---------------------------------------------
# Apply tide cross correlation and reconstruction

# TODO:

# Weight SWOT measurements by elevation uncertainty?

# 1) Run VMD on reference time series 
# 2) Apply SWOT elevation mean to the depth time series for comparison
# 3) Run tide cross correlation on 2+ stations

# 4) Detide prediction to get storm surges: predict total water level or surge water level as the detided residual

# 3 MUST DO updates: 
    # timestep (go to 6min), UMD, stations

# Figure out whether to remote mean time from SWOT data or not
    # remove mean tide when comparing to forest/wetland elevation
    # NGA/GTX file? which epoch?
    # Pole tides and earth tides should be kept inside the lagged regression
    # Keep tides in all stations?

# How to select stations? by distance?  
    # Or by similarity between ratio of tidal constituents to the prediction point 

# For extreme events:
    # Reconstruct based only on harmonic subordinate stations,
    # Then reconstruct based on actual measurements. 
    # The difference in reconstructions represent storm surges.

# Currently, the lag is static over time. To make it vary seasonally, we could alter  but could change seasonal 

# De-tided time series can remove the harmonic component of water levels 
# (low pass filter on moving window): Godin's filter (12, 25, etc. day window)

# For hindcasting: ensure no change in datum, measurement frequency.
# Smooting accounts for sub-timestep lags (below hourly); use 6min instead

# NS_Tide and TideEstimator:
# include ability to includ river discharge already
# Also in includes meteorological effects (wind, pressure)


# EMD : Mode mixing between bands,
# VMD: is cleaner.

# ?? Detect SWOT error by reconstructing SWOT at gauges, and exlude stations that degrade predictions? 
