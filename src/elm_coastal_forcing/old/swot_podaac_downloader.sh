# Command line query to podaac
# https://podaac.github.io/tutorials/quarto_text/DataSubscriberDownloader.html

podaac-data-downloader -c SWOT_SIMULATED_NA_CONTINENT_L2_HR_RiverSP_V1 \
 -d ./SWOT_SIMULATED_NA_CONTINENT_L2_HR_RiverSP_V1 \
 -start-date 2022-08-02T00:00:00Z \
 --end-date 2022-08-22T00:00:00Z \
 -b="-97,32.5,-96.5,33"