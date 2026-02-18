import numpy as np
import rioxarray


xr.set_options(keep_attrs=True)

# Get bounding box
synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')

# /-------------------------------------------------------------------------
#/  Loop through synoptic sites
import tempfile
import zipfile
from pyproj import CRS

# Loop through sites
for index, site_bbox in synoptic_bbox.iterrows():

    site_id = site_bbox.site_id #.iloc[0]
    # if site_id == 'SWH': continue
    print(site_id)

    # Convert row subset to geodataframe
    site_bbox = gpd.GeoDataFrame([site_bbox], geometry='geometry', crs='EPSG:4326')

    # Get a list of all .nc files in the directory using glob
    dir_path = '../../data/swot/raster/' + site_bbox.site_id.iloc[0]
    nc_files = glob.glob(f"{dir_path}/*.nc")


    ##################
    for nc_file in nc_files: #[0]

        # Get filename without extension
        base_name = os.path.basename(nc_file)
        root, _ = os.path.splitext(base_name)

        print(root)

        # Read in raster
        # with xr.open_dataset(nc_file, engine='h5netcdf') as ds:

        try:
            ds = xr.open_dataset(nc_file, engine='h5netcdf')
            # Get CRS from raster
            swot_crs = CRS.from_wkt(ds.crs.crs_wkt)  # .to_epsg()
        except Exception: continue
            pass


            # reproject bbox
            site_bbox_reproj = site_bbox.to_crs(swot_crs)

            # Extract the bounding box of the polygon
            bounding_box = site_bbox_reproj.geometry.bounds.values[0]

            xmin, ymin, xmax, ymax = bounding_box
            cropped_ds = ds.sel(y=slice(ymin, ymax), x=slice(xmin, xmax))

            # Combine variable selection and slicing
            cropped_ds = cropped_ds[['wse']]
            cropped_ds.rio.write_crs(swot_crs, inplace=True)


            # /----------------------------------------------------------------
            #/   SAVE CROPPED

            out_dir_path = '../../data/swot/raster/' + site_id + '/cropped'
            output_nc_file_path = out_dir_path + '/' + root + "_cropped.nc"

            # Create the directory if it doesn't exist
            if not os.path.exists(out_dir_path): os.makedirs(out_dir_path)

            # Delete the grid mapping variable that's created when clipping the xarray;
            # This can prevent an error when saving to .nc file
            # See this: https://stackoverflow.com/questions/69676744/saving-netcdf-with-grid-mapping-valueerror
            vars_list = list(cropped_ds.data_vars)
            for var in vars_list:
                del cropped_ds[var].attrs['grid_mapping']

            # Write the cropped dataset to a NetCDF file
            print('saved')
            cropped_ds.to_netcdf(output_nc_file_path, mode='w')


