

#%%-----------------------------------------------------------------
# Plot clustered pixC
from zipfile import Path
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
import matplotlib.colors as mcolors
import pandas as pd 
import geopandas as gpd
from shapely import LineString


# Make plotting function
def map_synoptic_swot_polygons(site_id, site_pts, gauge_pts, coastline, sonde_pt=None, nearshoreunit=None):

    fig, ax = plt.subplots(1,1, figsize=(14, 6))

    ax.margins(0)     # Remove margins inside the plot
    ax.set_aspect('equal')

    cmap = plt.cm.plasma.copy() 
    cmap.set_bad(color="#979797")



    # Nearshore unit 
    # nearshoreunit.boundary.plot(ax=ax, color="red", linewidth=.45, linestyle="-")
    nearshoreunit.plot(ax=ax, color="red", edgecolor=None, linewidth=0, alpha=0.4)

    plt.text(sonde_pt.geometry.x.iloc[0]-0.005, 
            sonde_pt.geometry.y.iloc[0]-0.005, 
            'SWOT\nNearshore\nUnit',
            fontweight='bold', color='red', fontsize=5, ha='center', va='center')


    # Coastline
    coastline.plot(ax=ax, edgecolor="#AAAAAA", linewidth=.6, alpha=1)   


    # Tide gauge point
    plt.scatter([gauge_pts.geometry.x], [gauge_pts.geometry.y], facecolors='blue', edgecolors='blue', s=20, zorder=2) 
    # Gauge Text label
    for i in range(len(gauge_pts)):
        plt.text(gauge_pts.geometry.x.iloc[i], 
                gauge_pts.geometry.y.iloc[i]+0.005, 
                f'Tide gauge\n{gauge_pts.data_source.iloc[i]}  {gauge_pts.station_name.iloc[i]}',
                fontweight='bold', color='blue', fontsize=5, ha='center', va='center')


    # Make transect
    from shapely import LineString
    transect_pts = site_pts[site_pts['zone_id'] != 'OW']
    transect = LineString(transect_pts.geometry.tolist())
    transect = gpd.GeoSeries([transect])
    transect.plot(ax=ax, color="#007120", edgecolor="#007120", linewidth=1, alpha=0.4)



    # Synoptic transect points
    plt.scatter(site_pts.geometry.x, site_pts.geometry.y, facecolors="#007120", edgecolors=None, s=8, zorder=2) 
    plt.text(site_pts.geometry.x.iloc[0], site_pts.geometry.y.iloc[0]-0.004, 'Transect', 
             color='#007120', fontsize=3, fontweight='bold', ha='center', va='center')
    # Text transect labels
    # for i in range(len(sonde_pt)):
    #     plt.text(sonde_pt.geometry.x.iloc[i], 
    #                 sonde_pt.geometry.y.iloc[i]+0.02, 
    #                 sonde_pt['zone_id'].iloc[i],
    #                 fontsize=2.5, color='black', ha='center', va='center')


    # If sonde points exist, plot them
    if sonde_pt is not None:
        plt.scatter(sonde_pt.geometry.x, sonde_pt.geometry.y, color='black', s=20, zorder=2) 
        # plt.scatter(sonde_pt.geometry.x, sonde_pt.geometry.y, facecolors='white', edgecolors='red', s=75, zorder=2)
        # Text transect labels
        for i in range(len(sonde_pt)):
            plt.text(sonde_pt.geometry.x.iloc[i], 
                        sonde_pt.geometry.y.iloc[i]+0.002, 
                        "EXO\nSonde", # sonde_pt['zone_id'].iloc[i],
                        fontsize=5.5, color='black', fontweight='bold',ha='center', va='center')


    # CLUSTER OUTLINES
    # allpolygons_gdf.boundary.plot(ax=ax, color="black", linewidth=.45, linestyle="-")

    # Define margin
    margin = 0.04

    # Use min() and max() with explicit scalarization
    x_min = float(min(site_pts.geometry.x.min(), gauge_pts.geometry.x.min()) - margin)
    x_max = float(max(site_pts.geometry.x.max(), gauge_pts.geometry.x.max()) + margin)
    y_min = float(min(site_pts.geometry.y.min(), gauge_pts.geometry.y.min()) - margin)
    y_max = float(max(site_pts.geometry.y.max(), gauge_pts.geometry.y.max()) + margin)

    # Pass limits to Matplotlib
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    # Customize tick size
    ax.set_aspect('equal', adjustable='box')
    ax.tick_params(axis='both', which='both', labelsize=8)  
    # ax.set_xticks([])
    # ax.set_yticks([])


    plt.title(site_id, fontsize=12, fontweight='bold')

    # plt.show()
    plt.savefig(f"../../output/figures/tide_gauges/map_{site_id}_tide_gauges_v02.png", dpi=400, bbox_inches='tight')
    plt.close()



