
import os
from pathlib import Path

import duckdb
import pytest


ROOT = Path(__file__).resolve().parents[1]

CURATED = Path(
    os.environ.get(
        "BASEBALL_CURATED_DIR",
        str(ROOT / "data" / "curated"),
    )
)

OVERALL = CURATED / "pitcher_overall_monthly.parquet"
SUMMARY = CURATED / "pitcher_summary_monthly.parquet"


@pytest.fixture(scope="module")
def con():
    if not OVERALL.exists() or not SUMMARY.exists():
        pytest.fail("Monthly aggregates are missing")

    connection = duckdb.connect(":memory:")

    overall_path = OVERALL.as_posix().replace("'", "''")
    summary_path = SUMMARY.as_posix().replace("'", "''")

    connection.execute(
        f"CREATE VIEW overall AS "
        f"SELECT * FROM read_parquet('{overall_path}')"
    )

    connection.execute(
        f"CREATE VIEW summary AS "
        f"SELECT * FROM read_parquet('{summary_path}')"
    )
    yield connection
    connection.close()


def test_ineligible_pitches_excluded(con):
    total = con.execute("""
        SELECT SUM(total_pitches)
        FROM overall
    """).fetchone()[0]

    assert total == 10


def test_pitcher_a_monthly_counts(con):
    rows = con.execute("""
        SELECT
            reporting_month,
            total_pitches,
            games
        FROM overall
        WHERE pitcher_id = 101
        ORDER BY reporting_month
    """).fetchall()

    assert rows == [
        (6, 3, 2),
        (7, 4, 2),
    ]


def test_null_velocity_excluded_from_average(con):
    row = con.execute("""
        SELECT
            velocity_sum,
            velocity_count,
            avg_velocity
        FROM summary
        WHERE pitcher_id = 101
          AND reporting_month = 7
          AND pitch_type = 'FF'
    """).fetchone()

    assert row[0] == pytest.approx(198.0)
    assert row[1] == 2
    assert row[2] == pytest.approx(99.0)


def test_null_spin_excluded_from_average(con):
    row = con.execute("""
        SELECT
            spin_sum,
            spin_count,
            avg_spin
        FROM summary
        WHERE pitcher_id = 101
          AND reporting_month = 7
          AND pitch_type = 'FF'
    """).fetchone()

    assert row[0] == pytest.approx(5100.0)
    assert row[1] == 2
    assert row[2] == pytest.approx(2550.0)


def test_weighted_fastball_velocity(con):
    row = con.execute("""
        SELECT
            SUM(velocity_sum) / NULLIF(
                SUM(velocity_count), 0
            )
        FROM summary
        WHERE pitcher_id = 101
          AND pitch_type = 'FF'
    """).fetchone()

    # Four non-null velocities: 90, 94, 98, 100
    assert row[0] == pytest.approx(95.5)


def test_combined_whiff_rate_uses_counts(con):
    row = con.execute("""
        SELECT
            SUM(whiffs),
            SUM(swings),
            100.0 * SUM(whiffs)
                / NULLIF(SUM(swings), 0)
        FROM overall
        WHERE pitcher_id = 101
    """).fetchone()

    # Three whiffs from five swings
    assert row[0] == 3
    assert row[1] == 5
    assert row[2] == pytest.approx(60.0)
