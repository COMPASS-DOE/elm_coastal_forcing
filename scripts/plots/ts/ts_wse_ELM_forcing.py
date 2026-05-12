import numpy as np
import xarray as xr
import matplotlib.pyplot as plt


#______________________________________________________________#
## Time series plot of all gridpoints and timeline
fn = "/Users/flue473/big_data/from_docs/projects/compass_fme/BenSulman_ELMruns/COMPASS_synoptic_sims/scripts/COMPASS_hydro_BC_fromL2.nc"

ds = xr.open_dataset(fn)
print(ds.variables)
print("dims:", dict(ds.sizes))

# pick a variable that has (time, gridcells)
time_dim = "time"
cell_dim = "gridcell"
cands = [v for v in ds.data_vars
         if time_dim in ds[v].dims and cell_dim in ds[v].dims]
print("vars with (time, gridcell):", cands)

var = "tide_height"  # <-- change to the variable you actually want
da = ds[var]

# Plot one line per gridcell (can be a lot of lines)
plt.figure(figsize=(10,5))
for i in range(da.sizes[cell_dim]):
    plt.plot(ds[time_dim].values, da.isel({cell_dim: i}).values, lw=0.7, alpha=0.6)

plt.title(f"{var} timeseries for each {cell_dim}")
plt.xlabel(time_dim)
plt.ylabel(var)
plt.tight_layout()
plt.show()


#______________________________________________________________#
## Time series plot of all gridpoints and timeline

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

fn = "/Users/flue473/big_data/from_docs/projects/compass_fme/BenSulman_ELMruns/COMPASS_synoptic_sims/scripts/COMPASS_hydro_BC_fromL2.nc"
ds = xr.open_dataset(fn)

var = "tide_height"
time_dim = "time"
cell_dim = "gridcell"
gc = [13,14,15]
t0 = 4203
halfwin = 100  # Half of window

da = ds[var].isel({cell_dim: gc})

# Convert time to a safe x-axis:
t = ds[time_dim]
if np.issubdtype(t.dtype, np.timedelta64):
    x = t.astype("timedelta64[s]").astype(float) / 3600.0   # hours since start
    xlabel = "hours since start"
else:
    x = t.values
    xlabel = time_dim

y = da.values

i1 = max(0, t0 - halfwin)
i2 = min(len(y) - 1, t0 + halfwin)

plt.figure(figsize=(10,5))
plt.plot(x[i1:i2+1], y[i1:i2+1], lw=1.2)
plt.scatter(x[t0].item(), float(y[t0]), c="r", s=50, zorder=3, label=f"timestep {t0}")
plt.title(f"{var} at {cell_dim}={gc} (zoom around timestep {t0})")
plt.xlabel(xlabel)
plt.ylabel(var)
plt.legend()
plt.tight_layout()
plt.show()





#______________________________________________________________#
# Explore surfdata

fn = '/Users/flue473/big_data/from_docs/projects/compass_fme/BenSulman_ELMruns/COMPASS_synoptic_sims/scripts/COMPASS_surfdata_fromgw.nc'

ds = xr.open_dataset(fn)


print(list(ds.variables))


for i, x in enumerate(list(ds.variables)):
    print(i, x)


import numpy as np

ds["fdrain"].values = np.full((21,), 5.0)   # or dtype=float/int as needed
ds.to_netcdf("/Users/flue473/big_data/from_docs/projects/compass_fme/BenSulman_ELMruns/COMPASS_synoptic_sims/scripts/COMPASS_surfdata_fromgw_fdrain.nc")