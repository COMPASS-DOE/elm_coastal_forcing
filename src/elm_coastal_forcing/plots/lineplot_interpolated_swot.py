
#%%-----------------------------------------------------------
### PLOT THE INTERPOLATED TIME SERIES
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_time_series_with_refs(df, sonde_df=None, start_date=None, end_date=None, suffix=''): 

    # Get site_id
    # site_id = df.loc[0, 'site_id']
    site_id = df.iloc[0]['site_id']


    if start_date is not None and end_date is not None:
        df = df[(df['datetime_LST'] >= start_date) & (df['datetime_LST'] <= end_date)]
        if sonde_df is not None:
            sonde_df = sonde_df[(sonde_df['timestamp_local_hr'] >= start_date) & (sonde_df['timestamp_local_hr'] <= end_date)]


    #---------------------------------------------------
    # Create the plot
    plt.figure(figsize=(12, 6))

    # Plot reference gauge
    plt.plot( df['datetime_LST'], df['gauge_wse_m'], '-', label='Reference tide gauge', 
             linewidth=.5, alpha=0.85)


    #---------------------------------------------------
    # Plot the original sparse time series

    # Reconstructed interpolated SWOT WSE
    plt.plot( df['datetime_LST'],  df['reconstructed_wse'], '-', label='Interpolated SWOT', 
             color="#fe5b5b", linewidth=.5, alpha=0.95)

    
    plt.errorbar(df['datetime_LST'], 
             df['swot_wse_m_navd_mean'], 
             yerr=df['swot_wse_m_navd_std'],
             fmt='o', capsize=0, capthick=0, 
             markersize=4, linewidth=0.5,
             color="#b40000", ecolor='red', 
             label='SWOT wse of nearshore cluster (mean +/- 1 stdev)',
             markeredgewidth=0.8,  # Thickness of the white outline
             markeredgecolor='white')  # White outline around the points


    #---------------------------------------------------
    # 
    if sonde_df is not None:
        plt.plot(sonde_df['timestamp_local_hr'],  
                 sonde_df['elev_m'], '-', 
                 label='GCReW weir elevation', 
                 color='black', linewidth=.5)



    #---------------------------------------------------
    # Format the x-axis to display dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # Set axis if argument provided
    if start_date is not None:
        plt.gca().set_xlim(start_date, end_date)

    # Autoscale only y-axis (use axis='both' for both x and y)
    plt.gca().autoscale(axis='y')  


    #---------------------------------------------------
    # Add labels, title, and legend
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Water Surface Elevation (NAVD88; m)', fontsize=12)
    plt.title(site_id, fontsize=12, fontweight='bold')
    
    # plt.title('Original vs Interpolated vs Reference Series', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)

    # Add grid
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.5)

    # Save the plot in the created directory
    plt.savefig(f"../../output/figures/swot/ts/ts_{site_id}_tiderecnst_{suffix}.png", 
                dpi=400, bbox_inches='tight')

    # Show plot
    plt.show()
