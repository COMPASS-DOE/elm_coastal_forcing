#%% 
import numpy as np
from sklearn.preprocessing import StandardScaler
import xarray as xr
from pyproj import CRS
import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.datasets import load_digits
import pandas as pd 
import geopandas as gpd
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, MultiPoint
from alphashape import alphashape
import shapely



#%%-------------------------------------------------------------------------
def cluster_swot_wse(ds, site_bbox):

    site_id = site_bbox.site_id.iloc[0]

    #%%--------------------------------------------------------------------- 
    # Prepare inputs for clustering
    # input_wse = np.vstack((lat_coords_reproj, lon_coords_reproj, ds.wse.values)).T
    input_wse = np.vstack((ds['latitude'].values, ds['longitude'].values, ds['wse'].values)).T

    #%% Scale values
    scaler = StandardScaler()
    input_wse_scaled = scaler.fit_transform(input_wse)  # Normalize all features


    #%%------------------------------------------------------------- 
    # Run clustering of points with HDBSCAN
    # TODO: Test other clustering methods: Mean shift clustering?  DBSCAN, Or Spectral clustering
    ### Or OPTICS clustering (better for points of varying density)
    # TODO: Remask cluster polygons by the estuarine polygons 
    # TODO: tune epsilon to the average spacing of points?

    # Apply clustering
    hdb = HDBSCAN(min_cluster_size=4,    # The minimum number of samples in a group for that group to be considered a cluster
                min_samples=  1,        # The number of samples in a neighborhood for a point to be considered as a core point
                cluster_selection_epsilon=.13,    # A distance threshold. Clusters below this value will be merged. 
                max_cluster_size=400,     # A limit to the size of clusters returned by the `"eom"` cluster 
                leaf_size=20,
                cluster_selection_method="eom",
                store_centers='medoid')

    # Fit the clustering tothe data
    hdb.fit(input_wse_scaled)

    # Print out the unique labels
    set(hdb.labels_)


    #%%------------------------------------------------------------------
    # Delineate nearshore polygon units per cluster

    # Convert to Pandas DataFrame
    input_wse_df = pd.DataFrame(input_wse, columns=['y', 'x','wse'])
    # Add labels column
    input_wse_df['label'] = hdb.labels_
    # Filter out -1 (no class points)
    input_wse_df.loc[input_wse_df['label'] == -1, 'label'] = np.nan

    # Create GeoPandas GeoDataFrame using Shapely Points
    input_wse_gdf = gpd.GeoDataFrame(input_wse_df, 
                                    geometry=gpd.points_from_xy(input_wse_df['x'], input_wse_df['y']),
                                    crs=CRS("EPSG:5498"))


    #%%---------------------------------------------------------
    #  Make convex hull polygon of each cluster

    # Create empty output gpd df projected in NAD83
    allpolygons_gdf = gpd.GeoDataFrame(columns=["label", "geometry"], 
                                       geometry="geometry", crs=CRS("EPSG:5498"))
                                       # crs=CRS("EPSG:32610"))

    # Loop through cluster labels
    for l in set(input_wse_df['label'].dropna()):

        # make array of points from a single cluster
        filtered_points = input_wse_gdf[input_wse_gdf.label == l]

        # filter to single cluster label
        filtered_points = input_wse_gdf.query("label == @l")
        filtered_muiltipoints = MultiPoint(list(filtered_points.geometry))

        # from shapely import concave_hull
        polygon = shapely.concave_hull(filtered_muiltipoints, ratio=0.02)  # Higher numbers will include fewer vertices in the hull.

        # Match CRS with original GeoDataFrame
        polygon_gdf = gpd.GeoDataFrame({'label': [l]}, geometry=[polygon], crs=CRS("EPSG:5498")) # 32610

        # Append the new row to the original GeoDataFrame
        allpolygons_gdf = pd.concat([allpolygons_gdf, polygon_gdf], ignore_index=True)



    #%%---------------------------------------------------------------------
    # Clip clustered polygons

    # Get estuary polygon
    # TODO: Why isn't this already reprojected in 5498?
    estuary = (
        gpd.read_file('../../output/results/coastlines/CUSP_site_estuary_poly_mansel/estuary_poly_' + site_id + '_mansel.shp')
        .dissolve()
        .set_crs("EPSG:5498", allow_override=True)
        )

    # Perform intersection using GeoPandas overlay
    allpolygons_gdf = gpd.overlay(allpolygons_gdf, estuary, how='intersection')

    # Average polygons from multiple timesteps:
    # https://gis.stackexchange.com/questions/68359/creating-average-polygon


    #%%----------------------------------------------------------------
    ## Filter the cluster polygons by area and/or point density

    # Write point count per polygon
    points_within = gpd.sjoin(input_wse_gdf, allpolygons_gdf, predicate="intersects")
    
    # Write stats to polygon gdf
    allpolygons_gdf["pt_count"] = points_within.groupby(["index_right"]).size().values
    allpolygons_gdf["poly_area"] = allpolygons_gdf["geometry"].area.values/1000
    # Calculate point density
    allpolygons_gdf["pt_dens"] = allpolygons_gdf["pt_count"] / allpolygons_gdf["poly_area"]
    allpolygons_gdf['pt_dens'] = allpolygons_gdf['pt_dens'] / 1000
    allpolygons_gdf['pt_dens'] = allpolygons_gdf['pt_dens'].round(4)  # Round to 2 decimal places

    # Write summary WSE to polygon gdf
    allpolygons_gdf["wse_mean"] = points_within.groupby(["index_right"])["wse"].mean().values
    allpolygons_gdf["wse_std"] = points_within.groupby(["index_right"])["wse"].std().values
    
    if 0:
        # Filter by area or density
        allpolygons_gdf = allpolygons_gdf[allpolygons_gdf["pt_dens"] > 0.5] 

    return allpolygons_gdf



