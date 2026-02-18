
import numpy as np
import pandas as pd
import glob
import xarray as xr
from pyproj import CRS
import rioxarray
import geopandas as gpd

# TODO: Extract Elevation at each site
# TODO: Find a way to run transofrmatin directly on the xarray dataset using xr.ufunc
# TODO: Use xarray's apply_ufunc to vectorize the reprojection process
# TODO: Apply to reprojection directly to the uncropped swot dataset; or find a way to keep dimensions intact from uncropped swot data
# TODO: add SWOT error; and propagate error to the mean WSE
# TODO: Extract pixC values near tide gauge as well; 
# TODO: Repeat with newer SWOT images


# /------------------------------------------------------------------------
#/    Get bounding box to loop over
synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')


# Create an empty DataFrame with 'date' and 'wse_mean' columns
swot_tidal_wse_df = pd.DataFrame(columns=['site_id', 'unit_area', 'datetime', 'pixc_count', 'wse_navd88_mean', 'data_type'])


# /------------------------------------------------------------------------
#/   Loop through sites

for index, site_bbox in synoptic_bbox.iterrows():

    site_id = site_bbox.site_id
    print(site_id)

    #/  Get tidal edge polygon for given site
    tidal_edge_zone = gpd.read_file('../../data/site_zones/water_tidal_forcing_zone.shp')
    tidal_edge_zone = tidal_edge_zone[tidal_edge_zone.site_id == site_id]
    tidal_edge_zone = tidal_edge_zone.to_crs("EPSG:5498")

    # /------------------------------------------------------------------------
    #/  List all cropped SWOT rasters

    out_dir_path = '/Users/flue473/big_data/swot/pixc/cropped_synoptic/' + site_id

    nc_files = glob.glob(f"{out_dir_path}/*.nc")
    nc_files

    # /------------------------------------------------------------------------
    #/ Loop through nc files
    for nc_file in nc_files[0:1]:

        print(nc_file)
        # Get datetime of granule
        # time_granule_end = ds_nad88.attrs.get('time_granule_end', None).split('.')[0]
        time_granule_end = pd.to_datetime(nc_file.split('_')[-4], format='%Y%m%dT%H%M%S', errors='coerce')


        #/  Read in cropped SWOT pixC
        with xr.open_dataset(nc_file, engine='h5netcdf') as ds:
        # group='pixel_cloud',


            # Convert to DataFrame: lat, lon, wse
            ds_xyz_df = pd.DataFrame(np.array(list(zip(ds["latitude"].values, 
                                                    ds["longitude"].values, 
                                                    ds['wse'].values))), 
                                    columns=['latitude', 'longitude', 'wse'])

            # /-----------------------------------------------------------------
            #/  Convert coordinates and height datum
            import pyproj
            from pyproj import CRS, transformer

            # Declare the CRS for the geoid model and the target vertical datum
            # COMBINED CRS:  EGM2008 height with pyproj which is EPSG:3855
            egm2008_crs = CRS("EPSG:4326+3855") 
            nad83_navd88 = CRS("EPSG:5498") # NAD83 / NAVD88 (Orthometric Height)

            # Create a transformer object to convert from EGM2008 to WGS84;    # Note: The EGM2008 geoid model is used to convert ellipsoidal heights to orthometric heights
            transformer = transformer.Transformer.from_crs(crs_from=egm2008_crs, crs_to=nad83_navd88, always_xy=True, allow_ballpark=False)

            # Transform the coordinates and water surface elevation from EGM2008 to NAVD88
            wse_navd88 = transformer.transform(
                ds_xyz_df["longitude"].values, 
                ds_xyz_df["latitude"].values, 
                ds_xyz_df["wse"].values)

            # Convert to DataFrame
            wse_navd88 = pd.DataFrame(np.array(wse_navd88).T, columns=['longitude', 'latitude', 'wse_navd88'])


            # Convert each point in the cloud becomes a GeoDataFrame row
            from shapely.geometry import Point
            wse_navd88 = gpd.GeoDataFrame(
                {
                    "latitude": wse_navd88.latitude.values,
                    "longitude": wse_navd88.longitude.values,
                    "wse_navd88": wse_navd88.wse_navd88.values,
                    "points": ds["points"].values  # Point IDs or indices
                },
                geometry=[Point(lon, lat) for lon, lat in zip(wse_navd88.longitude.values, wse_navd88.latitude.values)], 
                crs = "EPSG:5498"
            )

            # Clip points within the tidal edge polygon
            wse_navd88_clip = wse_navd88[wse_navd88.geometry.within(tidal_edge_zone.geometry.iloc[0])]


            # Create a DataFrame with the new row
            new_row = pd.DataFrame({
                'site_id': [site_id],
                'datetime': [time_granule_end],
                'unit_area': [float(tidal_edge_zone.geometry.area.iloc[0]*10e6)],
                'pixc_count': [wse_navd88_clip["wse_navd88"].notna().sum()],
                'wse_navd88_mean': [wse_navd88_clip['wse_navd88'].mean().item()],
                'data_type' :['swot_nearshore']
                })


            # Append the new row to the existing DataFrame using concat
            swot_tidal_wse_df = pd.concat([swot_tidal_wse_df, new_row], ignore_index=True)




