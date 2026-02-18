



# /-------------------------------------------------------------------------------
#/  Get synoptic groundwater wells data
gw_depth_df = pd.read_csv('../../output/results/sensor_gauges/synoptic_gw_elev.csv')  # synoptic_gw_pressure.csv')
gw_depth_df['TIMESTAMP_hourly'] = pd.to_datetime(gw_depth_df['TIMESTAMP_hourly'], errors='coerce')


# make lookup for conversion of site name and id
site_name_id_lut = gw_depth_df[['site_id', 'site_name']].drop_duplicates(subset=['site_id', 'site_name'])
site_name_id_lut



# /-------------------------------------------------------------------------------
#/   Read in Buoy data;  Not gapfilled or fixed because need until after 2020
# '../../output/results/hydro_forcing_gauges/buoy_wl_all_syn_v4_filled_fixed.csv',
boundary_wl_df = pd.read_csv('../../output/results/hydro_forcing_gauges/buoy_wl_all_syn_v4.csv',  low_memory=False)

boundary_wl_df = boundary_wl_df[(boundary_wl_df['datetime'] >= '2023-01-01') & (boundary_wl_df['datetime'] <= '2025-01-01')]


# Convert datatype
boundary_wl_df['water_height_m'] = pd.to_numeric(boundary_wl_df['water_height_m'], errors='coerce')
# boundary_wl_df['total_depth'] = pd.to_numeric(boundary_wl_df['total_depth'], errors='coerce')
boundary_wl_df['datetime'] = pd.to_datetime(boundary_wl_df['datetime'], errors='coerce')
boundary_wl_df['zone_name'] = 'Buoy / Tidal boundary'


# /-------------------------------------------------------------------------------
#/  Get SWOT water elevation
swot_tidal_wse_df = pd.read_csv('../../output/results/swot_wse_synoptic_tidal_edge.csv')
swot_tidal_wse_df['date'] = pd.to_datetime(swot_tidal_wse_df['date'], errors='coerce')

swot_tidal_wse_df = pd.merge(swot_tidal_wse_df, site_name_id_lut, on='site_id', how='left')
swot_tidal_wse_df['zone_name'] = 'SWOT'

# /-------------------------------------------------------------------------------
#/  ORDER SITES
site_order = ['Crane Creek', 'Portage River','Old Woman Creek',
              'GCReW', 'Goodwin Islands', 'Moneystump Swamp', 'Sweet Hall Marsh']

# Reorder sites for the facets
swot_tidal_wse_df['site_name'] = pd.Categorical(swot_tidal_wse_df['site_name'], categories=site_order, ordered=True)
gw_depth_df['site_name']    = pd.Categorical(gw_depth_df['site_name'], categories=site_order, ordered=True)



#---------------------------------------------------------------------------------------
from plotnine import *
import matplotlib
from datetime import datetime
matplotlib.use('agg')

# Plotting with Plotnine
plot = (
    ggplot()

    # plot buoy tidal forcing
    + geom_line(boundary_wl_df, aes(x='datetime', y='water_height_m'), size=0.25 , color='red') #'#bdbdbd')

    # Plot groundwater wells along transect
    + geom_line(gw_depth_df, aes(x='TIMESTAMP_hourly', y='gw_elev_m', color='zone_name'), size=0.25)

    # Add SWOT measurements
    + geom_point(swot_tidal_wse_df, aes(x='date', y='wse_mean', color='zone_name'), size=1.5) # , color='#000000',


    + scale_color_manual(values={'Wetland': 'blue',
                                 'Transition': 'green',
                                 'Upland':'#f003fc',
                                 'SWOT':'black'})

    + scale_x_datetime(date_labels="%m/%y",  date_breaks='2 months', #date_labels='%Y',
                       limits=(datetime(2023, 8, 1),
                               datetime(2024, 8, 1)), expand=[0,0])
    + labs(#title='Water Surface Elevation',
           x='Date',
           y='Water Elevation (NAVD88, m)')

    + facet_wrap("site_name", scales="free", ncol=1)

    + guides(color=guide_legend(title=""))
    + theme_classic()
    + theme(legend_position= 'top', #(0.5, 0.9), # 'none',
            panel_grid_major=element_blank(),
            panel_grid_minor=element_blank(),
            strip_background=element_blank(),
            strip_text=element_text(size=10, weight='bold'),
            panel_spacing=0.08)

    ).save(filename='../../output/figures/swot/ts/swot_time_series_v3.png',
       width = 4.5, height = 16.1, units='in', dpi=300)


