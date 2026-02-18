

# Get points per site
# synoptic_pts = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_pts_v2.geojson')
synoptic_pts = gpd.read_file('../data/processed/synoptic_pts_wgs84.geojson')


# /----------------------------------------------------------------------------------------------------
#/ Compute bounding box

synoptic_bbox = gpd.GeoDataFrame()

for site_id in synoptic_pts.site_id.unique():

    # Subset to synoptic
    site_pts = synoptic_pts[synoptic_pts.site_id == site_id]

    # Get bounds coordinates
    bbox_coords = site_pts.total_bounds

    # Expansion factor
    ex_fac = 10 ** -3  /2

    # Expand coordinates
    bbox_coords = [bbox_coords[0]-bbox_coords[0] * ex_fac,
                   bbox_coords[1]-bbox_coords[1] * ex_fac,
                   bbox_coords[2]+bbox_coords[2] * ex_fac,
                   bbox_coords[3]+bbox_coords[3] * ex_fac]


    # Convert the bounding box to a Polygons
    from shapely.geometry import Polygon
    bbox_polygon = Polygon([
        (bbox_coords[0], bbox_coords[1]),
        (bbox_coords[2], bbox_coords[1]),
        (bbox_coords[2], bbox_coords[3]),
        (bbox_coords[0], bbox_coords[3]),
        (bbox_coords[0], bbox_coords[1])
    ])

    # EPSG: 4326

    # Create a new GeoDataFrame with the bounding box geometry
    bbox_gdf = gpd.GeoDataFrame(geometry=[bbox_polygon], crs="EPSG:4326")

    # Write to new column
    bbox_gdf['site_id'] = site_id

    # Append to output gdf
    synoptic_bbox = gpd.GeoDataFrame(pd.concat([synoptic_bbox, bbox_gdf], ignore_index=True))



# /----------------------------------------------------------------------------------------------------
#/  Save to geojson

synoptic_bbox.to_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson', driver='GeoJSON')

