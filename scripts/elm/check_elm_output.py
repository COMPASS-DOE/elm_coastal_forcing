

# Load modules; doing this inside the venv resets the python to the original module, 
# to which libraries can't be installed.
ml python/3.10
ml py-pip
ml netcdf-c
ml mpi/2021.13


# Create local virtual env; specifying the python
# /usr/bin/python3 -m venv ~/venvs/elm-env-local

# Enter local virtual environment with installed packages
source ~/venvs/elm-env-local/bin/activate

python3
wait

import sys, os
import xarray as xr
import warnings
# from netCDF4 import Dataset
# from textwrap import indent

# Suppress errors about multiple fill values going to NaN
warnings.filterwarnings("ignore", category=xr.SerializationWarning,)

# elm.h0.*.nc → regular ELM history files (typically analyzed)
# elm.rh0.*.nc → restart-time history files from ELM
# elm.r.*.nc → ELM restart files (model state for continuing runs)
# cpl.r.*.nc → coupler restart files (CPL/driver state for continuing runs)

### what is h1?

NC_FILEPATH = "~/elm/elmoutput/test_marsh_US-PLM1_ICB20TRCNPRDCTCBC/run/test_marsh_US-PLM1_ICB20TRCNPRDCTCBC.elm.h0.1850-03-02-72000.nc"
NC_FILEPATH = os.path.expanduser(NC_FILEPATH)


ds = xr.open_dataset(NC_FILEPATH, decode_timedelta=True)



# with xr.open_dataset(NC_FILEPATH, decode_timedelta=True) as ds:
	print(list(ds.variables))
	# print(list(ds.data_vars))
	# print(list(ds.coords)) 
	# print(list(ds.dimensions))    
	# Access the variable
	var = ds["H2OSOI_LIQ"]
	# 1. Dimension names
	print(var.dims)       # e.g. ('column', 'levtot')
	# 2. Sizes along each dimension
	print(var.sizes)      # e.g. {'column': 48, 'levtot': 20}
	# 3. Coordinates associated with those dimensions (if present)
	print(var.coords)     # dictionary-like of coord arrays
	# 4. All info together
	print(var)            # summary: dims, shape, dtype, attrs
	print(var.attrs)      # attributes (long_name, units, etc.)
	# print(ds["watsat"])


# print values of
ds["gridcell"].values




# ZWT: water table depth (vegetated landunits only) (m)
# ZWT_PERCH: perched water table depth (vegetated landunits only) (m)
# TWS: total water storage (mm) 
# TWS_MONTH_BEGIN: total water storage at the beginning of a month (mm)
# TWS_MONTH_END: total water storage at the end of a month (mm)

# SOILLIQ: soil liquid water (vegetated landunits only) (kg/m2)
# SOILLIQ_ICE: soil liquid water (ice landunits only) (kg/m2)
# SOILPSI: soil water potential in each soil layer (MPa)
# SOILWATER_10CM: soil liquid water + ice in top 10cm of soil (veg landunit...) (kg)




# #!/usr/bin/env python3
# """
# Print basic structure of a NetCDF file:
# - Dimensions
# - Variables (with dims and types)
# - Global attributes
# """

# def print_netcdf_structure(nc_path):
#     with Dataset(nc_path, 'r') as ds:
#         print(f"File: {nc_path}")
#         print("-" * 60)
#         # Dimensions
#         print("Dimensions:")
#         for name, dim in ds.dimensions.items():
#             size = len(dim) if not dim.isunlimited() else "UNLIMITED"
#             print(f"  {name}: {size}")
#         print()
#         # Variables
#         print("Variables:")
#         for name, var in ds.variables.items():
#             dims = ", ".join(var.dimensions)
#             print(f"  {name}: {var.dtype} ({dims})")
#             # Uncomment the next lines to show variable attributes as well
#             # for attr_name in var.ncattrs():
#             #     attr_val = getattr(var, attr_name)
#             #     print(f"    @{attr_name} = {attr_val}")
#         print()

#         # Global attributes
#         print("Global attributes:")
#         for attr_name in ds.ncattrs():
#             attr_val = getattr(ds, attr_name)
#             print(f"  @{attr_name} = {attr_val}")


# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python print_nc_structure.py <file.nc>")
#         sys.exit(1)

#     nc_file = sys.argv[1]
#     print_netcdf_structure(nc_file)