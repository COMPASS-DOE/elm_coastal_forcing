
# Plot all the reconstructed 
import pandas as pd
import matplotlib.pyplot as plt


# Read in file
site_id = 'GCW'
wse_rcstr_df = pd.read_csv(f'../../output/results/reconstr_wse/{site_id}_nearshore_wse_reconstr.csv')

wse_rcstr_df = wse_rcstr_df.assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce')) 


#%% Filter to shorter time period -----------------------------------
from datetime import datetime
import pytz
eastern = pytz.timezone('US/Eastern')
start_date = eastern.localize(datetime(2025, 2, 12))
end_date   = eastern.localize(datetime(2025, 2, 23))

# Clean up wse dataframe
wse_rcstr_df = ( wse_rcstr_df
    # .drop_duplicates(subset=['datetime_LST'], keep='last')
    .query("(datetime_LST > @start_date) & (datetime_LST <= @end_date)"))

# Exclude problematic 
wse_rcstr_df = wse_rcstr_df[wse_rcstr_df.unit_id != 36]


wse_rcstr_df.unit_id.unique()
wse_rcstr_df.info()


#%% Make figure  ----------------------------------------------

fig, ax = plt.subplots(figsize=(8, 5))

for unit, grp in wse_rcstr_df.groupby('unit_id'):
    ax.plot(grp['datetime_LST'], grp['reconstructed_wse'], label=unit, linewidth=0.8)

ax.set_xlabel('Datetime (LST)')
ax.set_ylabel('Reconstructed WSE')
ax.set_title('Reconstructed hourly WSE per nearshore unit')
ax.legend(title='unit_id', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.get_legend().remove() # Remove legend
fig.tight_layout() 


# Save the plot in the created directory
plt.savefig(f"../../output/figures/reconstruct_wse/ts/ts_{site_id}_perunit_v01.png", 
            dpi=400, bbox_inches='tight')


plt.show()

