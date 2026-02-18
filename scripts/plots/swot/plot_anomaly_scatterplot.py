


# /-------------------------------------------------------------------------------
#/  Get SWOT water elevation
swot_tidal_wse_df = pd.read_csv('../../output/results/swot_wse_synoptic_tidal_edge.csv')
swot_tidal_wse_df['date'] = pd.to_datetime(swot_tidal_wse_df['date'], errors='coerce')

swot_tidal_wse_df = pd.merge(swot_tidal_wse_df, site_name_id_lut, on='site_id', how='left')
swot_tidal_wse_df['zone_name'] = 'SWOT'

# Round to hourly
swot_tidal_wse_df['date'] = swot_tidal_wse_df['date'].dt.round('h')



# /-------------------------------------------------------------------------------
#/  Get synoptic groundwater wells data
gw_depth_df = pd.read_csv('../../output/results/sensor_gauges/synoptic_gw_elev.csv')  # synoptic_gw_pressure.csv')
gw_depth_df['TIMESTAMP_hourly'] = pd.to_datetime(gw_depth_df['TIMESTAMP_hourly'], errors='coerce')
# Filter to wetlands only
gw_depth_df = gw_depth_df[gw_depth_df.zone_id == 'W']

# make lookup for conversion of site name and id
site_name_id_lut = gw_depth_df[['site_id', 'site_name']].drop_duplicates(subset=['site_id', 'site_name'])


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
#/    Combine into a single df

gw_depth_df_simp = gw_depth_df[['site_name','TIMESTAMP_hourly','gw_elev_m']]
boundary_wl_df_simp = boundary_wl_df[['site_name','datetime','water_height_m']]

# Rename column in boundary_wl_df_simp
boundary_wl_df_simp = boundary_wl_df_simp.rename(columns={'datetime': 'date'})
gw_depth_df_simp = gw_depth_df_simp.rename(columns={'TIMESTAMP_hourly': 'date'})

# Perform the first left join with gw_depth_df_simp
merged_df = swot_tidal_wse_df.merge(gw_depth_df_simp, how='left', on=['site_name', 'date'])
merged_df = merged_df.merge(boundary_wl_df_simp, how='left', on=['site_name', 'date'])


site_name = site.site_name
site_id = site.site_id
print(site_id + ' ' + site_name)


# /-------------------------------------------------------------------------------
#/  ORDER SITES
site_order = ['Crane Creek', 'Portage River','Old Woman Creek',
              'GCReW', 'Goodwin Islands', 'Moneystump Swamp', 'Sweet Hall Marsh']

# Reorder sites for the facets
merged_df['site_name'] = pd.Categorical(merged_df['site_name'], categories=site_order, ordered=True)
# gw_depth_df['site_name']    = pd.Categorical(gw_depth_df['site_name'], categories=site_order, ordered=True)




# /---------------------------------------------------------------------------------------
#/  # Compute the anomalies
merged_df['wse_mean_anomaly'] = merged_df['wse_mean'] - merged_df.groupby('site_name')['wse_mean'].transform('mean')
merged_df['gw_elev_m_anomaly'] = merged_df['gw_elev_m'] - merged_df.groupby('site_name')['gw_elev_m'].transform('mean')
merged_df['water_height_m_anomaly'] = merged_df['water_height_m'] - merged_df.groupby('site_name')['water_height_m'].transform('mean')


# /---------------------------------------------------------------------------------------
#/
# Define a function to calculate R² and RMSE
from sklearn.metrics import r2_score, mean_squared_error


# Define a function to calculate R² and RMSE
def compute_r2_rmse(df, x_col, y_col):
    # Drop rows with NaN values in either column
    df = df.dropna(subset=[x_col, y_col])

    # If no metrics can be computed, return blanks
    if len(df) < 2:
        return '', ''

    try:
        r2 = round(r2_score(df[x_col], df[y_col]), 2)
        rmse = round(np.sqrt(mean_squared_error(df[x_col], df[y_col])), 2)
        return r2, rmse
    except Exception as e:
        return '', ''


