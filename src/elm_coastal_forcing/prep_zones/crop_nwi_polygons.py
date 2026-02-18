
#%% Read inputs --------------------------

import pandas as pd
import geopandas as gpd

# Get bounding box
synoptic_bbox = gpd.read_file('../../../data/site_pts/synoptic/synoptic_sites_bbox.geojson').set_crs(epsg=4326, inplace=True)
# synoptic_bbox = gpd.GeoDataFrame(synoptic_bbox, geometry=synoptic_bbox.geometry)


# This file contains directories of the NWI polygons
synoptic_pts_df = pd.read_csv('../data/processed/synoptic_site_pts/synoptic_elev_zone_v3.csv')


#%%  Crop NWI with BBOX --------------------------

# Loop through sites
# for index, bbox in synoptic_bbox.iterrows():

for bbox in synoptic_bbox.itertuples(index=False):

	bbox = gpd.GeoDataFrame([bbox], crs="EPSG:4326").set_crs(epsg=4326, inplace=True)
	# print(bbox)

	# Subset 
	transect_pts = synoptic_pts_df[synoptic_pts_df.site_id == bbox.site_id.iloc[0]].iloc[0]

	# nwi filepath from subsetted
	nwi_filepath = transect_pts.nwi_file

	# Read NWI file
	nwi = gpd.read_file(f'../../../data/nwi/{transect_pts.nwi_file}')

	nwi = nwi.to_crs("EPSG:4326")  	# Reproject nwi to WGS84

	# Use the intersection method to crop the GeoDataFrame
	nwi_cropped = gpd.overlay(nwi, bbox, how='intersection')

	print("Cropped GeoDataFrame")

	# Save to file
	nwi_cropped.to_file(f"../../../output/results/nwi/{bbox.site_id.iloc[0]}/nwi_{bbox.site_id.iloc[0]}_cropped.shp")





#%%
# Select the open water polygons
# Filter by small size
# To limit to near shore
# Convert to polygon to line
# Buffer around marsh outlines
# Mask the open water with marsh buffer
# Select Voronoi polygons



