# Prep VECOS data


import os
from pathlib import Path
import pandas as pd
import glob


from scripts.config import DATA_DIR, SITE_CODE_LIST
from scripts.dataio import load_nerrs_gage_data
NERRS_DIR = DATA_DIR/'tide_gauges/nerrs/synoptic/'


# Make ouptut dir if needed
NERRS_COMB_DIR = DATA_DIR/'tide_gauges/nerrs/combined/'
NERRS_COMB_DIR.mkdir(exist_ok=True)


nerrs_files = glob.glob(os.path.join(NERRS_DIR, "*.csv")) # [0]


groups = {}
for f in nerrs_files:
    import re
    stem = os.path.basename(f).split(".")[0]
    file_id = re.split(r"\d", stem, maxsplit=1)[0]
    if file_id == 'sampling_stations': continue
    groups.setdefault(file_id, []).append(f)


# Loop through groups and combine files
for station_id, files in groups.items():
    print(f"Processing station {station_id} with {len(files)} files.")
    dfs = []
    for f in files:
        df = pd.read_csv(f) 
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    
    combined.to_csv(NERRS_COMB_DIR / f"{station_id}_2019_2025.csv", index=False)