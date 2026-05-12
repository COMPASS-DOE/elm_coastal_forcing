# Prep VECOS data


from pathlib import Path
import pandas as pd
from scripts.config import DATA_DIR
from scripts.dataio import load_vecos_gage_data

VECOS_DIR = DATA_DIR/'tide_gauges/vecos/annual/'


# Make ouptut dir if needed
VECOS_COMB_DIR = DATA_DIR/'tide_gauges/vecos/combined/'
VECOS_COMB_DIR.mkdir(exist_ok=True)

# collect files by identifier (text before first underscore)
groups = {}
for file in VECOS_DIR.iterdir():
    station_id = file.name.split("_", 2)[0]
    if station_id == '.DS': continue
    groups.setdefault(station_id, []).append(file)


# Loop through groups and combine files
for station_id, files in groups.items():
    print(f"Processing station {station_id} with {len(files)} files.")
    dfs = []
    for f in files:
        # df = pd.read_csv(f)
        df = load_vecos_gage_data(f)
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)


    # Drop exact duplicate rows
    before = len(combined)
    combined = combined.drop_duplicates()
    after = len(combined)
    print(f"  Dropped {before - after} duplicate rows")


    # Save to file
    combined.to_csv(VECOS_COMB_DIR / f"{station_id}_2018_2025.csv", index=False)





# combined = combined[["STATION", "SAMPLE_DATETIME", "DEPTH", "DEPTH_FLAG", "DEPTH_UNITS","DEPTH_A",
#                      "SALINITY", "SALINITY_FLAG", "SALINITY_UNITS", "SALINITY_A"]]

# combined = combined[["STATION", "SAMPLE_DATETIME", "DEPTH"]]

# combined = combined.rename(columns={"STATION": "station_id", 
#                                     "SAMPLE_DATETIME": "datetime_LST"})
