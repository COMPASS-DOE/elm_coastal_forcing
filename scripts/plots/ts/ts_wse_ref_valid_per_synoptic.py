
import glob
import os
import site
import pandas as pd
from pathlib import Path
import pytz
est = pytz.timezone('America/New_York')

from scripts.config import DATA_DIR, FIG_DIR, RESULTS_DIR, SITE_CODE_LIST


# for site_id in SITE_CODE_LIST:
#     COMBINED_GAUGE_DIR = RESULTS_DIR/'tide_gauges/combined/'
#     gauge_wse_combined = pd.read_csv(COMBINED_GAUGE_DIR / f"{site_id}_combined_gauge_swe_v01.csv")
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

COMBINED_GAUGE_DIR = RESULTS_DIR / "tide_gauges/combined/"

# --- station metadata (must include station_id, station_name, type, data_source, site_name, region_name) ---
meta_fp = Path(DATA_DIR) / "tide_gauges/all_gauges_list/synoptic_wse_train_val_stations.csv"
stations_meta = pd.read_csv(meta_fp)

stations_meta["station_id"] = stations_meta["station_id"].astype(str)
need_cols = ["station_id", "station_name", "site_id", "type", "data_source", "site_name", "region_name"]
stations_meta = stations_meta[[c for c in need_cols if c in stations_meta.columns]].drop_duplicates(["station_id", "site_id"])

region_name_map = stations_meta.set_index("station_id")["region_name"].to_dict() if "region_name" in stations_meta else {}

import numpy as np
import pandas as pd
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from scripts.config import DATA_DIR, FIG_DIR, RESULTS_DIR, SITE_CODE_LIST

est = pytz.timezone("America/New_York")
COMBINED_GAUGE_DIR = RESULTS_DIR / "tide_gauges/combined/"

# -------------------------
# Helpers: keep leading zeros
# -------------------------
def normalize_station_id(x, zfill: int = 8) -> str:
    """
    Force station_id to a string and restore leading zeros if it was
    read/converted as a number at any point (e.g., 1646500 or 1646500.0).
    Only zero-fills if the result is all digits.
    """
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    # undo common float formatting from CSV/inference
    if s.endswith(".0"):
        s = s[:-2]
    # handle scientific notation if it ever appears
    if "e" in s.lower():
        try:
            s = format(int(float(s)), "d")
        except Exception:
            pass
    # zfill only for purely numeric ids
    if s.isdigit():
        s = s.zfill(zfill)
    return s

def normalize_station_id_series(ser: pd.Series, zfill: int = 8) -> pd.Series:
    return ser.apply(lambda v: normalize_station_id(v, zfill=zfill)).astype("string")


# --- station metadata: read IDs as strings ---
meta_fp = Path(DATA_DIR) / "tide_gauges/all_gauges_list/synoptic_wse_train_val_stations.csv"
stations_meta = pd.read_csv(meta_fp, dtype={"station_id": "string", "site_id": "string"})
stations_meta["station_id"] = normalize_station_id_series(stations_meta["station_id"], zfill=8)
if "site_id" in stations_meta.columns:
    stations_meta["site_id"] = stations_meta["site_id"].astype("string").str.strip()

need_cols = ["station_id", "station_name", "site_id", "type", "data_source", "site_name", "region_name"]
stations_meta = stations_meta[[c for c in need_cols if c in stations_meta.columns]].drop_duplicates(
    ["station_id", "site_id"]
)

region_name_map = (
    stations_meta.set_index("station_id")["region_name"].to_dict()
    if "region_name" in stations_meta
    else {}
)

def region_label_for_sites(sites, fallback):
    for sid in sites:
        rn = region_name_map.get(str(sid))
        if pd.notna(rn):
            return rn
    return fallback

