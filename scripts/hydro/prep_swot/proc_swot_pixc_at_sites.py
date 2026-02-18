#%% 
import numpy as np
import geopandas as gpd
import glob
import xarray as xr
import os
import pandas as pd
from shapely.geometry import Point
from pyproj import CRS


import fiona
from fiona.drvsupport import supported_drivers
# Ensure the driver supports overwrites
fiona.supported_drivers["ESRI Shapefile"] = "rw"


# TODO: THE FILTERING BY PRODUCT ALREADY HAPPENS AT THE DOWNLOAD STAGE, JUST DELETE AND RERUN


#%%-----------------------------------------------------------------------------------
# Import functions
from prep_swot.fcn.prep_pixc import prep_pixc
from proc.prep_swot.fcn.make_wsecluster_nearshore_units import cluster_swot_wse
from proc.prep_swot.extract_wse_nearshore_unit import extract_wse_nearshore_unit



#%%-----------------------------------------------------------------------------------
#  Get bounding box
synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')


#%%-----------------------------------------------------------------------------------

# Loop through site bboxes
for index, site_bbox in synoptic_bbox.iterrows(): # synoptic_bbox[0:1].iterrows():

    # Get site ID
    site_id = site_bbox.site_id
    print(site_id)

    # Convert row subset to geodataframe
    site_bbox = gpd.GeoDataFrame([site_bbox], geometry='geometry', crs='EPSG:4326')

    #%%-------------------------------------------------------------------------------    
    # Get a list of all .nc files in the directory using glob
    nc_files = glob.glob(f"/Users/flue473/big_data/swot/pixc/original/{site_id}/*.nc")


    #%%-----------------------------------------------------------------------------------
    # Loop through netCDF files of raw SWOT PIXC files
    for nc_file in nc_files[0:1]: 

        # Get filename without extension
        base_name = os.path.basename(nc_file)
        root, _ = os.path.splitext(base_name)
        date = pd.to_datetime(root.split('_')[8], format='%Y%m%dT%H%M%S', errors='coerce')


        # Read in PixC file and load into memory
        with xr.open_dataset(nc_file, group='pixel_cloud', engine='h5netcdf').load() as ds:


            #%%-----------------------------------------------------------------
            # PREP PIXC (calc WSE, crop and reproject)
            dso = prep_pixc(ds, site_bbox)


            #%%-----------------------------------------------------------------
            #  Save to processed PixC NetCDF file

            # Declare output path and filename for cropped SWOT
            out_dir_path = f'/Users/flue473/big_data/swot/pixc/cropped_synoptic/{site_id}'
            output_nc_file_path = out_dir_path + '/' + root + "_cropped_navd88.nc"

            # Create the directory if it doesn't exist
            if not os.path.exists(out_dir_path): os.makedirs(out_dir_path)

            # Write the cropped dataset to a NetCDF file with compression
            encoding = {var: {'zlib': True} for var in dso.data_vars}
            dso.to_netcdf(output_nc_file_path, mode='w', encoding=encoding)


            # Save PixC as shapefile for visualization in GIS
            #  Create geometries (Point objects)
            geometry = [Point(lon_item, lat_item) for lon_item, lat_item in zip(dso['longitude'], dso['latitude'])]


            # Step 4: Create GeoPandas GeoDataFrame
            gdf = gpd.GeoDataFrame({
                "wse": dso['wse'].values,
                # "water_frac": water_frac,
                # "classification": classification,
            }, geometry=geometry, crs=CRS("EPSG:5498"))

            output_nc_file_path = out_dir_path + '/' + root + "_cropped_navd88.shp"
            gdf.to_file(output_nc_file_path, driver='ESRI Shapefile')




            #%%-----------------------------------------------------------------
            # CLUSTERING
            if 0:
                # Run clustering algorithm to segment water surface elevation
                cluster_poly = cluster_swot_wse(dso, site_bbox)
                

                #%%-----------------------------------------------------------------
                #  Save Polygon Cluster to fileto processed PixC NetCDF file

                # Declare output path and filename for cropped SWOT
                out_dir_path = f'/Users/flue473/big_data/swot/pixc/polygon_cluster/{site_id}'
                output_nc_file_path = out_dir_path + '/' + root + "_cropped_navd88.shp"

                # Create the directory if it doesn't exist
                if not os.path.exists(out_dir_path): os.makedirs(out_dir_path)

                cluster_poly.to_file(output_nc_file_path, driver='ESRI Shapefile')



