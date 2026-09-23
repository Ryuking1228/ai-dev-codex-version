"""Apply immutable SQL migrations transactionally; refuse edited applied migrations."""
import hashlib
import os
from pathlib import Path
import psycopg


def migrate():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(61472621)")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, checksum text NOT NULL)")
        for path in sorted((Path(__file__).resolve().parents[1] / "migrations").glob("*.sql")):
            sql = path.read_text()
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            previous = conn.execute("SELECT checksum FROM schema_migrations WHERE name = %s", (path.name,)).fetchone()
            if previous:
                if previous[0] != checksum:
                    raise RuntimeError(f"Applied migration changed: {path.name}")
                continue
            conn.execute(sql)
            conn.execute("INSERT INTO schema_migrations VALUES (%s, %s)", (path.name, checksum))


if __name__ == "__main__":
    migrate()
