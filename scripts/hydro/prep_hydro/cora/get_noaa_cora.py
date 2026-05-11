

from src.elm_coastal_forcing.prep_hydro.get_cora import fetch_long_timeseries, summarize
from scripts.config import SITE_CODE_LIST



STATION_ID = "8761724"   # Grand Isle, LA
START_DATE = "20150301"
END_DATE   = "20151031"
DATUM      = "MSL"
UNITS      = "metric"
OUTPUT_CSV = "wse_output.csv"  # set to None to skip saving

df = fetch_long_timeseries(
    station_id = STATION_ID,
    start_date = START_DATE,
    end_date   = END_DATE,
    datum      = DATUM,
    units      = UNITS,
)

summarize(df)

print(df.head(10))

if OUTPUT_CSV and not df.empty:
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[INFO] Saved to {OUTPUT_CSV}")