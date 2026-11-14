
from pathlib import Path

import pandas as pd
from pybaseball import statcast

# Project configuration
START_DATE = "2025-06-01"
END_DATE = "2025-06-30"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "statcast_2025_06.parquet"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Statcast data: {START_DATE} to {END_DATE}")

    df = statcast(
        start_dt=START_DATE,
        end_dt=END_DATE,
        verbose=True,
    )

    if df.empty:
        raise RuntimeError("No Statcast data returned.")

    print(f"Downloaded {len(df):,} pitches")
    print(f"Columns: {len(df.columns)}")
    print(f"Unique pitchers: {df['pitcher'].nunique():,}")

    # Normalize date and preserve all source columns
    df["game_date"] = pd.to_datetime(df["game_date"])

    # Write raw data to Parquet
    df.to_parquet(
        OUTPUT_FILE,
        engine="pyarrow",
        index=False,
        compression="zstd",
    )

    print(f"Saved to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024**2:.2f} MB")

    print("\nSample records:")
    print(
        df[
            ["game_date", "player_name", "pitch_type",
             "release_speed", "description"]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()
