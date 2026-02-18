#%% 
from pyproj import CRS
import numpy as np
import pandas as pd 
import geopandas as gpd



#%%-------------------------------------------------------------------------
def buffer_nearshore_units(sonde_pt, estuary, estuary_mask=None):
    
    """ Make a buffer around the sonde point, and clip to the estuary polygon.
        Then find the closest polygon to the sonde point.
    """

    # Make buffer around sonde point
    sonde_buffer = sonde_pt.buffer(0.01)  
    nearshore_unit = gpd.GeoDataFrame.from_features(sonde_buffer, crs=CRS("EPSG:5498"))

    if estuary_mask is not None:
        # Clip buffer with coastline
        nearshore_unit = gpd.overlay(nearshore_unit, estuary, how='intersection')

    # Use explode to split into individual polygons
    nearshore_units = nearshore_unit.explode(index_parts=True).reset_index(drop=True)

    # Find the Closest Polygon; ie the row with the smallest distance
    nearshore_units['distance'] = nearshore_units.geometry.distance(sonde_pt.geometry.iloc[0])
    closest_unit = nearshore_units.iloc[[nearshore_units['distance'].idxmin()]]

    return closest_unit





if __name__ == '__main__':


    #%%-------------------------------------------------------------------------
    ### RUN ON SONDES

    site_ow_sonde = gpd.read_file('../data/raw/transect_coords/compass_synoptic_wsonde.geojson')

    # Loop through site bboxes
    for site_id in site_ow_sonde.site_id.unique():
        
        print(site_id)

        # Subset to single site, and open water
        sonde_pt = site_ow_sonde[(site_ow_sonde['site_id'] == site_id) & (site_ow_sonde['zone_id'] == 'OW')]

        estuary = (
            gpd.read_file('../../output/results/coastlines/CUSP_site_estuary_poly_mansel/estuary_poly_' + site_id + '_mansel.shp')
            .dissolve()
            .set_crs("EPSG:5498", allow_override=True)
            )

        # Run function to buffer nearshore units
        closest_unit = buffer_nearshore_units(sonde_pt, estuary, estuary_mask=True)

        # Save nearshore unit to file
        closest_unit.to_file(f'../../output/results/swot/wse_nearshore_unit/swot_sondebuffer_{site_id}_v01.shp')


    #%%-------------------------------------------------------------------------
    # RUN ON TIDE GAUGES

    # TODO: Fix the estuary mask for tide gauges

    # Read site gauge points
    synoptic_gauges = gpd.read_file('../../data/tide_gauges/all_gauges_list/synoptic_tide_gauges.geojson')

    # Loop through site bboxes
    for site_id in synoptic_gauges.site_id.unique():
        
        print(site_id)

        # Subset to single site, and open water
        gauge_pt = synoptic_gauges[(synoptic_gauges['site_id'] == site_id)]

        estuary = (
            gpd.read_file('../../output/results/coastlines/CUSP_site_estuary_poly_mansel/estuary_poly_' + site_id + '_mansel.shp')
            .dissolve()
            .set_crs("EPSG:5498", allow_override=True)
            )

        # Run function to buffer nearshore units
        closest_unit = buffer_nearshore_units(gauge_pt, estuary, estuary_mask=None)


        # Save nearshore unit to file
        closest_unit.to_file(f'../../output/results/swot/wse_tide_gauges/swotwse_tidegauge_buffer_{site_id}_{gauge_pt.station_id.iloc[0]}_v01.shp')
