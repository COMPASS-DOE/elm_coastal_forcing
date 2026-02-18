

#%%-----------------------------------------------------------------
# Plot clustered pixC
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
import matplotlib.colors as mcolors
import pandas as pd 
import geopandas as gpd

# Make plotting function
def map_synoptic_swot_polygons(site_pts, gauge_pts, proc_pixc, estuary, allpolygons_gdf, site_id):


    # Split site points by land/open water
    transect_pts = site_pts[site_pts['zone_id'] != 'OW']  # Remove gauge points
    sonde_pts = site_pts[site_pts['zone_id'] == 'OW']  # Remove gauge points

    fig, ax = plt.subplots(1,1, figsize=(16, 3))

    ax.margins(0)     # Remove margins inside the plot
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])

    cmap = plt.cm.plasma.copy() 
    cmap.set_bad(color='#cccccc')

    # Estuary polygons
    estuary.plot(ax=ax, color="#bdbdbd", edgecolor=None, alpha=1)  # linewidth=.5, 

    # SWOT PIXC POINTS
    scatter = plt.scatter(
                    x=proc_pixc.geometry.x,
                    y=proc_pixc.geometry.y,
                    c=proc_pixc.wse,
                    s=0.5,
                    # color='#5c5c5c',
                    edgecolor='none', 
                    cmap=cmap,
                    plotnonfinite=True) #, norm=norm)

    # CLUSTER OUTLINES
    allpolygons_gdf.boundary.plot(ax=ax, color="black", linewidth=.45, linestyle="-")

    # Plot transect points
    plt.scatter(transect_pts.geometry.x, transect_pts.geometry.y, color='white', s=75, zorder=2) 
    plt.scatter(transect_pts.geometry.x, transect_pts.geometry.y, facecolors='white', edgecolors='black', s=75, zorder=2)


    # Text transect labels
    for i in range(len(transect_pts)):
        plt.text(transect_pts.geometry.x.iloc[i], 
                    transect_pts.geometry.y.iloc[i], 
                    transect_pts['zone_id'].iloc[i],
                    fontsize=4.5, ha='center', va='center')

    # If sonder points exist, plot them
    if len(sonde_pts) > 0:
        # Plot sonde point
        plt.scatter(sonde_pts.geometry.x, sonde_pts.geometry.y, color='white', s=75, zorder=2) 
        plt.scatter(sonde_pts.geometry.x, sonde_pts.geometry.y, facecolors='white', edgecolors='red', s=75, zorder=2)

        # Text transect labels
        for i in range(len(sonde_pts)):
            plt.text(sonde_pts.geometry.x.iloc[i], 
                        sonde_pts.geometry.y.iloc[i], 
                        sonde_pts['zone_id'].iloc[i],
                        fontsize=4.5, color='red', ha='center', va='center')
    
    #  Color bar with boundary norm
    cbar = plt.colorbar(mappable=scatter, ax=ax, extend='both', fraction=0.04, pad=0.04)
    cbar.set_label('SWOT WSE NAVD88 (m)')
       
    # Plot synoptic points
    if 0:
        plt.scatter(gauge_pts.longitude, gauge_pts.latitude, facecolors='#e3e3e3', edgecolors=None, s=75, zorder=2)

    ax.set_aspect('equal', adjustable='box')
    # plt.suptitle(site_id , fontsize=14)
    plt.title(site_id, fontsize=12, fontweight='bold')

    plt.savefig(f"../../output/figures/swot/map/cluster_poly/map_{site_id}_clusterpoly.png", dpi=400, bbox_inches='tight')
    plt.close()


#%%-----------------------------------------------------------------
# Test case
if __name__ == '__main__':

    import glob

    # Read synoptic points
    synoptic_pts = gpd.read_file('../data/raw/transect_coords/compass_synoptic_wsonde.geojson')
    # Read site gauge points
    synoptic_gauges = gpd.read_file('../../data/tide_gauges/synoptic_tide_gauges.csv')


    # Loop through site bboxes
    for site_id in synoptic_pts.site_id.unique():

        print(site_id)

        # Subset points to single site
        site_pts = synoptic_pts[synoptic_pts['site_id'] == site_id]
        gauge_pts = synoptic_gauges[synoptic_gauges['site_id'] == site_id]


        #%%-----------------------------------------------------------------------------------
        # Get a list of all .nc files in the directory using glob

        # Read in polygon clusters        # Select the last file for testing
        poly_files = glob.glob(f'/Users/flue473/big_data/swot/pixc/polygon_cluster/{site_id}/*_cropped_navd88.shp')
        cluster_polygons = gpd.read_file(poly_files[0])
        cluster_polygons.set_crs(epsg=5498, inplace=True, allow_override=True)  # EPSG:4326 = WGS84 Latitude/Longitude


        # Read in PixC
        proc_pixc_files = glob.glob(f'/Users/flue473/big_data/swot/pixc/cropped_synoptic/{site_id}/*_cropped_navd88.shp')
        proc_pixc = gpd.read_file(proc_pixc_files[0])
        

        # Read in estuarine polygons
        estuary = gpd.read_file('../../output/results/coastlines/CUSP_site_estuary_poly_mansel/estuary_poly_' + site_id + '_mansel.shp').dissolve()

        # Run plotting function
        map_synoptic_swot_polygons(site_pts, gauge_pts, proc_pixc, estuary, cluster_polygons, site_id)





# fig.show()
# fig.set_size_inches(7.5, 8)
# Save the plot in the created directory
# Add a title to the figure
# plot_title = site_id #transect_pts.site_name.iloc[0] + '    ' + date
#%%-----------------------------------------------------------------------------------
# Loop through all the polygons of SWOT WSE at site

# Loop through polygon shapefiles
# for poly_file in poly_files:

#     # Get filename without extension
#     base_name = os.path.basename(poly_file)
#     root, _   = os.path.splitext(base_name)
#     date = root.split('_')

#     date = pd.to_datetime(date[8], format='%Y%m%dT%H%M%S', errors='coerce')

# Read polygon clusters

#  Get bounding box
# synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')

# Read synoptic sonde 
# sonde_pts = gpd.read_file('../data/raw/transect_coords/compass_synoptic_wsonde.geojson')




