
import calendar

import pandas as pd
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
    page_title="Pitcher Comparison",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ Pitcher Comparison")
st.caption("Head-to-head MLB pitching analysis | Statcast")

# --------------------------------------------------
# Load monthly datasets
# --------------------------------------------------

monthly_overall = load_monthly_overall()
monthly_summary = load_monthly_summary()

periods = available_periods(monthly_overall)

if not periods:
    st.warning("No reporting periods are available.")
    st.stop()


def period_label(period):
    year, month = period
    return f"{calendar.month_name[month]} {year}"


# --------------------------------------------------
# Reporting period selection
# --------------------------------------------------

st.subheader("Reporting Period")

selected_periods = st.multiselect(
    "Select months to compare",
    options=periods,
    default=periods,
    format_func=period_label,
)

if not selected_periods:
    st.warning("Select at least one reporting month.")
    st.stop()

filtered_overall = filter_period(
    monthly_overall,
    selected_periods,
)
filtered_summary = filter_period(
    monthly_summary,
    selected_periods,
)

overall = aggregate_overall(filtered_overall)
summary = aggregate_summary(filtered_summary)

if overall.empty:
    st.warning("No pitchers found for the selected period.")
    st.stop()

period_description = ", ".join(
    period_label(period)
    for period in sorted(selected_periods)
)

st.caption(f"Selected reporting periods: {period_description}")

# --------------------------------------------------
# Pitcher selection
# --------------------------------------------------

pitcher_options = get_pitcher_options(overall)
ids = list(pitcher_options.keys())

if len(ids) < 2:
    st.warning(
        "At least two pitchers are required for comparison."
    )
    st.stop()

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
        index=1,
        format_func=lambda pid: pitcher_options[pid],
    )

if pitcher_a_id == pitcher_b_id:
    st.warning("Select two different pitchers.")
    st.stop()

a = overall.loc[
    overall["pitcher_id"] == pitcher_a_id
].iloc[0]

b = overall.loc[
    overall["pitcher_id"] == pitcher_b_id
].iloc[0]

name_a = a["player_name"]
name_b = b["player_name"]


def format_metric(value, fmt):
    if pd.isna(value):
        return "N/A"
    return fmt.format(value)


# --------------------------------------------------
# Overall performance
# --------------------------------------------------

st.divider()
st.subheader("Overall Performance")

metrics = [
    ("Total Pitches", "total_pitches", "{:,.0f}"),
    ("Games", "games", "{:,.0f}"),
    ("Swing Rate", "swing_pct", "{:.1f}%"),
    ("Whiff Rate", "whiff_pct", "{:.1f}%"),
    ("CSW%", "csw_pct", "{:.1f}%"),
    ("Average Velocity", "avg_velocity", "{:.1f} mph"),
    ("Average Spin", "avg_spin", "{:,.0f} rpm"),
]

comparison = pd.DataFrame({
    "Metric": [m[0] for m in metrics],
    name_a: [
        format_metric(a[m[1]], m[2])
        for m in metrics
    ],
    name_b: [
        format_metric(b[m[1]], m[2])
        for m in metrics
    ],
})

st.dataframe(
    comparison,
    hide_index=True,
    width="stretch",
)

st.caption(
    "Rates are recalculated from combined event counts. "
    "Average velocity and spin are weighted by their "
    "respective non-null observation counts."
)

# --------------------------------------------------
# Pitch type data
# --------------------------------------------------

a_types = add_pitch_names(
    summary.loc[
        summary["pitcher_id"] == pitcher_a_id
    ].copy()
)

b_types = add_pitch_names(
    summary.loc[
        summary["pitcher_id"] == pitcher_b_id
    ].copy()
)

# --------------------------------------------------
# Pitch mix comparison
# --------------------------------------------------

st.divider()
st.subheader("Pitch Mix Comparison")

mix_a = a_types.set_index("pitch_name")["usage_pct"]
mix_b = b_types.set_index("pitch_name")["usage_pct"]

mix = pd.concat(
    [
        mix_a.rename(name_a),
        mix_b.rename(name_b),
    ],
    axis=1,
).fillna(0)

if mix.empty:
    st.info("No pitch mix data is available.")
else:
    mix = mix.sort_index()

    st.bar_chart(
        mix,
        y_label="Usage (%)",
    )

st.caption(
    "Pitch usage represents the percentage of each "
    "pitcher's total pitches in the selected period."
)

# --------------------------------------------------
# Detailed pitch type comparison
# --------------------------------------------------

st.divider()
st.subheader("Pitch Type Details")

detail_columns = [
    "pitch_name",
    "pitches",
    "usage_pct",
    "avg_velocity",
    "avg_spin",
    "whiff_pct",
    "csw_pct",
]


def prepare_pitch_details(df, pitcher_name):
    result = df[detail_columns].copy()
    result.insert(0, "Pitcher", pitcher_name)

    return result.rename(columns={
        "pitch_name": "Pitch Type",
        "pitches": "Pitches",
        "usage_pct": "Usage %",
        "avg_velocity": "Avg Velocity (mph)",
        "avg_spin": "Avg Spin (rpm)",
        "whiff_pct": "Whiff %",
        "csw_pct": "CSW %",
    })


details = pd.concat(
    [
        prepare_pitch_details(a_types, name_a),
        prepare_pitch_details(b_types, name_b),
    ],
    ignore_index=True,
)

if details.empty:
    st.info("No pitch type details are available.")
else:
    st.dataframe(
        details.sort_values(
            ["Pitch Type", "Pitcher"]
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Usage %": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
            "Avg Velocity (mph)": (
                st.column_config.NumberColumn(
                    format="%.1f"
                )
            ),
            "Avg Spin (rpm)": (
                st.column_config.NumberColumn(
                    format="%.0f"
                )
            ),
            "Whiff %": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
            "CSW %": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
        },
    )

# --------------------------------------------------
# Pitch effectiveness versus league
# --------------------------------------------------

st.divider()
st.subheader("Pitch Effectiveness vs. League")

st.caption(
    "Positive values indicate a higher rate than the "
    "league average for the same pitch type across "
    "the selected reporting periods."
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


def league_relative(df, pitcher_name):
    filtered = df.loc[
        df["pitches"] >= min_pitches
    ].copy()

    filtered["vs_league"] = (
        filtered[actual_col]
        - filtered[league_col]
    )

    return (
        filtered.set_index("pitch_name")["vs_league"]
        .rename(pitcher_name)
    )


relative = pd.concat(
    [
        league_relative(a_types, name_a),
        league_relative(b_types, name_b),
    ],
    axis=1,
)

if relative.dropna(how="all").empty:
    st.warning(
        "No pitch types meet the selected threshold."
    )
else:
    relative = relative.sort_index()

    st.bar_chart(
        relative,
        y_label="Percentage points vs. league",
    )

st.caption(
    "League comparisons are pitch-type-specific. "
    "Whiff rate is whiffs divided by swings. "
    "CSW% is called strikes plus swinging strikes "
    "divided by total pitches."
)

st.divider()
st.caption(
    "Source: MLB Statcast via Baseball Savant. "
    f"Reporting periods: {period_description}."
)
