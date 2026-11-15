
import streamlit as st

from src.dashboard_data import (
    get_pitcher_options,
    add_pitch_names,
)

from src.monthly_dashboard_data import (
    load_monthly_overall,
    load_monthly_summary,
    available_periods,
    filter_period,
    aggregate_overall,
    aggregate_summary,
)

st.set_page_config(
    page_title="MLB Pitching Analytics",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ MLB Pitching Analytics")

# Load monthly data.
try:
    monthly_overall = load_monthly_overall()
    monthly_summary = load_monthly_summary()
except FileNotFoundError:
    st.error(
        "Monthly datasets not found. "
        "Run build_monthly_aggregates.py."
    )
    st.stop()

# Reporting-period selection.
periods = available_periods(monthly_overall)

period_labels = {
    (year, month): f"{year}-{month:02d}"
    for year, month in periods
}

selected_periods = st.sidebar.multiselect(
    "Reporting Period",
    options=periods,
    default=periods,
    format_func=lambda p: period_labels[p],
    key="reporting_period",
)

if not selected_periods:
    st.warning("Select at least one reporting period.")
    st.stop()

# Filter both datasets to the selected months.
filtered_overall = filter_period(
    monthly_overall,
    selected_periods,
)

filtered_summary = filter_period(
    monthly_summary,
    selected_periods,
)

# Aggregate across selected periods.
overall = aggregate_overall(filtered_overall)
summary = aggregate_summary(filtered_summary)

st.caption(
    "Reporting periods: "
    + ", ".join(period_labels[p] for p in selected_periods)
    + " | MLB Statcast | Pitcher Explorer"
)

# Pitcher selection.

# Normalize pitcher IDs to integers.
overall["pitcher_id"] = overall["pitcher_id"].astype(int)
summary["pitcher_id"] = summary["pitcher_id"].astype(int)

pitcher_options = get_pitcher_options(overall)

st.sidebar.header("Pitcher Selection")

# Only show pitchers available in the selected periods.
available_ids = list(pitcher_options.keys())

if not available_ids:
    st.warning(
        "No pitchers found for the selected reporting periods."
    )
    st.stop()

# Reset the selection if the previously selected pitcher
# isn't available in the current reporting period.
if (
    "selected_pitcher_id" in st.session_state
    and st.session_state.selected_pitcher_id
    not in available_ids
):
    del st.session_state["selected_pitcher_id"]

selected_id = st.sidebar.selectbox(
    "Select a pitcher",
    options=available_ids,
    format_func=lambda pid: pitcher_options[pid],
    key="selected_pitcher_id",
)


min_pitches = st.sidebar.slider(
    "Minimum pitches per pitch type",
    min_value=1,
    max_value=100,
    value=20,
)

pitcher_rows = overall[
    overall["pitcher_id"] == selected_id
]

if pitcher_rows.empty:
    st.error(
        f"No data found for pitcher ID {selected_id} "
        "in the selected reporting periods."
    )
    st.stop()

pitcher = pitcher_rows.iloc[0]

pitch_types = add_pitch_names(
    summary[summary["pitcher_id"] == selected_id]
)

st.header(pitcher["player_name"])

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Pitches",
    f"{pitcher['total_pitches']:,}",
)

col2.metric(
    "Whiff Rate",
    f"{pitcher['whiff_pct']:.1f}%",
)

col3.metric(
    "CSW%",
    f"{pitcher['csw_pct']:.1f}%",
)

filtered = pitch_types[
    pitch_types["pitches"] >= min_pitches
].copy()

if filtered.empty:
    st.warning(
        "No pitch types meet the minimum pitch count."
    )
    st.stop()

st.subheader("Pitch Mix")

mix = filtered.sort_values(
    "usage_pct", ascending=False
).set_index("pitch_name")

st.bar_chart(
    mix["usage_pct"],
    y_label="Usage (%)",
)

st.subheader("Pitch Effectiveness")

display_df = filtered[
    [
        "pitch_name",
        "pitches",
        "usage_pct",
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
    "Whiff% = misses / swings; "
    "CSW% = called strikes + misses / eligible pitches."
)
