
import streamlit as st

st.set_page_config(
    page_title="Baseball Analytics",
    page_icon="⚾",
    layout="wide",
)

st.title("⚾ Baseball Analytics Platform")
st.caption("Exploring MLB pitching performance with Statcast data")

st.info("Milestone 1: Application skeleton. Real data coming soon!")

st.sidebar.header("Filters")
pitcher = st.sidebar.selectbox(
    "Select a pitcher",
    ["Sample Pitcher A", "Sample Pitcher B"],
)

st.subheader(f"Pitching Overview: {pitcher}")

col1, col2, col3 = st.columns(3)

col1.metric("Total Pitches", "1,245")
col2.metric("Average Velocity", "95.2 mph")
col3.metric("Strikeout Rate", "28.4%")

st.subheader("Pitch Mix")
st.bar_chart({
    "Four-Seam Fastball": 45,
    "Slider": 30,
    "Changeup": 15,
    "Curveball": 10,
})

st.caption("All values are illustrative sample data, not actual MLB statistics.")
st.divider()
st.markdown("**Data source (planned):** MLB Statcast via Baseball Savant")
