
import pandas as pd
import streamlit as st

from src.dashboard_data import (
    load_pitcher_overall,
    load_pitcher_summary,
    get_pitcher_options,
    add_pitch_names,
)

st.set_page_config(
    page_title="Pitcher Comparison",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ Pitcher Comparison")
st.caption("Head-to-head MLB pitching analysis | June 2025")

overall = load_pitcher_overall()
summary = load_pitcher_summary()

pitcher_options = get_pitcher_options(overall)
ids = list(pitcher_options.keys())

left, right = st.columns(2)

with left:
    pitcher_a_id = st.selectbox(
        "Pitcher A",
        ids,
        index=0,
        format_func=lambda pid: pitcher_options[pid],
    )

with right:
    pitcher_b_id = st.selectbox(
        "Pitcher B",
        ids,
        index=min(1, len(ids) - 1),
        format_func=lambda pid: pitcher_options[pid],
    )

if pitcher_a_id == pitcher_b_id:
    st.warning("Select two different pitchers.")
    st.stop()

a = overall[overall["pitcher_id"] == pitcher_a_id].iloc[0]
b = overall[overall["pitcher_id"] == pitcher_b_id].iloc[0]

st.subheader("Overall Performance")

metrics = [
    ("Total Pitches", "total_pitches", "{:,.0f}"),
    ("Games", "games", "{:,.0f}"),
    ("Whiff Rate", "whiff_pct", "{:.1f}%"),
    ("CSW%", "csw_pct", "{:.1f}%"),
    ("Average Velocity", "avg_velocity", "{:.1f} mph"),
    ("Average Spin", "avg_spin", "{:,.0f} rpm"),
]

comparison = pd.DataFrame({
    "Metric": [m[0] for m in metrics],
    a["player_name"]: [
        m[2].format(a[m[1]]) for m in metrics
    ],
    b["player_name"]: [
        m[2].format(b[m[1]]) for m in metrics
    ],
})

st.dataframe(
    comparison,
    hide_index=True,
    width="stretch",
)

st.divider()
st.subheader("Pitch Mix Comparison")

a_types = add_pitch_names(
    summary[summary["pitcher_id"] == pitcher_a_id]
)
b_types = add_pitch_names(
    summary[summary["pitcher_id"] == pitcher_b_id]
)

mix_a = a_types.set_index("pitch_name")["usage_pct"]
mix_b = b_types.set_index("pitch_name")["usage_pct"]

mix = pd.concat(
    [mix_a.rename(a["player_name"]),
     mix_b.rename(b["player_name"])],
    axis=1,
).fillna(0)

st.bar_chart(
    mix,
    y_label="Usage (%)",
)

st.divider()
st.subheader("Pitch Effectiveness vs. League")

st.caption(
    "Positive values indicate performance above the "
    "June 2025 league average for that pitch type."
)

min_pitches = st.slider(
    "Minimum pitches per pitch type",
    min_value=1,
    max_value=150,
    value=30,
)

metric = st.radio(
    "Compare metric",
    ["Whiff Rate", "CSW%"],
    horizontal=True,
)

if metric == "Whiff Rate":
    actual_col = "whiff_pct"
    league_col = "league_whiff_pct"
else:
    actual_col = "csw_pct"
    league_col = "league_csw_pct"


def league_relative(df, name):
    filtered = df[df["pitches"] >= min_pitches].copy()

    filtered["vs_league"] = (
        filtered[actual_col] - filtered[league_col]
    )

    return filtered.set_index("pitch_name")[
        "vs_league"
    ].rename(name)


relative = pd.concat(
    [
        league_relative(a_types, a["player_name"]),
        league_relative(b_types, b["player_name"]),
    ],
    axis=1,
)

if relative.dropna(how="all").empty:
    st.warning("No pitch types meet the selected threshold.")
else:
    st.bar_chart(
        relative,
        y_label="Percentage points vs. league",
    )

st.caption(
    "Source: MLB Statcast via Baseball Savant. "
    "Results cover June 2025 only. "
    "League comparisons are pitch-type-specific."
)
