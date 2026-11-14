
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/curated/pitch_details.parquet"
OUTPUT_FILE = ROOT / "data/curated/pitcher_overall.parquet"
SQL_FILE = ROOT / "sql/03_pitcher_overall.sql"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    sql = SQL_FILE.read_text(encoding="utf-8")

    input_path = INPUT_FILE.as_posix().replace("'", "''")
    sql = sql.replace("{{CURATED_FILE}}", input_path)

    with duckdb.connect(":memory:") as con:
        con.execute("CREATE TEMP TABLE summary AS " + sql)

        results = con.execute("""
            SELECT
                COUNT(*) AS pitchers,
                SUM(total_pitches) AS pitches,
                MIN(total_pitches) AS min_pitches,
                MAX(total_pitches) AS max_pitches
            FROM summary
        """).fetchone()

        duplicates = con.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT pitcher_id)
            FROM summary
        """).fetchone()[0]

        if duplicates:
            raise ValueError(
                f"Duplicate pitcher IDs found: {duplicates}"
            )

        if results[0] != 552:
            raise ValueError(
                f"Expected 552 pitchers, found {results[0]}"
            )

        if results[1] != 115240:
            raise ValueError(
                f"Expected 115240 eligible pitches, found {results[1]}"
            )

        con.execute(
            "COPY summary TO ? "
            "(FORMAT PARQUET, COMPRESSION ZSTD)",
            [str(OUTPUT_FILE)]
        )

    print("\n=== PITCHER OVERALL SUMMARY ===")
    print(f"Pitchers: {results[0]:,}")
    print(f"Eligible pitches: {results[1]:,}")
    print(f"Fewest pitches: {results[2]:,}")
    print(f"Most pitches: {results[3]:,}")
    print(f"Duplicate pitcher IDs: {duplicates}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
