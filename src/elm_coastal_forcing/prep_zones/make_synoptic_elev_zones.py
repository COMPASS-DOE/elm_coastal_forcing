import geopandas as gpd
import pandas as pd
import numpy as np
from rasterstats import zonal_stats
from osgeo import gdal
import xarray as xr

#%% Read in site/zone coordinate file --------------------------------------
sites = \
    (pd.read_csv('../data/raw/transect_coords/compass_synoptic.csv')
    .assign(grid_points = lambda x: x.site_id + '_' + x.zone_id)
    .assign(site_cat = 'synoptic')
    .drop(columns=['distance'])
     )

# TODO: are the original coordinates from Ben on WGS84 or NAD83 datum?
sites = \
    (gpd.GeoDataFrame(sites,
                      geometry=gpd.points_from_xy(sites.long, sites.lat, crs="EPSG:4269"))
    .to_crs("EPSG:26918")  # Reproject to DEM's CRS: NAD83 / UTM zone 18N
    .rename(columns={"site": "site_id"}))

# Get bounding box
synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')



#%% Loop through sites   --------------------------------------
for site_id in sites.site_id.unique():
    print(site_id)

    ### SUBSET BBOX AND SITES PTS
    # Filter df to a single site
    transect_pts = sites.query('site_id=="' + site_id + '"')

    # Subset bbox
    bbox = synoptic_bbox.query('site_id=="' + site_id + '"')

	#%% Read in cropped NWI
    nwi_cropped = gpd.read_file(f"../../output/results/nwi/{site_id}/nwi_{site_id}_cropped.shp")
    nwi_cropped_ow = nwi_cropped[nwi_cropped.WETLAND_TY.isin(['Estuarine and Marine Deepwater', 
                                                              'Freshwater Pond', 'Riverine','Lake'])]
    nwi_cropped_ow = nwi_cropped_ow[(nwi_cropped_ow['ACRES'] >= 10)]

    #%% Reproject depending on region
    if (transect_pts.region_name.iloc[0] == "Chesapeake Bay"):
        bbox = bbox.to_crs("EPSG:26918")
        transect_pts = transect_pts.to_crs("EPSG:26918")
        nwi_cropped_ow = nwi_cropped_ow.to_crs("EPSG:26918")
        nwi_cropped = nwi_cropped.to_crs("EPSG:26918")
    else:
        bbox = bbox.to_crs("EPSG:6549")
        transect_pts = transect_pts.to_crs("EPSG:6549")
        nwi_cropped_ow = nwi_cropped_ow.to_crs("EPSG:6549")
        nwi_cropped = nwi_cropped.to_crs("EPSG:6549")

    # Extract the bounding box of the polygon
    xmin, ymin, xmax, ymax = bbox.geometry.bounds.values[0]

    bounds = bbox.total_bounds


    #%% CLIP DEM TO BBOX   -----------------------------------------------

    # Get DEM filename from df
    dem_filename = '../../data/dem/' + transect_pts['dem_tile'].iloc[0]

    ds = xr.open_dataset(dem_filename)

    # Invert the y-axis to have increasing coordinates. This is so stupid.
    # Fix here: https://stackoverflow.com/questions/78154441/unexpected-behavior-when-slicing-xarray-dataarray-over-the-y-dimension
    ds = ds.isel(y=slice(None, None, -1))

    # Crop to bbox
    cropped_ds = ds.sel(x=slice(xmin, xmax), y=slice(ymin, ymax))

    # Squeeze out the 1st dimension
    data = cropped_ds['band_data'].values.squeeze() 
    # data = data[::-1, :]       # Flip back y-axis

    # Because DEM and bbox do not align, we get the bounds of the cropped DEM and recrop nwi
    xmin, ymin, xmax, ymax = cropped_ds.rio.bounds()

    # Create a bounding box geometry
    from shapely.geometry import box
    bbox_polygon = box(xmin, ymin, xmax, ymax)
    dem_bbox_int = gpd.GeoDataFrame(index=[0], geometry=[bbox_polygon], crs=bbox.crs)

    # Clip the GeoDataFrame using the bbox
    nwi_cropped_ow = gpd.clip(nwi_cropped_ow, dem_bbox_int.geometry[0])


    #%% RASTERIZE ENTIRE NWI -----------------------------------------
    nwi_cropped = gpd.clip(nwi_cropped, dem_bbox_int.geometry[0])
    nwi_cropped = nwi_cropped[(nwi_cropped['ACRES'] >= 10)]

    # For this example, we will create a new categorical attribute
    nwi_cropped['WETLAND_TY_cat'] = nwi_cropped['WETLAND_TY'].astype('category')

    code = {
            'Riverine': 1,
            'Lake': 2,
            'Estuarine and Marine Deepwater': 3,
            'Estuarine and Marine Wetland': 4,
            'Freshwater Forested/Shrub Wetland': 5,
            'Freshwater Emergent Wetland': 6,
            'Freshwater Pond': 7,
            'Other': 8,
        }

    # Plotting NWI with colors
    nwi_cropped['code']  = nwi_cropped['WETLAND_TY_cat'].map(code)

    # Rasterize NWI wetlands
    import rasterio as rio 
    from rasterio.features import rasterize

    raster_width = data.shape[1]
    raster_height = data.shape[0]

    # Create raster metadata
    transform = rio.transform.from_bounds(xmin, ymin, xmax, ymax, raster_width, raster_height)

    meta = {
        'driver': 'GTiff',
        'count': 1,
        'dtype': 'float32',  # or appropriate type
        'width': raster_width,
        'height': raster_height,
        'crs': nwi_cropped_ow.crs,  # Coordinate reference system from the GeoDataFrame
        'transform': transform
        }

    nwi_cropped_rast = rasterize(
        [(geom, value) for geom, value in zip(nwi_cropped.geometry, nwi_cropped['code'])],  # Pairs of geometry and values
            out_shape=(raster_height, raster_width),
            transform=transform,
            fill=np.nan,  # background value
            dtype='float32'
            )

    # Convert to xarray DataArray
    nwi_cropped_rast = xr.DataArray(nwi_cropped_rast, dims=["y", "x"])


    #%% Mask out NWI water  ------------------------------------------------------
    # Convert NWI to raster/array

    # Rasterize PLYGONS
    # You can specify a field from the GeoDataFrame to burn into the raster
    raster_data = rasterize(
        [(geom, 1) for geom in nwi_cropped_ow.geometry],  # 1 represents the value to burn in
        out_shape=(raster_height, raster_width),
        transform=transform,
        fill=np.nan,  # background value
        dtype='float32'
        )

    # Convert to xarray DataArray
    nwi_ow_raster = xr.DataArray(raster_data, dims=["y", "x"])


    #%%  FAST MARCHING SEGMENTATION METHOD  -----------------------------------------------
    # https://scikit-fmm.readthedocs.io/en/master/#
    import skfmm
    import numpy as np
    from sklearn.preprocessing import MinMaxScaler

    from skimage.filters import gaussian
    data_gauss = gaussian(data, sigma=5)  # Apply Gaussian smoothing

    # Initialize MinMaxScaler to rescale the 2D array
    scaler = MinMaxScaler(feature_range=(0, 1))    
    normalized_data = scaler.fit_transform(data_gauss**2)   

    normalized_data = np.where(normalized_data == 0, 10e-10, normalized_data)    

    # Make seed for Fast Marching
    seed = nwi_ow_raster.copy()
    seed = np.where(seed == 0, np.nan, seed)
    seed = np.where(seed == 1, 0, seed)

    # Run Fast Marching
    fm_tt = skfmm.travel_time(phi= seed, dx=1, speed= 1/normalized_data)

    # Mask the DEM with open water polygons
    fm_tt = np.where(nwi_ow_raster == 1, np.nan, fm_tt)    

    # Mask out the high travel time values
    fm_tt_ceiling = np.nanpercentile(fm_tt, 80)
    fm_tt = np.where(fm_tt > fm_tt_ceiling, np.nan, fm_tt)


    #%% SEGMENT THE TRAVEL TIME ARRAY  -----------------------------------------------
    tai_zones = fm_tt.copy()

    # Define conditions (these will be compared against the array)
    conditions = [(fm_tt < 48),             
                (fm_tt >= 48) & (fm_tt < 55), 
                (fm_tt >= 55) & (fm_tt < 100), 
                (fm_tt >= 100) ]

    # Define output labels for each condition
    labels = [1, 2, 3, 4]  # Assign a label to each condition

    # Use numpy.select to classify the data based on conditions
    tai_zones = np.select(conditions, labels, default=4) #np.nan # Default label if no condition is met
    # Mask open water with NWI deepwater
    tai_zones = np.where(nwi_ow_raster == 1, 0, tai_zones) 


    #%% PLOT SEGMENTED IMAGE  -----------------------------------------------

    # Plot clusters
    # plt.imshow(segmented_data, interpolation='none', extent=[xmin, xmax, ymin, ymax])

    # Plot DEM
    # masked_data = np.where(nwi_ow_raster == 1, np.nan, data)
    # plt.imshow(normalized_data, interpolation='none', extent=[xmin, xmax, ymin, ymax])
    # plt.gca().invert_yaxis()
    # # Plot edgelines
    
    # plt.imshow(nwi_ow_raster, interpolation='none', extent=[xmin, xmax, ymin, ymax])
    # # plt.imshow(seed, interpolation='none', extent=[xmin, xmax, ymin, ymax])
    # plt.gca().invert_yaxis()



   #%% PLOT SEGMENTED IMAGE  -----------------------------------------------

    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib.colors as mcolors

    # Make grid of plots
    fig, axs = plt.subplots(2, 2, figsize=(16, 10),
                            sharex=True, sharey=True,  # axis values only on one edge?
                            constrained_layout=True, gridspec_kw={'hspace': 0.05, 'wspace': 0.05})


    # #%%  Panel 1: NWI wetland --------------------------------------------
    norm = mcolors.BoundaryNorm(boundaries=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5], ncolors=8)
    cmap_nwi = mcolors.ListedColormap(['#2737b0','#001ee3', '#000791', '#8b42ff','#0d7509','#96ffcb','#69a5ff','#9ea66f'])

    # Plot TAI zones with color bar with labels
    img0 = axs[0,0].imshow(nwi_cropped_rast, interpolation='none', cmap=cmap_nwi, norm=norm, extent=[xmin, xmax, ymin, ymax])
    cbar = plt.colorbar(img0, ax=axs[0,0], ticks=[1, 2, 3, 4, 5, 6, 7, 8])
    cbar.ax.set_yticklabels(['Riverine', 'Lake', 'Estuarine and Marine Deepwater', 'Estuarine and Marine Wetland', 
                             'Freshwater Forested/Shrub Wetland', 'Freshwater Emergent Wetland', 'Freshwater Pond', 'Other'])

    # Plot synoptic points
    axs[0,0].scatter(transect_pts.geometry.x, transect_pts.geometry.y, color='white', s=75, zorder=2) 
    axs[0,0].scatter(transect_pts.geometry.x, transect_pts.geometry.y, facecolors='white', edgecolors='black', s=75, zorder=2)

    # Text labels
    for i in range(len(transect_pts)):
        axs[0,0].text(transect_pts.geometry.x.iloc[i], 
                    transect_pts.geometry.y.iloc[i], 
                    transect_pts['zone_id'].iloc[i],
                    fontsize=5.5, ha='center', va='center')
        
    axs[0,0].set_title(transect_pts['site_name'].iloc[0] + ' - NWI wetlands')# , fontsize=15)


    # Panel 2: DEM elevation  ------------------------------

    # Plot DEM elevation
    cmap = plt.get_cmap('YlOrRd')
    img1 = axs[0,1].imshow(data, interpolation='none', cmap=cmap, extent=[xmin, xmax, ymin, ymax])
    plt.colorbar(img1, ax=axs[0,1], label='Elevation')#, extend='both')

    # Plot synoptic points
    axs[0,1].scatter(transect_pts.geometry.x, transect_pts.geometry.y, color='white', s=75, zorder=2) 
    axs[0,1].scatter(transect_pts.geometry.x, transect_pts.geometry.y, facecolors='white', edgecolors='black', s=75, zorder=2)

    # Text labels
    for i in range(len(transect_pts)):
        axs[0,1].text(transect_pts.geometry.x.iloc[i], 
                    transect_pts.geometry.y.iloc[i], 
                    transect_pts['zone_id'].iloc[i],
                    fontsize=5.5, ha='center', va='center')
        
    axs[0,1].set_title(transect_pts['site_name'].iloc[0] + ' - DEM Elevation')
    axs[0,1].invert_yaxis() 


    # Panel 3: Plot FMS speed and NWI open water ------------------------------

    # Plot FMS speed
    cmap = plt.get_cmap('rainbow')
    cmap.set_bad(color='gray')
    cmap.set_over('grey') 
    cmap.set_under('white')
    img1 = axs[1,0].imshow(fm_tt, interpolation='none', cmap=cmap, extent=[xmin, xmax, ymin, ymax])
    plt.colorbar(img1, ax=axs[1,0], label='Travel Time', extend='both')

    # Plot contours for FMS speed
    X, Y = np.meshgrid(cropped_ds['x'].values, cropped_ds['y'].values)
    axs[1,0].contour(X, Y, fm_tt, levels=15, linewidths=.5, colors='black', extent=[xmin, xmax, ymin, ymax])

    # Plot NWI open water 
    axs[1,0].imshow(nwi_ow_raster, interpolation='none', cmap=plt.cm.get_cmap('gray', 1), extent=[xmin, xmax, ymin, ymax])

    # Plot synoptic points
    axs[1,0].scatter(transect_pts.geometry.x, transect_pts.geometry.y, color='white', s=75, zorder=2) 
    axs[1,0].scatter(transect_pts.geometry.x, transect_pts.geometry.y, facecolors='white', edgecolors='black', s=75, zorder=2)

    # Text labels
    for i in range(len(transect_pts)):
        axs[1,0].text(transect_pts.geometry.x.iloc[i], 
                    transect_pts.geometry.y.iloc[i], 
                    transect_pts['zone_id'].iloc[i],
                    fontsize=5.5, ha='center', va='center')
        
    axs[1,0].set_title(transect_pts['site_name'].iloc[0] + ' - Fast Marching Method')
    axs[1,0].invert_yaxis() 
    # axs[0,1].axis('equal')


    # Panel 4: TAI zones with custom colors -----------------------------------------------

    norm = mcolors.BoundaryNorm(boundaries=[-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], ncolors=5)
    cmap_zones = mcolors.ListedColormap(['#0000ff','#cc962b', '#f7e700', '#64b000','#cccccc'])

    # Plot TAI zones with color bar with labels
    img2 = axs[1,1].imshow(tai_zones, interpolation='none', cmap=cmap_zones, norm=norm, extent=[xmin, xmax, ymin, ymax])
    cbar = plt.colorbar(img2, ax=axs[1,1], ticks=[0, 1, 2, 3, 4])
    cbar.ax.set_yticklabels(['Open Water (NWI)', 'Wetland', 'Transition', 'Upland', 'Inland'])

    # Plot synoptic points
    axs[1,1].scatter(transect_pts.geometry.x, transect_pts.geometry.y, color='white', s=75, zorder=2) 
    axs[1,1].scatter(transect_pts.geometry.x, transect_pts.geometry.y, facecolors='white', edgecolors='black', s=75, zorder=2)

    # Text labels
    for i in range(len(transect_pts)):
        axs[1,1].text(transect_pts.geometry.x.iloc[i], 
                    transect_pts.geometry.y.iloc[i], 
                    transect_pts['zone_id'].iloc[i],
                    fontsize=5.5, ha='center', va='center')

    axs[1,1].set_title(transect_pts['site_name'].iloc[0] + ' - Fast Marching Method')
    # axs[1,0].axis('equal')
    axs[1,1].invert_yaxis() 
    # plt.show()      # Show the plot


    # Panel #4: Empty panel --------------------------
    # fig.delaxes(axs[1][1])

    #%% plotwide arguments
    # plt.tight_layout()     # Adjust layout to prevent overlap
    plt.margins(0) 


    #%% Name image file based on input netCDF file -------------------------
    image_path = f'../../output/figures/transect_zones/fm_tt_zones_{site_id}_v8.png'
    plt.savefig(image_path, dpi=200)    # Save plot to an image file
    plt.close()






    # #%% Convert NWI to line
    # nwi_cropped_ow_lines = nwi_cropped_ow.copy()
    # # Small buffer
    # nwi_cropped_ow_lines['geometry'] = nwi_cropped_ow_lines.geometry.buffer(0.0001)
    # nwi_cropped_ow_lines['geometry'] = nwi_cropped_ow_lines['geometry'].boundary

    # # Rasterize LINES
    # raster_data = rasterize(
    #     [(geom, 0) for geom in nwi_cropped_ow_lines.geometry],  # 1 represents the value to burn in
    #     out_shape=(raster_height, raster_width),
    #     transform=transform,
    #     fill=np.nan,  # background value
    #     dtype='float32'
    #     )
    # # Convert to xarray DataArray
    # nwi_ow_lines_raster = xr.DataArray(raster_data, dims=["y", "x"])
    
    # import matplotlib.patches as mpatches

    # # For this example, we will create a new categorical attribute
    # nwi_cropped_ow['WETLAND_TY_cat'] = nwi_cropped_ow['WETLAND_TY'].astype('category')

    # # Define a color map based on the categories in the 'continent' attribute
    # colors = {
    #     'Riverine': '#2737b0',
    #     'Lake': '#001ee3',
    #     'Estuarine and Marine Deepwater': '#000791',
    #     'Estuarine and Marine Wetland': '#8b42ff',
    #     'Freshwater Forested/Shrub Wetland': '#0d7509',
    #     'Freshwater Pond': '#69a5ff',
    #     'Other': '#9ea66f',
    # }

    # # Plotting NWI with colors
    # nwi_cropped_ow['color']  = nwi_cropped_ow['WETLAND_TY_cat'].map(colors)
    # nwi_cropped_ow.plot(ax=axs[0,0], color=nwi_cropped_ow['color'], edgecolor='black')
    # patches = [mpatches.Patch(color=color, label=continent) for continent, color in colors.items()]
    # axs[0,0].legend(handles=patches, title='NWI Wetland Typpe', loc='upper left', frameon=False, bbox_to_anchor=(1, 1)) 




    # # axs[0,0].axis('equal')
    # # axs[0,0].set_aspect(adjustable='datalim')

