"""
STEP 2 - Create the database tables and load the sample data into PostgreSQL.

Run it with:
    backend/.venv/Scripts/python backend/scripts/seed_database.py

What it does, in order:

1. Runs backend/database/schema.sql, which drops and recreates all tables.
2. Loads every CSV file from the data/ folder into its matching table.
3. Prints a row count for each table so you can see it worked.

Because step 1 drops the tables, running this script again simply gives you
a clean database with the same data. That is what you want while
prototyping.

If the data/ folder is empty, run generate_data.py first.
"""

import csv
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import connect  # noqa: E402

PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_FILE = BACKEND_DIR / "database" / "schema.sql"

# CSV file -> table name. The order matters: a table must be loaded after
# any table it points to, otherwise the foreign keys fail.
LOAD_ORDER = [
    ("skills.csv",          "skills"),
    ("workers.csv",         "workers"),
    ("worker_skills.csv",   "worker_skills"),
    ("contractors.csv",     "contractors"),
    ("crews.csv",           "crews"),
    ("crew_members.csv",    "crew_members"),
    ("jobs.csv",            "jobs"),
    ("job_assignments.csv", "job_assignments"),
    ("ratings.csv",         "ratings"),
    ("availability.csv",    "availability"),
]


def load_csv(cursor, filename: str, table: str) -> int:
    """Insert every row of one CSV file into one table."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing. Run generate_data.py first."
        )

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)

    if not rows:
        return 0

    column_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    statement = f"insert into {table} ({column_list}) values ({placeholders})"

    # An empty cell in a CSV means "no value", which in SQL is NULL.
    values = [
        tuple(row[column] if row[column] != "" else None for column in columns)
        for row in rows
    ]

    cursor.executemany(statement, values)
    return len(values)


def main() -> int:
    print("ADAA - creating tables and loading sample data")
    print("-" * 50)

    try:
        with connect() as conn:
            with conn.cursor() as cur:
                print("Creating tables from schema.sql ...")
                cur.execute(SCHEMA_FILE.read_text(encoding="utf-8"))

                print("Loading data:")
                for filename, table in LOAD_ORDER:
                    count = load_csv(cur, filename, table)
                    print(f"  {table:<26} {count:>5} rows")

            conn.commit()

            # Read the counts back from the database itself, so we are
            # confirming what is actually stored, not what we think we sent.
            print("-" * 50)
            print("Verified in the database:")
            with conn.cursor() as cur:
                for _, table in LOAD_ORDER:
                    cur.execute(f"select count(*) from {table}")
                    print(f"  {table:<26} {cur.fetchone()[0]:>5} rows")

    except Exception as error:
        print("FAILED:", type(error).__name__)
        print(" ", str(error)[:500])
        return 1

    print("-" * 50)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
