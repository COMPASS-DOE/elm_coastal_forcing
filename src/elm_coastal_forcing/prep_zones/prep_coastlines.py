#%% 
import numpy as np
import geopandas as gpd
from pyproj import CRS, transformer
import geopandas as gpd
from shapely.geometry import Polygon  #, LineString, Point, MultiLineString
from shapely.ops import polygonize, unary_union
from shapely.ops import split


# NAD83 / NAVD88 (Orthometric Height)
nad83_navd88 = CRS("EPSG:5498")  # This is the destination proj.

# Create a transformer object to convert from EGM2008 to WGS84;    
# Note: The EGM2008 geoid model is used to convert ellipsoidal heights to orthometric heights
transformer = transformer.Transformer.from_crs(crs_from=CRS("EPSG:4269"), crs_to=nad83_navd88, always_xy=True, allow_ballpark=False)


#%%--------------------------------------------------------------

def prep_cusp_coastline(synoptic_bbox, coastline_gdf, local_bbox=0):

    # Get site id
    site_id = str(synoptic_bbox.site_id.iloc[0])

    #%% CUSP Bounding box
    bbox = coastline_gdf.total_bounds  # [minx, miny, maxx, maxy]

    # Step 2: Create a bounding box
    bounding_box = Polygon([
        (bbox[0], bbox[1]),  # Bottom-left
        (bbox[2], bbox[1]),  # Bottom-right
        (bbox[2], bbox[3]),  # Top-right
        (bbox[0], bbox[3]),  # Top-left
        (bbox[0], bbox[1])   # Close the box
    ])

    bounding_box_gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[bounding_box], crs=CRS("EPSG:4269"))


    #%%-----------------------------------------------------------------------------
    # Subset to coastlines within bbox
    # if local_bbox == 1:

    # Select 1st bounding box
    synoptic_bbox_geom = synoptic_bbox.geometry.iloc[0]

    # Clip coastline to bbox
    coastline_gdf_clip = coastline_gdf[coastline_gdf.geometry.intersects(synoptic_bbox_geom, align=False)]


    #%%-----------------------------------------------------------------------------
    #  Convert the coastlines to polygons by splitting bbox with lines
    # https://kuanbutts.com/2020/07/07/subdivide-polygon-with-linestring/

    # Set inputs; there are Polygon and Linestring objects
    # input_p = bounding_box_gdf  # If applied to entire CUSP tile
    input_p = synoptic_bbox_geom # synoptic_bbox_geom.boundary  # If applied to smaller bbox
    input_l = coastline_gdf_clip

    # Union the polygon boundary and the internal lines
    unioned = input_p.boundary.union(input_l.geometry, grid_size=.0001)


    unioned_gdf = gpd.GeoDataFrame(geometry=unioned, crs=CRS("EPSG:4269"))
    unioned_gdf.to_file('../../output/results/coastlines/unioned_t3.shp')



    #%%-----------------------------------------------------------------------------
    # use polygonize geos operator and filter out poygons ouside of original input polygon
    polygons, cuts, dangles, invalid = unioned.polygonize(full=True)

    # Select only polygons whose representative point is within the bounding box
    estuary_polys = [poly for poly in polygons if poly.representative_point().within(input_p)]

    # Convert to GDF
    estuary_polys_gdf = gpd.GeoDataFrame(geometry=estuary_polys, crs=CRS("EPSG:4269"))
    
    # Add ID column
    estuary_polys_gdf['id'] = estuary_polys_gdf.index


    #%%-----------------------------------------------------------------------------
    # Make buffer around CUSP coastlines

    # buffer lines
    buffered = input_l.buffer(0.005)

    # Convert polygon to gdf
    buffered_gdf = gpd.GeoDataFrame(geometry=buffered, crs=CRS("EPSG:4269"))

    # Dissolve into single polygon
    buffered_gdf = buffered_gdf.dissolve()


    #%%-------------------------------------------------------
    # Intersect the split CUSP polygons and buffer from coastline, to generate candidate nearshore units 
    # (these are then)
    merged = gpd.overlay(estuary_polys_gdf, buffered_gdf, how="intersection")

    # plot polygon ID
    # merged.plot(column='id', edgecolor='black')


    #%%-------------------------------------------------------
    merged =  merged.to_crs(nad83_navd88) # Then reproject to NAD83 / NAVD88; doesnt do anything to 2D geometry coords

    # Save to file
    merged.to_file('../../output/results/coastlines/CUSP_site_estuary_poly/estuary_poly_' + site_id + '.shp')



#%%
if __name__ == '__main__': 

    #%%-----------------------------------------------------------------------------
    # Get detailed coastlines CUSP:  https://coast.noaa.gov/digitalcoast/data/cusp.html

    coastline_CB_gdf = gpd.read_file('../../data/coastlines/usa/N35W080/N35W080.shp') # Chesapeake
    coastline_LE_gdf = gpd.read_file('../../output/results/coastlines/CUSP_manmod/N40W085_manmod.shp') # Lake Erie

    #%%-----------------------------------------------------------------------------
    #  Get bounding box
    synoptic_bbox = (
        gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')
        )
    
    # reproject
    synoptic_bbox = synoptic_bbox.to_crs("EPSG:4269")


    # Run function for each site
    prep_cusp_coastline(synoptic_bbox.query("site_id == 'SWH'"), coastline_CB_gdf, local_bbox=1)
    prep_cusp_coastline(synoptic_bbox.query("site_id == 'MSM'"), coastline_CB_gdf, local_bbox=1)
    prep_cusp_coastline(synoptic_bbox.query("site_id == 'GWI'"), coastline_CB_gdf, local_bbox=1)
    prep_cusp_coastline(synoptic_bbox.query("site_id == 'GCW'"), coastline_CB_gdf, local_bbox=1)
    prep_cusp_coastline(synoptic_bbox.query("site_id == 'PTR'"), coastline_LE_gdf, local_bbox=1)
    prep_cusp_coastline(synoptic_bbox.query("site_id == 'OWC'"), coastline_LE_gdf, local_bbox=1)
    prep_cusp_coastline(synoptic_bbox.query("site_id == 'CRC'"), coastline_LE_gdf, local_bbox=1)





# Plot
# estuary_polys_gdf.plot(column='id', edgecolor='black')

# Filter out water non water polygons; The ids are selected manually in this case bc of running over synoptic bbox;
# Hopefully this is easier when running over a larger region
# estuary_polys_gdf = estuary_polys_gdf[estuary_polys_gdf['id'].isin([0, 5])]

# Fix invalid geometries
# unioned_gdf['geometry'] = unioned_gdf['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)



# from shapely.ops import nearest_points
# # Define snapping function
# def snap_to_nearest(geom, target_gdf, tolerance):
#     for target in target_gdf['geometry']:
#         if geom.distance(target) < tolerance:
#             return geom.union(target)
#     return geom

# # # Apply snapping
# tolerance = 0.001  # Adjust as needed
# unioned_gdf['geometry'] = unioned_gdf['geometry'].apply(lambda geom: snap_to_nearest(geom, gdf, tolerance))

    # transformer.transform(merged
    #             ds["longitude"].values, 
    #             ds["latitude"].values, 
    #             ds["wse"].values)