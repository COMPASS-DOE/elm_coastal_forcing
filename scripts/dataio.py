# Data input/output functions


# Import libraries
import pandas as pd
from pathlib import Path
import geopandas as gpd
import glob
import numpy as np
import os
from pathlib import Path
from shapely.geometry import Point
from typing import Tuple, Union
import xarray as xr

from scripts.config import DATA_DIR


#%%   Loads CROPPED PixC file -----------------------------------------------------------------------------------
PathLike = Union[str, Path]

def load_cropped_pixc_file(nc_file: PathLike) -> Tuple[xr.Dataset, pd.Timestamp]:
    """
    Load a SWOT PixC NetCDF file and parse its timestamp from the filename.
    """
    nc_file = Path(nc_file)

    root = nc_file.stem
    parts = root.split("_")
    if len(parts) <= 8:
        raise ValueError(f"Unexpected filename format: {nc_file}")
    
    date_str = parts[8]
    date = pd.to_datetime(date_str, format="%Y%m%dT%H%M%S", errors="raise")

    ds = xr.open_dataset(nc_file, engine="h5netcdf").load()
    return ds, date


#%% Get SWOT water elevation  ---------------------------------------------------------------------------------------
def load_swot_tidal_wse(site_id=None) -> pd.DataFrame:
        
    from scripts.config import NEASHORE_WSE_PATH
    swot_tidal_wse_df = pd.read_csv(NEASHORE_WSE_PATH, low_memory=False)

    # Rename columns
    swot_tidal_wse_df = (swot_tidal_wse_df
        .rename(columns={'wse_mean':'swot_wse_m_navd_mean', 'wse_std':'swot_wse_m_navd_std'})    # Rename columns
        .assign(date = lambda x: pd.to_datetime(x['date'], errors='coerce'))           # Convert datatype
        .assign(date = lambda x: x['date'].dt.round('h'))                              # Round to hour
        .assign(date = lambda x: x['date'].dt.tz_localize('UTC-00:00'))                # If date not localized, localize to GMT
        .assign(datetime_EST = lambda x: x['date'].dt.tz_convert('UTC-04:00'))         # Convert to local time
        .loc[:, ['site_id', 'datetime_EST', 'swot_wse_m_navd_mean', 'swot_wse_m_navd_std']]      # Subset columns
        )

    # Filter to site of interest
    if site_id is not None: 
        swot_tidal_wse_df = swot_tidal_wse_df.query("site_id == @site_id")

    return swot_tidal_wse_df


#%% Load gage data for a given site -----------------------------------------------------------------------------------
def load_noaa_gage_data(site_id=None) -> pd.DataFrame:
    
    from scripts.config import NOAA_GAUGE_PATH

    noaa_wl_df = pd.read_csv(NOAA_GAUGE_PATH, low_memory=False, dtype= {'wse_m': 'float'}) 
    noaa_wl_df = ( noaa_wl_df
        .rename(columns={'wse_m':'gauge_wse_m'})
        .assign(datetime_LST = lambda x: pd.to_datetime(x['datetime_LST'], errors='coerce'))  # Convert datatype
        .assign(datetime_LST = lambda x: x['datetime_LST'].dt.tz_localize('UTC-04:00'))
        .sort_values(by='datetime_LST')
        .assign(dateindices = lambda x: pd.Categorical(x.datetime_LST.values).codes) # Add column of date indices
        .loc[:, ['dateindices', 'datetime_LST', 'site_id', 'gauge_wse_m']]
        )

    # Filter to site of interest
    if site_id is not None: 
        noaa_wl_df = noaa_wl_df.query("site_id == @site_id")

    return noaa_wl_df


#%% Load synoptic site points ---------------------------------
def load_synoptic_site_points(site_id=None) -> gpd.GeoDataFrame:
        
    synoptics_pts = \
        (gpd.read_file('../../data/synoptic_sites/pts/all/synoptic_sites_pts_v2.geojson')
        # .query('region=="Chesapeake Bay"')
        .query('site_cat=="synoptic"')
        .query('zone!="water"')
        .query('zone!="sediment"')
        )
    
        # Filter to site of interest
    if site_id is not None: 
        synoptics_pts = synoptics_pts.query("site_id == @site_id")

    return synoptics_pts


#%% Load synoptic site points ---------------------------------
def load_exchange_site_points(site_id=None) -> gpd.GeoDataFrame:
        
    exchange_pts = \
        (gpd.read_file(DATA_DIR / 'synoptic_sites/pts/exchange/ex_sites_pts.geojson'))
    
    return exchange_pts


#%% Load synoptic site points ---------------------------------
def load_all_site_points(proj=None) -> gpd.GeoDataFrame:
    
    if proj == 'utm':
        all_pts = \
            (gpd.read_file(DATA_DIR / 'synoptic_sites/pts/all/all_sites_utm_v01.geojson'))
        
    if proj == 'wgs84':
        all_pts = \
            (gpd.read_file(DATA_DIR / 'synoptic_sites/pts/all/all_sites_pts_wgs84_v01.geojson'))
        
    return all_pts


