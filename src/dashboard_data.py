
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"

PITCH_NAMES = {
    "FF": "Four-Seam Fastball",
    "SI": "Sinker",
    "SL": "Slider",
    "CH": "Changeup",
    "FC": "Cutter",
    "ST": "Sweeper",
    "CU": "Curveball",
    "FS": "Splitter",
    "KC": "Knuckle Curve",
    "SV": "Slurve",
    "EP": "Eephus",
    "FA": "Fastball",
    "CS": "Slow Curve",
    "KN": "Knuckleball",
    "FO": "Forkball",
}


@st.cache_data
def load_pitcher_overall():
    return pd.read_parquet(
        CURATED / "pitcher_overall.parquet"
    )


@st.cache_data
def load_pitcher_summary():
    return pd.read_parquet(
        CURATED / "pitcher_summary.parquet"
    )


def get_pitcher_options(overall_df):
    pitchers = overall_df.sort_values("player_name")

    return {
        int(row.pitcher_id): row.player_name
        for row in pitchers.itertuples(index=False)
    }


def add_pitch_names(df):
    result = df.copy()
    result["pitch_name"] = (
        result["pitch_type"]
        .map(PITCH_NAMES)
        .fillna(result["pitch_type"])
    )
    return result
