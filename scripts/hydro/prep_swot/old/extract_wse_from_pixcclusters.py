# TODO: Extract Elevation at each site
import numpy as np
import pandas as pd
import glob
from shapely import polygons
import xarray as xr
from pyproj import CRS
import rioxarray
import geopandas as gpd
#%%
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# TODO: Stack raster image and compute mean\
# TODO: Plot with PixC data instead?
# TODO: extract WSE at buoy coordinates too?
# TODO: extract WSE at the synoptic locations
# TODO: Fix vertical datum and ellipsoid conversions



#%%-----------------------------------------------------------------------------------
#  Open water point of each site

site_ow_sonde = (
    pd.read_csv('../data/raw/transect_coords/compass_synoptic_wsonde.csv')
    .reset_index(drop=True)
    )

# Create "Point" geometry from latitude and longitude
site_ow_sonde['geometry'] = site_ow_sonde.apply(lambda row: Point(row['long'], row['lat']), axis=1)

# Convert the DataFrame into a GeoDataFrame
gsite_ow_sonde = gpd.GeoDataFrame(site_ow_sonde, geometry='geometry')

# Set the Coordinate Reference System (CRS)
gsite_ow_sonde.set_crs(epsg=5498, inplace=True)  # EPSG:4326 = WGS84 Latitude/Longitude

gsite_ow_sonde.to_file('../data/raw/transect_coords/compass_synoptic_wsonde.geojson')



#%%------------------------------------------------------------------------------------
#  Create an empty DataFrame with 'date' and 'wse_mean' columns
swot_tidal_wse_df = pd.DataFrame(columns=['site_id', 'date','label', 'pt_count', 'poly_area', 'pt_dens', 'wse_mean', 'wse_std', 'distance'])


#%%-----------------------------------------------------------------------------------

# Loop through site bboxes
for index, row in gsite_ow_sonde.iterrows():

    site_ow_point = gsite_ow_sonde.iloc[[index]]

    # Get site ID
    site_id = site_ow_point.site_id.values[0] 
    print(site_id)


    #%%-----------------------------------------------------------------------------------
    # Loop through all the polygons of SWOT WSE at site

    # Get a list of all .shp files in the directory using glob
    poly_files = glob.glob(f'/Users/flue473/big_data/swot/pixc/polygon_cluster/{site_id}/*_cropped_navd88.shp')


    # Loop through polygon shapefiles
    for poly_file in poly_files:

        # Get filename without extension
        base_name = os.path.basename(poly_file)
        root, _   = os.path.splitext(base_name)
        date = pd.to_datetime(root.split('_')[8], format='%Y%m%dT%H%M%S', errors='coerce')

        # Read in cropped PixC
        cluster_polygons = gpd.read_file(poly_file)
        cluster_polygons.set_crs(epsg=5498, inplace=True, allow_override=True)  # EPSG:4326 = WGS84 Latitude/Longitude

        # Calculate distance to the point
        cluster_polygons['distance'] = cluster_polygons.geometry.distance(site_ow_point.geometry.iloc[0])
        #cluster_polygons.distance(site_ow_point, align=False)  

        # Find the Closest Polygon; ie the row with the smallest distance
        closest_polygon = cluster_polygons.iloc[[cluster_polygons['distance'].idxmin()]]


        # Save to file
        closest_polygon.to_file(f'../../output/results/swot/closest_swot_poly_{site_id}_{date}.shp')


        #%%-----------------------------------------------------------------------------------
        # Compile heights to dataframe
        closest_polygon_df = closest_polygon.drop(columns='geometry')#.T

        closest_polygon_df = pd.DataFrame(closest_polygon_df)

        # Add site_id and date columns
        closest_polygon_df['site_id'] = site_id
        closest_polygon_df['date'] = date

        # print(closest_polygon)

        # Append the new row to the existing DataFrame using concat
        swot_tidal_wse_df = pd.concat([swot_tidal_wse_df, closest_polygon_df], ignore_index=True)

        # Save to CSV
        swot_tidal_wse_df.to_csv('../../output/results/swot/swot_wse_synoptic_tidal_poly.csv', index=False)