#%%-----------------------------------------------------------------

# Convert the datetime from UTC to EST
swot_tidal_wse_df["date"] = pd.to_datetime(swot_tidal_wse_df["date"], utc=True)
swot_tidal_wse_df["datetime_est"] = swot_tidal_wse_df["date"].dt.tz_convert("US/Eastern")

swot_tidal_wse_df = swot_tidal_wse_df.rename(columns={'data_type': 'zone_name'})

#/   Save to CSV
swot_tidal_wse_df.to_csv('../../output/results/swot_wse_synoptic_nearshore_v01.csv', index=False)





# Filter points that fall within the polygon
# points_in_polygon = wse_navd88[wse_navd88.geometry.within(tidal_edge_zone)]

# Extract the indices of points that are inside the polygon
# filtered_indices = points_in_polygon["points"]

# Filter the original dataset to include only points within the polygon
# clipped_ds = ds.sel(points=filtered_indices)




# # Rewrite the dataset with the new coordinates and water surface elevation
# ds_nad88 = (
#     ds.copy()
#     .assign_coords(
#         latitude=("points", ds["latitude"].values),
#         longitude=("points", ds["longitude"].values))
#     # .assign(wse_navd88= ('points', wse_navd88['wse_navd88'].values))
#     .assign(wse_navd88= ('points', wse_navd88['wse_navd88'].values))
#     .drop_vars(['wse', 'height', 'water_frac','cross_track', 'sig0', 'classification', 'classification_qual'])
#     .set_index(points=["latitude", "longitude"])  # Use latitude and longitude as indices
#     .unstack("points")
#     # .rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=True)
#     .rio.write_crs("EPSG:5498", inplace=True)
# )


#             # Clip points within polygon
#             clipped = ds_nad88.rio.clip(tidal_edge_zone.geometry, tidal_edge_zone.crs, drop=True)

#             # Filter points within the polygon
#             # filtered_points = ds_nad88[ds_nad88.geometry.within(tidal_edge_zone.geometry.iloc[0])]

#             # Get average for polygon
#             wse_navd88_mean = clipped['wse_navd88'].mean().item()

#             # Create a DataFrame with the new row
#             new_row = pd.DataFrame({
#                 'site_id': [site_id],
#                 'data_type' :['swot_nearshore'],
#                 'date': [time_granule_end],
#                 'wse_navd88_mean': [wse_navd88_mean]})


#             # Append the new row to the existing DataFrame using concat
#             swot_tidal_wse_df = pd.concat([swot_tidal_wse_df, new_row], ignore_index=True)


# # /-----------------------------------------------------------------
# #/   Save to CSV
# swot_tidal_wse_df.to_csv('../../output/results/swot_wse_synoptic_tidal_edge.csv', index=False)






# # /------------------------------------------------------------------------
# #/    Function to reproject SWOT water surface elevation from EGM2008 to NAVD88
# #    vecrtorized
# def reproj_swot(long, lat, wse):

#     import pyproj
#     from pyproj import CRS, transformer

#     # Declare the CRS for the geoid model and the target vertical datum
#     # COMBINED CRS:  EGM2008 height with pyproj which is EPSG:3855
#     egm2008_crs = CRS("EPSG:4326+3855") 
#     nad83_navd88 = CRS("EPSG:5498") # NAD83 / NAVD88 (Orthometric Height)

#     # Create a transformer object to convert from EGM2008 to WGS84;    # Note: The EGM2008 geoid model is used to convert ellipsoidal heights to orthometric heights
#     transformer = transformer.Transformer.from_crs(crs_from=egm2008_crs, crs_to=nad83_navd88, always_xy=True, allow_ballpark=False)


#     func = lambda x, y, z: transformer.transform(x, y, z)

#     # func = lambda x, y: np.sqrt(x**2 + y**2)
#     return xr.apply_ufunc(func, long, lat, wse)

# reproj_swot(ds_xyz_df["longitude"].values, 
#             ds_xyz_df["latitude"].values, 
#             ds_xyz_df["wse"].values)



# Apply Pyproj transformer using xarray's vectorized apply_ufunc
# transformed_coords = xr.apply_ufunc(
#     transformer.transform,
#     ds["longitude"],
#     ds["latitude"],
#     ds["wse"],
#     vectorize=True,  # Allow vectorized operations
#     dask="parallelized",  # Enable Dask for large datasets (optional)
#     output_dtypes=(float, float, float)  # Specify the output types (x, y, z)
# )






