# Water Mask Pixel Cloud NetCDF - SWOT_L2_HR_PIXC_2.0
# Water Mask Pixel Cloud Vector Attribute NetCDF - SWOT_L2_HR_PIXCVec_2.0
# River Vector Shapefile - SWOT_L2_HR_RiverSP_2.0
# Lake Vector Shapefile - SWOT_L2_HR_LakeSP_2.0
# Raster NetCDF - SWOT_L2_HR_Raster_2.0


#--------------------------------------------------------------------------
#  GET LAKE_SP
def dl_lakepoly_persite(row):

    import json
    import earthaccess

    earthaccess.login(strategy='all', persist=True)  # 'interactive'
    auth = earthaccess.login()      # earthaccess.login()

    #  Only need pass and tile, not scene
    # C = Cycle;  P = Pass; T=Tile
    granule_search = '*_' + str(row.swot_pass) + '_' + '*NA*'



    results = (
        earthaccess.search_data(
            short_name = 'SWOT_L2_HR_LakeSP_D', #'SWOT_L2_HR_LakeSP_2.0',  # 'SWOT_L2_HR_LakeSP_Obs'  'SWOT_L2_HR_LakeSP_Unassigned' 'SWOT_L2_HR_LakeSP_Prior'
            granule_name = granule_search,
            count = 150,
            temporal = ('2023-01-01 00:00:00', '2025-11-29 23:59:59')))


    #--------------------------------------------------------------------------
    # Save results to json file
    with open('/Users/flue473/big_data/swot/swot_lakesp_search.json', 'w') as f:
        json.dump(results, f, indent=4)


    # Download last item to folder
    earthaccess.download(results[-4:], "/Users/flue473/big_data/swot/lakesp" + row.site_id + '/')




#--------------------------------------------------------------------------
def dl_pixc_persite(row):

    import json
    import earthaccess
    import pandas as pd

    #  Only need pass and tile, not scene
    # C = Cycle;  P = Pass; T=Tile
    granule_search = '*_' + str(row.swot_pass) + '_' + str(row.swot_tile) + str(row.swot_tile_l) + '*'

    results = (
        earthaccess.search_data(
            short_name = 'SWOT_L2_HR_PIXC_2.0',
            granule_name = granule_search,
            count = 150,
            temporal = ('2023-01-01 00:00:00', '2025-07-29 23:59:59')))  


    # Get list of granules
    granules = [item["umm"]["GranuleUR"] for item in results]
    # Split each string by the underscore
    granules_split = [item.split('_') for item in granules]
    granules_split = pd.DataFrame(granules_split,
                                  columns=["SWOT", "Level", "Resolution", "DataProduct", "Pass", "Orbit", "Tile", "StartDate", "EndDate", "CRID", "Counter"])
    granules_split["CRID_Counter"] = granules_split["CRID"] + '_' + granules_split["Counter"]


    # Get table ranking the priority of different versions of SWOT data
    swot_prod_rank = pd.read_csv('/Users/flue473/big_data/swot/swot_prod_rank.csv')[['CRID_Counter', 'Rank']]

    # Join the rank df
    granules_split = pd.merge(granules_split, swot_prod_rank, on="CRID_Counter", how='left')

    # Make the index a column
    granules_split = granules_split.reset_index()  # The index is moved to a column named 'index'


    # Group by 'StartDate' or 'EndDate', and keep the row with the smallest Rank
    # For each date/granule, keep only the best product
    granules_split = granules_split.loc[granules_split.groupby('StartDate')['Rank'].idxmin()]

    # Subset results to only indices with
    results_bestprod = [results[idx] for idx in granules_split['index']]


    # Save search results to file
    if 0:
        with open('../../output/results/swot/swot_pixcvec_search.json', 'w') as f:
            json.dump(results_bestprod, f, indent=4)


    # DOWNLOAD DATA and save to site subdirectory
    earthaccess.download(results_bestprod, '/Users/flue473/big_data/swot/pixc/' + row.site_id + '/')




#--------------------------------------------------------------------------
def dl_raster_persite(row):

    import json
    import earthaccess

    # For Raster Granules: PPP_SSS = Pass & scene
    # Two versions: 100m and 250m
    granule_search =  '*100m' + '*_' + str(row.swot_pass) + '_' + str(row.swot_scene) + '*'

    results = (
        earthaccess.search_data(
            short_name = 'SWOT_L2_HR_Raster_2.0',
            granule_name = granule_search,
            count = 250,
            temporal = ('2023-04-01 00:00:00', '2024-11-29 23:59:59')))

    # Get list of granules
    granules = [item["umm"]["GranuleUR"] for item in results]

    # Save search results to file
    with open('../../output/results/swot/swot_raster_search.json', 'w') as f:
        json.dump(results, f, indent=4)

    # DOWNLOAD DATA
    earthaccess.download(results, "../../data/swot/raster/" + row.site_id + '/')
