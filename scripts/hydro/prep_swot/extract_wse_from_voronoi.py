# Description: This script extracts water surface elevation (WSE) from SWOT PIXC files for nearshore Voronoi units. 
# It loops through each site, reads the corresponding Voronoi shapefile, and then iterates through the cropped PIXC netCDF files to extract WSE statistics for each unit. The results are compiled into a DataFrame and saved as a CSV file.


import pandas as pd
import geopandas as gpd
import glob
from pathlib import Path

from scripts.config import SITE_CODE_LIST, NEARSHORE_UNIT_DIR, CROPPED_PIXC_DIR, NEARSHORE_WSE_DIR
from scripts.dataio import load_cropped_pixc_file
from src.elm_coastal_forcing.prep_swot.extract_pixc_by_poly import extract_pixc_by_poly


# Function processing site
def process_site(site_id, pieces):
    print(site_id)

    # Read polygons once per site
    nearshore_unit = gpd.read_file(NEARSHORE_UNIT_DIR / f'estuary_poly_{site_id}_mansel_site.shp')
    # Convert rows to a list of dicts or records once
    units = list(nearshore_unit.itertuples())  # faster than iterrows

    # Find all cropped SWOT files for this site
    nc_files = glob.glob(str(Path(CROPPED_PIXC_DIR) / site_id / '*_cropped_navd88.nc'))

    for nc_file in nc_files:
        dso, date = load_cropped_pixc_file(nc_file)

        # For each nearshore unit polygon
        for unit in units:
            wse_df = extract_pixc_by_poly(dso, unit, site_id, date)
            if wse_df is None or wse_df.empty:
                continue
            wse_df['site_id'] = site_id
            pieces.append(wse_df)




#%%   RUN EXTRACTION  ------------------------------------------
# Initialize empty dataframe to hold results
nearshore_wse_df = pd.DataFrame(columns=['site_id', 'date', 'label',
                                         'unit_id', 'pt_count', 'poly_area', 'pt_dens', 
                                         'wse_mean', 'wse_std', 'distance'])

pieces = []   # List to hold pieces for concatenation

# Main loop
for site_id in SITE_CODE_LIST:
    process_site(site_id, pieces)

    # Append the new row to the existing DataFrame using concat
    nearshore_wse_df = pd.concat(pieces, ignore_index=True)


# Save to CSV
nearshore_wse_df.to_csv(NEARSHORE_WSE_DIR / f'{site_id}_swot_wse_nearshore_v04.csv', index=False)


#%% Parallel processing using concurrent.futures   -----------------------------------
from concurrent.futures import ProcessPoolExecutor

def process_site_collect(site_id):
    pieces = []
    process_site(site_id, pieces)
    return pd.concat(pieces, ignore_index=True) if pieces else None

with ProcessPoolExecutor() as ex:
    results = list(ex.map(process_site_collect, SITE_CODE_LIST))

# combine all sites
pieces = [r for r in results if r is not None]
all_wse = pd.concat(pieces, ignore_index=True)



# # Loop through sites   #%%------------------------------------------
# for site_id in SITE_CODE_LIST:

#     # Get site ID
#     print(site_id)

#     # Get nearshore Voronoi unit(s) nearest synoptic transect  ------------------------------
#     nearshore_unit = gpd.read_file(NEARSHORE_UNIT_DIR / f'estuary_poly_{site_id}_mansel_site.shp')

#     # Get a list of all .nc files in the PIXC directory using glob
#     nc_files = glob.glob(f'{CROPPED_PIXC_DIR}/{site_id}/*_cropped_navd88.nc')


#     #%%  EXTRACT WSE FROM PIXC -------------------------------------------------------------

#     # Loop through netCDF files of raw SWOT PIXC files
#     for nc_file in nc_files:

#         dso, date = load_cropped_pixc_file(nc_file)

#         for _, unit in nearshore_unit.iterrows():

#             wse_df = extract_pixc_by_poly(dso, unit, site_id, date)
#             wse_df['site_id'] = site_id
#             pieces.append(wse_df)





# nearshore_wse_df = pd.concat(pieces, ignore_index=True)

# # Loop through nearshore units
# for index, unit in nearshore_unit.iterrows():

#     print(unit.id)
    
#     # Run extraction
#     wse_df = extract_pixc_by_poly(dso, unit, date)

#     # Append the new row to the existing DataFrame using concat
#     nearshore_wse_df = pd.concat([nearshore_wse_df, wse_df], ignore_index=True)


# # Get filename without extension
# base_name = os.path.basename(nc_file)
# root, _ = os.path.splitext(base_name)
# date = pd.to_datetime(root.split('_')[8], format='%Y%m%dT%H%M%S', errors='coerce')
# # Read in PixC file and load into memory  # group='pixel_cloud'
# with xr.open_dataset(nc_file, engine='h5netcdf').load() as dso:    