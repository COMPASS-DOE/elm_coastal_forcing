

from pytides import *
# from pytides import tide #as Tide
# from pytides import Tide
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys

# NOTE: This incorrectly imports a different package called 'tide'.
# from pytides.tide import Tide


swot_tidal_wse_df = pd.read_csv('../../output/results/swot/wse_nearshore_unit/swot_wse_nearshore.csv', low_memory=False)

# Rename columns
swot_tidal_wse_df = (swot_tidal_wse_df
    .rename(columns={'wse_mean':'swot_wse_m_navd_mean', 'wse_std':'swot_wse_m_navd_std'})    # Rename columns
    .assign(date = lambda x: pd.to_datetime(x['date'], errors='coerce'))           # Convert datatype
    .assign(datetime_EST = lambda x: x['date'].dt.round('h'))                              # Round to hour
    # .assign(date = lambda x: x['date'].dt.tz_localize('UTC-00:00'))                # If date not localized, localize to GMT
    # .assign(datetime_EST = lambda x: x['date'].dt.tz_convert('UTC-04:00'))         # Convert to local time
    .loc[:, ['site_id', 'datetime_EST', 'swot_wse_m_navd_mean', 'swot_wse_m_navd_std']]      # Subset columns
    )


swot_tidal_wse_df = swot_tidal_wse_df[swot_tidal_wse_df.site_id == 'GCW']
swot_tidal_wse_df = swot_tidal_wse_df.sort_values(by="datetime_EST", ascending=True)


heights = swot_tidal_wse_df['swot_wse_m_navd_mean'].values
t = swot_tidal_wse_df['datetime_EST'].values


# t = swot_tidal_wse_df['datetime_EST'].values.dt.to_pydatetime()
# t = swot_tidal_wse_df['datetime_EST'].map(lambda x: x.to_pydatetime())

##Prepare a list of datetimes, each 6 minutes apart, for a week.
prediction_t0 = datetime(2023,8,1)
# hours = 0.1*np.arange(7 * 24 * 10)
hours = np.arange(7 * 24 * 10) 
times = Tide._times(prediction_t0, hours.tolist())  #modified from original to use Tide._times


t = pd.to_datetime(t).to_pydatetime()


##Fit the tidal data to the harmonic model using Pytides
my_tide = Tide.decompose(heights, t)
##Predict the tides using the Pytides model.
my_prediction = my_tide.at(times)

##Prepare NOAA's results
noaa_verified = []
noaa_predicted = []

# f = open('data/'+station_id+'_noaa', 'r')
# for line in f:
#     noaa_verified.append(line.split()[2])
#     noaa_predicted.append(line.split()[3])
# f.close()

##Plot the results
plt.plot(hours, my_prediction, label="Pytides")
plt.plot(hours, noaa_predicted, label="NOAA Prediction")
plt.plot(hours, noaa_verified, label="NOAA Verified")
plt.legend()
plt.title('Comparison of Pytides and NOAA predictions for Station: ' + str(station_id))
plt.xlabel('Hours since ' + str(prediction_t0) + '(GMT)')
plt.ylabel('Metres')
plt.show()





# Convert to a readable format "%Y-%m-%d %H:%M": Using datetime module
# human_readable = 
# datetime.datetime.utcfromtimestamp(swot_tidal_wse_df['datetime_EST'].values).strftime("%Y-%m-%d %H:%M")



# Convert to timezone-unaware format while keeping time values the same
# swot_tidal_wse_df["datetime_EST"] = swot_tidal_wse_df["datetime_EST"].dt.tz_convert(None) # .dt.tz_localize(None)
# 

# ##Prepare our tide data
# station_id = '8516945'

# heights = []
# t = []

# f = open('data/'+station_id, 'r')
# for i, line in enumerate(f):
#     t.append(datetime.strptime(" ".join(line.split()[:2]), "%Y-%m-%d %H:%M"))
#     heights.append(float(line.split()[2]))
# f.close()

#For a quicker decomposition, we'll only use hourly readings rather than 6-minutely readings.
# heights = np.array(heights[::10])
# t = np.array(t[::10])


# datetime.strptime(t, "%Y-%m-%d %H:%M")

# timestamp = np.int64(1696947600)  # Example: 2023-10-10 12:00 UTC
# # Convert to a readable format "%Y-%m-%d %H:%M": Using datetime module
# human_readable = datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

