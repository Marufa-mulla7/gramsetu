"""Merge raw Agmarknet Excel reports into one clean daily tomato price file."""
import glob
import pandas as pd

RAW_GLOB = "data/Daily*Price*Report-*.xlsx"
OUT_FILE = "data/tomato_daily.csv"

frames = []
for path in sorted(glob.glob(RAW_GLOB)):
    df = pd.read_excel(path, header=1)  # row 0 is just a title
    print(f"Read {len(df):>6} rows from {path}")
    frames.append(df)

data = pd.concat(frames, ignore_index=True)
total = len(data)

data["date"] = pd.to_datetime(data["Price Date"], format="%d-%m-%Y")
data = data.drop_duplicates()

# Cleaning rules: drop rows that are clearly data-entry mistakes
valid = (
    (data["Modal Price"] >= 200)                  # a few rows show prices like Rs 5/quintal
    & (data["Min Price"] <= data["Modal Price"])  # min <= modal <= max must hold
    & (data["Modal Price"] <= data["Max Price"])
)
data = data[valid]
print(f"Removed {total - len(data)} bad rows, kept {len(data)}")

# One row per day: median modal price across all Karnataka markets
daily = (
    data.groupby("date")
    .agg(price=("Modal Price", "median"), markets=("Market", "nunique"))
    .reset_index()
)
daily.to_csv(OUT_FILE, index=False)

print(f"\nSaved {len(daily)} days to {OUT_FILE}")
print(f"Date range: {daily['date'].min().date()} to {daily['date'].max().date()}")
print(daily.tail())