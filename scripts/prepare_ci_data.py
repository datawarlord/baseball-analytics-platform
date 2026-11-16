
"""Create deterministic curated Statcast fixtures for CI."""

import argparse
from pathlib import Path

import pandas as pd


def make_pitch(
    year, month, pitcher_id, player_name,
    pitch_type, game_pk, speed, spin,
    swing=0, whiff=0, called=0, eligible=1,
):
    return {
        "reporting_year": year,
        "reporting_month": month,
        "pitcher_id": pitcher_id,
        "player_name": player_name,
        "pitch_type": pitch_type,
        "game_pk": game_pk,
        "release_speed": speed,
        "release_spin_rate": spin,
        "is_swing": swing,
        "is_whiff": whiff,
        "is_called_strike": called,
        "is_csw": int(whiff or called),
        "is_eligible_pitch": eligible,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory for synthetic pitch_details partitions",
    )
    args = parser.parse_args()

    rows = [
        # June: Pitcher A, fastballs
        make_pitch(2025, 6, 101, "Pitcher A",
                   "FF", 1001, 90.0, 2200,
                   swing=1, whiff=1),
        make_pitch(2025, 6, 101, "Pitcher A",
                   "FF", 1001, 94.0, 2400,
                   called=1),

        # June: Pitcher A, slider
        make_pitch(2025, 6, 101, "Pitcher A",
                   "SL", 1002, 84.0, 2500,
                   swing=1),

        # June: Pitcher B, fastball
        make_pitch(2025, 6, 202, "Pitcher B",
                   "FF", 1003, 96.0, 2300,
                   swing=1, whiff=1),

        # July: Pitcher A, fastballs
        make_pitch(2025, 7, 101, "Pitcher A",
                   "FF", 2001, 98.0, 2600,
                   swing=1, whiff=1),
        make_pitch(2025, 7, 101, "Pitcher A",
                   "FF", 2001, None, 2500,
                   called=1),
        make_pitch(2025, 7, 101, "Pitcher A",
                   "FF", 2002, 100.0, None,
                   swing=1),

        # July: Pitcher A, slider
        make_pitch(2025, 7, 101, "Pitcher A",
                   "SL", 2002, 86.0, 2700,
                   swing=1, whiff=1),

        # July: Pitcher B
        make_pitch(2025, 7, 202, "Pitcher B",
                   "FF", 2003, 95.0, 2350,
                   called=1),
        make_pitch(2025, 7, 202, "Pitcher B",
                   "SL", 2003, 85.0, 2450,
                   swing=1, whiff=1),

        # Must be excluded from aggregates
        make_pitch(2025, 7, 101, "Pitcher A",
                   "FF", 2002, 110.0, 3000,
                   swing=1, whiff=1, eligible=0),
    ]

    df = pd.DataFrame(rows)

    for (year, month), group in df.groupby(
        ["reporting_year", "reporting_month"]
    ):
        partition = (
            args.output
            / f"year={year}"
            / f"month={month:02d}"
        )
        partition.mkdir(parents=True, exist_ok=True)

        group.to_parquet(
            partition / "pitches.parquet",
            index=False,
        )

    print(
        f"Created {len(df)} synthetic pitches "
        f"across 2 months in {args.output}"
    )


if __name__ == "__main__":
    main()
