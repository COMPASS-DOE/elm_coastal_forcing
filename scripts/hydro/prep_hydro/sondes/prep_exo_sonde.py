#%%
import os
import glob
import pandas as pd
import numpy as np


#%%--------------------------------------------------------------------
# Prep sonde data

# Define the directory and pattern
dirpath = "/Users/flue473/big_data/synoptic_data_release/v2-0"
# '../../data/synoptic_sensors/exo_sonde/*.csv'

# Find all files matching the pattern
files = glob.glob(dirpath, recursive=True)


# Initialize an empty DataFrame
sonde_data = pd.DataFrame()

# Loop through the files and append to the DataFrame
for file in files:
    print(file)
    df = pd.read_csv(file)
    sonde_data = pd.concat([sonde_data, df])  #, ignore_index=True)

# Filter to water depth
sonde_data = sonde_data[(sonde_data['research_name']=='sonde_depth')]


sonde_data = \
    (sonde_data
    .drop(columns=['ID'])
    .reset_index()
    # Remove these two NaN filled columns
    # 'Location','Sensor_ID',
    .pivot_table(index=['Site', 'Plot', 'TIMESTAMP', 'Instrument', 'Instrument_ID','F_OOB', 'F_OOS'],
                 columns='research_name', values='Value').reset_index() # , fill_value=NULL
    .assign(TIMESTAMP = lambda x: pd.to_datetime(x.TIMESTAMP),
            datetime = lambda x: x.TIMESTAMP.dt.floor('h'))
    # Drop flags
    .query('F_OOB!=1')
    .query('F_OOS!=1')
    .drop(columns=['TIMESTAMP', 'Instrument_ID', 'F_OOB', 'F_OOS'])  # 'Sensor_ID', 'Location', 'ID',
    .groupby(['Site', 'Plot', 'Instrument',  'datetime'])  # 'research_name'])  # 'Sensor_ID', 'Location',
    .mean()
    .reset_index()
    # .drop(columns=['Value'])
    )


#%%
site_order = ['Crane Creek', 'Portage River','Old Woman Creek',
              'GCReW', 'Goodwin Islands', 'Moneystump Swamp', 'Sweet Hall Marsh']

site_order = ['Crane Creek', 'Portage River','Old Woman Creek',
              'GCReW', 'Goodwin Islands', 'Moneystump Swamp', 'Sweet Hall Marsh']


# Reorder sites for the facets
sonde_data['site_name'] = pd.Categorical(sonde_data['site_name'], categories=site_order, ordered=True)



#%%
#/  Plot time series of water depth
import numpy as np
import pandas as pd
from plotnine import *
# import matplotlib as plt
# THIS PREVENTS INTERACTIVE WINDOW ERROR:
# "UserWarning: Starting a Matplotlib GUI outside of the main thread will likely fail."
import matplotlib
matplotlib.use('agg')
from mizani.breaks import date_breaks
from mizani.formatters import date_format
# Prevent continuous warnings from plotnine drawing not working
import warnings
warnings.filterwarnings("ignore")




#%%------------------------------------------------------------------
# p = (

(
    ggplot()

    + geom_hline(sonde_data, aes(yintercept=0), size=0.75, color='#303030')

    # Plot sensor data
    + geom_line(sonde_data, #.dropna(subset=['sonde_depth']),
                aes(x='datetime', y='sonde_depth', color='Site'), size=0.2)

    # + scale_x_datetime(breaks=date_breaks('1 year'), labels=date_format('%Y'))
    + scale_x_datetime(breaks=date_breaks('4 months')) #, labels=date_format('%Y'))
    + scale_y_continuous(trans='reverse')

    + labs(x='', y='OW Sonde water depth (m?)')
    + facet_wrap("Site", scales="free_y", ncol=1)

    + guides(color=guide_legend(title=""))
    + theme_bw()
    + theme(legend_position= 'none', #(0.8, 0.1), 
            panel_grid_major=element_blank(),
            panel_grid_minor=element_blank(),
            axis_text_x=element_text(rotation=45, hjust=1))
            # axis_text_x=element_text(rotation=90, hjust=1))

    ).save('../../output/figures/hydro_forcing_gauges/sonde_depth_timeline_v01.png',
       width=7, height=7, dpi=300, verbose = False)




    # Plot in synoptic wells WTD - DEPTH
    # + geom_line(gw_depth_df,
    #            aes(x='TIMESTAMP_hourly', y='gw_elev_m', color='zone_name'), size=0.2)