#         data_var = ds['wse']
#         data_var = data_var.rio.write_crs("EPSG:5498")
#         # Update the NoData value using rioxarray
#         data_var.rio.set_nodata(np.nan, inplace=True)

#         data_var = data_var.rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=False)

#         # Clip to polygon
#         clipped = data_var.rio.clip(tidal_edge_zone.geometry, tidal_edge_zone.crs, drop=True)
#         # Get average for polygon
#         wse_mean_value = clipped.mean().item()

#         # ds_nad99 = ds_nad88.swap_dims({"points": "x"}).swap_dims({"points": "y"})

#         ds_nad88

#         # ds_nad88.set_index(points=["y", "x"])

#         # Subset to a single variable
#         ds_nad88 = ds_nad88['wse_navd88']

#         # /-----------------------------------------------------------------
#         #/  
#         # Reproject tidal zone polygon
#         tidal_edge_zone = tidal_edge_zone.to_crs("EPSG:5498")




#         # Update the NoData value using rioxarray
#         ds.rio.set_nodata(np.nan, inplace=True)
#         ds_nad88.nodata= np.nan #rio.set_nodata(np.nan, inplace=True)

#         # Clip to polygon
#         clipped = ds_nad88.rio.clip(tidal_edge_zone.geometry, tidal_edge_zone.crs, drop=True)

#         # Get average for polygon
#         wse_navd88_mean = clipped.mean().item()



# ds = ds.expand_dims(time=[time_granule_end])
# Set CRS again
# ds = ds.rio.write_crs(swot_crs)


# # /------------------------------------------------------------------------
# #/
# #%% 
# import numpy as np
# import geopandas as gpd
# import glob
# import os
# import xarray as xr
# from pyproj import CRS

# # /-------------------------------------------------------------------------------
# #/  Get SWOT water elevation
# swot_tidal_wse_df = pd.read_csv('../../output/results/swot_wse_synoptic_tidal_edge.csv')
# swot_tidal_wse_df['date'] = pd.to_datetime(swot_tidal_wse_df['date'], errors='coerce')

# swot_tidal_wse_df = pd.merge(swot_tidal_wse_df, site_name_id_lut, on='site_id', how='left')
# swot_tidal_wse_df['zone_name'] = 'SWOT'


# # /-------------------------------------------------------------------------------
# #/  Get bounding box
# synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')


# # /-------------------------------------------------------------------------------
# #/  Get SWOT scenes
# out_dir_path = '../../../data/swot/pixc/' + site_id + '/cropped'
# output_nc_file_path = out_dir_path + '/' + root + "_cropped.nc"

# # Create the directory if it doesn't exist
# if not os.path.exists(out_dir_path): os.makedirs(out_dir_path)

# # Write the cropped dataset to a NetCDF file with compression
# encoding = {var: {'zlib': True} for var in ds_cropped.data_vars}
# ds_cropped.to_netcdf(output_nc_file_path, mode='w', encoding=encoding)



# # Loop through site bbox
# for index, site_bbox in synoptic_bbox.iterrows():

#     site_id='GCW'
#     dir_path = '/Users/flue473/big_data/swot/pixc/' + site_id
    
#     nc_files = glob.glob(f"{dir_path}/*.nc")

#     # Loop through netCDF files
#     for nc_file in nc_files:  # [0:1]: 

#         # Get filename without extension
#         base_name = os.path.basename(nc_file)
#         root, _ = os.path.splitext(base_name)
#         print(root)

#         with xr.open_dataset(nc_file, group='pixel_cloud', engine='h5netcdf') as ds:
#             swot_crs = CRS.from_wkt(ds.crs.crs_wkt)

# # SWOT measurements reference: WGS84 Ellipsoid (vertical datum).
# # Processed data often references: Geoid models like EGM2008 for scientific applications.
# import xarray as xr

# nc_file = '/Users/flue473/big_data/swot/pixc/CRC/SWOT_L2_HR_PIXC_004_453_228L_20231008T000058_20231008T000109_PGC0_01.nc'
# # '/Users/flue473/big_data/swot/pixc/CRC/SWOT_L2_HR_PIXC_008_453_228L_20231230T110120_20231230T110131_PGC0_02.nc'

# ds = xr.open_dataset(nc_file, group='pixel_cloud', engine='h5netcdf')
    
# ds.crs.crs_wkt
# data_var = data_var.rio.write_crs(swot_crs)
# egm2008_crs = CRS.from_proj4("+proj=latlong +datum=WGS84 +geoidgrids=egm2008-1.pgm") # Ellipsoid from SWOT

