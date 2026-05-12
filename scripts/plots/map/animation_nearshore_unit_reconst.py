
#%%
import glob
import os
import requests
import s3fs
import fiona
import glob
import netCDF4 as nc
import h5netcdf
import xarray as xr
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
# import hvplot.xarray
from datetime import datetime

from matplotlib import colors

#%%------------------------------------------------
#  Function to create map plot
def create_map_plot(nearshore_units_singlehour, site_id, date):

	
	min_val, max_val = -1, 1      # your static range
	levels = np.linspace(min_val, max_val, 9)  # fixed bins across all plots
	cmap = plt.cm.plasma
	cmap.set_under('grey')
	cmap.set_over('grey')

	# Norm using the fixed levels
	norm = colors.BoundaryNorm(levels, cmap.N, clip=False)

	fig, ax = plt.subplots(1, 1, figsize=(16, 8))
	ax.margins(0)
	ax.set_aspect('equal')
	ax.set_xticks([])
	ax.set_yticks([])
	ax.xaxis.set_tick_params(length=0)
	ax.yaxis.set_tick_params(length=0)


	# --- POLYGON LAYER with static levels ---
	poly = nearshore_units_singlehour.plot(
		column="reconstructed_wse",
		cmap=cmap,
		norm=norm,          # uses fixed levels
		edgecolor="black",
		linewidth=1.1,
		ax=ax,
		zorder=2 )

	# Plot NWI outlines 
	nwi_cropped_marwet.plot(
		ax=ax,
		facecolor='#80e8b9',   # fill color
		edgecolor='none',      # no outline (or set a color if you want)
		linewidth=0,
		zorder=1 )

	# # Plot NWI outlines 
	nwi_cropped_fwwet.plot(
		ax=ax,
		facecolor='#3ac754',   # fill color
		edgecolor='none',      # no outline (or set a color if you want)
		linewidth=0,
		zorder=1 )

	nwi_cropped_ow.plot(
		ax=ax,
		facecolor='#8c94ff',
		edgecolor='none',
		linewidth=0,
		zorder=1 )


	# Colorbar using same levels (static across plots)
	cbar = plt.colorbar(poly.collections[0],
						ax=ax,
						extend='both',
						boundaries=levels,
						spacing='proportional')
	cbar.set_label('Water Surface Elevation (m; NAVD88)')

	plot_title = site_id + '   -   ' + str(date)
	fig.suptitle(
		plot_title,
		fontsize=14,
		fontweight='bold',
		x=0.55,
		y=0.91
	)

	return(fig)




site_id = 'GCW'


#%%  NWI  ---------------------------------

# Read in cropped NWI
nwi_cropped = gpd.read_file(f"../../output/results/nwi/{site_id}/nwi_{site_id}_cropped.shp")
# Apply a negative buffer to shrink polygons
# nwi_cropped['geometry'] = nwi_cropped.geometry.buffer(-0.00005)
nwi_cropped_ow = nwi_cropped[nwi_cropped.WETLAND_TY.isin(['Estuarine and Marine Deepwater', 'Freshwater Pond', 'Riverine'])]
nwi_cropped_fwwet = nwi_cropped[nwi_cropped.WETLAND_TY.isin([ 'Freshwater Emergent Wetland', 'Freshwater Forested/Shrub Wetland', 'Freshwater Forested/Shrub Wetland'])]
nwi_cropped_marwet = nwi_cropped[nwi_cropped.WETLAND_TY.isin(['Estuarine and Marine Wetland'])]



#%% Get timeseries of reconstruction  ------------------------------------

wse_rcstr_df = pd.read_csv(f'../../output/results/reconstr_wse/{site_id}_nearshore_wse_reconstr.csv')
wse_rcstr_df = wse_rcstr_df.assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce')) 

# Filter dates to a few days
from datetime import datetime
import pytz
eastern = pytz.timezone('US/Eastern')
start_date = eastern.localize(datetime(2025, 2, 10))
end_date   = eastern.localize(datetime(2025, 2, 23))

# Clean up wse dataframe
wse_rcstr_df = ( wse_rcstr_df
    # .drop_duplicates(subset=['datetime_LST'], keep='last')
    .query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)"))


wse_rcstr_df = wse_rcstr_df[wse_rcstr_df.unit_id != 36]


wse_rcstr_df.unit_id.unique()
wse_rcstr_df.info()


#%% Get nearshore units  ----------------------------------------
nearshore_units = gpd.read_file('../../output/results/coastlines/nearshore_voronoi/nearshore_voronoi_GCW_v02.shp')
nearshore_units = nearshore_units.rename(columns={'id': 'unit_id'})


#%%  Loop through time 

images = []

for date in wse_rcstr_df.datetime_LST.unique():

	date_label = str(date)[:-6]
	print(date_label)

	# Subset the reconstructed elevations
	wse_rcstr_singlehour = wse_rcstr_df.query("(datetime_LST ==@date)")

	# Joint to nearshore units
	nearshore_units_singlehour = nearshore_units.merge(wse_rcstr_singlehour, on='unit_id', how='left')


	# Make map of units and save to file
	map_singlehour = create_map_plot(nearshore_units_singlehour, site_id, date_label)

	# Make output filename
	image_outfile = f"../../output/figures/reconstruct_wse/unit_map/reconstr_wse_perunit_{date_label}.png"

	# Save the plot in the created directory
	plt.savefig(image_outfile, dpi=150, bbox_inches='tight')
	plt.close()

	images.append(image_outfile)


#/----------------------------------------------------
#  Make animation
import imageio.v3 as iio
import imageio

# Assuming 'bbox.site_id' is defined and 'images.imagepath' is a list of image paths
gif_file = f"../../output/figures/reconstruct_wse/animation/reconstr_wse_perunit_v03.gif"

# Read all images into a list
image_list = [iio.imread(image_path) for image_path in images]

# Write images to GIF
iio.imwrite(gif_file, image_list, format='GIF', fps=8, loop=0) 


