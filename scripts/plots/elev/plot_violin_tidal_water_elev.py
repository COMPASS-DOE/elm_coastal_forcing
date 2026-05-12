# from plotnine import ggplot, aes, theme, geom_point, theme_minimal,  labs, geom_histogram, coord_flip, facet_wrap
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



#%%-------------------------------------------------------------------------------
#  Get synoptic groundwater wells data
gw_depth_df = pd.read_csv('../../output/results/sensor_gauges/synoptic_gw_elev.csv')  # synoptic_gw_pressure.csv')
gw_depth_df['TIMESTAMP_hourly'] = pd.to_datetime(gw_depth_df['TIMESTAMP_hourly'], errors='coerce')


#----------------------------------------------------------------------------------
#  Get buoy data

# Read in Buoy data
boundary_wl_df = pd.read_csv(
    '../../output/results/hydro_forcing_gauges/buoy_wl_all_syn_v4_filled_fixed.csv',
    low_memory=False)

# Convert datatype
boundary_wl_df['water_salinity'] = pd.to_numeric(boundary_wl_df['water_salinity'], errors='coerce')
boundary_wl_df['water_height_m'] = pd.to_numeric(boundary_wl_df['water_height_m'], errors='coerce')
# boundary_wl_df['total_depth'] = pd.to_numeric(boundary_wl_df['total_depth'], errors='coerce')
boundary_wl_df['datetime'] = pd.to_datetime(boundary_wl_df['datetime'], errors='coerce')
boundary_wl_df['zone_name'] = 'Tidal boundary'



# /-----------------------------------------------------------#
#/ VIOLIN PLOT OF WATER HEIGHT - NAD88 time series plot


# Get ground elevation
ground_elev = pd.read_csv('../data/processed/synoptic_site_pts/synoptic_elev_zone_v3.csv')
ground_elev['elev_m'] = ground_elev['elev']
# Convert to meters
ground_elev['elev_m'][(ground_elev['region_id'] == 'LE')] = ground_elev['elev'] * 0.3048
# Create a minimum for plotting
ground_elev['elev_m_min'] = ground_elev['elev']
ground_elev['elev_m_min'][(ground_elev['region_id'] == 'LE')] = 170
ground_elev['elev_m_min'][(ground_elev['region_id'] == 'CB')] = -1

# Make individual adjustments
ground_elev.loc[(ground_elev['site_id'] == 'OWC') & (ground_elev['zone_id'] == 'UP'), 'elev_m'] = 177
ground_elev.loc[(ground_elev['site_id'] == 'GCW') & (ground_elev['zone_id'] == 'UP'), 'elev_m'] = 2.6
ground_elev.loc[(ground_elev['site_id'] == 'SWH'), 'elev_m_min'] = -2.22


#----------------------------------------------------------------------------------
# REORDER FOR PLOTTING
site_order = ['Crane Creek', 'Portage River','Old Woman Creek',
              'GCReW', 'Goodwin Islands', 'Moneystump Swamp', 'Sweet Hall Marsh']

# Reorder sites for the facets
boundary_wl_df['site_name'] = pd.Categorical(boundary_wl_df['site_name'], categories=site_order, ordered=True)
gw_depth_df['site_name']    = pd.Categorical(gw_depth_df['site_name'], categories=site_order, ordered=True)
ground_elev['site_name']    = pd.Categorical(ground_elev['site_name'], categories=site_order, ordered=True)

# Order transect zones for plotting
zone_order = ['Upland', 'Transition', 'Wetland', 'Tidal boundary']
gw_depth_df['zone_name'] = pd.Categorical(gw_depth_df['zone_name'], categories=zone_order, ordered=True)
ground_elev['zone_name'] = pd.Categorical(ground_elev['zone_name'], categories=zone_order, ordered=True)




# GENERATE VIOLIN PLOT FOR LE
# Run twice; once for each
(
ggplot()

# Plot ground surface elevation
# [ground_elev['region_id']=='LE'],
+ geom_bar(ground_elev,
           aes(x='zone_name', y='elev_m'),
           stat='identity',
           width=0.99,
           size=0, fill='#cccccc', color='#FFFFFF')

# Plot negative ground surface elevation
+ geom_bar(ground_elev,
           aes(x='zone_name', y='elev_m_min'),
           stat='identity',
           width=0.99,
           size=0, fill='#cccccc', color='#FFFFFF')

# Plot buoys water HEIGHT
+ geom_violin(boundary_wl_df,
            aes(x='zone_name', y='water_height_m', fill='zone_name'),
              style='right', size = 0)


# Plot in synoptic wells WTD - DEPTH
+ geom_violin(gw_depth_df,
           aes(x='zone_name', y='gw_elev_m', fill='zone_name'),
              color=None,
              #color='#0003bd', fill='#0003bd',
              size = 0.2,
              style='right', width=1.75)

+ labs(x='', y='Water Elevation (NAVD88, m)')
+ facet_wrap("site_name", scales="free", ncol=1)

+ scale_y_continuous(expand=[0,0])
+ scale_x_discrete(breaks=['Upland', 'Transition', 'Wetland', 'Tidal boundary']) #, expand=[0,0])
+ scale_fill_manual(values={'Wetland': 'blue',
                             'Transition': 'green',
                             'Upland': '#f003fc',
                             'Tidal boundary': 'red'})

+ guides(color=guide_legend(title=""))
+ theme_classic()
+ theme(legend_position= 'none', # (0.8, 0.1),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        strip_background=element_blank(),
        strip_text=element_text(size = 10, weight='bold'),
        panel_spacing=0.1)

# + coord_cartesian(ylim=[170, 177], expand=True)
# ).save('../../output/figures/hydro_forcing_gauges/in_situ_wl_all_ts_violin_v27_CB.png',
#    width=4, height=16, dpi=300, verbose = False)
).save('../../output/figures/hydro_forcing_gauges/in_situ_wl_all_ts_violin_v27_LE.png',
   width = 4, height = 16, dpi = 300, verbose = False)



# ground_elev = gw_depth_df.drop_duplicates(subset=['site_name','zone_name','elev_m'])

# erie_hydro_df_3sites['buoy_name'] = 'Hydro boundary'
#
# import itertools
# # Generate all combinations of colors and sizes
# combinations = list(itertools.product(ground_elev.site_name, ground_elev.zone_name))
# # Create a DataFrame from the combinations
# combinations = pd.DataFrame(combinations, columns=['site_name', 'zone_name'])
#%% Add missing combinations of sites-zones for plotting to work.
# addons = pd.DataFrame({'site_name': ['GCReW', 'Old Woman Creek'],
#                        'zone_name': ['Upland', 'Upland'],
#                        'elev_m': [np.nan, np.nan]})
# ground_elev = pd.concat([ground_elev, addons], axis=0)
