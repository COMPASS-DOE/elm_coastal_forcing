#!/usr/bin/env python3

import rasterstats
from rasterstats import zonal_stats
import pandas as pd
import geopandas as gpd
# pip install py3dep pandas
import pandas as pd
from py3dep import elevation_bycoords  # HyRiver
from shapely.geometry import Point

import py3dep

from scripts.config import DATA_DIR, RESULTS_DIR

#-----------------------------------------------------------------------------------------------------------------------
# Read site coords with DEM tile IDs

# Get EXCHANGE SITES
sites = ( \
    pd.read_csv(DATA_DIR / 'synoptic_sites/pts/exchange/ex_sites_pts_demtileid.csv') \
    .query("latitude.notna()")
    )

sites['site_type'] = 'EXCHANGE'

# # Create geometry column from lon/lat
# geometry = [Point(xy) for xy in zip(sites["longitude"], sites["latitude"])]
# # Convert to GeoDataFrame
# sites_gdf = gpd.GeoDataFrame(sites, geometry=geometry, crs="EPSG:4326")  # WGS84
# buffered_areas = sites_gdf.buffer(0.0005)
# dem_elev = py3dep.get_dem(buffered_areas.iloc[0], resolution=10)

# Prep coords
coords = list(zip(sites["longitude"], sites["latitude"]))


# Use 3DEP static DEM VRTs ("tep") or The National Map bulk point service ("tnm")
# returns list of meters  [1](https://docs.hyriver.io/autoapi/py3dep/py3dep/index.html)
elev_m = elevation_bycoords(coords, crs=4326, source="tep")  

sites["elevation_m"] = elev_m

sites = sites.drop(columns=['zone_id','dem_tile', 'Comment', 'Unnamed: 8'],
                    errors="ignore")

sites = sites[['site_type', 'kit_id', 'zone_name', 'region', 'latitude', 'longitude', 'elevation_m']]

sites.to_csv(RESULTS_DIR / "site_pts/exchange_sites_elev.csv", index=False)




# # You can then use the buffered areas with py3dep.get_dem for the entire raster,
# # or sample points within these new geometries for specific elevations.

# # Example of getting DEM for a buffered area (using the first buffered geometry)
# # Note: This requires the geometry to be within the 3DEP service area (primarily CONUS)
# dem_data = py3dep.get_dem(buffered_areas.iloc[0], resolution=10) #

# from py3dep import get_map
# import geopandas as gpd
# import rioxarray

# # Define buffer around points
# gdf = gpd.read_file("points.shp").to_crs(4326)
# gdf["geometry"] = gdf.buffer(500)  # 500 m buffer

# # Download DEM covering AOI
# dem_path = get_map(bounds=gdf.total_bounds, resolution=1, crs=4326)

# # Open DEM and clip to buffer
# dem = rioxarray.open_rasterio(dem_path)
# for geom in gdf.geometry:
#     clipped = dem.rio.clip([geom], gdf.crs)
#     mean_elev = float(clipped.mean().values)
#     print(mean_elev)