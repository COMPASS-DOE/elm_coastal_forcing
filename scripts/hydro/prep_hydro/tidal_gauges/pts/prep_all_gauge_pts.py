
import pandas as pd
import geopandas as gpd
import numpy as np

# TODO: include LE gauges


#%%------------------------------------------------------------
# VECOS stations
vecos = (pd.read_csv("../../data/tide_gauges/all_gauges_list/vecos_all_stations_coords.csv")
         .query('Active == "y"')
         .filter(items=['StationCode','StationName','Latitude', 'Longitude'])
         .rename(columns={'StationCode': 'id', 
                          'StationName': 'name'})
        )

vecos['type'] = 'VECOS - Water Level' 


#%%------------------------------------------------------------
# NOAA active stations

# Tide water levels
noaa_wl = (pd.read_csv("../../data/tide_gauges/all_gauges_list/noaa_stations_waterlevel_MD_DL_VA.csv")
           .filter(items=['id','name','lat', 'lng'])
           .rename(columns={'lat': 'Latitude', 
                            'lng': 'Longitude'})
           )

noaa_wl['type'] = 'NOAA - Water Level' 


# Tide predictions
noaa_tp = (pd.read_csv("../../data/tide_gauges/all_gauges_list/noaa_stations_tidepredictions_MD_DL_VA.csv")
           .filter(items=['id','name','lat', 'lng','type'])
            .rename(columns={'lat': 'Latitude', 
                             'lng': 'Longitude'})
           )

noaa_tp['type'] = np.where(noaa_tp['type'] == 'S', 'NOAA - Subordinate', "NOAA - Harmonics")



#%%------------------------------------------------------------
# CB NERRS active stations
# NOTE: I made manual edits to the CSV to remove spaces before/after column names.

cbnerrs = (pd.read_csv("../../data/tide_gauges/all_gauges_list/cbnerrs_sampling_stations.csv")
           .query('Status == "Active    "')
           .query('Station_Type == 1')
           .query('NERR_Site_ID in ["cbm                                               ", "cbv                                               "]')
           .filter(items=['Station Code','Station Name', 'Latitude', 'Longitude'])
           .rename(columns={'Station Code':'id', 'Station Name':'name',
                            'Latitude':'Latitude', 'Longitude':'Longitude'})
            )
cbnerrs['Longitude'] = cbnerrs['Longitude'] * -1


cbnerrs['type'] = 'CBNERRS - Water Level' 

cbnerrs


#%------------------------------------------------------------
allstations_df = pd.concat([vecos, noaa_wl, noaa_tp, cbnerrs], ignore_index=True)


allstations_gdf = \
    (gpd.GeoDataFrame(allstations_df, 
                      geometry=gpd.points_from_xy(allstations_df.Longitude, 
                                                  allstations_df.Latitude, 
                                                  crs="EPSG:4269"))
    .to_crs("EPSG:4326")  
    )


# Save the filtered GeoDataFrame to a GeoJSON file
allstations_gdf.to_file("../../data/tide_gauges/all_gauges_list/all_stations_pts.geojson", driver='GeoJSON')


#%%------------------------------------------------------------

# Remove duplicates
gdf = allstations_gdf


# Find pairs of points within 10 meters and drop those with label == "noaa harmonics"
to_drop = []

for i, row in gdf.iterrows():
    for j, other_row in gdf.iterrows():
        if i != j:  # Skip self comparison
            distance = row['geometry'].distance(other_row['geometry'])
            
            if distance <= 0.0005:  # If within 10 meters
                # Mark the index of the row to be dropped if label is "noaa harmonics"
                if row['type'] in ["NOAA - Harmonics", 'VECOS - Water Level'] and i not in to_drop:
                    to_drop.append(i)

gdf.iloc[to_drop]

# Remove the marked rows
gdf = gdf.drop(index=to_drop)


# Save the filtered GeoDataFrame to a GeoJSON file
gdf.to_file("../../data/tide_gauges/all_gauges_list/all_stations_pts_nodups.geojson", driver='GeoJSON')

