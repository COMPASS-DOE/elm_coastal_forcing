

# Import libraries
import pandas as pd
import geopandas as gpd
import pandas as pd
import xarray as xr
from shapely.geometry import Point
import numpy as np


#%%-------------------------------------------------------------------
def extract_pixc_by_poly(dso, unit, site_id, date):

    # Boolean mask: Check if each point is within any of the polygons
    binary_mask = [ unit.geometry.contains(Point(lon, lat)) for lon, lat in zip(dso["longitude"].values, dso["latitude"].values) ]

    binary_mask = np.array(binary_mask).flatten()

    # Subset the Dataset with the binary mask using .isel()
    nearshore_ds = dso.isel(points=binary_mask, 
                            latitude=binary_mask, 
                            longitude=binary_mask, 
                            wse=binary_mask)

    # Initialize empty dataframe to hold results
    wse_df = pd.DataFrame([{'site_id': site_id,
                            'date': date,
                            'label': 'nearshore',
                            'unit_id': unit.id,
                            'pt_count': nearshore_ds.sizes['wse'],
                            'poly_area': np.nan,
                            'pt_dens': np.nan,
                            'wse_mean': nearshore_ds['wse'].mean().item(),
                            'wse_std': nearshore_ds['wse'].std().item(),
                            'distance': np.nan}])
    
    return wse_df




