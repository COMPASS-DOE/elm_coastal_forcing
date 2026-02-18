
from attr import attributes
from pyparsing import line
from shapely.geometry import Polygon
from centerline.geometry import Centerline
import geopandas as gpd
import numpy as np



#%% Read inputs  --------------------------------------

# Read polygon shapefile
shapefile_path = '../../output/results/coastlines/CUSP_site_estuary_poly_mansel/estuary_poly_GCW_mansel.shp'

# Read shapefile into a GeoDataFrame
estuary_poly = gpd.read_file(shapefile_path)  


#%% Generate centerlines  --------------------------------------

centerline = Centerline(input_geometry= estuary_poly.geometry[0],
                        interpolation_distance= .0044) 

line = centerline.geometry


#%% Generate Points along centerlines  --------------------------------------
import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union


# Generate points along the line at specified intervals
distances = np.arange(0, line.length, 0.00933)

# Make list of points
points = [line.interpolate(distance) for distance in distances]

# Add end points
# + [line.boundary[1]]

# Convert to MultiPoint
# points = list(points.geoms)


# Create MultiPoint object
multipoint = MultiPoint(points)


#%% Generate Voronoi diagram from points  --------------------------------------
import numpy as np
from shapely.geometry import MultiPoint, Polygon, Point
from shapely.ops import voronoi_diagram
import matplotlib.pyplot as plt

def generate_voronoi(multipoint, bounding_box=None):

    # Generate Voronoi diagram
    voronoi = voronoi_diagram(multipoint, envelope=None if not bounding_box else
                              Polygon([
                                  (bounding_box[0], bounding_box[1]),
                                  (bounding_box[2], bounding_box[1]),
                                  (bounding_box[2], bounding_box[3]),
                                  (bounding_box[0], bounding_box[3])
                              ]))
    
    # Extract polygons from geometry collection
    return list(voronoi.geoms)


# Generate Voronoi polygons   --------------------------------------
voronoi_polygons = generate_voronoi(multipoint)

# Convert to gdf  --------------------------------------
voronoi_gdf = gpd.GeoDataFrame({
    'geometry': voronoi_polygons,  
    'id': range(len(voronoi_polygons))}, 
    crs="EPSG:4326")  # Set a CRS (e.g., WGS84)


#%% Mask the Voronoi diagram with estuary mask  --------------------------------------

clipped_voronoi_gdf = gpd.clip(voronoi_gdf, estuary_poly)
# polygons = list(clipped_voronoi_gdf.geometry)

exploded_gdf = (clipped_voronoi_gdf.explode(index_parts=False)
                .reset_index()
                .drop(['index','id'], axis=1)
                .reset_index(names='id'))

exploded_gdf.plot()

# Save to file
exploded_gdf.to_file('../../output/results/coastlines/nearshore_voronoi/nearshore_voronoi_GCW_v02.shp')

