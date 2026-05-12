
#%%
from datetime import datetime
import netCDF4 as nc
import h5netcdf
import xarray as xr
import pandas as pd
import geopandas as gpd
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib import colors

#%% Function to create map plot ---------------------------------
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.ticker as mticker

import matplotlib as mpl
mpl.rcParams["font.family"] = "Arial"   # set before creating the plot

def plot_regions_two_pointsets_and_coastlines(
    gauges,
    coastlines_by_region,
    synoptic_pts=None,
    site_col="site_id",
    site_name_col="site_name",
    region_col="region_name",
    lat_col="latitude",
    lon_col="longitude",
    gauge_id_col="gauge_id",
    type_col="type",                 # "ref"/"valid" -> color
    source_col="data_source",        # -> marker
    target_crs="EPSG:4326",
    figsize_per_panel=(4, 4),
    coast_kwargs=None,
    gauge_point_size=80,
    gauge_alpha=1.0,
    syn_point_size=90,
    syn_alpha=1.0,
    syn_color="k",
    syn_marker="x",
    type_colors=None,
    source_markers=None,
    region_order=None,
    pad_frac=0.06,                   # <-- proportional padding for x/y
    top_pad_extra_frac=0.12,          # <-- extra proportional padding on TOP
    legend=True
):
    coast_kwargs = coast_kwargs or dict(color="0.75", linewidth=1.0, alpha=0.9, zorder=1)
    type_colors = type_colors or {"ref": "tab:blue", "valid": "tab:orange"}
    source_markers = source_markers or {}

    # ---- to GeoDataFrames ----
    gdf = gauges.dropna(subset=[site_col, lat_col, lon_col]).copy()
    g_gauges = gpd.GeoDataFrame(
        gdf, geometry=gpd.points_from_xy(gdf[lon_col], gdf[lat_col]), crs=target_crs
    )

    g_syn = None
    if synoptic_pts is not None:
        odf = synoptic_pts.dropna(subset=[site_col, lat_col, lon_col]).copy()
        g_syn = gpd.GeoDataFrame(
            odf, geometry=gpd.points_from_xy(odf[lon_col], odf[lat_col]), crs=target_crs
        )

    # ---- site metadata ----
    site_meta = (
        g_gauges[[site_col, site_name_col, region_col]]
        .drop_duplicates(subset=[site_col])
        .copy()
        .sort_values([region_col, site_name_col, site_col], kind="stable")
    )

    regions = list(pd.unique(site_meta[region_col]))
    if region_order is not None:
        regions = [r for r in region_order if r in regions]
    if len(regions) != 2:
        raise ValueError(f"Expected exactly 2 regions for 2 columns, found {len(regions)}: {regions}")

    # ---- coastlines per region ----
    def _as_gdf(x):
        gg = x.copy() if isinstance(x, gpd.GeoDataFrame) else gpd.read_file(x)
        if gg.crs is None:
            gg = gg.set_crs(target_crs)
        return gg.to_crs(target_crs)

    coast_gdf = {r: _as_gdf(coastlines_by_region[r]) for r in regions}

    # ---- layout ----
    sites_by_region = {r: site_meta.loc[site_meta[region_col] == r, site_col].tolist() for r in regions}
    nrows = max(len(v) for v in sites_by_region.values())

    fig, axes = plt.subplots(
        nrows, 2,
        figsize=(figsize_per_panel[0] * 2, figsize_per_panel[1] * nrows),
        sharex=False, sharey=False,
        constrained_layout=True
    )
    if nrows == 1:
        axes = axes.reshape(1, 2)

    axes[0, 0].set_title(str(regions[0]))
    axes[0, 1].set_title(str(regions[1]))

    # ---- source -> marker ----
    default_marker_cycle = ["o", "^", "s", "D", "P", "X", "v", "<", ">", "*", "h"]
    seen_sources = []

    def marker_for_source(src):
        if src in source_markers:
            return source_markers[src]
        if src not in seen_sources:
            seen_sources.append(src)
        return default_marker_cycle[seen_sources.index(src) % len(default_marker_cycle)]

    # ---- plot ----
    for c, region in enumerate(regions):
        cg = coast_gdf[region]

        for r_i in range(nrows):
            ax = axes[r_i, c]
            ax.set_box_aspect(1)
            ax.set_aspect("equal", adjustable="datalim")
            ax.grid(True, alpha=0.3)

            if r_i >= len(sites_by_region[region]):
                ax.set_visible(False)
                continue

            sid = sites_by_region[region][r_i]
            site_name = site_meta.loc[site_meta[site_col] == sid, site_name_col].iloc[0]

            # coastline behind
            if len(cg):
                cg.plot(ax=ax, **coast_kwargs)

            sub_g = g_gauges[g_gauges[site_col] == sid]
            sub_s = g_syn[g_syn[site_col] == sid] if g_syn is not None else None

            if len(sub_g):
                minx, miny, maxx, maxy = sub_g.total_bounds
                spanx = maxx - minx
                spany = maxy - miny

                # proportional padding; tiny fallback only if span is 0
                eps = 1e-6
                dx = max(spanx * pad_frac, eps)
                dy = max(spany * pad_frac, eps)

                ax.set_xlim(minx - dx, maxx + dx)
                ax.set_ylim(miny - dy, maxy + dy * (1 + top_pad_extra_frac))

            # synoptic points
            if sub_s is not None and len(sub_s):
                ax.scatter(sub_s.geometry.x, sub_s.geometry.y,
                           s=syn_point_size, c=syn_color, marker=syn_marker,
                           alpha=syn_alpha, zorder=2.5)

            # gauge points
            if len(sub_g):
                for (t, src), gg in sub_g.groupby([type_col, source_col], dropna=False):
                    ax.scatter(gg.geometry.x, gg.geometry.y,
                               s=gauge_point_size,
                               c=type_colors.get(t, "0.4"),
                               marker=marker_for_source(src),
                               alpha=gauge_alpha,
                               edgecolors="none",
                               zorder=3)

                if gauge_id_col in sub_g.columns:
                    for _, rr in sub_g.iterrows():
                        ax.annotate(str(rr[gauge_id_col]),
                                    (rr.geometry.x, rr.geometry.y),
                                    xytext=(3, 3), textcoords="offset points",
                                    fontsize=8, zorder=4)

            # site name label with white background
            ax.text(0.02, 0.98, str(site_name), transform=ax.transAxes,
                    ha="left", va="top",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2.5),
                    zorder=5)

            # fewer ticks + nicer formatting
            ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=3))
            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=3))
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

            # keep numeric tick labels everywhere; axis TITLES only on outer edges
            ax.set_ylabel("Latitude" if c == 0 else "")
            ax.set_xlabel("Longitude" if r_i == nrows - 1 else "")


    # legends
    if legend:
        type_handles = [
            Line2D([0], [0], marker="o", linestyle="None",
                   markerfacecolor=col, markeredgecolor="none",
                   markersize=9, label=str(t))
            for t, col in type_colors.items()
        ]

        sources_present = [s for s in pd.unique(g_gauges[source_col]) if pd.notna(s)] if source_col in g_gauges.columns else []
        source_handles = [
            Line2D([0], [0], marker=marker_for_source(s), linestyle="None",
                   markerfacecolor="0.2", markeredgecolor="none",
                   markersize=9, label=str(s))
            for s in sources_present
        ]

        leg_type = fig.legend(
            handles=type_handles,
            title="Gauge type",
            loc="lower right", bbox_to_anchor=(0.995, 0.02),
            frameon=False,  # <-- no border
            borderaxespad=0.2
        )
        fig.add_artist(leg_type)

        fig.legend(
            handles=source_handles,
            title="Data source",
            loc="lower right", bbox_to_anchor=(0.83, 0.02),
            frameon=False,  # <-- no border
            borderaxespad=0.2
        )

    return fig, axes