#%%-----------------------------------------------------------------
# Test case
if __name__ == '__main__':

    import glob

    # Read synoptic points
    synoptic_pts = gpd.read_file('../data/raw/transect_coords/compass_synoptic_wsonde.geojson')

    # Synoptic transect line for reference
    # '/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/output/results/transect_line/transect_lineOld Woman Creek.shp'


    # Read site gauge points
    synoptic_gauges = gpd.read_file('../../data/tide_gauges/all_gauges_list/synoptic_tide_gauges.geojson')


    # Loop through site bboxes
    for site_id in synoptic_pts.site_id.unique():

        print(site_id)


        # Subset points
        site_pts = synoptic_pts[synoptic_pts['site_id'] == site_id]#.iloc[[0]]
        # site_pts = site_pts.iloc[[0]]
        sonde_pt = synoptic_pts[(synoptic_pts['site_id'] == site_id) & (synoptic_pts['zone_id'] == "OW")]
        gauge_pts = synoptic_gauges[synoptic_gauges['site_id'] == site_id]


        # Read in SWOT wse clusters  
        poly_files = glob.glob(f'/Users/flue473/big_data/swot/pixc/polygon_cluster/{site_id}/*_cropped_navd88.shp')
        cluster_polygons = gpd.read_file(poly_files[0])        # Select the last file for testing
        cluster_polygons.set_crs(epsg=5498, inplace=True, allow_override=True)  # EPSG:4326 = WGS84 Latitude/Longitude


        # Get nearshore unit
        nearshoreunit = gpd.read_file(f'../../output/results/swot/wse_nearshore_unit/swot_sondebuffer_{site_id}_v01.shp')

        # # Find the Closest Polygon; ie the row with the smallest distance
        # closest_polygon = cluster_polygons.iloc[[cluster_polygons['distance'].idxmin()]]


        # Read in estuarine polygons
        estuary = gpd.read_file('../../output/results/coastlines/CUSP_site_estuary_poly_mansel/estuary_poly_' + site_id + '_mansel.shp').dissolve()


        # Coastline (uncropped) 
        if site_id in ['SWH','GCW','MSM','GWI']:
            coastline = gpd.read_file('../../data/coastlines/usa/N35W080/N35W080.shp') # Chesapeake
        else:
            coastline = gpd.read_file('../../output/results/coastlines/CUSP_manmod/N40W085_manmod.shp') # Lake Erie


        # Run plotting function
        map_synoptic_swot_polygons(site_id, site_pts, gauge_pts, coastline=coastline, sonde_pt=sonde_pt, nearshoreunit=nearshoreunit)







## FOR SOME REASON THIS FUCKING THING DOESNT RUN UNLESS THERE IS .ILOC[[0]] OUTSIDE THE FUNCTION
# INSIDE DOESNT WORK
# Get common framing of sites & gauges; can handles multiple gauges 
margin=0.04
# plt.xlim(float(pd.concat([pd.Series(site_pts.geometry.x.min()), pd.Series(gauge_pts.geometry.x.min())]).min() - margin), 
#          float(pd.concat([pd.Series(site_pts.geometry.x.max()), pd.Series(gauge_pts.geometry.x.max())]).max() + margin))

# plt.ylim(float(pd.concat([pd.Series(site_pts.geometry.y.min()), pd.Series(gauge_pts.geometry.y.min())]).min() - margin), 
#          float(pd.concat([pd.Series(site_pts.geometry.y.max()), pd.Series(gauge_pts.geometry.y.max())]).max() + margin))


# plt.xlim(float(pd.concat([pd.Series(site_pts.geometry.x.min()), pd.Series(gauge_pts.geometry.x.min())]).min() - margin), 
#          float(pd.concat([pd.Series(site_pts.geometry.x.max()), pd.Series(gauge_pts.geometry.x.max())]).max() + margin))

# plt.ylim(float(pd.concat([pd.Series(site_pts.geometry.y.min()), pd.Series(gauge_pts.geometry.y.min())]).min() - margin), 
#          float(pd.concat([pd.Series(site_pts.geometry.y.max()), pd.Series(gauge_pts.geometry.y.max())]).max() + margin))


    # # Plot transect points
    # plt.scatter(transect_pts.geometry.x, transect_pts.geometry.y, color='white', s=75, zorder=2) 
    # plt.scatter(transect_pts.geometry.x, transect_pts.geometry.y, facecolors='white', edgecolors='black', s=75, zorder=2)
    # plt.text([gauge_pts.geometry.x], [gauge_pts.geometry.y+0.016], 'Tide gauge', color='blue', fontsize=6.5, fontweight='bold', ha='center', va='center')
