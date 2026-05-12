
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt


ffn = "/Users/flue473/big_data/from_docs/projects/compass_fme/swot_tidal_forcing/output/results/elm_outputs/test_marsh3_US-GC3_ICB1850CNRDCTCBC_ad_spinup.elm.h0.0001-01-01-00000.nc"
ds = xr.open_dataset(fn)

print(list(ds.variables))


print("dims:", dict(ds.sizes))



import xarray as xr
import matplotlib.pyplot as plt
import glob

# point this to your ELM history files (the ones that contain lon/lat and lndgrid)
# files = sorted(glob.glob("/path/to/elm/hist/*.h0.*.nc"))  # adjust pattern

# ds = xr.open_mfdataset(files, combine="by_coords")  # stacks along time

var = "SUCSAT"   # or any variable that has dims including ('time','lndgrid') or can be reduced to lndgrid

da = ds[var]

# If da has extra dims (e.g., levgrnd), reduce them first; example:
# da = da.isel(levgrnd=0)  # top layer, or: da.mean("levgrnd")

# Now da should be (time, lndgrid)
plt.figure(figsize=(10,5))
for i in range(ds.sizes["lndgrid"]):
    plt.plot(ds["time"].values, da.isel(lndgrid=i).values, lw=0.7, alpha=0.5)

plt.xlabel("time")
plt.ylabel(f"{var} ({da.attrs.get('units','')})")
plt.title(f"{var}: time series for each lndgrid")
plt.tight_layout()
plt.show()


#____________________________________________-

# import numpy as np
# import xarray as xr
# import matplotlib.pyplot as plt

# fn = "/Users/flue473/big_data/from_docs/projects/compass_fme/BenSulman_ELMruns/COMPASS_synoptic_sims/scripts/COMPASS_hydro_BC_fromL2.nc"
# ds = xr.open_dataset(fn)

# var = "tide_height"
# time_dim = "time"
# cell_dim = "gridcell"
# gc = 15
# t0 = 4203
# halfwin = 200

# da = ds[var].isel({cell_dim: gc})

# # Convert time to a safe x-axis:
# t = ds[time_dim]
# if np.issubdtype(t.dtype, np.timedelta64):
#     x = t.astype("timedelta64[s]").astype(float) / 3600.0   # hours since start
#     xlabel = "hours since start"
# else:
#     x = t.values
#     xlabel = time_dim

# y = da.values

# i1 = max(0, t0 - halfwin)
# i2 = min(len(y) - 1, t0 + halfwin)

# plt.figure(figsize=(10,5))
# plt.plot(x[i1:i2+1], y[i1:i2+1], lw=1.2)
# plt.scatter(x[t0].item(), float(y[t0]), c="r", s=50, zorder=3, label=f"timestep {t0}")
# plt.title(f"{var} at {cell_dim}={gc} (zoom around timestep {t0})")
# plt.xlabel(xlabel)
# plt.ylabel(var)
# plt.legend()
# plt.tight_layout()
# plt.show()
