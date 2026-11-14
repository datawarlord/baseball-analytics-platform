
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data/curated/pitch_details.parquet"

file_path = FILE.as_posix().replace("'", "''")

with duckdb.connect(":memory:") as con:

    con.execute(
        f"CREATE VIEW pitches AS "
        f"SELECT * FROM read_parquet('{file_path}')"
    )

    results = con.execute("""
        SELECT
            COUNT(*) AS total_rows,
            SUM(is_eligible_pitch) AS eligible_pitches,
            SUM(is_swing * is_eligible_pitch) AS swings,
            SUM(is_whiff * is_eligible_pitch) AS whiffs,
            SUM(is_csw * is_eligible_pitch) AS csw,
            COUNT(DISTINCT pitcher_id) AS pitchers
        FROM pitches
    """).fetchone()

    print("Total rows:", results[0])
    print("Eligible pitches:", results[1])
    print("Swings:", results[2])
    print("Whiffs:", results[3])
    print("CSW events:", results[4])
    print("Pitchers:", results[5])

    assert results[0] == 115816
    assert results[5] == 552
    assert results[3] <= results[2]
    assert results[4] <= results[1]

    print("Validation passed!")
