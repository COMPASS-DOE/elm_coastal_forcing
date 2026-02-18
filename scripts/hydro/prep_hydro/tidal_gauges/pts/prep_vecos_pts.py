

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

#%%
import datetime as dt

# Convert date string to datetime
df = pd.read_csv('../../../data/buoys/vecos/vecos_all_stations_coords.csv')
df['MostRecentSample'] = pd.to_datetime(df['MostRecentSample'])
df['MostRecentSample'] = df['MostRecentSample'].dt.strftime('%B %d, %Y - %I:%M %p')

# Filter the DataFrame for dates greater than the comparison_date
# filtered_df = df[df['date'] > pd.to_datetime('2025-01-01')]


vecos = \
    (gpd.GeoDataFrame(df,
                      geometry=gpd.points_from_xy(df.Longitude, df.Latitude, crs="EPSG:4269"))
    .to_crs("EPSG:4326")  # Reproject to DEM's CRS: NAD83 / UTM zone 18N
    # .rename(columns={"site": "site_id"})
    )

# Save the filtered GeoDataFrame to a GeoJSON file
vecos.to_file("../../../data/buoys/vecos/vecos_all_stations_pts.geojson", driver='GeoJSON')


# # Convert DataFrame to GeoDataFrame with Point geometries
# gdf = gpd.GeoDataFrame(
#     df, 
#     geometry=df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1),
#     crs="EPSG:4326"  # Use the WGS84 coordinate reference system
# )
# df['geometry'] = df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
