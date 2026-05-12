
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


#%%------------------------------------------------
#  Function to create map plot
def create_map_plot(ds_cropped, site_id, date):

	import matplotlib.pyplot as plt
	from matplotlib import colors

	fig, ax = plt.subplots(1,1, figsize=(16, 8))

	ax.margins(0)     # Remove margins inside the plot
	ax.set_aspect('equal')
	ax.set_xticks([])
	ax.set_yticks([])

	# # Set the defined ticks
	# ax.set_xticks([xmin, xmax])
	# ax.set_yticks([ymin, ymax])	
	# ax.set_ylabel('Latitude')
	# ax.set_xlabel('Longitude')

	ax.xaxis.set_tick_params(length=0)  # Hide x-axis tick marks
	ax.yaxis.set_tick_params(length=0)  # Hide y-axis tick marks

	cmap = plt.cm.plasma    # Set colormap
	cmap.set_under('grey')  # color for values < vmin
	cmap.set_over('grey')   # color for values > vmax

	# Set limits according to the region
	import matplotlib.colors as mcolors
	if site_id in ['MSM', 'GWI', 'GCW', 'SWH']:
		norm = colors.Normalize(vmin=-3, vmax=8, clip=False)
	else:
		norm = colors.Normalize(vmin=171, vmax=177, clip=False)
	
	# SWOT PIXC POINTS
	scatter = ax.scatter(x=ds_cropped.longitude,
				   y=ds_cropped.latitude,
				   c=ds_cropped.wse,
				   s=8, 
				   edgecolor='none', cmap=cmap, norm=norm)

	# Color bar with boundary norm
	cbar = plt.colorbar(mappable=scatter, ax=ax, extend='both')
	cbar.set_label('SWOT Water Surface Elevation (m)')

	# Plot NWI outlines 
	nwi_cropped_wet.boundary.plot(ax=ax, color='#009e08', linewidth=0.75, zorder=1)
	nwi_cropped_ow.boundary.plot(ax=ax, color='blue', linewidth=0.75, zorder=1)
	

	# Plot synoptic points
	plt.scatter(transect_pts.geometry.x, transect_pts.geometry.y, 
			     color='white', s=50, zorder=2) 

	plt.scatter(transect_pts.geometry.x, transect_pts.geometry.y, 
			     facecolors='white', edgecolors='black', s=50, zorder=2) 
	
	for i in range(len(transect_pts)):
		plt.text(transect_pts.geometry.x.iloc[i], 
		   		 transect_pts.geometry.y.iloc[i], 
				 transect_pts['zone_id'].iloc[i],
				 fontsize=3.5, ha='center', va='center')

	# Plot LineString GeoDataFrame on the same axes
	# transect.plot(ax=ax, color='black', linewidth=0.75, label='LineString')
	# Plot tidal zone
	# tidal_edge_zone.boundary.plot(ax=ax, color='#48ff24', linewidth=1.5, label='LineString')

	plt.xlim(xmin, xmax)
	plt.ylim(ymin, ymax)

	# Add a title to the figure
	plot_title = transect_pts.site_name.iloc[0] + '    ' + date
	fig.suptitle(plot_title , fontsize=14)
	fig.set_size_inches(5.5, 4)
	# fig.tight_layout()


#%%-------------------------------------------------------------------------------
#  Load data

# /  Get synoptic transect
# transect = gpd.read_file('../../output/results/transect_line/transect_line' + site_name + '.shp').to_crs('EPSG:4326')

# synoptic_pts = gpd.read_file('../data/processed/synoptic_pts_wgs84.geojson')
synoptic_pts = gpd.read_file('../../data/processed/synoptic_site_pts/synoptic_elev_zone_v4.csv')
synoptic_pts = gpd.GeoDataFrame(synoptic_pts,
								geometry=gpd.points_from_xy(synoptic_pts.long, synoptic_pts.lat),
								crs="EPSG:4326")

synoptic_pts['zone_id'] = synoptic_pts['zone_id'].astype(str)

#  Get bounding box
synoptic_bbox = gpd.read_file('../../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')


#%%------------------------------------------------------------------------------

