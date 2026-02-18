
import os
import numpy as np
import numpy.ma as ma
import pandas as pd
import geopandas as gpd
from shapely import Point

#%%-----------------------------------------------------------------------------------
#  Open water point of each site

site_ow_sonde = (
    pd.read_csv('../data/raw/transect_coords/compass_synoptic_wsonde.csv')
    .reset_index(drop=True)
    )

# Create "Point" geometry from latitude and longitude
site_ow_sonde['geometry'] = site_ow_sonde.apply(lambda row: Point(row['long'], row['lat']), axis=1)

# Convert the DataFrame into a GeoDataFrame
gsite_ow_sonde = gpd.GeoDataFrame(site_ow_sonde, geometry='geometry')

# Set the Coordinate Reference System (CRS)
gsite_ow_sonde.set_crs(epsg=5498, inplace=True)  # EPSG:4326 = WGS84 Latitude/Longitude

gsite_ow_sonde.to_file('../data/raw/transect_coords/compass_synoptic_wsonde.geojson')


#%%-----------------------------------------------------------------------------------
#  Tide gauge points
tide_gauges = (
    pd.read_csv('../../data/tide_gauges/synoptic_tide_gauges.csv')
    .reset_index(drop=True)
    )

# Create "Point" geometry from latitude and longitude
tide_gauges['geometry'] = tide_gauges.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)

# Convert the DataFrame into a GeoDataFrame
tide_gauges = gpd.GeoDataFrame(tide_gauges, geometry='geometry')

# Set the Coordinate Reference System (CRS)
tide_gauges.set_crs(epsg=5498, inplace=True)  # EPSG:4326 = WGS84 Latitude/Longitude

tide_gauges.to_file('../../data/tide_gauges/synoptic_tide_gauges.geojson')


# --------------------------------------------------------------------------------------------------------------------
# Read file of synoptic site coords

# Read in site/zone coordinate file
synoptic = \
    (pd.read_csv('../../data/raw/transect_coords/compass_synoptic.csv')
    .assign(grid_points = lambda x: x.site_id + '_' + x.zone_id)
    .assign(site_cat = 'synoptic')
    .drop(columns=['distance'])
     )

# TODO: are the original coordinates from Ben on WGS84 or NAD83 datum?
synoptic = \
    (gpd.GeoDataFrame(synoptic,
                      geometry=gpd.points_from_xy(synoptic.long, synoptic.lat, crs="EPSG:4269"))
    .to_crs("EPSG:26918")  # Reproject to DEM's CRS: NAD83 / UTM zone 18N
    .rename(columns={"site": "site_id"})
    )


# WGS84 - Save synoptic points to file
synoptic_wgs84 = (synoptic.to_crs("EPSG:4326").reset_index())
synoptic_wgs84.to_file('../data/processed/synoptic_pts_wgs84.geojson')


# Save points
if 1:
    all_sites_utm.to_file('../../../data/site_pts/all/all_sites_utm_v01.geojson')
    all_sites_wgs84.to_file('../../../data/site_pts/all/all_sites_pts_wgs84_v01.geojson')



#--------------------------------------------------------------------------
#%% Get EXCHANGE sites

# Declare columns to keep
cols2keep = \
    ['kit_id', 'water_latitude', 'water_longitude', 'sediment_latitude', 'sediment_longitude',
    'wetland_latitude', 'wetland_longitude', 'transition_latitude', 'transition_longitude',
    'upland_latitude', 'upland_longitude']

# Read file of site locations;
# FIXME: Modified input longitude for two points;  one missing minus sign; other was lat=29 not 39
ex_sites = \
    (pd.read_csv('../../../data/exchange/EC1_Metadata_CollectionLevel_EFmod.csv')
    .loc[:, cols2keep]
    .melt(id_vars='kit_id'))

# Split column names into two; split by underscore
ex_sites[['zone', 'var']] = pd.DataFrame(ex_sites.variable.str.split('_').tolist(), columns=['zone', 'variable2'])

# Drop "var" column
ex_sites = ex_sites.drop(columns=['variable'])

# pivot lat/long into different columns
ex_sites = pd.pivot_table(ex_sites, index=['kit_id', 'zone'], values='value', columns='var')

# Convert coords to point
ex_sites = (
    gpd.GeoDataFrame(ex_sites, geometry=gpd.points_from_xy(ex_sites.longitude, ex_sites.latitude, crs="EPSG:4269"))
    .to_crs("EPSG:26918")
    .reset_index()
    .rename(columns={"kit_id": "site_id"}))

ex_sites['site_cat'] = 'exchange'

#--------------------------------------------------------------------------
#%% Combine sites
all_sites_utm = (pd.concat([ex_sites, syn_sites])
            .reset_index())

all_sites_wgs84 = (all_sites_utm.to_crs("EPSG:4326"))

#--------------------------------------------------------------------------
# Save points
if 1:
    all_sites_utm.to_file('../../../data/site_pts/all/all_sites_utm_v01.geojson')
    all_sites_wgs84.to_file('../../../data/site_pts/all/all_sites_pts_wgs84_v01.geojson')

    # Saving to shapefile for GEE
    all_sites_utm.to_file('../../../data/site_pts/all/all_sites_utm_v01.shp')
    all_sites_wgs84.to_file('../../../data/site_pts/all/all_sites_pts_wgs84_v01.shp')
