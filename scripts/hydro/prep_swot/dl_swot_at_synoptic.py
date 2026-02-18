
# Script downloading SWOT data from PODAAC for synoptic sites.


#%%--------------------------------------------------------------------------
# Impor packages
# https://podaac.github.io/tutorials/notebooks/SearchDownload_SWOTviaCMR.html
import geopandas as gpd
import glob
from pathlib import Path
import pandas as pd
import os
import zipfile
import earthaccess



#%%-----------------------------------------------------------------------------------
# Import functions download data from PODAAC
import prep_swot.fcn.dl_swot
from prep_swot.fcn.dl_swot import dl_pixc_persite, dl_lakepoly_persite, dl_raster_persite

# Reload module/function after modifying it
# This needs to be followed by an import statement to ensure updates are made
### TODO: move or copy this below the next import statement.
import importlib
importlib.reload(prep_swot.fcn.dl_swot)


# Print the source code of a module to verify it was updated
import inspect
print(inspect.getsource(prep_swot.fcn.dl_swot))



#%%--------------------------------------------------------------------------
#  Log into Earthdata

# Login:    efluet;   isthis1ANYSAFER
earthaccess.login(strategy='interactive', persist=True)
auth = earthaccess.login()
auth.refresh_tokens()
 


#%%--------------------------------------------------------------------------
# Read in SWOT pass/tiles over synoptic sites

synoptic_swot_tile_df = pd.read_csv('/Users/flue473/big_data/swot/synoptic_swot_scene.csv')


#--------------------------------------------------------------------------
# Loop through synoptic sites
for index, row in synoptic_swot_tile_df.iterrows():
    print(row)

    # Get PixC vec
    # L2_HR_PIXC	Point cloud of water mask pixels (“pixel cloud”) with geolocated heights, backscatter, geophysical fields, and flags.
    # L2_HR_PIXCVec	Auxiliary information for pixel cloud product indicating to which water bodies the pixels are assigned in river and lake products. Also includes height-constrained pixel geolocation after reach- or lake-scale averaging.
    if 1: dl_pixc_persite(row)

    # Get lake poly  #     # Lake SP Obs or Data: SWOT_L2_HR_LakeSP_D
    if 0: dl_lakepoly_persite(row)

    # Get raster data
    if 0: dl_raster_persite(row)


