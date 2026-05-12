# Query data from the NOAA COOPS API
# Description of query:  https://api.tidesandcurrents.noaa.gov/api/prod/
# Description of outputs: https://api.tidesandcurrents.noaa.gov/api/prod/responseHelp.html


from nbformat import read
import requests
import pandas as pd


#%%-----------------------------------------------------------------------
def query_noaa_hourly_tide_gauge(station_id, start_date, datum, output_dir):


    # NOAA CO-OPS URL for Data Retrieval
    base_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

    # Hourly interval data	Data length is limited to 1 year
    # Define parameters for the API request
    params = {
        "station": station_id,         # Numerical Id of station
        "begin_date": start_date,      # Start date in YYYYMMDD format
        "range":'8760',                # Number of hours in a year
        "interval": 'h', #'hilo', #'h',
        "product": "predictions",    # Request water level data
        "datum": 'MLLW',# datum, # 'MLLW',                # "IGLD" or  "NAVD"  # Vertical datum (use MLLW for mean lower low water)
        "units": "metric",             # Metric units (meters)
        "time_zone": "LST",            # GMT timezone
        "application": "python_script",# Application identifier
        "format": "json"               # JSON response format
    }

    # Make the HTTP GET request to the API
    response = requests.get(base_url, params=params)

    # Parse the JSON response
    if response.status_code == 200:

        data = response.json()
        print(data)
        # Convert the JSON data into a pandas DataFrame for easy analysis
        df = pd.DataFrame(data["predictions"])
        
        print(df.shape)  # Print shape of DataFrame

        # Rename columns
        df = df.rename(columns={'t': 'datetime_LST', 
                                'v': 'wse_m', 
                                # 's':'stdev', 
                                # 'f':'flag'
                                })
        # add site_id
        df['station_id'] = station_id
        df['datum'] = datum
    
        # Reorder columns
        # df = df[['station_id', 'datetime_LST', 'wse_m', 'datum', 'stdev', 'flag']]
        df = df[['station_id', 'datetime_LST', 'wse_m', 'datum']]

        # Return dataframe
        return(df)
    
    else:
        print(f"Error: Unable to fetch data. HTTP Status Code {response.status_code}")




#%%  Convert datum  -------------------
## TODO:  MAKE THE ELEVATION TRANSFORMATION FROM IGLD85 TO NAVD88

def conv_IGLD2NAVD():

    import pyproj
    # Enable PROJ network for the session
    pyproj.network.set_network_enabled(True)
    from pyproj import Transformer, CRS

    # # Define vertical CRS (IGLD85 -> NAVD88)

    # Define the transformer. This will trigger a network download if the grid is not found locally.
    transformer = Transformer.from_crs(
        # CRS('EPSG:5609'), # IGLD85
        "EPSG:4326+5609",  # IGLD85 height
        CRS("EPSG:5498"), # nad83_navd88 This i 
        # CRS("EPSG:5703"),  # NAVD88
        always_xy=True)

    transformer.transform( -83.3, 42.36, 174)



#%%-----------------------------------------------------------------------
# This saves for all stations in gauge_df file
def save_noaa_coops_wse(gauge_df, years, outdir):

    # Loop through gauges
    for index, row in gauge_df.iterrows():

        # Initialize an empty DataFrame
        results_df = pd.DataFrame()

        site_id = row['site_id']
        station_id = row['station_id']

        # Loop through year
        for year in years:

            print(site_id, station_id, year)

            # Run function, get df of wse data
            # df = query_noaa_hourly_tide_gauge(station_id, year, row['datum'], row['outdir'])
            df = query_noaa_hourly_tide_gauge(station_id, year, row["datum"], outdir)

            # TODO: CONVERT FROM IGLD85 TO NAVD88
            # if row['datum'] == 'IGLD':
            #     [site_id['longitude'], site_id['latitude'], 100]

            # Concatenate all DataFrames into a single DataFrame
            results_df = pd.concat([results_df, df], ignore_index=True)
            results_df['site_id'] = site_id

        # For each site, after all years, save the combined DataFrame to a new CSV file:
        outname = f'{outdir}/noaa_swe_harmonics_{station_id}.csv'
        results_df.to_csv(outname, index=False)



#%%--------------------------------------------------------------------
# Run function
if __name__ == '__main__':
    
    from scripts.config import DATA_DIR

    # # Read in gauge_df
    gauge_df = (
        pd.read_csv(DATA_DIR / 'tide_gauges/all_gauges_list/synoptic_wse_train_val_stations.csv', dtype=str)
        .query('data_source == "NOAA-Harmonics"'))
    

    # # Subset for to single row 
    # gauge_df = gauge_df.loc[[0]]
    # # Replace the id to get the 
    # gauge_df.iloc[0,1] = '8575787'
    

    # Define date for annual data pull
    years = ["20180101","20190101", "20200101","20210101","20220101","20230101", "20240101", "20250101"]

    # output dir
    outdir = DATA_DIR / 'tide_gauges/noaa/predictions'

    #%% Run function
    save_noaa_coops_wse(gauge_df, years, outdir)

