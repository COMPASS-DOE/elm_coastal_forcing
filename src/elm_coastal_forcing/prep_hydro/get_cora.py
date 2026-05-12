


import json
import fsspec
import xarray as xr
import pandas as pd
import numpy as np


from scripts.config import DATA_DIR, RESULTS_DIR


def get_cora_time_series(ref_json, lon, lat, var, start, end, outfile):

    with open(REF_JSON, "r") as f:
        refs = json.load(f)

    mapper = fsspec.get_mapper(
        "reference://",
        fo=refs,
        remote_protocol="s3",
        remote_options={"anon": True},
    )

    ds = xr.open_dataset(mapper, engine="zarr", consolidated=False, chunks={})

    # ---- nearest point using 1D lon/lat without .sel() indexes ----
    time_name = "time" if "time" in ds.coords else "Time"
    ds_t = ds.sel({time_name: slice(START, END)})

    lon = ds_t["lon"]
    lat = ds_t["lat"]

    # compute nearest indices (this triggers only lon/lat reads, not full dataset)
    dlon = ((lon - LON0 + 180) % 360) - 180
    i = int(np.nanargmin(np.abs(dlon).values))
    j = int(np.nanargmin(np.abs((lat - LAT0)).values))

    xdim = lon.dims[0]
    ydim = lat.dims[0]

    p = ds_t.isel({xdim: i, ydim: j})

    ts = p[VAR].to_series().rename("wse_m").loc[START:END]
    out = ts.reset_index()
    out.columns = ["time", "wse_m"]
    out["lon_req"] = LON0
    out["lat_req"] = LAT0
    out["lon_grid"] = float(lon.isel({xdim: i}).values)
    out["lat_grid"] = float(lat.isel({ydim: j}).values)

    # Save to files
    out.to_csv(outfile, index=False)


#%%------------------------------------------------------------

# Define static inputs
REF_JSON = DATA_DIR/"cora/500m_grid_zeta_1979-2022.zarr"   # it's actually a kerchunk reference JSON
START, END = "2018-01-01", "2025-12-31"
VAR = "zeta"

synoptic_pts = pd.read_csv(DATA_DIR/'synoptic_sites/pts/synoptic/synoptic_elev_zone_v5.csv')
synoptic_pts = synoptic_pts.query("zone_id == 'W'").copy()


for idx, row in synoptic_pts.iterrows():

    print(row.site_id)

    # Get coordinates
    LON, LAT = row.longitude, row.latitude

    # Extract zeta a the nearest grid point to the site coordinates and save to file
    get_cora_time_series(REF_JSON, LON, LAT, VAR, START, END, 
                         outfile = RESULTS_DIR/f"cora_zeta_{row.site_id}_{START}_{END}.csv")