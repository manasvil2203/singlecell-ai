import sqlite3
import pandas as pd
from pathlib import Path


DB_PATH = Path("data/clinical_luad.db")


def run_query(query: str, db_path=DB_PATH) -> pd.DataFrame:
    """
    Execute a read-only SQL query on the clinical database
    and return the results as a pandas DataFrame.
    """
    cleaned_query = query.strip()

    if not cleaned_query.lower().startswith(("select", "with")):
        raise ValueError("Only read-only SELECT queries are allowed.")

    with sqlite3.connect(db_path) as conn:
        results = pd.read_sql_query(cleaned_query, conn)

    return results

def get_database_schema(db_path=DB_PATH) -> str:
    """
    Inspect a SQLite database and return its tables and columns
    as a readable schema string.
    """

    schema_lines = []

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        tables = cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        for (table_name,) in tables:
            columns = cursor.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall()

            column_definitions = [
                f"{column[1]} {column[2]}"
                for column in columns
            ]

            schema_lines.append(
                f"{table_name}({', '.join(column_definitions)})"
)


    return "\n".join(schema_lines)

if __name__ == "__main__":

    query = """
    SELECT DISTINCT vital_status
    FROM patients;
    """

    df = run_query(query)

    print(df)