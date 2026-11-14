
import streamlit as st

from src.dashboard_data import (
    load_pitcher_overall,
    load_pitcher_summary,
    get_pitcher_options,
    add_pitch_names,
)

st.set_page_config(
    page_title="MLB Pitching Analytics",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ MLB Pitching Analytics")
st.caption("June 2025 | MLB Statcast | Pitcher Explorer")

try:
    overall = load_pitcher_overall()
    summary = load_pitcher_summary()
except FileNotFoundError:
    st.error("Curated datasets not found. Run the data pipeline.")
    st.stop()

pitcher_options = get_pitcher_options(overall)

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

pitcher = overall[
    overall["pitcher_id"] == selected_id
].iloc[0]

pitch_types = add_pitch_names(
    summary[summary["pitcher_id"] == selected_id]
)

st.header(pitcher["player_name"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Pitches", f"{pitcher['total_pitches']:,}")
col2.metric("Games", f"{pitcher['games']:,}")
col3.metric("Whiff Rate", f"{pitcher['whiff_pct']:.1f}%")
col4.metric("CSW%", f"{pitcher['csw_pct']:.1f}%")

filtered = pitch_types[
    pitch_types["pitches"] >= min_pitches
].copy()

if filtered.empty:
    st.warning("No pitch types meet the minimum pitch count.")
    st.stop()

st.subheader("Pitch Mix")

mix = filtered.sort_values(
    "usage_pct", ascending=False
).set_index("pitch_name")

st.bar_chart(mix["usage_pct"], y_label="Usage (%)")

st.subheader("Average Velocity")

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

st.caption(
    "Source: MLB Statcast via Baseball Savant. "
    "June 2025 only. Whiff% = misses / swings; "
    "CSW% = called strikes + misses / eligible pitches."
)

from pathlib import Path

with st.sidebar.expander("Deployment Diagnostics"):
    app_dir = Path(__file__).resolve().parent
    pages_dir = app_dir / "pages"

    st.write("App directory:", str(app_dir))
    st.write("Pages directory exists:", pages_dir.exists())
    st.write(
        "Page files:",
        [p.name for p in pages_dir.glob("*.py")]
    )