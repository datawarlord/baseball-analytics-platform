
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = (
    PROJECT_ROOT
    / "data/raw/statcast_2025_06.parquet"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data/curated/pitch_details.parquet"
)

SQL_FILE = (
    PROJECT_ROOT
    / "sql/01_curate_pitches.sql"
)


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(RAW_FILE)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    sql = SQL_FILE.read_text(encoding="utf-8")

    # Our own controlled template, not user input.
    raw_path = RAW_FILE.as_posix().replace("'", "''")
    sql = sql.replace("{{RAW_FILE}}", raw_path)

    with duckdb.connect(":memory:") as con:
        con.execute(
            "CREATE TEMP TABLE curated AS " + sql
        )

        row_count = con.execute(
            "SELECT COUNT(*) FROM curated"
        ).fetchone()[0]

        duplicates = con.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT (
                game_pk,
                at_bat_number,
                pitch_number
            ))
            FROM curated
        """).fetchone()[0]

        if duplicates:
            raise ValueError(
                f"Found {duplicates} duplicate pitch keys"
            )

        if row_count == 0:
            raise ValueError("Curated table is empty")

        con.execute(
            "COPY curated TO ? "
            "(FORMAT PARQUET, COMPRESSION ZSTD)",
            [str(OUTPUT_FILE)]
        )

        eligible = con.execute("""
            SELECT SUM(is_eligible_pitch)
            FROM curated
        """).fetchone()[0]

    print(f"Source records: {row_count:,}")
    print(f"Eligible pitches: {eligible:,}")
    print(f"Duplicate keys: {duplicates:,}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
