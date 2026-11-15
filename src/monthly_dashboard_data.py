
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"

@st.cache_data
def _read_parquet(path: str, modified_time: int):
    return pd.read_parquet(path)

# @st.cache_data
def load_monthly_summary():
    path = CURATED / "pitcher_summary_monthly.parquet"
    df = _read_parquet(str(path), path.stat().st_mtime_ns)

    df["reporting_year"] = df["reporting_year"].astype(int)
    df["reporting_month"] = df["reporting_month"].astype(int)
    return df


# @st.cache_data
def load_monthly_overall():
    path = CURATED / "pitcher_overall_monthly.parquet"
    df = _read_parquet(str(path), path.stat().st_mtime_ns)

    df["reporting_year"] = df["reporting_year"].astype(int)
    df["reporting_month"] = df["reporting_month"].astype(int)

    return df

def available_periods(df):
    periods = (
        df[["reporting_year", "reporting_month"]]
        .drop_duplicates()
        .sort_values(
            ["reporting_year", "reporting_month"]
        )
    )

    return [
        (int(row.reporting_year), int(row.reporting_month))
        for row in periods.itertuples(index=False)
    ]

def filter_period(df, selected_periods):
    """
    Filter monthly data using normalized year/month values.
    """

    if not selected_periods:
        return df.iloc[0:0].copy()

    selected = {
        (int(year), int(month))
        for year, month in selected_periods
    }

    years = df["reporting_year"].astype(int)
    months = df["reporting_month"].astype(int)

    period_keys = list(zip(years, months))

    mask = [
        period in selected
        for period in period_keys
    ]

    return df.loc[mask].copy()


def aggregate_overall(df):
    result = (
        df.groupby("pitcher_id", as_index=False)
        .agg(
            player_name=("player_name", "first"),
            total_pitches=("total_pitches", "sum"),
            games=("games", "sum"),
            swings=("swings", "sum"),
            whiffs=("whiffs", "sum"),
            called_strikes=("called_strikes", "sum"),
            csw_events=("csw_events", "sum"),
            velocity_sum=("velocity_sum", "sum"),
            velocity_count=("velocity_count", "sum"),
            spin_sum=("spin_sum", "sum"),
            spin_count=("spin_count", "sum"),
        )
    )

    result["avg_velocity"] = (
        result["velocity_sum"]
        / result["velocity_count"].replace(0, float("nan"))
    ).round(1)

    result["avg_spin"] = (
        result["spin_sum"]
        / result["spin_count"].replace(0, float("nan"))
    ).round(0)

    result["swing_pct"] = (
        100 * result["swings"]
        / result["total_pitches"]
    ).round(1)

    result["whiff_pct"] = (
        100 * result["whiffs"]
        / result["swings"].replace(0, float("nan"))
    ).round(1)

    result["csw_pct"] = (
        100 * result["csw_events"]
        / result["total_pitches"]
    ).round(1)

    return result


def aggregate_summary(df):
    """
    Aggregate monthly pitch-type data across selected periods.

    Recalculate rates from counts rather than averaging
    monthly percentages.
    """

    # League counts repeat for each pitcher within a month.
    # Keep one record per month and pitch type.
    league = (
        df[
            [
                "reporting_year",
                "reporting_month",
                "pitch_type",
                "league_pitches",
                "league_swings",
                "league_whiffs",
                "league_csw_events",
            ]
        ]
        .drop_duplicates(
            subset=[
                "reporting_year",
                "reporting_month",
                "pitch_type",
            ]
        )
        .groupby("pitch_type", as_index=False)
        .agg(
            league_pitches=("league_pitches", "sum"),
            league_swings=("league_swings", "sum"),
            league_whiffs=("league_whiffs", "sum"),
            league_csw_events=("league_csw_events", "sum"),
        )
    )

    # Aggregate individual pitcher statistics.
    pitcher = (
        df.groupby(
            ["pitcher_id", "pitch_type"],
            as_index=False,
        )
        .agg(
            player_name=("player_name", "first"),
            pitches=("pitches", "sum"),
            swings=("swings", "sum"),
            whiffs=("whiffs", "sum"),
            csw_events=("csw_events", "sum"),
            velocity_sum=("velocity_sum", "sum"),
            velocity_count=("velocity_count", "sum"),
            spin_sum=("spin_sum", "sum"),
            spin_count=("spin_count", "sum"),
        )
    )

    pitcher["avg_velocity"] = (
        pitcher["velocity_sum"]
        / pitcher["velocity_count"].replace(0, float("nan"))
    ).round(1)

    pitcher["avg_spin"] = (
        pitcher["spin_sum"]
        / pitcher["spin_count"].replace(0, float("nan"))
    ).round(0)
    
    # Calculate total pitches for each pitcher.
    pitcher["total_pitches"] = (
        pitcher.groupby("pitcher_id")["pitches"]
        .transform("sum")
    )

    pitcher["usage_pct"] = (
        100 * pitcher["pitches"]
        / pitcher["total_pitches"]
    ).round(1)

    pitcher["whiff_pct"] = (
        100 * pitcher["whiffs"]
        / pitcher["swings"].replace(0, float("nan"))
    ).round(1)

    pitcher["csw_pct"] = (
        100 * pitcher["csw_events"]
        / pitcher["pitches"]
    ).round(1)

    result = pitcher.merge(
        league,
        on="pitch_type",
        how="left",
    )

    result["league_whiff_pct"] = (
        100 * result["league_whiffs"]
        / result["league_swings"].replace(
            0, float("nan")
        )
    ).round(1)

    result["league_csw_pct"] = (
        100 * result["league_csw_events"]
        / result["league_pitches"]
    ).round(1)

    return result
