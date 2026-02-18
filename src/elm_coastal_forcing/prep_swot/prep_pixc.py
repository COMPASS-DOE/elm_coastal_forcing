
from logging import root
from pyproj import CRS, transformer
import pandas as pd
import xarray as xr
import numpy as np
import geopandas as gpd
from shapely.geometry import Point



# /-----------------------------------------------------------------
#/  Declare Projections

# COMBINED CRS:  EGM2008 height with pyproj which is EPSG:3855:  CRS for the geoid model and the target vertical datum
# In SWOT: variable 'geoid' is geoid_height_above_reference_ellipsoid  source EGM2008 (Pavlis et al., 2012) 
# Geoid height above the reference ellipsoid with a correction to refer the value to the mean tide system, i.e. includes the permanent tide (zero frequency).  This value is reported for reference but is not applied to the reported height. 
#  geoid: Model for geoid height above the reference ellipsoid whose parameters are given in the global attributes of the product.  The geoid model is EGM2008 [6].  The geoid model includes a correction to refer the value to the mean tide system (i.e., it includes the zero-frequency permanent tide). • solid_earth_tide: Model for the solid Earth (body) tide height. The reported value is calculated using Cartwright/Taylor/Edden [7] [8] tide-generating potential coefficients and consists of the second and third degree constituents. The permanent tide (zero frequency) is not included. • load_tide_fes: Model for geocentric surface height displacement from the load tide. The value is from the FES2022b model [9]. • load_tide_got: Model for geocentric surface height displacement from the load tide. The value is from the GOT4.10c ocean tide model [10]. • pole_tide: Model for the surface height displacement from the geocentric pole tide. The value is the sum total of the contribution from the solid-Earth (body) pole tide height [11], and a model for the load pole tide height. 
# The value is computed using the reported Earth pole location after correction for a linear drift [13]: in 
egm2008_crs = CRS("EPSG:4326+3855")  
# egm2008_crs = CRS.from_proj4("+proj=latlong +datum=WGS84 +geoidgrids=egm2008-1.pgm") # Ellipsoid from SWOT

# NAD83 / NAVD88 (Orthometric Height)
nad83_navd88 = CRS("EPSG:5498")  # This is the destination proj.
# navd88_crs = CRS("EPSG:5703")  # NAVD88 EPSG is vertical-only


# Create a transformer object to convert from EGM2008 to WGS84;    
# # Note: The EGM2008 geoid model is used to convert ellipsoidal heights to orthometric heights
transformer = transformer.Transformer.from_crs(crs_from=egm2008_crs, crs_to=nad83_navd88, always_xy=True, allow_ballpark=False)


# /-----------------------------------------------------------------
#/   FUNCTION PREPROCESSING PIXC FOR SYNOPTIC SITES
def prep_pixc(ds, site_bbox):

    site_id = site_bbox.site_id.iloc[0] #.values

    # Extract the bounding box of the polygon
    xmin, ymin, xmax, ymax = site_bbox.geometry.bounds.values[0]


    # Crop the dataset to the bounding box
    ds = ds.where(
        (ds.latitude >= ymin) &
        (ds.latitude <= ymax) &
        (ds.longitude >= xmin) &
        (ds.longitude <= xmax), drop=True).dropna(dim='points', how='all')

    # NOTE: Slicing should work; but dimensions/indexes throw error
    # subset = ds.sel(latitude=slice(ymin, ymax), longitude=slice(xmin, xmax))

    # Filter by land cover classificaiton
    ds = ds.where(~ds.classification.isin([1, 2, 6, 7]), drop=True)

    # Compute WSE from height
    # WSE = (H −geoid_height −solid_earth_tide_height −load_tide_height −pole_tide_height)
    ds['wse'] = ds.height - ds.geoid - ds.solid_earth_tide - ds.pole_tide - ds.load_tide_got

    # Select variables
    ds = ds[['wse', 'height', 'water_frac', 'cross_track', 'sig0', 'classification', 'classification_qual']]


    # /-----------------------------------------------------------------
    #/  Convert coordinates and height datum:  NAD83 / NAVD88 (Orthometric Height)

    # Transform the coordinates and water surface elevation from EGM2008 to NAVD88
    wse_navd88 = transformer.transform(
                ds["longitude"].values, 
                ds["latitude"].values, 
                ds["wse"].values)
    
    #/   Reinsert reprojected coords and wse to netcdf object
    ds['longitude'] = wse_navd88[0]
    ds['latitude'] = wse_navd88[1]

    ds = ds.drop_vars("wse")  # Remove the existing variable
    ds['wse'] = wse_navd88[2]

    # Set CRS
    ds.rio.write_crs(nad83_navd88, inplace=True)  # To reread CRS from file: ds.rio.crs


    #%%-----------------------------------------------------------------
    # Crop PIXC to estuary waters

    # Get polygon of estuary
    estuary = gpd.read_file('../../output/results/coastlines/CUSP_site_estuary_poly_mansel/estuary_poly_' + site_id + '_mansel.shp').dissolve()

    #%% Convert to geodataframe for spatial operations
    geometry = [Point(x, y) for x, y in zip(ds['longitude'], ds['latitude'])]

    # Boolean mask: Check if each point is within any of the polygons
    binary_mask = [ estuary.contains(Point(lon, lat)) for lon, lat in zip(ds["longitude"].values, ds["latitude"].values) ]
    binary_mask = np.array(binary_mask).flatten() 

    # Subset the Dataset with the binary mask using .isel()
    filtered_ds = ds.isel(points=binary_mask, latitude=binary_mask, longitude=binary_mask, wse=binary_mask)

    # Return the processed dataset
    return filtered_ds





#%%-------------------------------------------------
if __name__ == '__main__':

    # Get input SWOT PIXC file
    nc_file = '/Users/flue473/big_data/swot/pixc/original/GCW/SWOT_L2_HR_PIXC_015_369_223L_20240521T121429_20240521T121440_PIC0_01.nc'
    ds = xr.open_dataset(nc_file, group='pixel_cloud', engine='h5netcdf').load()

    # Get site bounding box
    synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')
    site_bbox = synoptic_bbox.iloc[3,:]

    # Convert row subset to geodataframe
    site_bbox = gpd.GeoDataFrame([site_bbox], geometry='geometry', crs='EPSG:4326')

    # Extract the bounding box of the polygon
    xmin, ymin, xmax, ymax = site_bbox.geometry.bounds.values[0]


    # /----------------------------------------------------------------
    #/   SAVE CROPPED

    out_dir_path = f'/Users/flue473/big_data/swot/pixc/cropped_synoptic/{site_id}'
    output_nc_file_path = out_dir_path + '/' + root + "_cropped_navd88.nc"

    # Create the directory if it doesn't exist
    if not os.path.exists(out_dir_path): os.makedirs(out_dir_path)


    # Write the cropped dataset to a NetCDF file with compression
    encoding = {var: {'zlib': True} for var in dso.data_vars}
    dso.to_netcdf(output_nc_file_path, mode='w', encoding=encoding)



    # Delete the grid mapping variable that's created when clipping the xarray;
    # This can prevent an error when saving to .nc file
    # See this: https://stackoverflow.com/questions/69676744/saving-netcdf-with-grid-mapping-valueerror
    # vars_list = list(cropped_ds.data_vars)
    # for var in vars_list:
    #     del cropped_ds[var].attrs['grid_mapping']

    # Write the cropped dataset to a NetCDF file
    # cropped_ds.to_netcdf(output_nc_file_path, mode='w')


