
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MLB Pitching Analytics",
    page_icon="⚾",
    layout="wide",
)

DATA_FILE = (
    Path(__file__).resolve().parent
    / "data/curated/pitcher_summary.parquet"
)

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
def load_data():
    return pd.read_parquet(DATA_FILE)


st.title("⚾ MLB Pitching Analytics")
st.caption("June 2025 | MLB Statcast | Pitch-level analytics")

if not DATA_FILE.exists():
    st.error("Curated dataset not found. Run the data pipeline.")
    st.stop()

df = load_data()

# Create a pitcher lookup keyed by MLB player ID.
pitchers = (
    df[["pitcher_id", "player_name"]]
    .drop_duplicates(subset=["pitcher_id"])
    .sort_values("player_name")
)

pitcher_options = {
    int(row.pitcher_id): row.player_name
    for row in pitchers.itertuples(index=False)
}

st.sidebar.header("Pitcher Selection")

selected_id = st.sidebar.selectbox(
    "Select a pitcher",
    options=list(pitcher_options.keys()),
    format_func=lambda pid: pitcher_options[pid],
)

min_pitches = st.sidebar.slider(
    "Minimum pitches per pitch type",
    min_value=1,
    max_value=100,
    value=20,
)

pitcher_df = df[df["pitcher_id"] == selected_id].copy()

pitcher_name = pitcher_options[selected_id]

pitcher_df["pitch_name"] = (
    pitcher_df["pitch_type"]
    .map(PITCH_NAMES)
    .fillna(pitcher_df["pitch_type"])
)

total_pitches = int(pitcher_df["pitches"].sum())
total_swings = int(pitcher_df["swings"].sum())
total_whiffs = int(pitcher_df["whiffs"].sum())

whiff_pct = (
    100 * total_whiffs / total_swings
    if total_swings > 0 else None
)

# Overall CSW is weighted by pitch count.
# The summary stores rounded percentages.
csw_pct = (
    (pitcher_df["csw_pct"] * pitcher_df["pitches"]).sum()
    / total_pitches
    if total_pitches > 0 else None
)

st.header(pitcher_name)

col1, col2, col3 = st.columns(3)

col1.metric("Total Pitches", f"{total_pitches:,}")
col2.metric(
    "Whiff Rate",
    f"{whiff_pct:.1f}%" if whiff_pct is not None else "N/A",
)
col3.metric(
    "CSW%",
    f"{csw_pct:.1f}%" if csw_pct is not None else "N/A",
)

filtered = pitcher_df[
    pitcher_df["pitches"] >= min_pitches
].copy()

if filtered.empty:
    st.warning("No pitch types meet the minimum pitch count.")
    st.stop()

st.subheader("Pitch Mix")

mix = filtered.sort_values(
    "usage_pct", ascending=False
).set_index("pitch_name")

st.bar_chart(mix["usage_pct"], y_label="Usage (%)")

st.subheader("Average Velocity by Pitch Type")

velocity = filtered.sort_values(
    "avg_velocity", ascending=False
).set_index("pitch_name")

st.bar_chart(
    velocity["avg_velocity"],
    y_label="Velocity (mph)",
)

st.subheader("Pitch Effectiveness")

display_df = filtered[
    [
        "pitch_name",
        "pitches",
        "usage_pct",
        "avg_velocity",
        "avg_spin",
        "whiff_pct",
        "league_whiff_pct",
        "csw_pct",
        "league_csw_pct",
    ]
].copy()

display_df.columns = [
    "Pitch Type",
    "Pitches",
    "Usage %",
    "Avg Velocity",
    "Avg Spin",
    "Whiff %",
    "League Whiff %",
    "CSW %",
    "League CSW %",
]

st.dataframe(
    display_df,
    hide_index=True,
    width="stretch",
)

st.divider()

st.caption(
    "Source: MLB Statcast via Baseball Savant. "
    "League benchmarks reflect June 2025 only. "
    "Whiff% = misses / swings; "
    "CSW% = called strikes + misses / eligible pitches."
)
