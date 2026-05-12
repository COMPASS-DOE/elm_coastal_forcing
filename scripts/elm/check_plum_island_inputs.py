

import xarray as xr



# Read data
surf_ds = xr.open_dataset("~/elm/elmdata/plum_island/PIE_surfdata_threecell.nc", decode_timedelta=True)
domain_ds = xr.open_dataset("~/elm/elmdata/plum_island/PIE_domain_threecell.nc", decode_timedelta=True)
tide_forcing_ds = xr.open_dataset("~/elm/elmdata/plum_island/PIE_tide_forcing.nc", decode_timedelta=True)



ds = tide_forcing_ds



print(ds.dims)
print(list(ds.data_vars))
print(list(ds.coords)) 
# print(list(ds.dimensions))    


# # GET VARIABLE
var = ds['tide_height'] 

print(var.sizes)    # Sizes along each dimension
print(var.coords)   # Coordinates associated with those dimensions (if present)
print(var)            # summary: dims, shape, dtype, attrs
print(var.attrs)  