#%%-------------------------------------------------------------------
if __name__ == '__main__':

    #  Get bounding box
    site_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')


    if 0:
        #%%-----------------------------------------------------------------
        # Plot clustered pixC
        import matplotlib.gridspec as gridspec
        import matplotlib.pyplot as plt
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib import colors
        import matplotlib.colors as mcolors

        fig, ax = plt.subplots(1,1, figsize=(16, 8))

        # Remove margins inside the plot
        ax.margins(0)     
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])

        cmap = plt.cm.plasma.copy() 
        cmap.set_bad(color='#cccccc')

        # SWOT PIXC POINTS
        scatter = ax.scatter(
                        x=input_wse_gdf.x,
                        y=input_wse_gdf.y,
                        c=input_wse_gdf.label,
                        s=8, 
                        edgecolor='none', 
                        cmap=cmap,
                        plotnonfinite=True) #, norm=norm)

        # CLUSTER OUTLINES
        allpolygons_gdf.boundary.plot(ax=ax, color="black", linewidth=.5, linestyle="--")

        # Color bar with boundary norm
        cbar = plt.colorbar(mappable=scatter, ax=ax, extend='both', fraction=0.04, pad=0.04)

        cbar.set_label('SWOT Water Surface Elevation cluster IDs')

        # Add a title to the figure
        # plot_title = site_id #transect_pts.site_name.iloc[0] + '    ' + date
        fig.suptitle(site_id , fontsize=14)
        fig.set_size_inches(7.5, 8)






# Back-transform the scaled data to the original scale
# medoids = scaler.inverse_transform(hdb.medoids_)

# # Loop through site bbox
# for index, site_bbox in synoptic_bbox.iterrows():
# Make convex Hull
# cluster_hull = ConvexHull(filtered_points)
# Step 3: Compute the concave hull using alphashape
# alpha = 1  # Adjust alpha value (higher = less concave, lower = tighter fit)
# concave_hull = alphashape(filtered_points, alpha)

# x=lon_coords_reproj,
# y=lat_coords_reproj,
# x=ds.longitude.values,
# y=ds.latitude.values,
# # c=labels,
# c=hdb.labels_,
# c=ds.wse.values,

# If your data is in x,y coordinates, you might need to flatten them
# x_coords = ds['x'].values.flatten()
# y_coords = ds['y'].values.flatten()

#%%--------------------------------------------------------------------- 
# Estimate bandwidth for Mean Shift
# bandwidth = estimate_bandwidth(X, quantile=0.2, n_samples=500)

# ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
# clusters = ms.fit_predict(X)

# #%%
# from sklearn.cluster import OPTICS, cluster_optics_dbscan

# clust = OPTICS(min_samples=5, 
#             #    max_eps=10e5,
#                metric='minkowski', 
#                p=2, 
#                cluster_method='xi',
#             #    eps=10e6,
#                xi=0.05, 
#                min_cluster_size=0.01)

# # Run the fit
# clust.fit(X)

# reachability = clust.reachability_[clust.ordering_]
# labels = clust.labels_[clust.ordering_]

# # Print unique labels
# set(labels)






    # if site_id == 'SWH': continue

    # Convert row subset to geodataframe
    # site_bbox = gpd.GeoDataFrame([site_bbox], geometry='geometry', crs='EPSG:4326')

    # Get a list of all .nc files in the directory using glob
    # dir_path = '/Users/flue473/big_data/swot/pixc/' + site_id + '/cropped'


    # nc_files = glob.glob(f"{dir_path}/*.nc")

    # # Loop through netCDF files
    # for nc_file in nc_files[0:1]: 

    #     # Get filename without extension
    #     base_name = os.path.basename(nc_file)
    #     root, _ = os.path.splitext(base_name)

    #     print(root)

    #     # Read in cropped PixC 
    #     ds = xr.open_dataset(nc_file, engine='h5netcdf')  #  group='pixel_cloud',  as ds:


    #%%-----------------------------------------
    # # Reproject the PixC data
    # from pyproj import CRS, Transformer

    # # Extract coordinates (assuming 'lon' and 'lat' are present)
    # lon_coords = ds.longitude.values
    # lat_coords = ds.latitude.values

    # # Reproject from source CRS (e.g., WGS 84 - EPSG:4326) to target CRS (e.g., UTM Zone 10N - EPSG:32610)
    # transformer = Transformer.from_crs(CRS("EPSG:4326"), CRS("EPSG:32610"), always_xy=True)

    # lon_coords_reproj, lat_coords_reproj = transformer.transform(lon_coords, lat_coords)

    # # TODO: filter outlier points? using Anselin Local Moran's I statistic.

