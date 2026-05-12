import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from netCDF4 import Dataset

from scripts.config import FIG_DIR, RESULTS_DIR


#%% ---------------------------------------------------------------
# Read input

f = "/Users/flue473/big_data/compass_fme/mpas_mesh/delaware_60_30_5_2_v2/ocn_cull_mesh.nc"
ds = Dataset(f)

print("dims:", {k: len(v) for k, v in ds.dimensions.items()})
print("vars:", list(ds.variables.keys())[:30])   # first 30 variable names
print("attrs:", ds.ncattrs())


#%%---------------------------------------------------------------  
# Plot zoomed in on Delaware region

lonmin, lonmax = 282.58, 284.42
latmin, latmax =  36.8, 39.7

ds = Dataset(f)
lonC = np.degrees(ds["lonCell"][:])
latC = np.degrees(ds["latCell"][:])

mask = (lonC >= lonmin) & (lonC <= lonmax) & (latC >= latmin) & (latC <= latmax)
cells = np.where(mask)[0]

voc = ds["verticesOnCell"][:]
nE  = ds["nEdgesOnCell"][:]
lonV = np.degrees(ds["lonVertex"][:])
latV = np.degrees(ds["latVertex"][:])

segments = []
for c in cells:
    k = int(nE[c])
    vids = voc[c, :k] - 1
    vids = vids[vids >= 0]
    if len(vids) < 3:
        continue
    x = lonV[vids]; y = latV[vids]
    pts = np.column_stack([x, y])
    segments.append(np.vstack([pts, pts[0]]))

lc = LineCollection(segments, colors="k", linewidths=0.2)

fig, ax = plt.subplots(figsize=(8,6))
ax.add_collection(lc)
ax.set_xlim(lonmin, lonmax)
ax.set_ylim(latmin, latmax)
ax.set_aspect("equal", adjustable="box")
plt.show()
ds.close()

# Save to file
mm_to_in = 1 / 25.4
fig.set_size_inches(90*mm_to_in, 160*mm_to_in)   # width_mm, height_mm

out_png = f"{FIG_DIR}/maps/mpas_mesh_chesapeake.png"
fig.savefig(out_png, dpi=300, bbox_inches="tight")


#%%---------------------------------------------------------------
# Save subseted mesh polygon to shapefile

import numpy as np
from netCDF4 import Dataset
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.validation import make_valid

f = "/Users/flue473/big_data/compass_fme/mpas_mesh/delaware_60_30_5_2_v2/ocn_cull_mesh.nc"

# bbox in degrees (0-360 lon like your plot)
lonmin, lonmax = 282.58, 284.42
latmin, latmax =  36.8,  39.7


with Dataset(f) as ds:
    lonC = np.degrees(ds["lonCell"][:])
    latC = np.degrees(ds["latCell"][:])

    mask  = (lonC >= lonmin) & (lonC <= lonmax) & (latC >= latmin) & (latC <= latmax)
    cells = np.where(mask)[0]

    voc = ds["verticesOnCell"][:]     # (nCells, maxEdges) 1-based
    nE  = ds["nEdgesOnCell"][:]       # number of vertices used in each row
    lonV = np.degrees(ds["lonVertex"][:])
    latV = np.degrees(ds["latVertex"][:])

    geoms = []
    cell_ids = []

    for c in cells:
        k = int(nE[c])
        vids = voc[c, :k] - 1         # -> 0-based
        vids = vids[vids >= 0]
        if len(vids) < 3:
            continue

        ring = [(float(lonV[v]), float(latV[v])) for v in vids]

        # close ring
        if ring[0] != ring[-1]:
            ring.append(ring[0])

        poly = Polygon(ring)

        # optionally repair any rare invalid polygons
        if not poly.is_valid:
            poly = make_valid(poly)
            # make_valid can return GeometryCollection; keep polygonal part if needed
            if poly.geom_type != "Polygon":
                polys = [g for g in getattr(poly, "geoms", []) if g.geom_type == "Polygon"]
                if not polys:
                    continue
                poly = max(polys, key=lambda p: p.area)

        geoms.append(poly)
        cell_ids.append(int(c))

# Optional: convert lon 0–360 to -180–180 for GIS friendliness
def lon360_to_180(x):
    return x - 360 if x > 180 else x

geoms_180 = []
for p in geoms:
    coords = [(lon360_to_180(x), y) for (x, y) in p.exterior.coords]
    geoms_180.append(Polygon(coords))

gdf = gpd.GeoDataFrame(
    {"cell_id": cell_ids},
    geometry=geoms_180,   # or use geoms if you want to keep 0–360
    crs="EPSG:4326"
)


# Save to file
out_shp = RESULTS_DIR / 'mpas_mesh/delaware_mpas_cells.shp'
gdf.to_file(out_shp)




#%%---------------------------------------------------------------

# DELAWARE base mesh is GLOBAL!!!
# This plot 


ds = Dataset(f)

voc = ds["verticesOnCell"][:]          # (nCells, maxEdges), 1-based
nE  = ds["nEdgesOnCell"][:]
lonV = np.degrees(ds["lonVertex"][:])
latV = np.degrees(ds["latVertex"][:])

segments = []
for c in range(voc.shape[0]):
    k = int(nE[c])
    vids = voc[c, :k] - 1
    vids = vids[vids >= 0]
    if len(vids) < 3:
        continue
    x = lonV[vids]; y = latV[vids]
    pts = np.column_stack([x, y])
    segments.append(np.vstack([pts, pts[0]]))   # close ring

lc = LineCollection(segments, colors="k", linewidths=0.1)

fig, ax = plt.subplots(figsize=(10,6))
ax.add_collection(lc)
ax.autoscale()
ax.set_aspect("equal", adjustable="box")
plt.show()

ds.close()
