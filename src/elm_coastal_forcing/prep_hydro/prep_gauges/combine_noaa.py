






def combine_noaa(indir, site_id, suffix): 
        
    # Find all files matching the pattern
    files = glob.glob(indir, recursive=False)

    # Initialize an empty list to store DataFrames
    dfs = pd.DataFrame()

    # Loop through the list of CSV files and read each one into a DataFrame
    for f in files:
        print(f)
        df = pd.read_csv(f)
        dfs = pd.concat([dfs, df])


    dfs = ( \
        dfs
        # (pd.concat(dfs, ignore_index=True)

        #  .rename(columns={'Verified (m)': 'wse_m_navd88'}) # verified the datum is NAVD88
        .assign(swe_navd88_m=lambda x: pd.to_numeric(x.swe_navd88_m, errors='coerce'))
        .assign(datetime_LST=lambda x: pd.to_datetime(x['datetime_LST']))
        #  .assign(datetime_est=lambda x: pd.to_datetime(x['Date'] + ' ' + x['Time (GMT)']) -pd.Timedelta(hours=5))
        .assign(source='NOAA',
                # station='Annapolis-8575512',
                site_id = site_id)
        )
    

    # Save to file
    swe_all.to_csv('../../output/results/tide_gauges/synoptic_tide_gauges.csv', index=False)







if __name__ == '__main__':

    if 0: 
        #----------------------------------------------------------------------------------
        #  GOODWIN - NOAA
        swe_GWI = combine_noaa('../../data/tide_gauges/GWI', 'GWI', 'swe_8637689_all.csv')
        # swe_GWI = '../data/tide_gauges/CRC/swe_noaa_coops_CRC_9063079.csv'

        #----------------------------------------------------------------------------------
        #  GCREW - NOAA
        swe_GCW = combine_noaa('../../data/tide_gauges/GCW', 'GCW', 'swe_8575512_all.csv')


        #----------------------------------------------------------------------------------
        #  MONEYSTUMP - NOAA
        swe_MSM = combine_noaa('../../data/tide_gauges/MSM', 'MSM', 'swe_8571892_all.csv')


        #----------------------------------------------------------------------------------
        # Combine upto date SWE
        swe_all = pd.concat([
                swe_GWI,
                swe_GCW,
                swe_MSM,],
                axis=0)
        
        # Save DataFrame to CSV
        swe_all.to_csv('../../output/results/tide_gauges/synoptic_tide_gauges.csv', index=False)

