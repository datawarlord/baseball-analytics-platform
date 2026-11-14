from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data/curated/pitcher_summary.parquet"

with duckdb.connect(":memory:") as con:
    results = con.execute("""
        SELECT
            pitcher_id,
            player_name,
            ROUND(SUM(usage_pct), 1) AS total_usage
        FROM read_parquet(?)
        GROUP BY pitcher_id, player_name
        HAVING ABS(SUM(usage_pct) - 100) > 0.5
    """, [str(FILE)]).fetchdf()

    print(results.to_string(index=False))

    if results.empty:
        print("Validation passed! All pitchers have approximately 100% pitch usage.")