# In SWOT: variable 'geoid' is geoid_height_above_reference_ellipsoid  source EGM2008 (Pavlis et al., 2012) 
# swot_crs = CRS.from_wkt(ds.crs.crs_wkt) #.to_epsg()
# Geoid height above the reference ellipsoid with a correction to refer the value to the mean tide system, i.e. includes the permanent tide (zero frequency).  This value is reported for reference but is not applied to the reported height. 
#  geoid: Model for geoid height above the reference ellipsoid whose parameters are given in the global attributes of the product.  The geoid model is EGM2008 [6].  The geoid model includes a correction to refer the value to the mean tide system (i.e., it includes the zero-frequency permanent tide). • solid_earth_tide: Model for the solid Earth (body) tide height. The reported value is calculated using Cartwright/Taylor/Edden [7] [8] tide-generating potential coefficients and consists of the second and third degree constituents. The permanent tide (zero frequency) is not included. • load_tide_fes: Model for geocentric surface height displacement from the load tide. The value is from the FES2022b model [9]. • load_tide_got: Model for geocentric surface height displacement from the load tide. The value is from the GOT4.10c ocean tide model [10]. • pole_tide: Model for the surface height displacement from the geocentric pole tide. The value is the sum total of the contribution from the solid-Earth (body) pole tide height [11], and a model for the load pole tide height [12]. The value is computed using the reported Earth pole location after correction for a linear drift [13]: in 

# Output CRS: NAVD88 vertical heights
# navd88_crs = CRS("EPSG:5703")  # NAVD88 EPSG is vertical-only

# # Combine horizontal CRS with NAVD88 vertical CRS to create a compound CRS
# compound_crs = CRS.from_dict({
#     "name": "WGS84 + NAVD88",
#     "type": "CompoundCRS",
#     "components": [CRS("EPSG:4326"), navd88_crs]
# })

# Perform the transformation
# Your input WGS84 coordinates (lon, lat, ellipsoid height in meters)
# lon, lat, ellipsoid_height = -75.0, 40.0, 50.0  # Example values
# transformer.transform(lon, lat, ellipsoid_height)

# # #-----------------------------------------------------------------

# import pyproj
# lat = 43.70012234
# lon = -79.41629234
# z = 100
# wgs84 = pyproj.crs.CRS.from_epsg(4979)
# nad83_navd88 = pyproj.crs.CRS.from_epsg(5498)

# transformer = pyproj.transformer.Transformer.from_crs(crs_from=wgs84, crs_to=nad83_navd88, allow_ballpark=0) #, always_xy=True)

# # Perform the transformation
# oot = transformer.transform(lon, lat, z) # [2]
# oot

# #------------------------------------------------------------------
# Pyproj can use datum grids from NOAA's VDatum system to convert between vertical datums.
# Vyperdatum is a Python package that provides access to NOAA's VDatum system for vertical datum transformations.
# https://github.com/noaa-ocs-hydrography/vyperdatum

# import os
# # Set the environment variable to point to VDatum's grids directory
# # os.environ['VYPER_GRIDS'] = "/Users/flue473/Downloads/vdatum"
# os.environ['VYPER_GRIDS'] = "/Users/flue473/anaconda3/envs/fresh2/lib/python3.9/site-packages/vyperdatum/assets/vdatum"

# # https://pypi.org/project/vyperdatum/
# # Download NOAA proj.db from here:  https://zenodo.org/records/15184045

# from vyperdatum.vdatum import VyperDatum

# # Step 1: Initialize VyperDatum to set up NOAA VDatum grids
# vd = VyperDatum()

# # Your input WGS84 coordinates (lon, lat, elevation in meters)
# lon, lat, ellipsoid_height = -75.0, 40.0, 50.0  # Example values

# # Step 2: Convert from WGS84 (Ellipsoid height) to NAVD88 (Orthometric height)
# converted = vd.transform(
#     longitude=lon,
#     latitude=lat,
#     altitude=ellipsoid_height,
#     source_crs='EPSG:4326',  # WGS84
#     target_crs='EPSG:5703'   # NAVD88
# )

# print(f"Converted NAVD88 Height: {converted['altitude']} meters")

# # Combine horizontal CRS with NAVD88 vertical CRS to create a compound CRS
# compound_crs = CRS.from_dict({
#     "name": "WGS84 + NAVD88",
#     "type": "CompoundCRS",
#     "components": [CRS("EPSG:4326").to_dict(), CRS("EPSG:3855").to_dict() ] })

        # egm2008_crs = CRS.from_proj4("proj +proj=vgridshift +grids=egm08_25.gtx")  # EGM2008 Geoid Model (Ellipsoid)
        # wgs84 = CRS("EPSG:4979")  # WGS84 (Ellipsoid)
        # navd88 = CRS("EPSG:5703") # NAVD88 (Orthometric Height)
        # wgs84_navd88 = CRS("EPSG:6360") #  (NAVD88 combined with WGS84 in the U.S.)s