

# #------------------------------------------------------------------
# # Function searching and downloading data from bbox coordinates
# def download_swot_poly_persite(x):
#
#     # x = df.copy() #synoptic_bbox[1:2]
#     # x.info()
#     # print(x.long_min)
#
#     results = earthaccess.search_data(
#         short_name = 'SWOT_L2_HR_LakeSP_2.0',
#         # version = '006',
#         # cloud_hosted = True,
#         bounding_box=(x.long_min, x.lat_min, x.long_max, x.lat_max),
#         # bounding_box = (x.long_min.iloc[0], x.lat_min.iloc[0], x.long_max.iloc[0], x.lat_max.iloc[0]),
#         # bounding_box = ( -97, 32.5, -96.5, 33),
#         temporal = ('2022-03-01','2024-08-02'),
#         count = 100,
#         granule_name='*_NA*'  # here we filter by Reach files (not node), pass=013, continent code=NA
#         # granule_name = '*Reach*_013_NA*') # here we filter by Reach files (not node), pass=013, continent code=NA
#     )
#
#     print(results)
#     results = results[0:1]
#
#
#     # DOWNLOAD DATA
#     earthaccess.download(results, "../../data/swot/poly/")
#
#     # UNZIP
#     from pathlib import Path
#     folder = Path("../../data/swot/poly/")
#     for item in os.listdir(folder): # loop through items in dir
#         if item.endswith(".zip"): # check for ".zip" extension
#             zip_ref = zipfile.ZipFile(f"{folder}/{item}") # create zipfile object
#             zip_ref.extractall(folder) # extract file to dir
#             zip_ref.close() # close file
#
#     os.listdir(folder)

# Command line query to podaac
# https://podaac.github.io/tutorials/quarto_text/DataSubscriberDownloader.html

# '*453_228*', # '*004_353_264R*',
#  + str(row.swot_scene) + '*'
# granule_name = '*NA*'))  #'*' + str(row.swot_pass) + '_' + str(row.swot_tile) + '*' ))