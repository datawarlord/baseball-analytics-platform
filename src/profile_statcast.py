
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "statcast_2025_06.parquet"


def main():
    df = pd.read_parquet(DATA_FILE)

    print("\n=== DATASET OVERVIEW ===")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Pitchers: {df['pitcher'].nunique():,}")
    print(f"Games: {df['game_pk'].nunique():,}")
    print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")

    print("\n=== NULL ANALYSIS ===")
    nulls = (
        df.isna()
        .mean()
        .mul(100)
        .sort_values(ascending=False)
    )
    print(nulls.head(25).round(2).to_string())

    print("\n=== PITCH TYPES ===")
    print(df["pitch_type"].value_counts(dropna=False).to_string())

    print("\n=== PITCH DESCRIPTIONS ===")
    print(df["description"].value_counts(dropna=False).to_string())

    print("\n=== PLATE APPEARANCE EVENTS ===")
    print(df["events"].value_counts(dropna=False).to_string())

    print("\n=== KEY UNIQUENESS ===")
    key = ["game_pk", "at_bat_number", "pitch_number"]

    duplicates = df.duplicated(subset=key).sum()
    print(f"Duplicate pitch keys: {duplicates:,}")

    print("\n=== IMPORTANT FIELD COMPLETENESS ===")
    fields = [
        "pitcher",
        "player_name",
        "pitch_type",
        "release_speed",
        "release_spin_rate",
        "plate_x",
        "plate_z",
        "description",
        "events",
        "launch_speed",
    ]

    for field in fields:
        populated = df[field].notna().mean() * 100
        print(f"{field:25} {populated:6.2f}% populated")


if __name__ == "__main__":
    main()