#%% Load and combine gauge data ---------------------------------
import glob
import os
import pandas as pd
import pytz
from pathlib import Path
est = pytz.timezone('America/New_York')

from scripts.config import DATA_DIR, FIG_DIR, RESULTS_DIR, SITE_CODE_LIST
# from scripts.dataio import load_noaa_gage_data, load_nerrs_gage_data

# Get all the reference and training stations together
gauges = pd.read_csv(DATA_DIR/'tide_gauges/all_gauges_list/synoptic_wse_train_val_stations.csv')
gauges = gauges.query("run == 1").copy()


#%% Get synoptic points
synoptic_pts = pd.read_csv(DATA_DIR/'synoptic_sites/pts/synoptic/synoptic_elev_zone_v5.csv')
synoptic_pts = synoptic_pts.query("zone_id == 'TR'").copy()

#  Get coastlines
# dir_path = Path(f'{RESULTS_DIR}/nearshore_units/CUSP_site_estuary_poly_mansel')
dir_path = Path(f'{DATA_DIR}/coastlines/usa')
shps = sorted(dir_path.rglob("*.shp"))   # use .glob("*.shp") for non-recursive
shp = [str(p) for p in shps]   # convert to string

coastlines_by_region = {
    'Chesapeake Bay': shp[0],
    'Lake Erie': shp[1]}

source_markers = {
    "NOAA": "s",         
    "USGS": "^",         
    "NERRS": "*",        
    "COMPASS-FME": "D",  
    "VECOS": "P",        
    "SONDE": "X",        
    "NOAA-Harmonics": "s",
}

fig, axes = plot_regions_two_pointsets_and_coastlines(
    gauges=gauges.query("run != 2"),
    synoptic_pts=synoptic_pts,
    coastlines_by_region=coastlines_by_region,
    source_markers=source_markers,   # gauges shapes
    syn_color="k",                   # synoptic points: black
    syn_marker="o",                  # synoptic points: circles
    pad_frac=0.08,
    top_pad_extra_frac=1.15
)

#%% Save to file
out_png = f"{FIG_DIR}/maps/synoptic_gauges_val_ref.png"

mm_to_in = 1 / 25.4
fig.set_size_inches(190*mm_to_in, 320*mm_to_in)   # width_mm, height_mm
fig.savefig(out_png, dpi=300, bbox_inches="tight")