# Loop through site bounding boxes
for index, bbox in synoptic_bbox.iterrows():

	print(bbox.site_id)
	xmin, ymin, xmax, ymax = bbox.geometry.bounds

	# Initialize list to store image file paths
	images = pd.DataFrame(columns=['imagepath', 'date'])

	#/  Subset synoptic points
	transect_pts = synoptic_pts[synoptic_pts.site_id == bbox.site_id]
	
	# Read in cropped NWI
	nwi_cropped = gpd.read_file(f"../../../output/results/nwi/{bbox.site_id}/nwi_{bbox.site_id}_cropped.shp")
	# Apply a negative buffer to shrink polygons
	nwi_cropped['geometry'] = nwi_cropped.geometry.buffer(-0.00005)
	nwi_cropped_ow = nwi_cropped[nwi_cropped.WETLAND_TY.isin(['Estuarine and Marine Deepwater', 'Freshwater Pond', 'Riverine'])]
	nwi_cropped_wet = nwi_cropped[nwi_cropped.WETLAND_TY.isin(['Estuarine and Marine Wetland', 'Freshwater Emergent Wetland', 'Freshwater Forested/Shrub Wetland'])]

	# Get a list of all SWOT .nc files in the directory using glob
	cropped_dir = '../../../data/swot/pixc/' + bbox.site_id + '/cropped'
	nc_filepaths = glob.glob(f"{cropped_dir}/*.nc")

	# Loop through netCDF filepaths; each a SWOT PIXC file
	for nc_filepath in nc_filepaths:
		
		# Get filename without extension
		base_name = os.path.basename(nc_filepath)
		root, _   = os.path.splitext(base_name)
		print(root)

		# Get date from file name
		date = datetime.strptime(nc_filepath.split('_')[-4],'%Y%m%dT%H%M%S').strftime('%Y-%m-%d %H:%M:%S')

		# Load netCDF file
		with xr.open_dataset(nc_filepath, engine='h5netcdf') as ds_cropped:

			ds_cropped.load()

			# Create map plot
			create_map_plot(ds_cropped, bbox.site_id, date)

			# Name image file based on input netCDF file
			image_path = '../../../output/figures/swot/map/pixc/imgs_for_gif/' + bbox.site_id + '/' + root + '.png'

			# Save plot to an image file
			plt.savefig(image_path, dpi=300)
			plt.close()

			# Append image path to list of images
			new_row =  pd.DataFrame([{'imagepath': image_path, 'date': date}])
			images = pd.concat([images, new_row], ignore_index=True)
			images.sort_values(by='date', inplace=True)  # Sort by date for GIF


	#/----------------------------------------------------
	#  Make animation
	import imageio.v3 as iio
	import imageio

	# Assuming 'bbox.site_id' is defined and 'images.imagepath' is a list of image paths
	gif_file = f"../../../output/figures/swot/map/pixc/gif/pixc_swe_{bbox.site_id}_v01.gif"

	# Read all images into a list
	image_list = [iio.imread(image_path) for image_path in images.imagepath]

	# Write images to GIF
	iio.imwrite(gif_file, image_list, format='GIF', fps=1, loop=1) #  duration=20,




#%%

# Get date from file name
crid = nc_filepath.split('_')[-3]
counter = nc_filepath.split('_')[-2]


# Filter files to keep single one per date; giving preference to better quality releases 
crid_order = [
    "PGC0", "PIC0", "POC0", 
    "PGB0", "PIB0", "POB0", 
    "PGC1", "PIC1", "POC1", 
    "PGB1", "PIB1", "POB1", 
    "PGC2", "PIC2", "POC2", 
    "PGB2", "PIB2", "POB2", "D"]

# Create a DataFrame from the lists
crid_lut_df = pd.DataFrame({'crid_order': crid_order) 
						#    'rank': list(range(1, len(crid_order)+1)) })
crid_lut_df.reset_index(inplace=True)



# Create a rank DataFrame from the crid_order
rank_df = pd.DataFrame(crid_order, columns=['crid'])
rank_df['rank'] = rank_df.index

# Convert sample data to a DataFrame
df = pd.DataFrame(data)

# Create regex pattern to match any crid from the list
pattern = '|'.join(crid_order)

# Extract 'crid' from 'imagepath', assuming the 'crid' appears in the path
df['crid'] = df['imagepath'].apply(lambda x: re.search(pattern, x).group() if re.search(pattern, x) else None)

# Merge the DataFrames on 'crid'
merged_df = pd.merge(df, rank_df, on='crid', how='left')

# Group by 'date' and select the row with the highest 'rank'
result_df = merged_df.sort_values('rank').groupby('date', as_index=False).first()

# Drop the 'crid' and 'rank' columns if no longer needed
result_df = result_df.drop(columns=['crid', 'rank'])

# Display the result DataFrame
print(result_df)
