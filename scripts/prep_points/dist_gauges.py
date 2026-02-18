# Distance to gauges


import pandas as pd
import geopandas as gpd
import numpy as np

from scripts.config import SITE_CODE_LIST, SYN_PTS_PATH




# Get synoptic points
synoptic_pts = (\
    gpd.read_file(SYN_PTS_PATH)
    .query('zone_num == 3') # Filter to zone 3 only
    .to_crs("EPSG:5070"))  # North America Albers Equal Area: EPSG:5070 - for distance calc in meters


# Get gauge points
disallowed = ["NOAA - Harmonics", "NOAA - Subordinate"]
allgauges_gdf = ( \
    gpd.read_file("../../data/tide_gauges/all_gauges_list/all_stations_pts_nodups.geojson")
    .query("type not in @disallowed")
    .to_crs("EPSG:5070")
    )

cols = [c for c in allgauges_gdf.columns if c != "id"]  # columns to consider to remove duplicates
allgauges_gdf = allgauges_gdf.drop_duplicates(subset=cols)



# Loop through sites
# for site_id in SITE_CODE_LIST:

# Get Shapely geometry arrays for site
geom_a = synoptic_pts.geometry.values
geom_b = allgauges_gdf.geometry.values

# Compute all pairwise distances: |A| x |B| matrix
dist_matrix = np.array([[a.distance(b) for b in geom_b] for a in geom_a])

# Example: build the matrix as a DataFrame with ids as index/columns
dist_df = pd.DataFrame(
    dist_matrix,
    index=synoptic_pts["site_id"].values,   # or gdf_a.index
    columns=allgauges_gdf["id"].values  # or gdf_b.index
)

# Convert to long/tidy format: id_a, id_b, distance
pairs_df = dist_df.stack().reset_index()
pairs_df.columns = ["site_id", "gauge_id", "distance"]


pairs_df = pairs_df[pairs_df['distance'] <= 5*10e3]

pairs_df
