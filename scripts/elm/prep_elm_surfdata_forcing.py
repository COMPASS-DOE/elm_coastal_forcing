#!/usr/bin/env python3
import xarray as xr

infile = "/Users/flue473/big_data/from_docs/projects/compass_fme/BenSulman_ELMruns/COMPASS_synoptic_sims/scripts/COMPASS_surfdata_fromgw.nc"
outfile = infile.replace(".nc", "_elev_pointgrid15.nc")

# Open (no decoding needed, but fine either way)
ds = xr.open_dataset(infile)

# Find cells where 3gridcell == 15
mask = (ds["gridcell"] == 15)

# Set elev to 4.59 for those cells
ds["ht_above_stream"] = ds["ht_above_stream"].where(~mask, other=4.59)


ds["ht_above_stream"].values
ds["dist_from_stream"].values
ds["fdrain"].values



# Write new file (keeps original intact)
# ds.to_netcdf(outfile)
# print(f"Wrote: {outfile}")


