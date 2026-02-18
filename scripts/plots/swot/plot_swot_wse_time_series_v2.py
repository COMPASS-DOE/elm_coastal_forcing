

import pandas as pd



#%%-------------------------------------------------------------------------------
#  Get synoptic groundwater wells data
gw_depth_df = pd.read_csv('../../output/results/sensor_gauges/synoptic_gw_elev.csv')  # synoptic_gw_pressure.csv')
gw_depth_df['TIMESTAMP_hourly'] = pd.to_datetime(gw_depth_df['TIMESTAMP_hourly'], errors='coerce')


# make lookup for conversion of site name and id
site_name_id_lut = gw_depth_df[['site_id', 'site_name']].drop_duplicates(subset=['site_id', 'site_name'])
site_name_id_lut



#%%-------------------------------------------------------------------------------
#  TIDE GAUGES;  Not gapfilled or fixed because need until after 2020

boundary_wl_df = pd.read_csv('../../output/results/hydro_forcing_gauges/buoy_wl_all_syn_v05.csv',  low_memory=False)

boundary_wl_df['datetime_est'] = pd.to_datetime(boundary_wl_df['datetime_est'], errors='coerce')
boundary_wl_df = boundary_wl_df[(boundary_wl_df['datetime_est'] >= '2023-01-01') & (boundary_wl_df['datetime_est'] <= '2025-01-01')]

# Convert datatype
boundary_wl_df['wse_m_navd88'] = pd.to_numeric(boundary_wl_df['wse_m_navd88'], errors='coerce')
boundary_wl_df['datetime'] = pd.to_datetime(boundary_wl_df['datetime_est'], errors='coerce')



#%%-------------------------------------------------------------------------------
#/  Get SWOT water elevation - sparse

swot_tidal_wse_df = pd.read_csv('../../output/results/swot_wse_synoptic_nearshore_v01.csv', low_memory=False)
swot_tidal_wse_df['date'] = pd.to_datetime(swot_tidal_wse_df['date'], errors='coerce')


swot_tidal_wse_df = pd.merge(swot_tidal_wse_df, site_name_id_lut, on='site_id', how='left')
# swot_tidal_wse_df['zone_name'] = 'SWOT'



# Get 


#%%-------------------------------------------------------------------------------
#/  ORDER SITES
site_order = ['Crane Creek', 'Portage River','Old Woman Creek',
              'GCReW', 'Goodwin Islands', 'Moneystump Swamp', 'Sweet Hall Marsh']

# Reorder sites for the facets
boundary_wl_df['site_name'] = pd.Categorical(boundary_wl_df['site_name'], categories=site_order, ordered=True)
swot_tidal_wse_df['site_name'] = pd.Categorical(swot_tidal_wse_df['site_name'], categories=site_order, ordered=True)
gw_depth_df['site_name']    = pd.Categorical(gw_depth_df['site_name'], categories=site_order, ordered=True)



#%%---------------------------------------------------------------------------------------
from plotnine import *
import matplotlib
from datetime import datetime
matplotlib.use('agg')

# Plotting with Plotnine
plot = (
    ggplot()

    # plot buoy tidal forcing
    + geom_line(boundary_wl_df, aes(x='datetime_est', y='wse_m_navd88', color='zone_name'), size=0.25 ) # , color='red'   '#bdbdbd')

    # Plot groundwater wells along transect
#     + geom_line(gw_depth_df, aes(x='TIMESTAMP_hourly', y='gw_elev_m', color='zone_name'), size=0.25)

    # Add SWOT measurements
    + geom_point(swot_tidal_wse_df, aes(x='date', y='wse_navd88_mean', color='zone_name'), size=1.5)  # , color='#000000',


    + scale_color_manual(values={'Wetland': 'blue',
                                 'Transition': 'green',
                                 'Upland':'#f003fc',
                                 'swot_nearshore':'black',
                                 'Open Water; Tidal forcing':'red'})

    + scale_x_datetime(date_labels="%m/%y",  date_breaks='2 months',  #date_labels='%Y',
                       limits=(datetime(2023, 8, 1),
                               datetime(2024, 8, 1)), expand=[0,0])
    + labs(#title='Water Surface Elevation',
           x='Date',
           y='Water Surface Elevation (NAVD88, m)')

    + facet_wrap("site_name", scales="free", ncol=2)

    + guides(color=guide_legend(title=""))
    + theme_classic()
    + theme(legend_position= 'top', #(0.5, 0.9), # 'none',
            panel_grid_major=element_blank(),
            panel_grid_minor=element_blank(),
            strip_background=element_blank(),
            strip_text=element_text(size=10, weight='bold'),
            panel_spacing=0.04)

    ).save(filename='../../output/figures/swot/ts/swot_time_series_v6.png',
       width = 390, height = 350, units='mm', dpi=300)


