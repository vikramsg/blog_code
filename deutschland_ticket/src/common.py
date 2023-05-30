import sqlite3
from pathlib import Path


def city_table_connection(table_name: str) -> sqlite3.Connection:
    db_path = Path(".").resolve() / "data" / "cities.sqlite"
    conn = sqlite3.connect(db_path)

    # FIXME: Connection should not be responsible for this
    # We should wrap our orchestrators in test so that we can
    # change these with confidence
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    return conn
