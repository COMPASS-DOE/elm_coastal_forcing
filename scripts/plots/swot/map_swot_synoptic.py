
# /------------------------------------------------------------------------
# /  Get synoptic points
synoptic_pts = gpd.read_file('../data/processed/synoptic_pts_wgs84.geojson')
synoptic_pts = synoptic_pts[synoptic_pts.site_id == site_id]
synoptic_pts = synoptic_pts.to_crs(swot_crs)

# /------------------------------------------------------------------------
#/  Get synoptic transect
# d = {'col1': ['name1'], 'geometry': [line]}
# line_gdf = gpd.GeoDataFrame(d, crs="EPSG:32618")  # (change epsg)


#%%--------------------------------------------------------------------------------------
# SITE COORDS

# Read in site/zone coordinate file
synoptic = \
    (pd.read_csv('../data/raw/transect_coords/compass_synoptic.csv')
    .assign(grid_points = lambda x: x.site_id + '_' + x.zone_id)
    .assign(site_cat = 'synoptic')
    .drop(columns=['distance'])
    )

synoptic = synoptic[['site_id','site_name']].drop_duplicates(keep='last')


# /------------------------------------------------------------------------
#/   Get bounding box
synoptic_bbox = gpd.read_file('../../data/site_pts/synoptic/synoptic_sites_bbox.geojson')


# /-------------------------------------------------------------------------
#/  Loop through synoptic sites

# Loop through sites
for index, site in synoptic.iterrows():

    site_name = site.site_name
    site_id = site.site_id
    print(site_id + ' ' + site_name)

    # /  Get synoptic transect
    transect = gpd.read_file('../../output/results/transect_line/transect_line' + site_name + '.shp').to_crs('EPSG:4326')

    # /------------------------------------------------------------------------
    #/  Get synoptic points
    synoptic_pts = gpd.read_file('../data/processed/synoptic_pts_wgs84.geojson')
    synoptic_pts = synoptic_pts[synoptic_pts.site_id == site_id]
    # synoptic_pts = synoptic_pts.to_crs(swot_crs)

    # Convert row subset to geodataframe
    site_bbox = synoptic_bbox[synoptic_bbox.site_id == site_id]
    # site_bbox = gpd.GeoDataFrame([site_bbox], geometry='geometry', crs='EPSG:4326')

    # Get a list of all .nc files in the directory using glob
    dir_path = '../../data/swot/pixc/' + site_id + '/cropped'
    nc_files = glob.glob(f"{dir_path}/*.nc")


    ##################
    # for nc_file in nc_files[-2:-1]: #[0]
    nc_file = nc_files[0]#[-2:-1]  # [0]

    # Get filename without extension
    base_name = os.path.basename(nc_file)
    root, _ = os.path.splitext(base_name)

    print(root)

    # Read in cropped pixc
    ds_cropped = xr.open_dataset(nc_file, engine='h5netcdf') # group='pixel_cloud',

    # Filter height values
    wse_values = ds_cropped.wse.values
    mean_wse = np.mean(wse_values)
    std_wse = np.std(wse_values)


    ds_cropped = ds_cropped.where(
        (ds_cropped.wse <= mean_wse + std_wse * 6) & (ds_cropped.wse >= mean_wse - std_wse * 6),
        drop=True)#.dropna(dim='points', how='all')

    # variable_name = 'MSM'
    # new_variable_name = variable_name + '_plot'
    # globals()[new_variable_name] = "This is the value of the new variable"
    # print(MSM_plot)  # Output: This is the value of the new variable

    # /------------------------------------------------------------------------
    #/  Get tidal edge polygon
    tidal_edge_zone = gpd.read_file('../../data/site_zones/water_tidal_forcing_zone.shp')
    tidal_edge_zone = tidal_edge_zone[tidal_edge_zone.site_id == site_id]



    # /------------------------------------------------------------------------
    #/  PLOT MAP

    import matplotlib.pyplot as plt
    from matplotlib import colors

    fig, ax = plt.subplots(1,1, figsize=(16, 8))

    ax.margins(0)     # Remove margins inside the plot
    ax.set_aspect('equal')
    ax.set_ylabel('Latitude')
    ax.set_xlabel('Longitude')

    # SWOT PIXC POINTS
    s = ax.scatter(x=ds_cropped.longitude,
                   y=ds_cropped.latitude,
                   c=ds_cropped.wse,
                   s=8, edgecolor='none',
                   cmap=plt.cm.plasma) # nipy_spectral

    cbar = fig.colorbar(mappable=s, ax=ax)
    cbar.set_label('Water Surface Elevation (m)')

    # Plot tidal zone
    tidal_edge_zone.boundary.plot(ax=ax, color='#48ff24', linewidth=1.5, label='LineString')

    # Plot synoptic points
    plt.scatter(synoptic_pts.geometry.x, synoptic_pts.geometry.y, color='black', s=22, label='Data Points')

    # Plot LineString GeoDataFrame on the same axes
    transect.plot(ax=ax, color='black', linewidth=0.75, label='LineString')

    # Add a title to the figure
    fig.suptitle(site_name, fontsize=16)

    # Save the plot to a file
    output_file_path = '../../output/figures/swot/map/pixc/swot_wse_pixc_' + site_id + '_v2.png'
    fig.set_size_inches(8, 4)
    plt.savefig(output_file_path, dpi=400)
    # plt.show()
    plt.close()



# # /------------------------------------------------------------------------
# # /  PLOT RASTER
# import matplotlib.pyplot as plt
#
# data_var = cropped_ds['wse']
#
# # fig, ax = (plt.subplots(1,1, figsize=(10, 6)))
# plt.figure(figsize=(10, 6))
#
# # Plot the raster data
# plt.imshow(data_var,
#            extent=[data_var.x.min(), data_var.x.max(), data_var.y.min(), data_var.y.max()],
#            origin='lower', cmap='viridis', aspect='auto') # plt.cm.nipy_spectral
# plt.colorbar(label= 'Water surface elevation (m)'  )# data_var.units)
#
# plt.scatter(synoptic_pts.geometry.x, synoptic_pts.geometry.y, color='red', label='Data Points')
#
# plt.title(site_id)
#
# # Save the plot to a file
# output_file_path = '../../output/figures/swot/swot_wse_' + site_id + '_v2.png'
# plt.savefig(output_file_path, dpi=400)
# # plt.show()
# plt.close()

