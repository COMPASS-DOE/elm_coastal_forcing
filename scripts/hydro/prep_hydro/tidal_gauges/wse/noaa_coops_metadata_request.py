

# Use metadata API to get all water level stations in Maryland (MD)

import requests

def fetch_sation_metadata(states, params=None):
    # base_url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"
    base_url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json" #?type=waterlevels"
    
    # base_url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions"
    #"&expand=details,sensors,floodlevels,tidepredoffsets,products,disclaimers,notices&units=metric"
    # Products:  https://api.tidesandcurrents.noaa.gov/mdapi/prod/

    
    try:
        # Make API request
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            stations = data.get("stations", [])
            # for station
            # Filter stations by state
            stations = [station for station in stations if station.get("state") in states]
            # stations = stations.get("state", "MD")
            return stations
        else:
            print(f"Failed to fetch stations. HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error during API request: {e}")
        return None




#%%---------------------------------------------------------------------
import pandas as pd


# Fetch all water level stations in Maryland (MD)
states = ['MD','DL','VA']

# Specific metric for water levels
wl_stations = fetch_sation_metadata(states, { "type": "waterlevels" })  
wl_stations = pd.DataFrame(wl_stations)# [columns_to_extract]
wl_stations.to_csv('../../data/tide_gauges/all_gauges_list/noaa_stations_waterlevel_MD_DL_VA.csv', index=False)



# Query stattions with tide predictions
# R for reference stations, S for subordinate stations.
tidepred_stations = fetch_sation_metadata(states, { "type": "tidepredictions" })  # Specific metric for tide predictions
tidepred_stations = pd.DataFrame(tidepred_stations)# [columns_to_extract]
tidepred_stations.to_csv('../../data/tide_gauges/all_gauges_list/noaa_stations_tidepredictions_MD_DL_VA.csv', index=False)

