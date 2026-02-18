


from pathlib import Path
import datetime
from datetime import datetime
import pytz
import numpy as np


#%% File paths and constants --------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / 'data'
RESULTS_DIR = PROJECT_ROOT / 'output/results'

# List of site codes
SITE_CODE_LIST = ['OWC'] #, 'GCW', 'SWM', 'PTR', 'SNC', 'TNC', 'WSC']

# Time constants
EASTERN_TZ = pytz.timezone("US/Eastern")
START_DATE = EASTERN_TZ.localize(datetime(2022, 9, 1))
END_DATE = EASTERN_TZ.localize(datetime(2025, 5, 1))


#%%  INPUTS DATA ------------------------------------------


#%% SYNOPTIC SITES ----------------------------------------

# Path to synoptic site bounding boxes
SYN_BBOX_PATH = DATA_DIR / 'site_pts/synoptic/synoptic_sites_bbox.geojson'
# Path to synoptic site points
SYN_PTS_PATH = DATA_DIR / 'synoptic_sites/pts/processed/synoptic_pts_wgs84.geojson'

# TIDE GAGES
NOAA_GAUGE_PATH = RESULTS_DIR / 'tide_gauges/noaa_coops_tide_gauges.csv'

#%% NEARSHORE UNITS
NEARSHORE_UNIT_DIR = RESULTS_DIR / 'nearshore_units/site_unit/'


# Directory for cropped PixC files
CROPPED_PIXC_DIR = '/Users/flue473/big_data/compass_fme/swot/pixc/cropped' # PROJECT_ROOT / 'data/swot/pixc/cropped_synoptic/'

#%% GAMS reconstruction
N_MODES = 8   # Max mode index (is the number of IMFs + number of cyclic predictors)
MAX_LAG = 10  # in samples (6-min intervals)
N_SPLINES = 4  # Number of spline basis functions per IMF mode
LAMBDA_VAL = 5.5  # Smoothing parameter for final GAM fit
INIT_LAGS = np.zeros(N_MODES)  # Initial guess for lags (zero lag for all modes)

#%%  WSE -----------------------------------------------------------------------------------

NEARSHORE_WSE_DIR = RESULTS_DIR / 'swot/wse_nearshore_unit'

NEASHORE_WSE_PATH = RESULTS_DIR / 'swot/wse_nearshore_unit/swot_wse_nearshore.csv'

