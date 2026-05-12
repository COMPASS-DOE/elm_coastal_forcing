from netCDF4 import Dataset

DIR = "/Users/flue473/big_data/from_docs/projects/compass_fme/swot_tidal_forcing/data/elm_forcing/"


# Plum island
fn = DIR + "PIE_tide_forcing.nc"

with Dataset(fn, "r") as nc:
    print(nc)  # prints groups, dimensions, variables, global attributes
    print("\nDimensions:")
    for name, dim in nc.dimensions.items():
        print(f"  {name}: size={len(dim)} (unlimited={dim.isunlimited()})")

    print("\nVariables:")
    for name, var in nc.variables.items():
        print(f"  {name}: dtype={var.dtype}, dims={var.dimensions}, shape={var.shape}")
        # print variable attributes (optional)
        for a in var.ncattrs():
            print(f"    {a}: {getattr(var, a)}")


####


# Plum island
fn = DIR + "PIE_surfdata_threecell.nc"


with Dataset(fn, "r") as nc:
    print(nc)  # prints groups, dimensions, variables, global attributes
    print("\nDimensions:")
    for name, dim in nc.dimensions.items():
        print(f"  {name}: size={len(dim)} (unlimited={dim.isunlimited()})")

    print("\nVariables:")
    for name, var in nc.variables.items():
        print(f"  {name}: dtype={var.dtype}, dims={var.dimensions}, shape={var.shape}")
        # print variable attributes (optional)
        for a in var.ncattrs():
            print(f"    {a}: {getattr(var, a)}")



# Plum island
fn = DIR + "PIE_domain_threecell.nc"


with Dataset(fn, "r") as nc:
    print(nc)  # prints groups, dimensions, variables, global attributes
    print("\nDimensions:")
    for name, dim in nc.dimensions.items():
        print(f"  {name}: size={len(dim)} (unlimited={dim.isunlimited()})")

    print("\nVariables:")
    for name, var in nc.variables.items():
        print(f"  {name}: dtype={var.dtype}, dims={var.dimensions}, shape={var.shape}")
        # print variable attributes (optional)
        for a in var.ncattrs():
            print(f"    {a}: {getattr(var, a)}")
            



# Synoptic
fn = DIR + "COMPASS_hydro_BC_fromL2.nc"
with Dataset(fn, "r") as nc:
    print(nc)  # prints groups, dimensions, variables, global attributes
    print("\nDimensions:")
    for name, dim in nc.dimensions.items():
        print(f"  {name}: size={len(dim)} (unlimited={dim.isunlimited()})")

    print("\nVariables:")
    for name, var in nc.variables.items():
        print(f"  {name}: dtype={var.dtype}, dims={var.dimensions}, shape={var.shape}")
        # print variable attributes (optional)
        for a in var.ncattrs():
            print(f"    {a}: {getattr(var, a)}")
            


fn = DIR + "COMPASS_surfdata_fromgw.nc"

with Dataset(fn, "r") as nc:
    print(nc)  # prints groups, dimensions, variables, global attributes
    print("\nDimensions:")
    for name, dim in nc.dimensions.items():
        print(f"  {name}: size={len(dim)} (unlimited={dim.isunlimited()})")

    print("\nVariables:")
    for name, var in nc.variables.items():
        print(f"  {name}: dtype={var.dtype}, dims={var.dimensions}, shape={var.shape}")
        # print variable attributes (optional)
        for a in var.ncattrs():
            print(f"    {a}: {getattr(var, a)}")
            


fn = DIR + "COMPASS_domain_multicell_fromgw.nc"

with Dataset(fn, "r") as nc:
    print(nc)  # prints groups, dimensions, variables, global attributes
    print("\nDimensions:")
    for name, dim in nc.dimensions.items():
        print(f"  {name}: size={len(dim)} (unlimited={dim.isunlimited()})")

    print("\nVariables:")
    for name, var in nc.variables.items():
        print(f"  {name}: dtype={var.dtype}, dims={var.dimensions}, shape={var.shape}")
        # print variable attributes (optional)
        for a in var.ncattrs():
            print(f"    {a}: {getattr(var, a)}")
            



#%%------------------------------------
# PLOT THE OUTPUT ZWT

fn = DIR + "test_marsh_US-GC3_ICB20TRCNPRDCTCBC.elm.h0.1850-01-01-00000.nc"

with Dataset(fn, "r") as nc:
    print(nc)  # prints groups, dimensions, variables, global attributes
    print("\nDimensions:")
    for name, dim in nc.dimensions.items():
        print(f"  {name}: size={len(dim)} (unlimited={dim.isunlimited()})")

    print("\nVariables:")
    for name, var in nc.variables.items():
        print(f"  {name}: dtype={var.dtype}, dims={var.dimensions}, shape={var.shape}")
        # print variable attributes (optional)
        for a in var.ncattrs():
            print(f"    {a}: {getattr(var, a)}")


import xarray as xr
import matplotlib.pyplot as plt

# fn = "your_elm_hist_file.nc"

ds  = xr.open_dataset(fn, decode_times=False)  # <-- key change
zwt = ds["ZWT"]                                # (time, lndgrid)
t   = ds["time"].values                        # float days since 1850-01-01...

fig, ax = plt.subplots(figsize=(11, 5))
for i in range(zwt.sizes["lndgrid"]):
    ax.plot(t, zwt.isel(lndgrid=i).values, lw=1, alpha=0.8)

ax.set_title("ZWT time series (one line per lndgrid)")
ax.set_xlabel(ds["time"].attrs.get("units", "time"))
ax.set_ylabel(f"ZWT ({zwt.attrs.get('units','')})")
plt.tight_layout()
plt.show()



#%%------------------------------------
# Plot the tide height from the COMPASS_hydro_BC_fromL2.nc file
import xarray as xr
import matplotlib.pyplot as plt

fn = DIR + "COMPASS_hydro_BC_fromL2.nc"
ds  = xr.open_dataset(fn, decode_times=False)

zwt = ds["tide_height"]          # (time, gridcell)
t   = ds["time"].values

# focus on first 365 days (assuming t is in "days since ...")
mask = t < (t[0] + 365)

fig, ax = plt.subplots(figsize=(11, 5))
for i in range(zwt.sizes["gridcell"]):
    ax.plot(t[mask], zwt.isel(time=mask, gridcell=i).values, lw=1, alpha=0.8)

ax.set_title("Tide Height time series (first 365 days; one line per gridcell)")
ax.set_xlabel(ds["time"].attrs.get("units", "time"))
ax.set_ylabel(f"Tide Height ({zwt.attrs.get('units','')})")
plt.tight_layout()
plt.show()