def plot_site_panel(ax, site_id, df, stations_meta, lw=0.45):
    df = df.copy()

    # IMPORTANT: normalize station_id in the gauge time series too
    if "station_id" not in df.columns:
        raise ValueError("Gauge dataframe is missing required column 'station_id'.")
    df["station_id"] = normalize_station_id_series(df["station_id"], zfill=8)

    if "site_id" in df.columns:
        df["site_id"] = df["site_id"].astype("string").str.strip()
    else:
        df["site_id"] = str(site_id)

    # time handling / filtering
    df["datetime_LST"] = pd.to_datetime(df["datetime_LST"])
    df = df[df["datetime_LST"] >= "2018-01-01"].sort_values("datetime_LST")

    if "depth_m" in df.columns:
        df["depth_m"] = pd.to_numeric(df["depth_m"], errors="coerce")
        df.loc[df["depth_m"] < 0, "depth_m"] = np.nan

    # merge metadata using composite key
    meta = stations_meta.copy()
    if "site_id" not in meta.columns:
        raise ValueError("stations_meta must include 'site_id' to merge on ['station_id', 'site_id'].")

    meta["station_id"] = normalize_station_id_series(meta["station_id"], zfill=8)
    meta["site_id"] = meta["site_id"].astype("string").str.strip()
    meta = meta.drop_duplicates(["station_id", "site_id"])

    df = df.merge(meta, on=["station_id", "site_id"], how="left")

    # fill defaults
    df["type"] = df["type"].fillna("unknown") if "type" in df.columns else "unknown"
    df["data_source"] = df["data_source"].fillna("unknown") if "data_source" in df.columns else "unknown"

    if "site_name" in df.columns:
        df["site_name"] = df["site_name"].fillna(str(site_id))
    else:
        df["site_name"] = str(site_id)

    # labels use station_name (fallback to station_id)
    if "station_name" in df.columns:
        df["station_name"] = df["station_name"].fillna(df["station_id"])
    else:
        df["station_name"] = df["station_id"]

    # plotting
    ax_r = ax.twinx()
    wse_cmap = plt.get_cmap("Blues")
    depth_cmap = plt.get_cmap("Greens")

    station_ids = list(dict.fromkeys(df["station_id"].dropna().tolist()))
    idx_map = {sid: i for i, sid in enumerate(station_ids)}
    n = max(len(station_ids), 1)

    def shade(cmap, i):
        t = 0.65 if n == 1 else (0.35 + 0.55 * (i / (n - 1)))
        return cmap(t)

    for valid_flag in [False, True]:
        for station_id, g in df.groupby("station_id"):
            g = g.sort_values("datetime_LST")
            g_type = g["type"].iloc[0] if "type" in g.columns else "unknown"
            is_valid = (g_type == "valid")
            if is_valid != valid_flag:
                continue

            if is_valid:
                wse_color = depth_color = "tab:orange"
                z = 5
            else:
                i = idx_map[station_id]
                wse_color = shade(wse_cmap, i)
                depth_color = shade(depth_cmap, i)
                z = 2

            src = g["data_source"].iloc[0] if "data_source" in g.columns else "unknown"
            stn_name = g["station_name"].iloc[0] if "station_name" in g.columns else station_id
            station_label_base = f"{src}_{stn_name}_{g_type}"

            # pick line color for WSE: red if this is the NOAA CORA station
            wse_color_plot = "red" if str(station_id) == "NOAA CORA" else wse_color

            if "wse_m" in g.columns and g["wse_m"].notna().any():
                ax.plot(
                    g["datetime_LST"], g["wse_m"],
                    lw=lw, color=wse_color_plot, zorder=z,
                    label=station_label_base + "_WSE"
                )

            if "depth_m" in g.columns and g["depth_m"].notna().any():
                ax_r.plot(
                    g["datetime_LST"], g["depth_m"],
                    lw=lw, ls="--", color=depth_color, zorder=z,
                    label=station_label_base + "_DEPTH"
                )

    ax.margins(x=0)
    panel_title = site_display_name.get(str(site_id), str(site_id))
    ax.set_title(panel_title, fontsize=10)

    ax.set_ylabel("Water Surface Elevation (m)")
    ax_r.set_ylabel("Depth (m)")

    # --- add padding so legend doesn't overlap lines ---
    ax.margins(x=0, y=0.20)      # ~12% vertical padding on left axis
    ax_r.margins(x=0, y=0.20)    # same for right axis (twin)

    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.grid(True, alpha=0.25)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax_r.get_legend_handles_labels()
    if l1 or l2:
        ax.legend(h1 + h2, l1 + l2, fontsize=6.5, loc="upper left", frameon=False)


# ---- figure layout (Chesapeake left, Erie right) ----
regions = {
    "Lake Erie": ["CRC", "PTR", "OWC"],
    "Chesapeake Bay": ["SWH", "GCW", "MSM", "GWI"]}

left_key, right_key = "Lake Erie", "Chesapeake Bay"
left_sites, right_sites = regions[left_key], regions[right_key]
nrows = max(len(left_sites), len(right_sites))

site_display_name = {
    "CRC": "Crane Creek",
    "PTR": "Portage River",
    "OWC": "Old Woman Creek",
    "SWH": "Sweethall Marsh",
    "GCW": "GCReW Marsh",
    "MSM": "Moneystump Marsh",
    "GWI": "Goodwin Island",
}

fig, axes = plt.subplots(
    nrows=nrows,
    ncols=2,
    figsize=(18, 3.6 * nrows),
    sharex=False,
    constrained_layout=True,
)

axes[0, 0].set_title(region_label_for_sites(left_sites, left_key), fontsize=12, pad=12)
axes[0, 1].set_title(region_label_for_sites(right_sites, right_key), fontsize=12, pad=12)

for r in range(nrows):
    ax = axes[r, 0]
    if r < len(left_sites):
        site_id = left_sites[r]
        df = pd.read_csv(COMBINED_GAUGE_DIR / f"{site_id}_combined_gauge_swe_v04_outlierrej.csv")
        plot_site_panel(ax, site_id, df, stations_meta, lw=0.55)
    else:
        ax.axis("off")

for r in range(nrows):
    ax = axes[r, 1]
    if r < len(right_sites):
        site_id = right_sites[r]
        df = pd.read_csv(COMBINED_GAUGE_DIR / f"{site_id}_combined_gauge_swe_v04_outlierrej.csv")
        plot_site_panel(ax, site_id, df, stations_meta, lw=0.55)
    else:
        ax.axis("off")

fig.set_constrained_layout_pads(w_pad=0.01, h_pad=0.01, wspace=0.02, hspace=0.02)
fig.suptitle("Water surface elevation or depth", y=0.995)
fig.tight_layout()
plt.show()

#%% Save to file ----------------------------------------------------
out_png = f"{FIG_DIR}/ts/synoptic_gauges_val_ref_v05.png"
mm_to_in = 1 / 25.4
fig.set_size_inches(290 * mm_to_in, 320 * mm_to_in)
fig.savefig(out_png, dpi=300, bbox_inches="tight")