# Initialize lists to store results
n_rows = []
r2_gw = []
rmse_gw = []
r2_wh = []
rmse_wh = []

# Group by site_name and compute metrics
for name, group in merged_df.groupby('site_name'):
    n_rows.append(group.shape[0])

    r2, rmse = compute_r2_rmse(group, 'wse_mean_anomaly', 'gw_elev_m_anomaly')
    r2_gw.append(r2)
    rmse_gw.append(rmse)

    r2, rmse = compute_r2_rmse(group, 'wse_mean_anomaly', 'water_height_m_anomaly')
    r2_wh.append(r2)
    rmse_wh.append(rmse)

# Create a DataFrame to hold the computed values
results_df = pd.DataFrame({
    'site_name': merged_df['site_name'].unique(),
    'nrow': n_rows,
    'R2_gw': r2_gw,
    'RMSE_gw': rmse_gw,
    'R2_wh': r2_wh,
    'RMSE_wh': rmse_wh })



results_df['nrow']    = 'n=' + results_df['nrow'].astype(str)
results_df['R2_gw']   = 'R^2=' + results_df['R2_gw'].astype(str)
results_df['RMSE_gw'] = 'RMSE=' + results_df['RMSE_gw'].astype(str)
results_df['R2_wh']   = 'R^2=' + results_df['R2_wh'].astype(str)
results_df['RMSE_wh'] = 'RMSE=' + results_df['RMSE_wh'].astype(str)

# Merge the results back into the original DataFrame
merged_df = pd.merge(merged_df, results_df, on='site_name', how='left')



# /---------------------------------------------------------------------------------------
#/
# from plotnine import *
import matplotlib
from datetime import datetime

matplotlib.use('agg')

# Plotting with Plotnine
plot = (
        ggplot(merged_df)

        # Add 1:1 line
        + geom_abline(slope=1, intercept=0, color='grey', size=0.2)

        # Add SWOT measurements
        + geom_point(merged_df, aes(x='gw_elev_m_anomaly', y='wse_mean_anomaly'),
                     color='red', size=2)

        # Add SWOT measurements
        + geom_point(merged_df, aes(x='water_height_m_anomaly', y='wse_mean_anomaly'),
                     color='blue', size=2)

        # + geom_text(aes(x=0.44, y=1.1, label='nrow'), color='black', ha='left', size=7)
        + geom_text(aes(x=0.44, y=1.0), label='Tidal boundary', color='red', ha='left', size=7)
        + geom_text(aes(x=0.5, y=0.9, label='R2_gw'), color='red', ha='left', size=7)
        + geom_text(aes(x=0.5, y=0.8, label='RMSE_gw'), color='red', ha='left', size=7)
        + geom_text(aes(x=0.44, y=0.7), label='Marsh well', color='blue', ha='left', size=7)
        + geom_text(aes(x=0.5, y=0.6, label='R2_wh'), color='blue', ha='left', size=7)
        + geom_text(aes(x=0.5, y=0.5, label='RMSE_wh'), color='blue', ha='left', size=7)

        + scale_x_continuous(limits=[-0.3, 0.75])
        + scale_y_continuous(limits=[-0.5, 1.25])

        + labs(# title='Water Surface Elevation',
           x='In situ water elevation anomaly (NAVD88, m)',
            y='SWOT water surface elevation anomaly (m)')

        + facet_wrap("site_name", scales="free", ncol=1)

        + guides(color=guide_legend(title=""))
        + theme_classic()
        + theme(legend_position='top',  # (0.5, 0.9), # 'none',
                panel_grid_major=element_blank(),
                panel_grid_minor=element_blank(),
                strip_background=element_blank(),
                strip_text_x =element_text(size=10, weight='bold'),
                panel_spacing=0.08)

).save(filename='../../output/figures/swot/scatterplot/swot_wse_scatterplot_v2.png',
       width=3, height=16, units='in', dpi=300)


