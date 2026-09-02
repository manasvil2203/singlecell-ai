import sqlite3
from pathlib import Path


DB_PATH = Path("data/clinical_luad.db")
SCHEMA_PATH = Path("data/schema.sql")


def build_database() -> None:
    """Create the clinical metadata SQLite database from schema.sql."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())

    print(f"Created database: {DB_PATH}")


if __name__ == "__main__":
    build_database()